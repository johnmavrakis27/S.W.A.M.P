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

    def run(self):
        self.jetson = Jetson()
        display.show('B')
        while True:
            data = self.jetson.get_data()
            if data is not None and data[0] == 1:
                print(data)
                self.servo_motor.smooth_steering(data[1], 10)
                display.show('H')

    

print("test 1")
display.show("y")
car = Car()

car.dc.stop()
display.show("A")
while not button_a.is_pressed():
    pass
car.run()
# print("test 1")
# car.remote_control(take_photos=False, ppm=400)

# car._ticks_counter()
# car.control_speed(30)
sleep(10)
car.count_ticks = False