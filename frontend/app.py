import gradio as gr
from backend.model_services import get_available_models, get_available_whisper_models
from backend.summarizer import translate_and_summarize
from backend.rag_app.query_rag import query_rag

# Function to handle summarization and return transcript file path
def gradio_app(file, context: str, whisper_model_name: str, llm_model_name: str) -> tuple[str, gr.File]:
    if file.endswith(".txt"):
        with open(file, "r") as f:
            transcript = f.read().strip()
        summary, transcript_file = translate_and_summarize(
            transcript, context, whisper_model_name, llm_model_name, is_transcript=True
        )
    else:
        summary, transcript_file = translate_and_summarize(
            file, context, whisper_model_name, llm_model_name
        )
    return summary, gr.update(value=transcript_file, visible=True)

# Function to handle chat queries to the transcript
def chat_with_transcript(transcript_file, query_text, history):
    response = query_rag(transcript_file, query_text, history).response_text
    # Return updated history and clear input
    return history, ""  # History is updated within query_rag

# Function to clear the inputs and outputs
def clear_all():
    return None, "", gr.update(value=None, visible=False), [], gr.update(interactive=False)

# Function to update clear button visibility
def update_clear_button(file, summary, history):
    if file or summary or history:
        return gr.update(interactive=True)
    return gr.update(interactive=False)

# Function to create and configure the Gradio interface
def create_gradio_interface():
    ollama_models = get_available_models()
    whisper_models = get_available_whisper_models()

    with gr.Blocks() as app:
        gr.Markdown(
            "<h2 style='text-align: center;'>Meeting Summarizer and Interactive Chat</h2>"
        )

        with gr.Row():
            with gr.Column():
                file_input = gr.File(label="Upload Audio/Video or Transcription File (.txt)")
                context_input = gr.Textbox(
                    label="Context (optional)",
                    placeholder="Provide any additional context for the summary",
                )
                whisper_model_dropdown = gr.Dropdown(
                    choices=whisper_models,
                    label="Select a Whisper model for audio-to-text conversion",
                    value=whisper_models[0] if whisper_models else None,
                )
                ollama_model_dropdown = gr.Dropdown(
                    choices=ollama_models,
                    label="Select a model for summarization",
                    value=ollama_models[0] if ollama_models else None,
                )
                submit_button = gr.Button("Submit")
                clear_button = gr.Button("Clear", interactive=False)  # Initially disabled

            with gr.Column():
                summary_output = gr.Textbox(label="Summary", show_copy_button=True)
                transcript_download = gr.File(label="Download Transcript", visible=False)
                
                gr.Markdown("### Ask questions about the transcript content below:")
                chat_history = gr.Chatbot(label="Chatbot", type="messages")
                user_query_input = gr.Textbox(label="Your Question", placeholder="Ask about the transcript content")
                query_button = gr.Button("Ask")

        submit_button.click(
            fn=gradio_app,
            inputs=[file_input, context_input, whisper_model_dropdown, ollama_model_dropdown],
            outputs=[summary_output, transcript_download]
        )

        # Initialize an empty history list for managing conversation context
        query_button.click(
            fn=chat_with_transcript,
            inputs=[transcript_download, user_query_input, gr.State([])],  # Initialize history as an empty list
            outputs=[chat_history, user_query_input]
        )

        clear_button.click(
            fn=clear_all,
            inputs=[],
            outputs=[file_input, summary_output, transcript_download, chat_history, clear_button]
        )

        file_input.change(fn=update_clear_button, inputs=[file_input, summary_output, chat_history], outputs=clear_button)
        summary_output.change(fn=update_clear_button, inputs=[file_input, summary_output, chat_history], outputs=clear_button)
        chat_history.change(fn=update_clear_button, inputs=[file_input, summary_output, chat_history], outputs=clear_button)

    return app

# Launch the Gradio app
if __name__ == "__main__":
    create_gradio_interface().launch()
