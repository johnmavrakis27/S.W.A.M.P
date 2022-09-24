import RPi.GPIO as GPIO
from modules.button import Button
from modules.distance import Distance
from modules.oled import OLED
from modules.line2turn import Line2Turn
from modules.color import Color
from modules.compass import Compass
from modules.camera import Camera
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

TRIGGER_LEFT_GPIO = 22
ECHO_LEFT_GPIO = 24
TRIGGER_RIGHT_GPIO = 26
ECHO_RIGHT_GPIO = 23

BUTTON_UP_GPIO = 18
BUTTON_DOWN_GPIO = 12
BUTTON_CENTER_GPIO = 16

class Car:
    def __init__(self, level=logging.WARNING, cnf_file="cnf.txt", net=None):
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
        self.run_threads = True

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
        kd = 3
        ki = 0
        target = 30
        previous_ns = 0
        derivative = 0
        integral = 0
        previous_error = 0
        self.tick_delay_target = int(1000000 / (20 * self.speed / 60))
        self.set_direction()
        self.run_threads = True
        while self.run_threads:
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

    def menu(self):
        main_options = {}
        cnf_options = {}
        # Run 1 Options
        run1_options = {"GO":1, "BACK":"main_options"}
        # Run 2 Options
        run2_options = {"GO":2, "BACK":"main_options"}
        # Info options
        info_options = {"Read Distances":3, "Read Color":4, "Read Compass":5, "BACK":"main_options"}
        # Configuration options
        cnf_options = {"Calibtate Color":6, "Calibrate Orientation":7, "Calibrate Compass":8, "Get Photos":9, "BACK":"main_options"}
        # Main menu options
        main_options = {"RUN 1":run1_options, "RUN 2":run2_options, "INFO":info_options, "CONFIGURATION":cnf_options}
        
        current_options = main_options
        exit_menu = False
        request = 0
        while not exit_menu:
            selected = 1
            option_list = list(current_options.keys())
            update_display = True
            
            while True:
                if update_display:
                    self.oled.show_text_list(txt_list=option_list, selected=selected)
                    update_display = False
                 
                 
                if self.button_down.is_pressed():
                    print("down")
                    selected += 1
                    if selected >= len(option_list):
                        selected = len(option_list) - 1
                    time.sleep(0.5)
                    update_display = True
                if self.button_up.is_pressed():
                    print("up")
                    selected -= 1
                    if selected < 0:
                        selected = 1
                    time.sleep(0.5)
                    update_display = True
                if self.button_center.is_pressed():
                    option = current_options[option_list[selected]]
                    time.sleep(0.5)
                    if type(option) is dict:
                        # Next level of options
                        current_options = option
                        update_display = True
                        break
                    else:
                        if option_list[selected] == "BACK":
                            if current_options["BACK"] == "main_options":
                                current_options = main_options
                            elif current_options["BACK"] == "cnf_options":
                                current_options = cnf_options
                        request = option
                        exit_menu = True
                        break
        self.run_request(request)

    def run_request(self, request):
        print("Run request: ", request)

        if request == 1:
            self.logger.debug("New request: RUN 1")
        elif request == 2:
            self.logger.debug("New request: RUN 2")
            # self.run_2_debug()
            self.run_2()
        elif request == 3:
            self.logger.debug("New request: Read Distances")
        elif request == 4:
            self.logger.debug("New request: Read Color")
        elif request == 5:
            self.logger.debug("New request: Read Compass")
        elif request == 6:
            self.logger.debug("New request: Calibrate Color Sensor")
            self.calibrate_lines()
        elif request == 7:
            self.logger.debug("New request: Calibrate Orientations")
        elif request == 8:
            self.logger.debug("New request: Calibrate Compass")
            self.callibrate_compass(seconds=60)
        elif request == 9:
            self.logger.debug("New request: Get Photos")
    
        self.menu()
    

    def run_1(self):

        pass

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

    def run_2(self, speed=65, rounds=3):
        speed_thread = threading.Thread(target=self._t_control_speed, args=(speed, ))
        current_round = 0
        loop = 0
        speed_thread.start()
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
            
            # img = jetson.utils.cudaToNumpy(image, 640, 480, 3)
            # cv2.imshow("Image", img)
            # cv2.waitKey(0)
            self.microbit.send_data([1, steering])
            self.logger.warn(f"Steering: {steering}")
            self.logger.warn(class_desc)
            if self.button_down.is_pressed():
                self.run_threads = False
                self.stop()
                self.microbit.send_data([1,0])
                return None
            # cv2.putText(img, "steering: " + str(steering), (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 1)            
            # cv2.imwrite("images/frame_" + str(loop) + ".png", img)


    def parse_class(self, class_desc, class_name=None):
        if class_desc is None or class_desc == "":
            return 0
        steering_edges = class_desc.split('_')
        # self.logger.warn(class_desc)
        # self.logger.warn(steering_edges)
        if len(steering_edges) == 2:
            try:
                first_num = int(steering_edges[0])
                second_num = int(steering_edges[1])
                steering = (first_num + second_num) // 2
                # self.logger.warn(first_num)
                # self.logger.warn(second_num)
                # self.logger.warn(steering)
                # if steering > 0 and class_name[0] == '-':
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
                    if self.round_direction == 1:
                        self.compass.orientations = self.compass.orientations_1
                    else:
                        self.compass.orientations = self.compass.orientations_2
                if line == self.round_direction:
                    self.lines_passed += 1
                    time.sleep(0.5)
        self.running = False

    

    def read_distances(self):
        pass

    def read_color(self):
        pass

    def read_compass(self):
        pass

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

    def calibrate_orientations(self):
        for index in range(4):
            for j in range(2):
                while True:
                    heading = self.compass.heading()
                    txt_list = []
                    txt_list.append(str(self.compass.orientations_1))
                    txt_list.append(str(self.compass.orientations_2))
                    txt_list.append(str(heading))
                    txt_list.append("or_" + str(j+1) + ": CENTER (index:" + str(index) + ")")
                    self.oled.show_text_list(txt_list)
                    if self.button_center.is_pressed():
                        if j == 0:
                            self.compass.orientations_1[index] = heading
                        else:
                            self.compass.orientations_2[index] = heading
                        break
        txt_list = []
        txt_list.append("Cal/ted values:")
        txt_list.append(str(self.compass.orientations_1))
        txt_list.append(str(self.compass.orientations_2))
        txt_list.append("Write: CENTER")
        txt_list.append("Cancel: DOWN")
        self.oled.show_text_list(txt_list)
        while True:
            if self.button_down.is_pressed():
                self.compass.read_cnf_file()
                txt_list = []
                txt_list.append("Calibration canceled")
                self.oled.show_text_list(txt_list)
                break
            if self.button_center.is_pressed():
                self.compass.write_cnf_file()
                txt_list = []
                txt_list.append("Calibration saved")
                self.oled.show_text_list(txt_list)
                break

    def callibrate_compass(self, seconds=60):
        msg = "Press center to start"
        self.oled.show_text(msg)
        self.button_center.wait()
        msg = ["Role the model from all", "over directions", "for " + str(seconds) + " seconds"]
        self.oled.show_text_list(txt_list=msg)
        self.compass.calibrate(seconds)
        msg = ["CENTER: save values", "DOWN: cancel calibration"]        
        self.oled.show_text_list(msg)
        while True:
            if self.button_center.is_pressed():
                self.compass.write_cnf_file()
                msg = ["Compass calibration saved", "Wait 3 seconds ..."]
                time.sleep(3)        
                self.oled.clear()
                break
            if self.button_down.is_pressed():
                msg = ["Compass calibration CANCELED!", "Wait 3 seconds ..."]
                time.sleep(3)        
                self.oled.clear()
                break

    def get_photos(self):
        pass

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
    # image_folder = "mat_images_2/70_100"
    # car.run_2_debug('mat_images/-10_9')
    car.menu()
    # car.calibrate_orientations()
    # car.callibrate_compass()
    # time.sleep(2)


if __name__== "__main__":
    main()
