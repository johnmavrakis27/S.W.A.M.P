from microbit import *

def map(value, in_min, in_max, out_min, out_max):
    scaled_value = (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(scaled_value)

class DC:
    def __init__(self, pin_in1=pin1, pin_in2=pin2, pin_ena=pin9, filename='cnf.txt'):
        self.cnf_file = filename
        self.in1 = pin_in1
        self.in2 = pin_in2
        self.ena = pin_ena
        self.speed = 0
        self.duty = 0
        self.stopped = True
        self.stop()
        self.read_cnf_file()
        self.set_direction(forward=True)

    def set_direction(self, forward=True):
        if forward:
            self.in1.write_digital(1)
            self.in2.write_digital(0)
        else:
            self.in1.write_digital(0)
            self.in2.write_digital(1)

    def move(self, speed=None):
        if self.stopped:
            self.stopped = False
            self.set_direction(forward=True)
        if speed is not None:
            if speed > 0:
                self.set_direction(True)
            elif speed < 0:
                self.set_direction(False)
            self.speed = abs(speed)
        self.duty = map(self.speed, 0, 100, 0, 1023)
        # print("Duty: ", duty)
        self.ena.write_analog(self.duty)

    def stop(self):
        self.in1.write_digital(0)
        self.in2.write_digital(0)
        self.stopped = True

    def read_cnf_file(self):
        with open(self.cnf_file, 'r') as f:
            txt = f.read()
            lines = txt.split('\n')
            for line in lines:
                # print(line)
                if 'DC' in line:
                    dc_data = line.split(', ')
                    self.speed = int(dc_data[1])
