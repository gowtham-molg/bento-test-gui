from control.coap_client import send_controller_comand

async def pneumatic_set_valve(channel_number: int, open_value: bool):
    return await send_controller_comand("RELAY_TO_MODULE_J", {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": 544,
        "cmd": "set_valve",
        "data": {"valve_n": channel_number, "open": open_value}
    }, close_connection=True)

async def pneumatic_read_valve_state(channel_number: int):
    return await send_controller_comand("RELAY_TO_MODULE_J", {
        "origin_can_id": 0x0402,
        "dest_can_bus_id": 544,
        "cmd": "p_read",
        "data": {"valve_n": channel_number}
    }, close_connection=True)
