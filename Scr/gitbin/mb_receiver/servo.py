from microbit import *

def map(value, in_min, in_max, out_min, out_max):
    scaled_value = (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(scaled_value)

class Servo:
    # Servo control: 
    # 50 = ~1 millisecond pulse all right 
    # 75 = ~1.5 millisecond pulse center 
    # 100 = ~2.0 millisecond pulse all left 
    def __init__(self, pin=pin8, filename='cnf.txt'):
        self.servo_pin = pin
        self.servo_pin.set_analog_period(20)
        self.cnf_file = filename
        self.left_duty = 50
        self.right_duty = 85
        self.forward_duty = 70 
        self.read_cnf_file()
        self.steering(0)
        self.current_steer = 0
        
    def steering(self, steer=0):
        self.duty = map(steer, -100, 100, self.left_duty, self.right_duty)
        self.servo_pin.write_analog(self.duty)
        self.current_steer = steer

    def smooth_steering(self, new_steer=0, max_angle=5):
        angle = new_steer - self.current_steer
        if abs(angle) > max_angle:
            smooth_steer = int(self.current_steer + max_angle * (angle/abs(angle)))
        else:
            smooth_steer = new_steer
        self.steering(smooth_steer)

    def _steering_duty(self, duty):
        self.duty = duty
        self.servo_pin.write_analog(self.duty)

    def read_cnf_file(self):
        with open(self.cnf_file, 'r') as f:
            txt = f.read()
            lines = txt.split('\n')
            for line in lines:
                if 'servo' in line:
                    servo_data = line.split(', ')
                    self.left_duty = int(servo_data[1])
                    self.forward_duty = int(servo_data[2])
                    self.right_duty = int(servo_data[3])
