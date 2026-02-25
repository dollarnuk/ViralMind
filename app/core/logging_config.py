import logging
import sys

def setup_logging():
    """Configures the standard logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Get a global logger for the main app
logger = logging.getLogger("viralmind")
