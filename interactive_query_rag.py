from backend.rag_app.query_rag import query_rag

print("Chat with the transcript (type 'exit' to quit):")
while True:
    query = input("You: ")
    if query.lower() == 'exit':
        break
    try:
        response = query_rag(query)
        print("Response:", response)
    except Exception as e:
        print("An error occurred:", e)