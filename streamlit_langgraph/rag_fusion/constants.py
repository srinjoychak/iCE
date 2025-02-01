import os
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_chroma import Chroma
import torch
import gc
from dotenv import load_dotenv
from logger_config import configure_logging

load_dotenv()
logger = configure_logging('logs', 'application.log')

try:
    ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
except NameError:
    ROOT_DIRECTORY = os.getcwd()
    
PERSIST_DIRECTORY = f"{ROOT_DIRECTORY}/DB"

# Define the folder for storing database
SOURCE_DIRECTORY = f"{ROOT_DIRECTORY}/SOURCE_DOCUMENTS"

# Define the Chroma settings
CHROMA_SETTINGS = Settings(
    anonymized_telemetry=False,
    is_persistent=True,
)

try:
    # Get environment variables
    DEVICE_TYPE = os.getenv("DEVICE_TYPE")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

    # Validate environment variables
    if not DEVICE_TYPE or not EMBEDDING_MODEL_NAME:
        raise ValueError("DEVICE_TYPE or EMBEDDING_MODEL_NAME environment variables are not set.")

    # Initialize embeddings
    EMBEDDINGS = HuggingFaceInstructEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": DEVICE_TYPE}
    )

    # Initialize database
    DB = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=EMBEDDINGS,
        client_settings=CHROMA_SETTINGS,
    )

    logger.info("Vector DB (Chroma) initialized successfully.")

except ValueError as ve:
    logger.error(f"Configuration error: {ve}")
except ImportError as ie:
    logger.error(f"Import error: {ie}")
except Exception as e:
    logger.error(f"Error initializing Vector DB (Chroma): {e}")

def get_device_type():
    if torch.backends.mps.is_available():
        return "mps"  # Apple Silicon Macs
    elif torch.cuda.is_available():
        return "cuda"  # NVIDIA GPU
    else:
        return "cpu"  # Fallback to CPU
    
def release_model_memory():
    """Release the memory used by the embedding model."""
    device_type = get_device_type()  
    if device_type == "cuda" and torch.cuda.is_available():
        torch.cuda.empty_cache()
    elif device_type == "mps" and torch.backends.mps.is_available():
        torch.mps.empty_cache()
    elif device_type == "cpu":
        pass

    gc.collect()
