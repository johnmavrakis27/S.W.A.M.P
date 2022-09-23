from microbit import *
from utime import ticks_ms
import gc
import radio

RADIO_CHANNEL = 8
SPEED_PIN = pin0
STEER_PIN = pin2
HIT_PIN = pin1

def map(value, in_min, in_max, out_min, out_max):
    scaled_value = (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(scaled_value)

class Joystick:
    def __init__(self):
        self.speed_controller = SPEED_PIN
        self.steer_controller = STEER_PIN
        self.hit_button = HIT_PIN
        self.hit_button.set_pull(self.hit_button.PULL_UP)
        self.speed_changed = False
        self.current_steer = 0
        self.last_steer_msg = ticks_ms()
        self.last_speed_msg = ticks_ms()
        self.last_stop_msg = ticks_ms()
        self.steer_delay = 150
        self.speed_delay = 100
        self.stop_delay = 500
        radio.config(group=RADIO_CHANNEL, length=8, power=7)
        radio.on()  

    def control_speed(self, upper_threshold=700, lower_threshold=100):
        current_ms = ticks_ms()
        if current_ms - self.last_speed_msg > self.speed_delay:
            analog_value = self.speed_controller.read_analog()
            if analog_value > upper_threshold:
                radio.send("FAST")            
                # print("FAST")    
                display.show("F")
            elif analog_value < lower_threshold:
                radio.send("SLOW")
                # print("SLOW")
                display.show("S")
            self.last_speed_msg = current_ms

    def control_steer(self, min_change=5):
        current_ms = ticks_ms()
        if current_ms - self.last_steer_msg > self.steer_delay:
            analog_value = self.steer_controller.read_analog()
            steer_value = map(analog_value, 0, 1023, -100, 100)
            if abs(steer_value) > min_change:
                self.current_steer = steer_value
                display.show("N")
                radio.send(str(self.current_steer))
                # print(str(self.current_steer))
            self.last_steer_msg = current_ms

    def control_stop(self):
        current_ms = ticks_ms()
        if joystick.hit_button.read_digital() == 0 and current_ms - self.last_stop_msg > self.stop_delay:
            radio.send("STOP")
            display.show("S")
            self.last_stop_msg = current_ms

joystick = Joystick()
display.show("H")
while joystick.hit_button.read_digital():
    # print(joystick.hit_button.read_digital())
    sleep(20)
radio.send("GO")
display.show("G")
sleep(500)
while True:
    joystick.control_speed()
    joystick.control_steer()
    joystick.control_stop()
    if button_a.is_pressed():
        radio.send("END")
        break
display.show(Image.HEART)
    
    