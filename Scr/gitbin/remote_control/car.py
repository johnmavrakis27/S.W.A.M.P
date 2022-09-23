import cv2
from cvtool import CVTool
# from wall import Wall
# from pillar import Pillar
# from line import Line
from microbit import Microbit
# import jetson.inference
import RPi.GPIO as GPIO
import time
import sys
from datetime import datetime
import signal 
import threading

GPIO_IN1 = 37
GPIO_IN2 = 38
GPIO_ENA = 32
GPIO_ENCODER = 35

class Car:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        self.cvtool = CVTool(use_cam=True)
        self.microbit = Microbit()
        # self.net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
        GPIO.setup(GPIO_ENA, GPIO.OUT, initial=GPIO.HIGH)
        self.throttle = GPIO.PWM(channel=GPIO_ENA, frequency_hz=1000)
        self.in1 = GPIO_IN1
        GPIO.setup(self.in1, GPIO.OUT, initial=GPIO.LOW)
        self.in2 = GPIO_IN2
        GPIO.setup(self.in2, GPIO.OUT, initial=GPIO.LOW)
        self.throttle.start(0)
        self.speed = 0
        self.stop()
        self.stopped = True
        GPIO.setup(GPIO_ENCODER, GPIO.IN)
        self.ticks = 0
        GPIO.add_event_detect(GPIO_ENCODER, GPIO.FALLING, 
            callback=self.encoder_callback)
        self.last_tick_ns = 0
        self.tick_delay_target = 0

    def encoder_callback(self, channel):
        self.last_tick_ns = time.time() * 1000000
        self.ticks += 1
        

    def set_direction(self, forward=True):
        if not forward:
            GPIO.output(GPIO_IN1, GPIO.HIGH)
            GPIO.output(GPIO_IN2, GPIO.LOW)
        else:
            GPIO.output(GPIO_IN1, GPIO.LOW)
            GPIO.output(GPIO_IN2, GPIO.HIGH)
        self.stopped = False

    def stop(self):
        GPIO.output(GPIO_IN1, GPIO.LOW)
        GPIO.output(GPIO_IN2, GPIO.LOW)
        self.stopped = True

    def signal_handler(sig, frame):
        GPIO.cleanup()
        sys.exit(0)

    def set_speed(self, speed=None):
        # self.stopped = False
        # self.set_direction(True)
        # if speed is not None:
        #     self.speed = speed
        # if self.speed >= 0:
        #     self.set_direction(True)
        # elif self.speed < 0:
        #     self.set_direction(False)

        self.throttle.ChangeDutyCycle(abs(speed))

    def _t_control_speed(self, speed=80):
        self.speed = speed
        kp = 0.4
        kd = 100
        ki = 0
        target = 30
        previous_ns = 0
        derivative = 0
        integral = 0
        previous_error = 0
        self.tick_delay_target = int(1000000 / (20 * self.speed / 60))
        self.set_direction()
        while True:
            try:
                current_ns = time.time() * 1000000
                if current_ns - previous_ns > 0.005:
                    previous_ns = current_ns
                    delta_time = current_ns - self.last_tick_ns
                    error = delta_time - self.tick_delay_target 
                    derivative = (error - previous_error) #/ delta_time
                    integral = integral + error #* delta_time
                    u = max(0, kp * error + kd * derivative + ki * integral)
                    current_speed = max(17, min(100, abs(u)))
                    self.set_speed(speed=current_speed)
                    time.sleep(0.005)
            except:
                self.stop()
                break
            

    def remote_control(self, folder_path=None):
        self.cvtool.open_cam()
        self.microbit = Microbit()
        
        if folder_path == None:
            now = datetime.now()
            dt_string = now.strftime("%d_%m_%Y_%H_%M")
            folder_path = "images_" + dt_string
        dir_structure = self.cvtool.create_steering_folders(folder_path)
        print(dir_structure)
        time.sleep(1)
        counter = 0
        dir_number = 0

        speed_thread = threading.Thread(target=self._t_control_speed, args=(80, ))

        in_data = self.microbit.get_data()
        print("waiting mb")
        while in_data is None or in_data[0] != 1:
            in_data = self.microbit.get_data()
        print("GO!")
        speed_thread.start()
        self.set_direction()
        while True:
            in_data = self.microbit.get_data()

            if self.cvtool.camera_is_open():
                _, img = self.cvtool.camera.read()
                #cv2.imshow("Image",img)
                key = cv2.waitKey(1) & 0xFF
                if in_data is not None:
                    print(in_data)
                    if len(in_data) == 2 and in_data[0] == 7:
                        steering = in_data[1]
                        structure = dir_structure["train"]
                        if dir_number == 9 or dir_number == 8:
                            # 20% of images in val directory
                            structure = dir_structure["val"]
                        elif dir_number == 10:
                            # 10% of images in test directory
                            structure = dir_structure["test"]
                            dir_number = 0
                        dir_number += 1
                        for dir, steer_range in structure.items():
                            if steer_range[0] <= steering <= steer_range[1]:
                                filename = dir + "/img_" + str(counter) + ".png"                            
                                cv2.imwrite(filename, img)
                                print("Image saved with name ", filename)
                                counter += 1
                                break
                    
                    elif in_data[0] == 2:
                        # print("stop")
                        if self.stopped:
                            self.set_direction()
                        else:
                            self.stop()
                    elif in_data[0] == 3:
                        # print("speed up")
                        self.speed = min(300, self.speed + 10)
                        self.tick_delay_target = int(1000000 / (20 * self.speed / 60))
                    elif in_data[0] == 4:
                        # print("speed down")
                        self.speed = max(1, self.speed - 10) # SOS: zero devision case is speed == 0
                        self.tick_delay_target = int(1000000 / (20 * self.speed / 60))
                    elif in_data[0] == 5:
                        print("exit!")
                        self.stop()
                        break
        cv2.destroyAllWindows()


            
    # def run(self):
    #     self.cvtool.open_cam() 
    #     run = True
    #     while run:
    #         _, frame = self.cvtool.camera.read()
    #         detections = self.net.Detect(frame)
    #         print(detections)
    #         # direction = self.dir_from_lines(frame)
    #         # if direction != 0:
    #         #     self.microbit.send_data([3, direction])

def main():
    car = Car()
    car.stop()
    # time.sleep(5)
    try:
        car.remote_control()
    except KeyboardInterrupt:
        print("This is the end!!!")
    # speed = 0
    # for i in range(5):
    #     speed += 10
    #     print(speed)
    #     car.move(speed)
    #     time.sleep(3)        
    # car.stop()
    # print("Stopped")
    # print("Ticks", car.ticks)
    # print("Rotations: ", car.ticks / 20)

    # signal.signal(signal.SIGINT, car.signal_handler)
    # signal.pause()

if __name__ == "__main__":
    main()
    