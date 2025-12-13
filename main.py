"""
Telegram Bot Controller - Main Entry Point
Controla el navegador Brave mediante comandos de texto en Telegram
"""

import os
import sys
import asyncio
import signal
from pathlib import Path
from dotenv import load_dotenv

# Agregar el directorio raíz al path para imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.utils.logger import setup_logger
from src.utils.config_loader import ConfigLoader
from src.telegram_bot import TelegramBot
from src.llm_processor import LLMProcessor
from src.browser_controller import BrowserController

# Cargar variables de entorno
load_dotenv()

# Configurar logger
logger = setup_logger()


class BotApplication:
    """Clase principal que coordina todos los componentes del bot"""
    
    def __init__(self):
        self.config = None
        self.telegram_bot = None
        self.llm_processor = None
        self.browser_controller = None
        self.running = False
        
    def load_configuration(self):
        """Carga la configuración del sistema"""
        try:
            config_path = ROOT_DIR / "config" / "config.json"
            self.config = ConfigLoader(config_path).load()
            logger.info("Configuración cargada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            return False
    
    def validate_environment(self):
        """Valida que todas las variables de entorno necesarias estén presentes"""
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "LLM_API_KEY",
            "LLM_PROVIDER"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
            logger.error("Por favor configura el archivo .env correctamente")
            return False
        
        logger.info("Variables de entorno validadas correctamente")
        return True
    
    def initialize_components(self):
        """Inicializa todos los componentes del sistema"""
        try:
            # Inicializar el procesador LLM
            self.llm_processor = LLMProcessor(
                api_key=os.getenv("LLM_API_KEY"),
                provider=os.getenv("LLM_PROVIDER"),
                config=self.config.get("llm", {})
            )
            logger.info("Procesador LLM inicializado")
            
            # Inicializar el controlador del navegador
            self.browser_controller = BrowserController(
                config=self.config.get("browser", {})
            )
            logger.info("Controlador de navegador inicializado")
            
            # Inicializar el bot de Telegram
            self.telegram_bot = TelegramBot(
                token=os.getenv("TELEGRAM_BOT_TOKEN"),
                allowed_chat_ids=os.getenv("TELEGRAM_CHAT_ID").split(","),
                llm_processor=self.llm_processor,
                browser_controller=self.browser_controller,
                config=self.config
            )
            logger.info("Bot de Telegram inicializado")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar componentes: {e}")
            return False
    
    async def start(self):
        """Inicia la aplicación"""
        logger.info("=" * 60)
        logger.info("Iniciando Telegram Bot Controller")
        logger.info("=" * 60)
        
        # Validar entorno
        if not self.validate_environment():
            return False
        
        # Cargar configuración
        if not self.load_configuration():
            return False
        
        # Inicializar componentes
        if not self.initialize_components():
            return False
        
        # Iniciar el bot
        try:
            self.running = True
            logger.info("Bot iniciado correctamente. Esperando mensajes...")
            logger.info("Presiona Ctrl+C para detener el bot")
            
            await self.telegram_bot.start()
            
        except Exception as e:
            logger.error(f"Error al iniciar el bot: {e}")
            return False
        
        return True
    
    async def stop(self):
        """Detiene la aplicación de forma limpia"""
        logger.info("Deteniendo el bot...")
        self.running = False
        
        if self.telegram_bot:
            await self.telegram_bot.stop()
        
        if self.browser_controller:
            self.browser_controller.cleanup()
        
        logger.info("Bot detenido correctamente")
    
    def handle_shutdown(self, signum, frame):
        """Maneja las señales de cierre del sistema"""
        logger.info(f"Señal {signum} recibida. Cerrando aplicación...")
        asyncio.create_task(self.stop())


async def main():
    """Función principal"""
    app = BotApplication()
    
    # Registrar manejadores de señales para cierre limpio
    signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(app.stop()))
    signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(app.stop()))
    
    try:
        # Iniciar la aplicación
        success = await app.start()
        
        if not success:
            logger.error("No se pudo iniciar la aplicación")
            sys.exit(1)
        
        # Mantener el bot corriendo
        while app.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupción de teclado detectada")
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
    finally:
        await app.stop()


if __name__ == "__main__":
    try:
        # Verificar versión de Python
        if sys.version_info < (3, 8):
            print("Error: Se requiere Python 3.8 o superior")
            sys.exit(1)
        
        # Ejecutar la aplicación
        asyncio.run(main())
        
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)