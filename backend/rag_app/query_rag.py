import os
import sys

# Ensure the project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

import argparse
from dataclasses import dataclass
from typing import List
from typing_extensions import TypedDict
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from backend.rag_app.get_chroma_db import get_chroma_db
from langchain.schema import HumanMessage

# Define the prompt template with clear instructions for contextual memory and direct recall
PROMPT_TEMPLATE = """
You are an assistant who answers the user's question based on the provided context and the conversation history. Use the context and the conversation history to provide a concise and accurate answer to the user's question. Do not include the context, the history, or any extraneous information in your response.

Conversation History:
{history}

Context:
{context}

Question:
{question}

Answer:
"""

# Initialize LLaMA model
local_llm = "llama3.2"
llm = ChatOllama(model=local_llm, temperature=0)

# Function to retrieve the last question from history
def get_last_question(history):
    for message in reversed(history):
        if message.get("role") == "user":
            return message["content"]
    return "No previous question found."

# Function to format conversation history
def format_history(history):
    return "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])

@dataclass
class QueryResponse:
    query_text: str
    response_text: str
    sources: List[str]

# Function to generate response from LLM
def generate_response(prompt: str) -> str:
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])
    # Split the response to extract the text after "Answer:"
    answer = response.content.strip()
    if "Answer:" in answer:
        answer = answer.split("Answer:")[-1].strip()
    return answer

def query_rag(transcript_file: str, query_text: str, history: list, thread_id: str = "1") -> QueryResponse:
    # If the user asks for the last question
    if "last question" in query_text.lower():
        last_question = get_last_question(history)
        response_text = f"Your last question was: {last_question}"
        history.append({"role": "user", "content": query_text})
        history.append({"role": "assistant", "content": response_text})
        return QueryResponse(
            query_text=query_text, response_text=response_text, sources=[]
        )
    
    # Connect to the existing Chroma vectorstore
    db = get_chroma_db()

    # Search the vectorstore
    results = db.similarity_search_with_score(query_text, k=3)

    if not results:
        print("No relevant documents found.")
        response_text = "No relevant information found."
        history.append({"role": "user", "content": query_text})
        history.append({"role": "assistant", "content": response_text})
        return QueryResponse(
            query_text=query_text, response_text=response_text, sources=[]
        )

    # Prepare context and sources
    context_text = "\n".join([doc.page_content for doc, _ in results])
    sources = [doc.metadata.get("source", "Unknown") for doc, _ in results]

    # Format conversation history
    history_text = format_history(history)

    # Prepare the prompt with history
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(history=history_text, context=context_text, question=query_text)

    # Generate response using LLM
    response_text = generate_response(prompt)

    # Update history with the new question and response
    history.append({"role": "user", "content": query_text})
    history.append({"role": "assistant", "content": response_text})

    return QueryResponse(
        query_text=query_text, response_text=response_text, sources=sources
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query the RAG system.')
    parser.add_argument('query', type=str, help='The question to ask')
    args = parser.parse_args()
    # Initialize an empty history if needed
    response = query_rag("", args.query, history=[])
    print(response.response_text)
