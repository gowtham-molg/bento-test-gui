import tkinter as tk

class PneumaticControlGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pneumatic Control GUI")
        self.root.resizable(False, False)
        self._build_widgets()
        self.root.mainloop()

    def _build_widgets(self):
        # Padding around everything
        pad_x, pad_y = 20, 10

        # Hardware IP Address label + entry
        tk.Label(self.root, text="Hardware IP Address:", font=("Arial", 12)).pack(pady=(pad_y, 2))
        self.ip_entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.pack(pady=(0, pad_y))

        # Fetch button
        tk.Button(
            self.root,
            text="Fetch IP Address",
            font=("Arial", 12),
            command=self.fetch_ip
        ).pack(pady=(0, pad_y))

        # Connection status indicator
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=(0, pad_y))
        tk.Label(status_frame, text="Connection Status:", font=("Arial", 12)).pack(side="left")
        self.status_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=10)
        self._update_status("green")

        # Channel buttons
        channels_frame = tk.Frame(self.root)
        channels_frame.pack(pady=(0, pad_y))
        for i in range(5):
            btn = tk.Button(
                channels_frame,
                text=f"Channel {i+1}\n(Open)",
                font=("Arial", 10),
                width=12,
                height=2
            )
            btn.grid(row=0, column=i, padx=5)

    def _update_status(self, color):
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 18, 18, fill=color, outline=color)

    def fetch_ip(self):
        ip = self.ip_entry.get()
        # TODO: add your real fetch logic here
        print(f"Fetching status for {ip}…")
        # simulate a successful connection
        self._update_status("green")


if __name__ == "__main__":
    PneumaticControlGUI()