from dotenv import load_dotenv
import os
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent
ENV_PATH = PROJECT_PATH / ".env"

# Load environment variables
load_dotenv(ENV_PATH)

# Get QUOTES_FILE with fallback to default value
QUOTES_FILE = os.getenv('QUOTES_FILE', 'quotes.txt')
