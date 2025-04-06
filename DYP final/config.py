import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Configuration settings
DEFAULT_GROQ_API_KEY = "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"
GROQ_MODEL_VERSATILE = "llama3-70b-8192"
GROQ_MODEL_FAST = "llama3-8b-8192"  # Or use versatile for all
DATABASE_PATH = "./adaptlearn_data.db"