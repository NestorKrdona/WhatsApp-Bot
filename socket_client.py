import asyncio
import websockets
import json
import base64
from loguru import logger

async def test_ws():
    uri = "ws://localhost:3060"
    # PDF vacío en base64 (un PDF válido pero sin contenido)
    pdf_base64 = "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0tpZHMgWzMgMCBSXS9Db3VudCAxPj4KZW5kb2JqCjMgMCBvYmoKPDwvVHlwZS9QYWdlL1BhcmVudCAyIDAgUi9NZWRpYUJveCBbMCAwIDYxMiA3OTJdL0NvbnRlbnRzIDQgMCBSL1Jlc291cmNlczw8Pj4+PgplbmRvYmoKNCAwIG9iago8PC9MZW5ndGggMTAgPj4Kc3RyZWFtCgpzdHJlYW0KZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTAgMDAwMDAgbiAKMDAwMDAwMDAyNSAwMDAwMCBuIAowMDAwMDAwMDYwIDAwMDAwIG4gCjAwMDAwMDAxMDUgMDAwMDAgbiAKdHJhaWxlcgo8PC9TaXplIDUvUm9vdCAxIDAgUi9JbmZvIDUgMCBSCj4+CnN0YXJ0eHJlZgo2MTYKJSVFT0YK"
    pdf_bytes = base64.b64decode(pdf_base64)
    async with websockets.connect(uri) as websocket:
        logger.info("Conectado al servidor WebSocket.")
        # Mensaje de prueba tipo JSON
        mensaje = {
            "metadata": {
                "phoneNumber": "3027032694",
                "message": "Hola, este es un mensaje de prueba.",
                "fileName": "test.pdf"
            },
            "PDF": {
                "data": list(pdf_bytes)  # Enviar como lista de bytes
                # "data": pdf_base64  # Enviar como lista de bytes
            }
        }
        await websocket.send(json.dumps(mensaje))
        logger.info("Mensaje enviado al servidor.")
        try:
            while True:
                respuesta = await websocket.recv()
                logger.info(f"Respuesta del servidor: {respuesta}")
        except websockets.ConnectionClosed:
            logger.info("Conexión cerrada por el servidor.")

if __name__ == "__main__":
    asyncio.run(test_ws()) 