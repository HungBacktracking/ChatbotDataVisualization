import logging
import sys
import os

def setup_logging():
    """Setup logging configuration with UTF-8 encoding support"""
    
    # Set UTF-8 encoding for stdout/stderr on Windows
    if sys.platform.startswith('win'):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", encoding='utf-8')
        ]
    )
    
    # Set logging level for specific loggers to reduce noise
    logging.getLogger("llama_index.core.chat_engine.condense_plus_context").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)
