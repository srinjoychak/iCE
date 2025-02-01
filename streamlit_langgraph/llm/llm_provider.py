from dotenv import load_dotenv
from . import azure_openai_llm
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import os
from logger_config import logging

load_dotenv()

MODE = os.getenv("MODE")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

def get_llm_by_mode():
    if MODE is not None and MODE.lower() == "AzureOpenAI".lower():
        logging.info("Using Azure OpenAI LLM")
        return azure_openai_llm.get_llm()
    elif MODE is not None and MODE.lower() == "Offline".lower():
        logging.info("Using Ollama LLM")
        return ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
    elif MODE is not None and MODE.lower() == "OpenAI".lower():
        logging.info("Using OpenAI LLM")
        return ChatOpenAI(model=OPENAI_MODEL)