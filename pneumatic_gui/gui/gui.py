import tkinter as tk
from tkinter import ttk, simpledialog
from control.pneumatic_control import pneumatic_set_valve, pneumatic_read_valve_state
from control.gimatic_control import send_gimatic_cmd, check_gimatic_status
from utils.ip_utils import get_ip_controller
from utils.task_scheduler import schedule_coro

class PneumaticControlGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pneumatic Control GUI")
        self.root.resizable(False, False)
        self._build_widgets()
        self.root.mainloop()

    def _build_widgets(self):
        pad_y = 10

        tk.Label(self.root, text="Hardware IP Address:", font=("Arial", 12)).pack(pady=(pad_y, 2))
        self.ip_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.ip_entry.pack(pady=(0, pad_y))

        self.status_canvas = tk.Canvas(self.root, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack()
        self._update_status("grey")

        self.message_label = tk.Label(self.root, text="", font=("Arial", 10), fg="red")
        self.message_label.pack(pady=(0, 10))

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack()

        self.manual_tab = tk.Frame(self.tabs)
        self.auto_tab = tk.Frame(self.tabs)
        self.tabs.add(self.manual_tab, text="Manual Control")
        self.tabs.add(self.auto_tab, text="Auto Test")

        self._build_manual_tab()
        self._build_auto_tab()

    def _update_status(self, color):
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 18, 18, fill=color, outline=color)

    def _build_manual_tab(self):
        tk.Button(self.manual_tab, text="Fetch IP Address", command=self.fetch_ip).pack(pady=5)
        frame = tk.Frame(self.manual_tab)
        frame.pack()
        for i in range(6):
            tk.Button(frame, text=f"Open {i+1}", command=lambda i=i: self.control_valve(i+1, True)).grid(row=0, column=i)
            tk.Button(frame, text=f"Close {i+1}", command=lambda i=i: self.control_valve(i+1, False)).grid(row=1, column=i)

        tk.Button(self.manual_tab, text="Gimatic Open", command=lambda: self.run_gimatic_cmd("GIMATIC_CMD_OPEN")).pack(pady=5)
        tk.Button(self.manual_tab, text="Gimatic Close", command=lambda: self.run_gimatic_cmd("GIMATIC_CMD_CLOSE")).pack(pady=5)
        tk.Button(self.manual_tab, text="Gimatic Status", command=self.run_gimatic_status_check).pack(pady=5)

    def _build_auto_tab(self):
        tk.Button(self.auto_tab, text="Start Valve Test", command=self.start_sequence).pack(pady=10)
        tk.Button(self.auto_tab, text="Start Gimatic Test", command=self.start_gimatic_test).pack(pady=10)

    def fetch_ip(self):
        from control.coap_client import set_controller_ip
        ip = get_ip_controller()
        if ip:
            set_controller_ip(ip)
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, ip)
            self._update_status("green")
            self.message_label.config(text="IP fetched successfully")
        else:
            self._update_status("red")
            self.message_label.config(text="Failed to fetch IP")

    def control_valve(self, channel, open_valve):
        self._update_status("orange")
        async def task():
            try:
                await pneumatic_set_valve(channel, open_valve)
                self.root.after(0, lambda: self._update_status("green"))
                self.root.after(0, lambda: self.message_label.config(text=f"Valve {channel} {'opened' if open_valve else 'closed'}"))
            except:
                self.root.after(0, lambda: self._update_status("red"))
                self.root.after(0, lambda: self.message_label.config(text=f"Failed to {'open' if open_valve else 'close'} valve {channel}"))
        schedule_coro(task())

    def run_gimatic_cmd(self, action):
        self._update_status("orange")
        async def task():
            try:
                await send_gimatic_cmd(action)
                self.root.after(0, lambda: self._update_status("green"))
                self.root.after(0, lambda: self.message_label.config(text=f"Gimatic {action.split('_')[-1].capitalize()} command sent"))
            except Exception as e:
                self.root.after(0, lambda: self._update_status("red"))
                exc = e
                self.root.after(0, lambda: self.message_label.config(text=f"Gimatic command failed: {exc}"))
        schedule_coro(task())

    def run_gimatic_status_check(self):
        self._update_status("orange")
        async def task():
            try:
                ret = await check_gimatic_status()
                self.root.after(0, lambda: self._update_status("green"))
                self.root.after(0, lambda: self.message_label.config(text=f"Gimatic status: {ret}"))
            except Exception as e:
                self.root.after(0, lambda: self._update_status("red"))
                self.root.after(0, lambda: self.message_label.config(text=f"Gimatic status check failed: {e}"))
        schedule_coro(task())

    def start_sequence(self):
        # Placeholder for valve test sequence
        self.message_label.config(text="Valve test started (not yet implemented)")
        self._update_status("orange")

    def start_gimatic_test(self):
        # Placeholder for gimatic test sequence
        self.message_label.config(text="Gimatic test started (not yet implemented)")
        self._update_status("orange")
