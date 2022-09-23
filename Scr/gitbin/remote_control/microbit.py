import serial
from time import sleep, time

class Microbit:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyACM0', 115200)

    def empty_que(self):
        while self.ser.inWaiting() > 0:
            self.ser.read()

    def send_data(self, data, sign='#'):
        '''
        Send a list of numbers to jetson
        data: list of int nums
        '''
        msg = sign
        for d in data:
            msg += str(d) + ','
        msg = msg[:-1] + "\n"
        print("sending:" + msg)
        try:
            self.ser.write(msg.encode())
        except:
            print("Data Transmission Failed")

    def get_data(self, sign='#'):
        '''
        Send a valid list of numbers from jetson
        returns the list of int nums
        '''
        if self.ser.inWaiting() > 0:
            msg = self.ser.readline()
            msg_str = msg.decode("utf-8")
            if msg_str[0] == sign:
                data = []
                msg_str = msg_str[1:-1]
                msg_list_str = msg_str.split(',')
                for m in msg_list_str:
                    try:
                        num = int(m)
                        data.append(num)
                    except:
                        return None
                if len(data) > 0:
                    return data
        return None

    def handshake(self):
        mb_responed = False
        while not mb_responed:
            self.send_data([1111], sign='!')
            in_data = self.get_data(sign='!')
            if in_data is not None and in_data[0] == 1111:
                mb_responed = True
            sleep(1)
        self.send_data([1111], sign='!')
        sleep(1)
        # self.empty_que()

def main():
    mb = Microbit()
    # mb.handshake()
    sleep(5)
    last_send = 0
    print("after handshake")
    while True:
        current_scd = time()
        if current_scd - last_send > 5:
            mb.send_data([3, 100])
            last_send = current_scd
        data = mb.get_data()
        if data is not None:
            print("Jetson received from mb: " + str(data))


if __name__ == "__main__":
    main()