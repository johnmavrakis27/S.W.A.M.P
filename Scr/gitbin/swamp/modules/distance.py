#Libraries
import RPi.GPIO as GPIO
import time
from statistics import median

class Distance:
    def __init__(self, gpio_trigger, gpio_echo):
        self.trigger = gpio_trigger
        self.echo = gpio_echo
        #GPIO Mode (BOARD / BCM)
        GPIO.setmode(GPIO.BOARD)

        #set GPIO direction (IN / OUT)
        GPIO.setup(self.trigger, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)
 
    def distance_cm(self, tries=1):
        distance_list = []
        for i in range(tries):
            # set Trigger to HIGH
            GPIO.output(self.trigger, True)
        
            # set Trigger after 0.01ms to LOW
            time.sleep(0.00001)
            GPIO.output(self.trigger, False)
        
            StartTime = time.time()
            StopTime = time.time()
        
            # save StartTime
            while GPIO.input(self.echo) == 0:
                StartTime = time.time()
        
            # save time of arrival
            while GPIO.input(self.echo) == 1:
                StopTime = time.time()
        
            # time difference between start and arrival
            TimeElapsed = StopTime - StartTime
            # multiply with the sonic speed (34300 cm/s)
            # and divide by 2, because there and back
            distance_list.append((TimeElapsed * 34300) // 2)
        # distance_list.sort()
        # median_distance = (distance_list[tries//2-1]/2.0+distance_list[tries//2]/2.0, distance_list[tries//2])[tries % 2]
        median_distance = median(distance_list)
        if median_distance == 0 or median_distance > 400:
            median_distance = 400
        return int(median_distance)

    
def main():
    try:
        left = Distance(gpio_trigger=22, gpio_echo=24)
        right = Distance(gpio_trigger=26, gpio_echo=23)
        counter = 0
        while True:
            print("Counter:", counter)
            counter += 1
            left_distance = left.distance_cm(tries=1)
            right_distance = right.distance_cm(tries=1)
            print (f"Left Distance = {left_distance} cm")
            print (f"Right Distance = {right_distance} cm")
            time.sleep(0.1)
    # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()

if __name__ == '__main__':
    main()