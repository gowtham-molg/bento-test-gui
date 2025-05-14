import tkinter as tk
from tkinter import messagebox
# Add these imports for the async network command functions
import asyncio
import logging
import time

# You will also need to install and import aiocoap and its components
# import aiocoap
# from aiocoap import Context, Message, POST

# Set up a logger for demonstration (replace with your own logger if needed)
logger = logging.getLogger("controller")
logging.basicConfig(level=logging.DEBUG)

# Set your controller IP here or dynamically as needed
bento_controller_ip = "192.168.1.100"


class PneumaticControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pneumatic Control GUI")
        self.root.geometry("400x300")

        # Connection Status
        self.connection_status = True  # Assume always connected
        self.hardware_ip = "192.168.1.100"  # Example IP address

        # IP Address Display
        self.ip_label = tk.Label(root, text="Hardware IP Address:")
        self.ip_label.pack(pady=5)
        self.ip_entry = tk.Entry(root, width=30, justify="center")
        self.ip_entry.insert(0, self.hardware_ip)
        self.ip_entry.config(state="readonly")
        self.ip_entry.pack(pady=5)

        # Fetch IP Address Button
        self.fetch_ip_button = tk.Button(
            root,
            text="Fetch IP Address",
            command=self.fetch_ip_address
        )
        self.fetch_ip_button.pack(pady=5)

        # Connection Status Indicator
        self.status_label = tk.Label(root, text="Connection Status:")
        self.status_label.pack(pady=5)
        self.status_indicator = tk.Canvas(root, width=20, height=20)
        self.status_indicator.pack(pady=5)
        self.update_status_indicator()

        # Pneumatic Channel Buttons
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(pady=10)
        for i in range(1, 6):
            button = tk.Button(
                self.buttons_frame,
                text=f"Channel {i}",
                width=10,
                command=lambda ch=i: self.control_channel(ch),
            )
            button.grid(row=0, column=i - 1, padx=5)

    def update_status_indicator(self):
        self.status_indicator.delete("all")
        color = "green" if self.connection_status else "red"
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color)

    def control_channel(self, channel):
        if not self.connection_status:
            messagebox.showwarning(
                "Warning", "Please connect to the hardware before controlling channels."
            )
            return

        # Example: Toggle valve open/close (True/False)
        open_value = True  # or False, depending on your UI logic

        async def set_valve():
            try:
                await pneumatic_set_valve(channel, open_value)
                messagebox.showinfo("Channel Control", f"Channel {channel} set to {'open' if open_value else 'closed'}!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        asyncio.run(set_valve())

    def fetch_ip_address(self):
        # Placeholder for actual IP fetching logic
        # For now, just show a message box with the current IP
        messagebox.showinfo("Fetch IP", f"Current hardware IP: {self.hardware_ip}")


def get_ip_controller(serial_port: str = "/dev/ttyUSB0"):
    # get the ip of the controller connected via usb
    ip_str = send_usb_command_retrieve_response(serial_port, "net ipv4")
    # one of the lines has the format :
    #   DHCP    preferred       1       172.16.50.2/255.255.255.0
    for line in ip_str:
        if "DHCP" in line and "preferred" in line:
            parts = line.split()
            if len(parts) > 3:
                ip_with_mask = parts[3]
                ip = ip_with_mask.split('/')[0]
                return ip
    return None

# --- Add the async network command functions here ---

async def send_controller_comand(register: str, value, close_connection=False) -> dict:
    # sends the command to the controller
    # on success returns the payload of the reply as a dictionary
    timeout_s = 60

    logger.debug("send_controller_comand")
    import json

    if isinstance(value, str):
        payload = json.dumps({"reg": register, "val": value}).encode('utf-8')
    if isinstance(value, dict):
        if register not in ["RELAY_TO_MODULE_J", "FW_MNG", "LOG"]:
            raise Exception("Only relay to module J is allowed to send dictionaries")
        payload = json.dumps({"reg": register, "val": value}).encode('utf-8')

    logger.debug(f"target ip: {bento_controller_ip}")
    logger.debug(f"register: {register}, value: {value}")
    logger.debug(f"payload: {payload}")

    # Uncomment and use these lines if aiocoap is installed and configured
    # context = await Context.create_client_context()
    # ts = time.time()
    # request = Message(code=POST,
    #                   payload=payload,
    #                   uri=f"coap://{bento_controller_ip}/controller",
    #                   no_response=True)
    # try:
    #     response = await asyncio.wait_for(context.request(request).response, timeout=timeout_s)
    #     dt = (time.time() - ts)
    # except asyncio.TimeoutError:
    #     logger.error("Request timed out")
    #     raise Exception(f"Request timed out while waiting for CoAP cmd reply. {timeout_s} [s]")
    # except aiocoap.error.NetworkError:
    #     logger.error("Network error")
    #     raise Exception("Network error while sending CoAP cmd")
    # except Exception as e:
    #     logger.error(str(e))
    #     raise
    # if close_connection:
    #     await context.shutdown()
    # logger.debug(f"Request <-> Reply in dt: {dt:.4f} [s]\n Result: {response.code}\n{response.payload}")
    # logger.debug(f"Success: {response.code.is_successful()}")
    # logger.debug(f"host info: {response.remote.hostinfo}")
    # logger.debug(f"Response: {response}")
    # logger.debug(f"reponse payload: {len(response.payload)}, {response.payload}")
    # if (len(response.payload) > 0):
    #     try:
    #         decode_json = json.loads(response.payload.decode('utf-8'))
    #         json_formatted_str = json.dumps(decode_json, indent=2)
    #         logger.debug(f"json_formatted_str: {json_formatted_str}")
    #         return decode_json
    #     except Exception as ex:
    #         logger.info(f"response: {response}")
    #         logger.info(f"response.payload: {response.payload}")
    #         logger.error(f"Error decoding json: {ex}")
    #         return response.payload
    # else:
    #     logger.error("Error sending command")
    #     raise Exception("Error receiving reply")
    # For demonstration, just return a dummy dict
    return {"status": "success", "register": register, "value": value}

async def send_jInterface_cmd_relay_to_module(dest_can_bus_id: int, jinterface_data: dict):
    import json
    value_data_dict = {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": dest_can_bus_id,
        "cmd": jinterface_data["cmd"],
        "data": jinterface_data["data"]
    }
    logger.debug(f"""value_data_dict: {value_data_dict}""")
    reply = await send_controller_comand(register="RELAY_TO_MODULE_J", value=value_data_dict, close_connection=True)
    try:
        data = reply["data"]
    except Exception as e:
        logger.error("Reply does not contain data field ")
        logger.error(f"reply: {reply}")
        raise Exception("Error sending/executing request update memory")
    return data


if __name__ == "__main__":
    root = tk.Tk()
    app = PneumaticControlApp(root)
    root.mainloop()