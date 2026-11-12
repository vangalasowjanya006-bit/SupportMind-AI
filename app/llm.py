from os import getenv

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 2


def get_chat_model(**overrides) -> ChatGoogleGenerativeAI:
    api_key = getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured")

    params = {
        "model": getenv("GEMINI_MODEL", DEFAULT_MODEL),
        "google_api_key": api_key,
        "temperature": DEFAULT_TEMPERATURE,
        "timeout": DEFAULT_TIMEOUT,
        "max_retries": DEFAULT_MAX_RETRIES,
    }
    params.update(overrides)
    return ChatGoogleGenerativeAI(**params)
