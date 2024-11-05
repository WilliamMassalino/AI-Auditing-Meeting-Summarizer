import os
import subprocess
import json
import requests
from .model_services import OLLAMA_SERVER_URL  # Import the URL for the Ollama server from the model services module
from .audio_processing import preprocess_audio_file  # Import the audio preprocessing function
from langdetect import detect, LangDetectException  # Import language detection and exception handling

# Function to generate a summary using a specified language model on the Ollama server
def summarize_with_model(llm_model_name: str, context: str, text: str, language: str) -> str:
    # Construct the prompt based on the detected language
    if language == "pt":
        # Prompt in Portuguese if the language is detected as Portuguese
        prompt = f"""Você recebeu uma transcrição de uma reunião, juntamente com um contexto opcional.
        
        Contexto: {context if context else 'Nenhum contexto adicional fornecido.'}
        
        A transcrição é a seguinte:
        
        {text}
        
        Por favor, resuma a transcrição."""
    else:
        # Default to English if the language is not Portuguese
        prompt = f"""You are given a transcript from a meeting, along with some optional context.
        
        Context: {context if context else 'No additional context provided.'}
        
        The transcript is as follows:
        
        {text}
        
        Please summarize the transcript."""

    # Set headers for the HTTP request
    headers = {"Content-Type": "application/json"}
    # Prepare the data payload with the model name and prompt
    data = {"model": llm_model_name, "prompt": prompt}
    
    # Make a POST request to the Ollama server to generate the summary
    response = requests.post(
        f"{OLLAMA_SERVER_URL}/api/generate",
        json=data,
        headers=headers,
        stream=True  # Enable streaming response
    )

    # If the request is successful, process the streaming response
    if response.status_code == 200:
        full_response = ""
        try:
            for line in response.iter_lines():
                if line:
                    # Decode and parse each line of the streaming response
                    decoded_line = line.decode("utf-8")
                    json_line = json.loads(decoded_line)
                    # Append the response text from each line
                    full_response += json_line.get("response", "")
                    # Break if the "done" flag is True, indicating the response is complete
                    if json_line.get("done", False):
                        break
            return full_response
        except json.JSONDecodeError:
            # Handle JSON decoding errors
            print("Error: Response contains invalid JSON data.")
            return f"Failed to parse the response from the server. Raw response: {response.text}"
    else:
        # Raise an exception if the server response is unsuccessful
        raise Exception(f"Failed to summarize with model {llm_model_name}: {response.text}")

# Function to process an audio file or direct text and generate a summary
def translate_and_summarize(
    file_path_or_text: str,
    context: str,
    whisper_model_name: str,
    llm_model_name: str,
    is_transcript: bool = False  # Flag to indicate if the input is a direct transcript
) -> tuple[str, str]:
    if is_transcript:
        # If the input is a transcript, use the text directly
        transcript = file_path_or_text
    else:
        # If the input is an audio file, preprocess and convert it to a transcript
        output_file = "output.txt"
        # Convert audio to WAV format suitable for Whisper
        audio_file_wav = preprocess_audio_file(file_path_or_text)
        # Construct and execute the Whisper command for transcription
        whisper_command = (
            f'./whisper.cpp/main -m ./whisper.cpp/models/ggml-{whisper_model_name}.bin '
            f'-f "{audio_file_wav}" --language auto > {output_file}'
        )
        subprocess.run(whisper_command, shell=True, check=True)  # Run the command using subprocess
        # Read the generated transcript from the output file
        with open(output_file, "r") as f:
            transcript = f.read().strip()
        # Clean up temporary files
        os.remove(audio_file_wav)
        os.remove(output_file)

    # Validate the transcript length
    if not transcript or len(transcript) < 20:
        raise ValueError("Transcript is empty or too short for language detection.")

    try:
        # Detect the language of the transcript
        detected_language = detect(transcript)
    except LangDetectException:
        # Handle cases where language detection fails
        raise ValueError("Failed to detect language due to insufficient text.")

    # Determine the language for summarization
    language = "pt" if detected_language.startswith("pt") else "en"
    # Generate the summary using the specified model
    summary = summarize_with_model(llm_model_name, context, transcript, language)
    
    # Save the transcript to a file
    transcript_file_path = "transcript.txt"
    with open(transcript_file_path, "w") as f:
        f.write(transcript)
    
    # Return the summary and the path to the saved transcript file
    return summary, transcript_file_path
