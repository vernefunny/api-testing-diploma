import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 10
