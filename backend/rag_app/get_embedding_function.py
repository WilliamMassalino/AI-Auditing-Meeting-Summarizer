from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_function():
    # Use a CPU-friendly model
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    return embeddings