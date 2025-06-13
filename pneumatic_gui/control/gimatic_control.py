from control.coap_client import send_controller_comand

async def send_gimatic_cmd(action: str):
    return await send_controller_comand("RELAY_TO_MODULE_J", {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": 0x0320,
        "cmd": "gimatic",
        "data": {"action": action, "wait": "no"}
    }, close_connection=True)

async def check_gimatic_status():
    return await send_controller_comand("RELAY_TO_MODULE_J", {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": 0x0320,
        "cmd": "gimatic",
        "data": {"action": "GIMATIC_CMD_STATUS"}
    }, close_connection=True)