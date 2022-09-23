from microbit import *
from dc import DC
# from oled import OLED
from servo import Servo
from jetson import Jetson
import music
from utime import ticks_ms, ticks_us, ticks_diff , sleep
import gc
import radio

gc.enable()  # enable automatic memory recycle

notes_A = ['c4:1', 'e', 'g', 'c5', 'g4']
notes_B = ['g4:1', 'c5', 'g', 'e', 'c4']
notes_T = ['d4:2', 'g', 'd5', 'f5', 'g4', 'd5', 'f5', 'b3']

RADIO_CHANNEL = 8

PIN_SERVO = pin12
PIN_IN1 = pin8
PIN_IN2 = pin2
PIN_ENA = pin1

class Car:
    def __init__(self, filename='cnf.txt'):
        self.servo_motor = Servo(pin=PIN_SERVO, filename=filename)
        self.dc = DC(pin_in1=PIN_IN1, pin_in2=PIN_IN2, pin_ena=PIN_ENA, filename=filename)
        self.jetson = None # initialize when you use it
        radio.config(group=RADIO_CHANNEL, length=8, power=7)
        self.speed = 25
        self.last_speed_change_ms = ticks_ms()
        self.last_photo_ms = 0
        self.stop = False
        self.ticks = 0
        self.count_ticks = False

     
    def remote_control(self, ppm=300):
        # jetson messages (commands)
        # 1: start dc
        # 2: stop dc
        # 3: speed up
        # 4: speed down
        # 5: exit
        # 7, #: take photo with steering #
        self.jetson = Jetson()
        photo_delay = 60000 // ppm
        radio.on()
        
        display.show("R")
        start_remote = False
        while not start_remote:
            msg = radio.receive()
            if msg == "GO":
                start_remote = True
        self.jetson.send_data([1]) # start dc
        display.show("R")

        speed = 0
        self.dc.move(speed=self.speed)
        messages = 0
        while start_remote:
            current_ms = ticks_ms()
            msg = str(radio.receive())
            
            if msg == "STOP":
                self.jetson.send_data([2]) # stop dc
                sleep(0.5)
                while True:
                    new_msg = str(radio.receive())
                    if new_msg == "STOP":
                        self.jetson.send_data([2]) # start dc  
                        break
                    elif new_msg == "FAST":
                        self.jetson.send_data([3]) # speed up
                    elif new_msg == "SLOW":
                        self.jetson.send_data([4]) # speed down
                    elif new_msg == "END":
                        self.jetson.send_data([5]) # stop dc
                        self.servo_motor.steering(0)
                        start_remote = False
                        break
                    elif new_msg != "None":
                        try:
                            # print(new_msg)
                            msg_int = int(new_msg)
                            # print(msg_int)
                            self.servo_motor.smooth_steering(new_steer=msg_int, max_angle=15)
                            # self.servo_motor.steering(msg_int)
                        except:
                            print("Invalid msg '" + new_msg + "'")    
                    
            elif msg == "FAST":
                self.jetson.send_data([3]) # speed up
            elif msg == "SLOW":
                self.jetson.send_data([4]) # speed down          
            elif msg == "END":
                self.jetson.send_data([5]) # stop dc
                self.servo_motor.steering(0)
                start_remote = False
            elif msg != "None":
                try:
                    msg_int = int(msg)
                    # print("msg int:", msg_int)
                    self.servo_motor.smooth_steering(new_steer=msg_int, max_angle=20)
                    # self.servo_motor.steering(msg_int)
                except:
                    print("Invalid msg '" + msg + "'")
            if current_ms - self.last_photo_ms > photo_delay:
                self.jetson.send_data([7, self.servo_motor.current_steer])
                self.last_photo_ms = current_ms
                messages += 1
        self.jetson.send_data([2]) # stop dc

print("test 1")
display.show("y")
car = Car()

car.dc.stop()
display.show("A")
while not button_a.is_pressed():
    pass
car.remote_control(300)
# print("test 1")
# car.remote_control(take_photos=False, ppm=400)

# car._ticks_counter()
# car.control_speed(30)
sleep(10)
car.count_ticks = False