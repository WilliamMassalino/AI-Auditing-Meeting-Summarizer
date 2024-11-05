import os
import requests

OLLAMA_SERVER_URL = "http://localhost:11434"
WHISPER_MODEL_DIR = "./whisper.cpp/models"

def get_available_models() -> list[str]:
    """
    Retrieves a list of all available models from the Ollama server and extracts the model names.

    Returns:
        A list of model names available on the Ollama server.
    """
    response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags")
    if response.status_code == 200:
        models = response.json()["models"]
        llm_model_names = [model["model"] for model in models]
        return llm_model_names
    else:
        raise Exception(f"Failed to retrieve models from Ollama server: {response.text}")

def get_available_whisper_models() -> list[str]:
    """
    Retrieves a list of available Whisper models based on downloaded .bin files.

    Returns:
        A list of available Whisper model names.
    """
    valid_models = ["base", "small", "medium", "large", "large-V3"]
    model_files = [f for f in os.listdir(WHISPER_MODEL_DIR) if f.endswith(".bin")]
    whisper_models = [
        os.path.splitext(f)[0].replace("ggml-", "")
        for f in model_files
        if any(valid_model in f for valid_model in valid_models) and "test" not in f
    ]
    return list(set(whisper_models))