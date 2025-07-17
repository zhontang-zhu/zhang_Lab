import threading
import time
from tkinter import ttk, StringVar
from GUI_2612b import GUI_2612b
from OT3507 import OT3507_SLCAN
def Continuous_bidirectional_scan(angle_range, angle_step):
    is_continuous_bidirectional = True
    while is_continuous_bidirectional:
        if not GUI_2612b.SM.is_running:
             return
        GUI_2612b.Bidirectional_scan()
        #filename : I_V_12μW_HWPxxx_+
        num = int(GUI_2612b.filename_var.get()[-5:-2])
        if num < angle_range:
            num += angle_step
            GUI_2612b.filename_var.set(GUI_2612b.filename_var.get()[:-5] + str(num).zfill(3) + GUI_2612b.filename_var.get()[-2:])
            rtAngle = ot3507.set_read_parameter(num, 0.5)[1]
            while abs(rtAngle-num) > 0.02:
                 rtAngle = ot3507.set_read_parameter(num, 0.5)[1]
                 time.sleep(0.1)
        else:
            is_continuous_bidirectional = False
def update_current_angle():
    def worker():
        try:
            data = ot3507.choose_mode('enable')
            if data :
                current_angle.set(f"{data[1]:.3f}")
            else:
                current_angle.set("No Data")
        except Exception:
            current_angle.set("Error")
        GUI_2612b.root.after(500, update_current_angle)
    threading.Thread(target=worker, daemon=True).start()
    
GUI_2612b = GUI_2612b(channel='a')
try:
    ot3507 = OT3507_SLCAN(port='COM7')
    # 添加Continuous_bidirectional_scan按钮
    ot3507.choose_mode('enable')
    ot3507.set_read_parameter(0, 2)
    time.sleep(1)
    scan_p_n_button = ttk.Button(GUI_2612b.bottom_frame, text="Continuous_bidirectional_scan", command=lambda:Continuous_bidirectional_scan(60, 5))
    scan_p_n_button.grid(row=5, column=3, padx=5, pady=10)
    ttk.Label(GUI_2612b.bottom_frame, text="current_angle").grid(row=4, column=3, padx=5, pady=5)
    current_angle = StringVar()
    current_angle_entry = ttk.Entry(GUI_2612b.bottom_frame, textvariable=current_angle, state="readonly")
    current_angle_entry.grid(row=4, column=4, padx=5, pady=5)
    update_current_angle()
    
except Exception as e:
        print(f"串口通信失败: {e}")


GUI_2612b.plotting()
GUI_2612b.root.mainloop()