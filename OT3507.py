import serial
import time
import struct
class OT3507_SLCAN:
    def __init__(self, port='COM7', baudrate=1000000, timeout=1.0, current=0.5, KP=100, KD=100):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )
        self.current = current
        self.KP = KP
        self.KD = KD
        self.send_serial_message('S8\r') 
        self.send_serial_message('O\r')
    def choose_mode(self, mode = 'disable'):
        if mode == 'enable' : #motor_enable
            data = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFC])
        elif mode == 'disable' : #motor_disable
            data = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFD])
        elif mode == 't' : #torque mode
            data = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xF9])
        elif mode == 'v' : #velocity_torque mode
            data = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFA])
        elif mode == 'p' : #position_velocity_torque mdoe
            data = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFB])
        elif mode == 'zero' : #set_ZeroPoint
            data = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFE])
        else:
            raise ValueError("Invalid mode selected. Please choose a valid mode.")
        self.send_serial_message(data)
        value = self.receive_serial_message()
        return value
    def set_read_parameter(self, angle, speed): # °, rad/s, A, _, _
        position = angle * 0x8000 / 360 + 0x8000
        velocity = speed*0x800 / 58.639 +0x800
        torque = self.current*0x800 / 4 + 0x800
        position = int(position) & 0xFFFF
        velocity = int(velocity) & 0xFFF
        torque = int(torque) & 0xFFF
        kp = int(self.KP) & 0xFFF
        kd = int(self.KD) & 0xFFF
        value = ((position << 48) |(velocity << 36) |(kp << 24) |(kd << 12) |torque)
        data = struct.pack('>Q', value)
        self.send_serial_message(data)
        value = self.receive_serial_message()
        return value
    def review_data_handle(self, data):
        try:
            data = data[5:] # abandon 't0646'
            data_str = data.decode('ascii') # b'ffff___' → 'ffff___'
            data_bytes = bytes.fromhex(data_str) # 'ffff___' → b'\xff\xff\x__\x__'
            MotorID = data_bytes[0]
            position = (data_bytes[1]<<8) | data_bytes[2]
            velocity = (data_bytes[3]<<4) | (data_bytes[4]>>4)
            torque = ((data_bytes[4] & 0x0F)<<8) | data_bytes[5]
            angle = (position-0x8000)*360/0x8000
            speed = (velocity-0x800)*58.639/0x800
            current = (torque-0x800)*4/0x800
            return MotorID, angle, speed, current
        except Exception as e:
            print(f"解析数据失败: {e}")
            return None


    def send_serial_message(self, data):
        self.ser.reset_input_buffer() #clear input buffer before sending
        if isinstance(data, (bytes, bytearray)):
            can_data = 't0018'+data.hex()+'\r'
            self.ser.write(can_data.encode('ascii', errors='replace'))
            time.sleep(0.001)
        elif isinstance(data, str):
            self.ser.write(data.encode('ascii'))
            time.sleep(0.001)
        else:
            raise ValueError("data必须为bytes、bytearray或str类型")

    def receive_serial_message(self, timeout=1.0):
        self.ser.timeout = timeout
        data = self.ser.read_until(expected=b'\r') #readline() method may be blocking the program
        if data:
            try:
                result = self.review_data_handle(data)
                if result is not None:
                    return result
            except Exception as e:
                print(f"单帧解析失败: {e}")
            return None
        else:
            print("串口接收超时")
            return None
    

        
def update_current_angle():
    global angle, speed, is_recieve
    def worker():
        if is_recieve:
            try:
                data = ot3507.set_read_parameter(angle, speed)
                if data is not None:
                    current_angle.set(f"{data[1]:.3f}")
                else:
                    current_angle.set("No Data")
            except Exception:
                current_angle.set("Error")
        root.after(500, update_current_angle)
    threading.Thread(target=worker, daemon=True).start()

def update_parameters():
    global angle, speed
    angle = float(angle_entry.get())
    speed = float(speed_entry.get())
    ot3507.set_read_parameter(angle, speed)

def Motor_Enable():
    try:
        ot3507.choose_mode('enable')
        print("电机已使能")
    except Exception as e:
        print(f"使能电机失败: {e}")

def Motor_Disable():
    try:
        ot3507.choose_mode('disable')
        print("电机已失能")
    except Exception as e:
        print(f"禁用电机失败: {e}")

def is_receive_data():
    global is_recieve
    is_recieve = not is_recieve


import threading
import tkinter as tk
from tkinter import ttk, StringVar, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

if __name__ == "__main__":
    angle = 0
    speed = 0
    is_recieve = True 
    try:
        ot3507 = OT3507_SLCAN(port='COM7', baudrate=1000000, timeout=1.0, current=0.5, KP=100, KD=100)
        # 'S8\r',set can baudrate to 1M. 
        # 'O\r', open can bus.
        # 'C\r', close can bus.
        ot3507.send_serial_message('S8\r') 
        ot3507.send_serial_message('O\r')
        print("串口已初始化")

        # 创建Tkinter窗口
        root = tk.Tk()
        root.title("motor")

        # 创建输入框和标签
        BOTTOM_frame = ttk.Frame(root)
        BOTTOM_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        ttk.Label(BOTTOM_frame, text="angle:").grid(row=0, column=0, padx=5, pady=5)
        angle_entry = ttk.Entry(BOTTOM_frame)
        angle_entry.insert(0, str(angle))
        angle_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(BOTTOM_frame, text="speed:").grid(row=1, column=0, padx=5, pady=5)
        speed_entry = ttk.Entry(BOTTOM_frame)
        speed_entry.insert(0, str(speed))
        speed_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(BOTTOM_frame, text="current_angle").grid(row=0, column=4, padx=5, pady=5)
        current_angle = StringVar()
        current_angle_entry = ttk.Entry(BOTTOM_frame, textvariable=current_angle, state="readonly")
        current_angle_entry.grid(row=0, column=5, padx=5, pady=5)

        update_button = ttk.Button(BOTTOM_frame, text="Update Parameters", command=update_parameters)
        update_button.grid(row=4, column=0, columnspan=2, pady=10)

        Motor_Enable_button = ttk.Button(BOTTOM_frame, text="Motor_Enable", command=Motor_Enable)
        Motor_Enable_button.grid(row=1, column=4, columnspan=2, pady=10)

        Motor_Disable_button = ttk.Button(BOTTOM_frame, text="Motor_Disable", command=Motor_Disable)
        Motor_Disable_button.grid(row=2, column=4, columnspan=2, pady=10)

        is_receive_data_button = ttk.Button(BOTTOM_frame, text="is_receive_data", command=is_receive_data)
        is_receive_data_button.grid(row=3, column=4, columnspan=2, pady=10)

        update_current_angle()
        root.mainloop()
    except Exception as e:
        print(f"串口通信失败: {e}")




