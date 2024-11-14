import os
import subprocess
import json
import requests
from .model_services import OLLAMA_SERVER_URL
from .audio_processing import preprocess_audio_file
from langdetect import detect, LangDetectException
from backend.populate_database import main as update_database

# Define the path to the transcript file
TRANSCRIPT_PATH = os.path.join("data", "transcript.txt")

def ensure_data_directory():
    """Ensure that the 'data' directory exists."""
    os.makedirs(os.path.dirname(TRANSCRIPT_PATH), exist_ok=True)

def summarize_with_model(llm_model_name: str, context: str, text: str, language: str) -> str:
    """Generate a summary using the specified language model on the Ollama server."""
    # Construct the prompt based on the detected language
    prompt = (
        f"Você recebeu uma transcrição de uma reunião, juntamente com um contexto opcional.\n\n"
        f"Contexto: {context if context else 'Nenhum contexto adicional fornecido.'}\n\n"
        f"A transcrição é a seguinte:\n\n{text}\n\nPor favor, resuma a transcrição."
        if language == "pt" else
        f"You are given a transcript from a meeting, along with some optional context.\n\n"
        f"Context: {context if context else 'No additional context provided.'}\n\n"
        f"The transcript is as follows:\n\n{text}\n\nPlease summarize the transcript."
    )

    headers = {"Content-Type": "application/json"}
    data = {"model": llm_model_name, "prompt": prompt}

    response = requests.post(
        f"{OLLAMA_SERVER_URL}/api/generate",
        json=data,
        headers=headers,
        stream=True
    )

    # Process the streaming response from the server
    if response.status_code == 200:
        full_response = ""
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    json_line = json.loads(decoded_line)
                    full_response += json_line.get("response", "")
                    if json_line.get("done", False):
                        break
            return full_response
        except json.JSONDecodeError:
            print("Error: Response contains invalid JSON data.")
            return f"Failed to parse the response from the server. Raw response: {response.text}"
    else:
        raise Exception(f"Failed to summarize with model {llm_model_name}: {response.text}")

def translate_and_summarize(
    file_path_or_text: str,
    context: str,
    whisper_model_name: str,
    llm_model_name: str,
    is_transcript: bool = False
) -> tuple[str, str]:
    """Process an audio file or direct text and generate a summary."""
    # Check if the 'data' directory exists, create it if not
    ensure_data_directory()

    # Handle transcript text or audio file
    if is_transcript:
        transcript = file_path_or_text
    else:
        output_file = "output.txt"
        audio_file_wav = preprocess_audio_file(file_path_or_text)
        
        whisper_command = (
            f'./whisper.cpp/main -m ./whisper.cpp/models/ggml-{whisper_model_name}.bin '
            f'-f "{audio_file_wav}" --language auto > {output_file}'
        )
        subprocess.run(whisper_command, shell=True, check=True)
        
        with open(output_file, "r") as f:
            transcript = f.read().strip()
        
        os.remove(audio_file_wav)
        os.remove(output_file)

    # Validate transcript length
    if not transcript or len(transcript) < 20:
        raise ValueError("Transcript is empty or too short for language detection.")

    # Detect language
    try:
        detected_language = detect(transcript)
    except LangDetectException:
        raise ValueError("Failed to detect language due to insufficient text.")

    # Determine language for summarization
    language = "pt" if detected_language.startswith("pt") else "en"
    summary = summarize_with_model(llm_model_name, context, transcript, language)

    # Save the transcript to 'transcript.txt' and update the database
    with open(TRANSCRIPT_PATH, "w") as f:
        f.write(transcript)
    
    update_database(TRANSCRIPT_PATH, reset=False)
    
    return summary, TRANSCRIPT_PATH
