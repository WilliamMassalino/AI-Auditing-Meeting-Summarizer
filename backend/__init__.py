"""
Initialize the backend package.
"""
from .audio_processing import preprocess_audio_file
from .model_services import get_available_models, get_available_whisper_models
from .summarizer import translate_and_summarize

# Import RAG application functions
from .populate_database import main as update_chroma_database
from .rag_app.get_chroma_db import get_chroma_db
from .rag_app.get_embedding_function import get_embedding_function
from .rag_app.query_rag import query_rag