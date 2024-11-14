import argparse
import os
import sys
import shutil
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from backend.rag_app.get_embedding_function import get_embedding_function

# Ensure the project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Paths to data directories in the root directory
CHROMA_PATH = os.path.join('data', 'chroma')  # This will be 'data/chroma' in the root directory
DATA_SOURCE_PATH = os.path.join('data', 'transcript.txt')  # 'data/transcript.txt' in root directory

def main(transcript_path=DATA_SOURCE_PATH, reset=False):
    if reset:
        print("✨ Clearing Database")
        clear_database()

    # Load and process the transcript file
    documents = load_transcription(transcript_path)
    chunks = split_documents(documents)
    add_to_chroma(chunks)

def load_transcription(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    document = Document(page_content=content, metadata={"source": file_path})
    return [document]

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_chroma(chunks: list[Document]):
    embeddings = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    chunks_with_ids = calculate_chunk_ids(chunks)
    # Check if the database exists and retrieve existing IDs
    if os.path.exists(CHROMA_PATH):
        existing_ids = db.get(include=[])["ids"]
    else:
        existing_ids = []
    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

    if new_chunks:
        print(f"👉 Adding new documents: {len(new_chunks)}")
        db.add_documents(new_chunks, ids=[chunk.metadata["id"] for chunk in new_chunks])
        # Remove or comment out the line below
        # db.persist()
    else:
        print("✅ No new documents to add")


def calculate_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        current_page_id = f"{source}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk.metadata["id"] = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

    return chunks

def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    main(reset=args.reset)
