from microbit import *

class Jetson:
    def __init__(self):
        uart.init(baudrate=115200)

    def empty_que(self):
        while uart.any():
            uart.read()

    def send_data(self, data, sign='#'):
        '''
        Send a list of numbers to jetson
        data: list of int nums
        '''
        msg = sign
        for d in data:
            msg += str(d) + ','
        msg = msg[:-1] + "\n"
        uart.write(msg)

    def get_data(self, sign='#'):
        '''
        Send a valid list of numbers from jetson
        returns the list of int nums
        '''
        if uart.any():
            msg = str(uart.read(1), 'UTF-8')
            if msg == sign:
                c = ""
                msg_text = ""
                while c != '\n':
                    if uart.any():
                        c = str(uart.read(1), 'UTF-8')
                        msg_text += c
                msg_text = msg_text[:-1]
                msg_list_str = msg_text.split(',')
                data = []
                for m in msg_list_str:
                    try:
                        num = int(m)
                        data.append(num)
                    except:
                        return None
                if len(data) > 0:
                    return data
        return None

    
