import asyncio
from core.logger_config import setup_logger
from server.ws_server import main
from modules.web_manager import WebHandler

if __name__ == '__main__':
    # Configurar logging antes de iniciar la aplicación
    setup_logger()
    
    asyncio.run(main())
    
    # Testing
    # web = WebHandler()
    # data = {
    #     "number": "+573027032694",
    #     "message": "Hello, this is a test message.",
    #     "pdf_path": None,
    #     "test": True
    # }
    # web.execute(**data)
    