import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import logging
import json
import time
import datetime
from typing import Optional, List
import serial
from aiocoap import Context, Message, POST
import aiocoap.error

# --- Logging setup ---
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Placeholder controller IP ---
bento_controller_ip = None

# --- Async CoAP command ---
async def send_controller_comand(register: str, value, close_connection=False) -> dict:
    timeout_s = 60
    logger.debug("send_controller_comand")

    payload = json.dumps({"reg": register, "val": value}).encode('utf-8')
    logger.debug(f"target ip: {bento_controller_ip}")
    logger.debug(f"payload: {payload}")

    context = await Context.create_client_context()
    request = Message(code=POST, payload=payload, uri=f"coap://{bento_controller_ip}/controller", no_response=True)

    try:
        response = await asyncio.wait_for(context.request(request).response, timeout=timeout_s)
    except Exception as e:
        raise Exception("CoAP command failed: " + str(e))
    finally:
        if close_connection:
            await context.shutdown()

    if len(response.payload) > 0:
        return json.loads(response.payload.decode('utf-8'))
    else:
        raise Exception("Empty response payload")

async def pneumatic_set_valve(channel_number: int, open_value: bool):
    return await send_controller_comand("RELAY_TO_MODULE_J", {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": 544,
        "cmd": "set_valve",
        "data": {"valve_n": channel_number, "open": open_value}
    }, close_connection=True)

async def pneumatic_read_valve_state(channel_number: int):
    reply = await send_controller_comand("RELAY_TO_MODULE_J", {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": 544,
        "cmd": "p_read",
        "data": {"valve_n": channel_number}
    }, close_connection=True)
    return reply

async def pneumatic_read_pressure():
    reply = await send_controller_comand("RELAY_TO_MODULE_J", {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": 544,
        "cmd": "read_pressure",
        "data": {}
    }, close_connection=True)
    return reply

def send_usb_command_retrieve_response(serial_port: str, command: str) -> List[str]:
    try:
        with serial.Serial(serial_port, baudrate=115200, timeout=2) as ser:
            ser.write((command + '\n').encode('utf-8'))
            response = ser.read_until(b'\n\n').decode('utf-8')
            return response.strip().splitlines()
    except Exception as e:
        print(f"Error communicating with USB controller: {e}")
        return []

def get_ip_controller(serial_port: str = "/dev/ttyUSB0") -> Optional[str]:
    lines = send_usb_command_retrieve_response(serial_port, "net ipv4")
    for line in lines:
        if "DHCP" in line and "preferred" in line:
            parts = line.split()
            if len(parts) > 3:
                return parts[3].split('/')[0]
    return None

loop = asyncio.new_event_loop()

def _start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=_start_loop, daemon=True).start()

def schedule_coro(coro):
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    def _on_done(fut):
        try:
            fut.result()
        except Exception:
            logger.exception("Async task failed")
    future.add_done_callback(_on_done)

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

    def _build_auto_tab(self):
        tk.Button(self.auto_tab, text="Start Test", command=self.start_sequence).pack(pady=20)

    def fetch_ip(self):
        global bento_controller_ip
        ip = get_ip_controller()
        if ip:
            bento_controller_ip = ip
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

    def start_sequence(self):
        self.message_label.config(text="Starting test...")
        self._update_status("orange")

        async def run_and_prompt():
            report_lines = await self._run_sequence_task()
            self._prompt_report_filename(report_lines)

        schedule_coro(run_and_prompt())

    async def _run_sequence_task(self):
        global bento_controller_ip
        report_lines = []

        ip = None
        for attempt in range(1, 4):
            ip = get_ip_controller()
            if ip:
                report_lines.append(f"IP Fetch - Success on attempt {attempt}: {ip}")
                break
            else:
                await asyncio.sleep(0.5)

        if not ip:
            report_lines.append("IP Fetch - Failed after 3 attempts")
            self.root.after(0, lambda: self._update_status("red"))
            self.root.after(0, lambda: self.message_label.config(text="Failed to fetch IP."))
            return report_lines

        bento_controller_ip = ip
        self.root.after(0, lambda: self.ip_entry.delete(0, tk.END))
        self.root.after(0, lambda: self.ip_entry.insert(0, ip))
        self.root.after(0, lambda: self._update_status("green"))

        for channel in range(1, 7):
            try:
                pre_pressure = await pneumatic_read_pressure()
                report_lines.append(f"Valve {channel} - Pre-open pressure: {pre_pressure}")

                await pneumatic_set_valve(channel, True)
                await asyncio.sleep(1)

                post_pressure = await pneumatic_read_pressure()
                report_lines.append(f"Valve {channel} - Post-open pressure: {post_pressure}")

                valve_state = await pneumatic_read_valve_state(channel)
                report_lines.append(f"Valve {channel} - State after open: {valve_state}")

                await pneumatic_set_valve(channel, False)
                report_lines.append(f"Valve {channel} - Closed")

                self.root.after(0, lambda: self._update_status("green"))
                await asyncio.sleep(0.5)

            except Exception as e:
                report_lines.append(f"Valve {channel} - Error: {str(e)}")
                self.root.after(0, lambda: self._update_status("red"))
                await asyncio.sleep(0.5)

        return report_lines

    def _prompt_report_filename(self, report_lines):
        popup = tk.Toplevel(self.root)
        popup.title("Save Report As")
        tk.Label(popup, text="Enter filename for the report:").pack(pady=10)
        entry = tk.Entry(popup, width=40)
        entry.insert(0, f"auto_test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        entry.pack(pady=5)

        def confirm():
            filename = entry.get().strip()
            if not filename.endswith(".txt"):
                filename += ".txt"
            popup.destroy()
            with open(filename, "w") as f:
                for line in report_lines:
                    f.write(line + "\n")
            self.message_label.config(text=f"Test complete. Report saved: {filename}")

        tk.Button(popup, text="Save", command=confirm).pack(pady=10)

if __name__ == "__main__":
    PneumaticControlGUI()
