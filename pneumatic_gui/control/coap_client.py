import json
import logging
from aiocoap import Context, Message, POST
import asyncio

logger = logging.getLogger(__name__)

bento_controller_ip = None  # This should be set externally by GUI or config

def set_controller_ip(ip: str):
    global bento_controller_ip
    bento_controller_ip = ip

def get_controller_ip():
    return bento_controller_ip

async def send_controller_comand(register: str, value, close_connection=False) -> dict:
    if not bento_controller_ip:
        raise Exception("Controller IP not set.")

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
