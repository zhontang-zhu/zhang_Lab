import qcodes as qc
import time
from qcodes.instrument_drivers.Keithley import Keithley2612B
class Kei_2612b:
    def __init__(self, channel = 'b'):
       
        self.channel = channel
        self.is_running = True
        self.is_move_to_start = False
        self.is_scan_finished = False
        self.scanning_I = []
        self.scanning_V = []
        self.current_V = 0

        station = qc.Station()
        self.keith = Keithley2612B("keithley", "USB0::0x05E6::0x2612::4611642::INSTR")
        station.add_component(self.keith)
        self.keith.print_readable_snapshot()
        if self.channel == 'A' or self.channel == 'a': 
            self.keith.smua.mode("voltage")
            self.keith.smua.nplc(1)
            self.keith.smua.sourcerange_v(20)  # only in {0.2, 2, 20, 200}
            self.keith.smua.measurerange_i(1e-05)  # only in {0.1, 1, 1.5, 1e-05, 0.01, 0.0001, 1e-07, 1e-06, 0.001}
            self.keith.smua.output("on")
        if self.channel == 'B' or self.channel == 'b':
            self.keith.smub.mode("voltage")
            self.keith.smub.nplc(1) #integration time = nplc*PLC , plc = 20ms in China 
            self.keith.smub.sourcerange_v(20)  # only in {0.2, 2, 20, 200}
            self.keith.smub.measurerange_i(1e-06)  # only in {0.1, 1, 1.5, 1e-05, 0.01, 0.0001, 1e-07, 1e-06, 0.001}
            self.keith.smub.output("on")
    def set_output_V(self, output):
        if self.channel == 'A' or self.channel == 'a':
            self.keith.smua.volt(output)
        if self.channel == 'B' or self.channel == 'b':
            self.keith.smub.volt(output)
    def read_IV_data(self):
        if self.channel  == 'A' or self.channel  == 'a':
            return self.keith.smua.volt(), self.keith.smua.curr()
        if self.channel  == 'B' or self.channel  == 'b':
            return self.keith.smub.volt(), self.keith.smub.curr() 
    
    def continue_running(self):
        self.is_running = True
        
    def stop_running(self):
        self.is_running = False

    def current_V_move_to_start(self, start, step):
        current_V = self.read_IV_data()[0]
        if self.is_running:
            if not self.is_move_to_start:
                if  current_V != start:
                    if start < current_V: 
                        current_V -= abs(step) 
                    elif start > current_V:
                        current_V += abs(step)
                    if current_V > start-abs(step) and current_V < start+abs(step):
                        current_V = start
                        self.current_V = start
                        self.is_move_to_start = True
                        self.set_output_V(current_V) # supplement the first (V,I) data
                        V, I = self.read_IV_data() 
                        self.scanning_V.append(V)
                        self.scanning_I.append(I)
                    self.set_output_V(current_V) 
                else:
                    self.current_V = start
                    self.is_move_to_start = True

    def scan(self, start, end, step):
        if self.is_running:
            if not self.is_scan_finished:
                if self.is_move_to_start:
                    if  self.current_V != end:
                        if self.current_V > end - abs(step) and self.current_V < end + abs(step):
                            self.current_V = end
                        else:
                            if start <= end :
                                self.current_V += abs(step)
                            else :
                                self.current_V -= abs(step)
                        self.set_output_V(self.current_V) #loss the first (V,I) data
                        V, I = self.read_IV_data()
                        self.scanning_V.append(V)
                        self.scanning_I.append(I)
                    else :  
                        self.is_scan_finished = True
                        return
                else :
                    self.current_V_move_to_start(start, step)          

import tkinter as tk
from tkinter import ttk, StringVar, filedialog
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
class GUI_2612b:
    def __init__(self, channel):
        try:
            if channel == 'A' or channel == 'a':
                self.SM=Kei_2612b('a')
            if channel == 'B' or channel == 'b':
                self.SM=Kei_2612b('b')
        except Exception as e:
            print(f"invalid channel: {e}")
        self.start = 0
        self.end = 0
        self.step = 0.01
        self.csv_file = None
        self.csv_folder = ""
        self.csv_filename = ""
        self.csv_fullpath = ""

        self.root = tk.Tk()
        self.root.title("V-I")
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel('(V)')
        self.ax.set_ylabel('(I)')
        self.ax.set_title('real-time V-I')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.line, = self.ax.plot([], [], color="blue")
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.status_label = ttk.Label(self.bottom_frame, text="")
        self.status_label.grid(row=6, column=0, columnspan=2)

        ttk.Label(self.bottom_frame, text="Start:").grid(row=0, column=0, padx=5, pady=5)
        self.start_entry = ttk.Entry(self.bottom_frame)
        self.start_entry.insert(0, str(self.start))
        self.start_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(self.bottom_frame, text="Step:").grid(row=1, column=0, padx=5, pady=5)
        self.step_entry = ttk.Entry(self.bottom_frame)
        self.step_entry.insert(0, str(self.step))
        self.step_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(self.bottom_frame, text="End:").grid(row=2, column=0, padx=5, pady=5)
        self.end_entry = ttk.Entry(self.bottom_frame)
        self.end_entry.insert(0, str(self.end))
        self.end_entry.grid(row=2, column=1, padx=5, pady=5)

        update_button = ttk.Button(self.bottom_frame, text="Update Parameters", command=self.update_parameters)
        update_button.grid(row=5, column=0, columnspan=2, pady=10)
        stop_button = ttk.Button(self.root, text="stop", command=self.SM.stop_running)
        stop_button.pack(side=tk.BOTTOM)
        continue_button = ttk.Button(self.root, text="continue", command=self.SM.continue_running)
        continue_button.pack(side=tk.BOTTOM)
        scan_p_n_button = ttk.Button(self.bottom_frame, text="Bidirectional_scan", command=self.Bidirectional_scan)
        scan_p_n_button.grid(row=5, column=2, padx=5, pady=10)

        self.folder_var = StringVar()
        self.filename_var = StringVar()
        self.filename_var.trace_add("write", self.update_csv_fullpath)
        ttk.Label(self.bottom_frame, text="folder:").grid(row=3, column=0, padx=5, pady=5)
        folder_entry = ttk.Entry(self.bottom_frame, textvariable=self.folder_var, width=30, state="readonly")
        folder_entry.grid(row=3, column=1, padx=5, pady=5)
        choose_folder_btn = ttk.Button(self.bottom_frame, text="choose  folder", command=self.choose_folder)
        choose_folder_btn.grid(row=3, column=2, padx=5, pady=5)
        ttk.Label(self.bottom_frame, text="name_csv:").grid(row=4, column=0, padx=5, pady=5)
        filename_entry = ttk.Entry(self.bottom_frame, textvariable=self.filename_var)
        filename_entry.grid(row=4, column=1, padx=5, pady=5)

    


        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


        
    def plotting(self):
        if self.SM.is_running:
            self.SM.scan(self.start, self.end, self.step)
            if self.SM.scanning_V  and self.SM.scanning_I :
                self.line.set_data(self.SM.scanning_V, self.SM.scanning_I)
                self.ax.relim()
                self.ax.autoscale_view()
                if self.csv_file and not self.SM.is_scan_finished:
                    self.csv_file.write(f"{self.SM.scanning_V[-1]},{self.SM.scanning_I[-1]}\n")
                    self.csv_file.flush()
        self.canvas.draw()
        self.root.after(10, self.plotting)

    def update_parameters(self):
        try:
            # 更新参数
            self.start = float(self.start_entry.get())
            self.step = float(self.step_entry.get())
            self.end = float(self.end_entry.get())

            self.SM.scanning_V.clear()
            self.SM.scanning_I.clear()

            # 重置扫描状态
            self.SM.is_running = True
            self.SM.is_move_to_start = False
            self.SM.is_scan_finished =False

            self.close_csv_file()
            self.open_csv_file()

            # 提示更新成功
            self.status_label.config(text="Parameters updated successfully!")
        except ValueError:
            self.status_label.config(text="Invalid input! Please enter numbers.")

    def Bidirectional_scan(self):
        # positive_sweep
        base_name = self.filename_var.get().rstrip("_+").rstrip("_-")
        if base_name:
            self.filename_var.set(base_name + "_+")
        self.update_parameters()
        while not self.SM.is_scan_finished:
            if not self.SM.is_running:
                return
            self.root.update()
            time.sleep(0.01)
        #negative_sweep
        s = float(self.end_entry.get())
        e = float(self.start_entry.get())
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, str(s))
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, str(e))
        base_name = self.filename_var.get().rstrip("_+").rstrip("_-")
        if base_name:
            self.filename_var.set(base_name + "_-")
        self.update_parameters()
        while not self.SM.is_scan_finished :
            if not self.SM.is_running:
                return
            self.root.update()
            time.sleep(0.01)
        #set_original_value
        s = float(self.end_entry.get())
        e = float(self.start_entry.get())
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, str(s))
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, str(e))

    def choose_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.csv_folder = folder_selected
            self.folder_var.set(self.csv_folder)
            self.update_csv_fullpath()

    def update_csv_fullpath(self, *args):
        name = self.filename_var.get()
        if self.csv_folder and name:
            self.csv_fullpath = os.path.join(self.csv_folder, name + ".csv")
        else:
            self.csv_fullpath = ""

    def open_csv_file(self):
        if self.csv_fullpath:
            self.csv_file = open(self.csv_fullpath, "w", encoding="utf-8")
            self.csv_file.write("Voltage,Current\n")  # 写入表头

    def close_csv_file(self):
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None

    def on_closing(self):
        self.close_csv_file()
        self.root.quit()
        self.root.destroy()