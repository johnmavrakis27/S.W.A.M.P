import RPi.GPIO as GPIO
from modules.button import Button
from modules.oled import OLED
from modules.line2turn import Line2Turn
from modules.color import Color
from modules.microbit import Microbit
from statistics import median
import time
import logging
import os
import jetson.inference
import sys
import jetson.utils
from json import loads
import threading
import cv2

GPIO_IN1 = 37
GPIO_IN2 = 38
GPIO_ENA = 32
GPIO_ENCODER = 35

BUTTON_UP_GPIO = 18
BUTTON_DOWN_GPIO = 12
BUTTON_CENTER_GPIO = 16

class Car:
    def __init__(self, level=logging.DEBUG, cnf_file="cnf.txt", net=None):
        project_path = os.path.dirname(os.path.realpath(__file__))
        self.cnf_file = os.path.join(project_path, cnf_file) 
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)

        # Create objects
        self.button_up = Button(BUTTON_UP_GPIO)
        self.button_down = Button(BUTTON_DOWN_GPIO)
        self.button_center = Button(BUTTON_CENTER_GPIO) 
        self.oled = OLED()
        self.line2turn = Line2Turn(cnf_file=self.cnf_file)        
        self.color = Color()
        # self.compass = Compass(self.cnf_file)
        self.microbit = Microbit()
        self.video_source = jetson.utils.videoSource("csi://0")
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
        # Useful properties
        self.run_direction = 0
        # Configure log file
        log_file_path = os.path.dirname(__file__) + "/logfile.log"
        logging.basicConfig(filename=log_file_path,
                            format="%(asctime)s %(message)s",
                            filemode='w')
        self.logger = logging.getLogger()
        self.logger.setLevel(level)
        # if net is not None:
        #     self.logger.debug("Load network")
        #     #print("net path", os.path.join(path, net))
        net_path = os.path.join(project_path, "resnet18.onnx")
        labels_path = os.path.join(project_path, "labels.txt")
        # print("net_path:", net_path)
        # print("labels path", labels_path)
        # net = jetson.inference.imageNet(model="model/resnet18.onnx", labels="model/labels.txt", 
        #     input_blob="input_0", output_blob="output_0")
        self.net = jetson.inference.imageNet(argv=['--model=' + net_path, '--labels=' + labels_path, '--input-blob=input_0', '--output_blob=output_0'])
        # self.net = jetson.inference.imageNet(model=net_path, labels=labels_path, 
        #     input_blob="input_0", output_blob="output_0")
        self.logger.debug("net loaded ...")
        self.servo_positions = {}
        self.load_labels()
        self.round_direction = 0
        self.running = True

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
        self.throttle.ChangeDutyCycle(abs(speed))

    def _t_control_speed(self, speed=80):
        self.speed = speed
        kp = 0.4
        kd = 100
        ki = 0
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

    
    def run_1(self):
        self.run_2()
        

    def run_2_debug(self, image_dir="images"):
        # self.cvtool.open_cam() 
        path = os.path.dirname(os.path.realpath(__file__))
        image_dir = os.path.join(path, image_dir)
        valids = invalids = 0 
        for file in os.listdir(image_dir):
            if file.endswith(".png"):
                image = jetson.utils.loadImage(os.path.join(image_dir, file)) 
                print("Start:", time.time())
                # classify the image
                class_idx, confidence = self.net.Classify(image)
                # find the object description
                class_desc = self.net.GetClassDesc(class_idx)
                # print out the result
                print("image is recognized as '{:s}' (class #{:d}) with {:f}% confidence".format(class_desc, class_idx, confidence * 100))
                print("End:", time.time())
                steering = self.parse_class(class_desc)
                
                img = jetson.utils.cudaToNumpy(image, 640, 480, 3)
                cv2.putText(img, "steering: " + str(steering), (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 1)
                cv2.imshow("Image", img)
                cv2.waitKey(0)

    def run_2(self, speed=100, rounds=3):
        speed_thread = threading.Thread(target=self._t_control_speed, args=(80, ))
        current_round = 0
        loop = 0
        speed_thread.start()
        self.set_direction()
        while current_round < rounds:
            image = self.video_source.Capture() 
            print("Start:", time.time())
            # classify the image
            class_idx, confidence = self.net.Classify(image)
            # find the object description
            class_desc = self.net.GetClassDesc(class_idx)
            # print out the result
            print("image is recognized as '{:s}' (class #{:d}) with {:f}% confidence".format(class_desc, class_idx, confidence * 100))
            print("End:", time.time())
            steering = self.parse_class(class_desc)
            
            img = jetson.utils.cudaToNumpy(image, 640, 480, 3)
            # cv2.imshow("Image", img)
            # cv2.waitKey(0)
            self.microbit.send_data([1, steering])
            self.logger.debug(f"Steering: {steering}")
            
            # cv2.putText(img, "steering: " + str(steering), (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 1)            
            # cv2.imwrite("images/frame_" + str(loop) + ".png", img)


    def parse_class(self, class_desc, class_name=None):
        if class_desc is None or class_desc == "":
            return 0
        steering_edges = class_desc.split('_')
        if len(steering_edges) == 2:
            try:
                first_num = int(steering_edges[0])
                second_num = int(steering_edges[1])
                steering = (first_num + second_num) // 2
                if steering > 0 and class_name[0] == '-':
                    return steering
            except:
                return 0


    def _t_read_lines(self, lines_to_pass=12):
        lines_passed = 0
        while lines_to_pass < lines_passed:
            line = self.line2turn.detect_line()
            if line != 0:
                if self.round_direction == 0:
                    self.round_direction = line
                    
                if line == self.round_direction:
                    self.lines_passed += 1
                    time.sleep(0.5)
        self.running = False

    def calibrate_lines(self):
        color_names = self.color.lines.keys()
        for color_name in color_names:
            hmin = 359
            smin = vmin = 255
            hmax = smax = vmax = 0
            while not self.button_down.is_pressed():
                hsv = self.color.read_hsv()
                txt_list = []
                txt_list.append("CENTER to keep value")
                txt_list.append("DOWN for next color")
                txt_list.append("MIN: " + str(hmin) + " " + str(smin) + " " +  str(vmin))
                txt_list.append("MIN: " + str(hmax) + " " + str(smax) + " " +  str(vmax))
                txt_list.append(str(hsv))
                txt_list.append("Calibrate " + color_name)
                self.oled.show_text_list(txt_list)
                if self.button_center.is_pressed():
                    if hsv[0] < hmin:
                        hmin = hsv[0]
                    if hsv[1] < smin:
                        smin = hsv[1]
                    if hsv[2] < vmin:
                        vmin = hsv[2]
                    if hsv[0] > hmax:
                        hmax = hsv[0]
                    if hsv[1] > smax:
                        smax = hsv[1]
                    if hsv[2] > vmax:
                        vmax = hsv[2]
            txt_list= []
            txt_list.append("CENTER to save to file")
            txt_list.append("UP to ignore values")
            txt_list.append("Color: " + color_name)
            txt_list.append("MIN: " + str(hmin) + " " + str(smin) + " " +  str(vmin))
            txt_list.append("MIN: " + str(hmax) + " " + str(smax) + " " +  str(vmax))
            self.oled.show_text_list(txt_list)
            while True:
                if self.button_up.is_pressed():
                    txt_list= []
                    txt_list.append(color_name + " calibration canceled")
                    txt_list.append("Wait 2\"")
                    self.oled.show_text_list(txt_list)
                    break
                if self.button_center.is_pressed():
                    self.color.lines[color_name]['hmin'] = hmin
                    self.color.lines[color_name]['hmax'] = hmax
                    self.color.lines[color_name]['smin'] = smin
                    self.color.lines[color_name]['smax'] = smax
                    self.color.lines[color_name]['vmin'] = vmin
                    self.color.lines[color_name]['vmax'] = vmax
                    self.color.write_cnf_file(color_name)
                    txt_list= []
                    txt_list.append(color_name + " calibration saved")
                    txt_list.append("Wait 2\"")
                    self.oled.show_text_list(txt_list)
                    break

    def load_labels(self):
        path = os.path.dirname(os.path.realpath(__file__))
        labels_file_dir = os.path.join(path, "labels.txt") 
        with open(labels_file_dir, 'r') as f:
            for line in f:
                line = line[:-1]
                # print(line)
                edges = line.split('_')
                if edges is not None and len(edges) == 2:
                    steering_value = int((int(edges[0]) + int(edges[1])) // 2 + 1)
                    self.servo_positions[line] = steering_value

def main():
    # NET = "models/cat_dog"
    car = Car()
    car.load_labels()
    car.run_2()


if __name__== "__main__":
    main()
