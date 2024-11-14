import os
import sys

# Ensure the project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from langchain_chroma import Chroma
from .get_embedding_function import get_embedding_function

# CHROMA_PATH in the root directory
CHROMA_PATH = os.path.join('data', 'chroma')  # 'data/chroma' in root directory

def get_chroma_db():
    # Get the embedding object
    embeddings = get_embedding_function()
    # Connect to the existing Chroma database
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )
    return vectorstore
