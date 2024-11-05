import gradio as gr  # Import the Gradio library for creating a web interface
from backend.model_services import get_available_models, get_available_whisper_models  # Import functions to retrieve available models
from backend.summarizer import translate_and_summarize  # Import the function to process and summarize audio or text

# Main function to handle the Gradio interface logic
def gradio_app(file, context: str, whisper_model_name: str, llm_model_name: str) -> tuple[str, str]:
    """
    Handles the uploaded file and generates a summary based on the content.
    
    Args:
        file: The uploaded file (can be audio, video, or a .txt file containing a transcription)
        context (str): Optional context provided by the user for a better summary
        whisper_model_name (str): Name of the Whisper model to use for audio-to-text conversion
        llm_model_name (str): Name of the model to use for summarization
    
    Returns:
        tuple[str, str]: The generated summary and the path to the transcript file
    """
    # Check if the uploaded file is a text file (.txt)
    if file.endswith(".txt"):
        # Read the text from the .txt file
        with open(file, "r") as f:
            transcript = f.read().strip()
        # If the file is a transcript, skip audio processing and directly summarize
        summary, transcript_file = translate_and_summarize(
            transcript, context, whisper_model_name, llm_model_name, is_transcript=True
        )
    else:
        # If the file is an audio/video file, process it to generate a transcript and then summarize
        summary, transcript_file = translate_and_summarize(
            file, context, whisper_model_name, llm_model_name
        )
    
    return summary, transcript_file  # Return the summary and the downloadable transcript

# Function to create and configure the Gradio interface
def create_gradio_interface():
    """
    Creates the Gradio interface for the meeting summarizer application.
    
    Returns:
        Gradio Interface object
    """
    # Retrieve available models for audio-to-text and summarization
    ollama_models = get_available_models()
    whisper_models = get_available_whisper_models()

    # Define the Gradio interface
    iface = gr.Interface(
        fn=gradio_app,  # Function to call when the user interacts with the interface
        inputs=[
            gr.File(label="Upload Audio/Video or Transcription File (.txt)"),  # File input for audio/video or .txt
            gr.Textbox(
                label="Context (optional)",  # Optional textbox for additional context
                placeholder="Provide any additional context for the summary",
            ),
            gr.Dropdown(
                choices=whisper_models,  # Dropdown to select the Whisper model
                label="Select a Whisper model for audio-to-text conversion",
                value=whisper_models[0] if whisper_models else None,  # Default selection
            ),
            gr.Dropdown(
                choices=ollama_models,  # Dropdown to select the summarization model
                label="Select a model for summarization",
                value=ollama_models[0] if ollama_models else None,  # Default selection
            ),
        ],
        outputs=[
            gr.Textbox(label="Summary", show_copy_button=True),  # Textbox to display the generated summary
            gr.File(label="Download Transcript"),  # File output for the downloadable transcript
        ],
        analytics_enabled=False,  # Disable analytics for the interface
        title="Auditing Meeting Summarizer",  # Title of the interface
        description="Upload an audio/video file or a transcription (.txt) and get a summary of the key concepts discussed.",  # Description
    )
    return iface  # Return the configured interface
