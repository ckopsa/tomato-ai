import logging

from tomato_ai.entrypoints.fastapi_app import create_app
from tomato_ai import bootstrap

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("tomato_ai").setLevel(logging.INFO)

# Bootstrap the application
bootstrap.bootstrap()

app = create_app()
