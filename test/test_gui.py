import pytest
from gui import get_ip_controller, send_usb_command_retrieve_response
import types
from gui import get_ip_controller, send_usb_command_retrieve_response

# Mocked USB command function for testing
def mocked_send_usb_command_retrieve_response(serial_port: str, command: str):
    return [
        "Some text",
        " DHCP    preferred       1       172.16.50.2/255.255.255.0",
        "Other line"
    ]

def test_get_ip_controller(monkeypatch):
    monkeypatch.setattr("gui.send_usb_command_retrieve_response", mocked_send_usb_command_retrieve_response)
    ip = get_ip_controller("/dev/ttyUSB0")
    assert ip == "172.16.50.2"

def test_send_usb_command_retrieve_response_type():
    # Make sure mocked function returns a list of strings
    result = mocked_send_usb_command_retrieve_response("/dev/ttyUSB0", "net ipv4")
    assert isinstance(result, list)
    assert all(isinstance(line, str) for line in result)
