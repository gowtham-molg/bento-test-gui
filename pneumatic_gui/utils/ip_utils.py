from typing import Optional

def send_usb_command_retrieve_response(serial_port: str, command: str):
    # Mocked response for now
    return [" DHCP    preferred       1       172.16.50.74/255.255.255.0"]

def get_ip_controller(serial_port: str = "/dev/ttyUSB0") -> Optional[str]:
    lines = send_usb_command_retrieve_response(serial_port, "net ipv4")
    for line in lines:
        if "DHCP" in line and "preferred" in line:
            parts = line.split()
            if len(parts) > 3:
                return parts[3].split('/')[0]
    return None
