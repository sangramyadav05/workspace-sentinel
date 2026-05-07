import os
from dotenv import load_dotenv

from core.paths import ENV_FILE

load_dotenv(dotenv_path=ENV_FILE)


class ConfigurationError(RuntimeError):
    """Raised when required local configuration is missing."""



def get_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ConfigurationError(
            "OPENROUTER_API_KEY is not set. "
            "Make sure it exists in your .env file."
        )

    return api_key
