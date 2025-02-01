import os
import sys
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_ollama import OllamaLLM, ChatOllama
from llm import llm_provider
from logger_config import configure_logging

# Add parent directory to the Python path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Configure logging
logger = configure_logging('logs', 'rag_query.log')

# Get LLM instance
llm = llm_provider.get_llm_by_mode()

def log_and_handle_error(message, exception):
    """
    Logs error messages and exception details.
    """
    logger.error(f"{message}: {exception}")
    return None

def handle_response(response):
    """
    Handles the response object and returns the content if valid.
    """
    if isinstance(response, str):
        return response
    elif hasattr(response, 'content'):
        return response.content
    else:
        logger.warning("Unexpected response format")
        return None

def generate_non_streaming_response(system_prompt, user_query):
    """
    Handles non-streaming responses from the LLM.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    try:
        if isinstance(llm, (AzureChatOpenAI, ChatOpenAI)):
            logger.info("Using AzureChatOpenAI - Non-streaming")
            response = llm.invoke(input=messages)
            return handle_response(response)

        elif isinstance(llm, OllamaLLM):
            logger.info("Using OllamaLLM - Non-streaming")
            response = llm.invoke(input=messages)
            return handle_response(response)

        elif isinstance(llm, ChatOllama):
            logger.info("Using ChatOllama - Non-streaming")
            response = llm.invoke(input=messages)
            return handle_response(response)

        else:
            logger.error("Unsupported LLM type.")
            return None

    except Exception as e:
        return log_and_handle_error("Error during non-streaming response generation", e)

def generate_streaming_response(system_prompt, user_query):
    """
    Handles streaming responses from the LLM.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    try:
        if isinstance(llm, (AzureChatOpenAI, ChatOpenAI)):
            logger.info("Using AzureChatOpenAI - Streaming")
            response_stream = llm.stream(input=messages)
            for chunk in response_stream:
                yield chunk.content

        elif isinstance(llm, OllamaLLM):
            logger.info("Using OllamaLLM - Streaming")
            response_stream = llm.stream(input=messages)
            for chunk in response_stream:
                yield chunk

        elif isinstance(llm, ChatOllama):
            logger.info("Using ChatOllama - Streaming")
            response_stream = llm.stream(input=messages)
            for chunk in response_stream:
                yield chunk.content

        else:
            logger.error("Unsupported LLM type.")
            return None

    except Exception as e:
        log_and_handle_error("Error during streaming response generation", e)
        return None
