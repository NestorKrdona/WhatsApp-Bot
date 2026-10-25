from server.ws_server import main
from core.logger_config import setup_logger

if __name__ == "__main__":
    import asyncio
    setup_logger()
    asyncio.run(main())
