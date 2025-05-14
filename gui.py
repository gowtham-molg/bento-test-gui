import tkinter as tk
import asyncio
import threading
import logging
import json
import time
from aiocoap import Context, Message, POST
import aiocoap.error

# --- Logging setup ---
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Global IP of controller (set it after getting from USB) ---
bento_controller_ip = "192.168.1.100"

# --- Async CoAP command ---
async def send_controller_comand(register: str, value, close_connection=False) -> dict:
    timeout_s = 60
    logger.debug("send_controller_comand")

    if isinstance(value, str):
        payload = json.dumps({"reg": register, "val": value}).encode('utf-8')
    elif isinstance(value, dict):
        if register not in ["RELAY_TO_MODULE_J", "FW_MNG", "LOG"]:
            raise Exception("Only relay to module J is allowed to send dictionaries")
        payload = json.dumps({"reg": register, "val": value}).encode('utf-8')

    logger.debug(f"target ip: {bento_controller_ip}")
    logger.debug(f"payload: {payload}")

    context = await Context.create_client_context()
    ts = time.time()
    request = Message(code=POST, payload=payload, uri=f"coap://{bento_controller_ip}/controller", no_response=True)

    try:
        response = await asyncio.wait_for(context.request(request).response, timeout=timeout_s)
    except asyncio.TimeoutError:
        logger.error("Request timed out")
        raise Exception("Timeout waiting for CoAP command reply")
    except aiocoap.error.NetworkError:
        logger.error("Network error")
        raise Exception("Network error while sending CoAP cmd")
    except Exception as e:
        logger.error(str(e))
        raise

    if close_connection:
        await context.shutdown()

    logger.debug(f"Response: {response.payload}")
    if len(response.payload) > 0:
        try:
            return json.loads(response.payload.decode('utf-8'))
        except Exception as ex:
            logger.error(f"Error decoding JSON: {ex}")
            return response.payload
    else:
        raise Exception("Empty response payload")

# --- J-Interface wrapper ---
async def send_jInterface_cmd_relay_to_module(dest_can_bus_id: int, jinterface_data: dict):
    value_data_dict = {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": dest_can_bus_id,
        "cmd": jinterface_data["cmd"],
        "data": jinterface_data["data"]
    }
    reply = await send_controller_comand("RELAY_TO_MODULE_J", value_data_dict, close_connection=True)
    return reply["data"]

# --- Valve control ---
async def pneumatic_set_valve(channel_number: int, open_value: bool):
    ret = await send_jInterface_cmd_relay_to_module(
        dest_can_bus_id=544,
        jinterface_data={
            "cmd": "set_valve",
            "data": {"valve_n": channel_number, "open": open_value}
        }
    )
    return ret

# --- USB IP fetch simulation ---
def send_usb_command_retrieve_response(serial_port: str, command: str):
    return [" DHCP    preferred       1       172.16.50.2/255.255.255.0"]

def get_ip_controller(serial_port: str = "/dev/ttyUSB0") -> str | None:
    lines = send_usb_command_retrieve_response(serial_port, "net ipv4")
    for line in lines:
        if "DHCP" in line and "preferred" in line:
            parts = line.split()
            if len(parts) > 3:
                return parts[3].split('/')[0]
    return None

# --- Start asyncio event loop ---
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

# --- GUI ---
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
        self.ip_entry.insert(0, "")
        self.ip_entry.pack(pady=(0, pad_y))

        tk.Button(self.root, text="Fetch IP Address", font=("Arial", 12), command=self.fetch_ip).pack(pady=(0, pad_y))

        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=(0, pad_y))
        tk.Label(status_frame, text="Connection Status:", font=("Arial", 12)).pack(side="left")
        self.status_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=10)
        self._update_status("grey")

        channels_frame = tk.Frame(self.root)
        channels_frame.pack(pady=(0, pad_y))
        for i in range(5):
            btn_open = tk.Button(
                channels_frame,
                text=f"Ch {i+1} Open",
                font=("Arial", 10),
                width=10,
                command=lambda n=i: self.on_valve(n, True)
            )
            btn_open.grid(row=0, column=2*i, padx=5)

            btn_close = tk.Button(
                channels_frame,
                text=f"Ch {i+1} Close",
                font=("Arial", 10),
                width=10,
                command=lambda n=i: self.on_valve(n, False)
            )
            btn_close.grid(row=0, column=2*i + 1, padx=5)

    def _update_status(self, color: str):
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 18, 18, fill=color, outline=color)

    def fetch_ip(self):
        global bento_controller_ip
        ip = get_ip_controller()
        if ip:
            bento_controller_ip = ip
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, ip)
            self._update_status("green")
        else:
            self._update_status("red")

    def on_valve(self, channel_number: int, open_value: bool):
        self._update_status("orange")
        async def _task():
            try:
                await pneumatic_set_valve(channel_number, open_value)
                self.root.after(0, lambda: self._update_status("green"))
            except Exception:
                self.root.after(0, lambda: self._update_status("red"))
        schedule_coro(_task())

if __name__ == "__main__":
    PneumaticControlGUI()
