import chromadb
import json
import ollama

def main():
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")

    # Create or get the collection
    collection = client.get_or_create_collection("scenarios")

    # --- Load all data sources ---
    all_documents = []

    # 1. Load scenarios from scenarios.json
    with open('../app-server/scenarios.json', 'r', encoding='utf-8') as f:
        scenarios_data = json.load(f)
        for scenario in scenarios_data['data']:
            all_documents.append({
                'id': scenario['title'],  # Use title as ID for scenarios
                'content': f"{scenario['category']} {scenario['title']} {scenario['question']} {scenario['answer']}",
                'metadata': {'category': scenario.get('category', 'general')}
            })

    # 2. Load meta information from meta_info.json
    with open('meta_info.json', 'r', encoding='utf-8') as f:
        meta_data = json.load(f)
        for item in meta_data:
            all_documents.append({
                'id': item['id'],  # Use 'id' field from the file
                'content': f"{item['title']} {item['question']} {item['answer']}",
                'metadata': {'category': 'meta'}
            })

    # --- Process and ingest all documents ---
    for doc in all_documents:
        # Generate embedding using Ollama
        response = ollama.embeddings(model='mxbai-embed-large', prompt=doc['content'])
        embedding = response["embedding"]
        
        # Add to ChromaDB collection
        collection.add(
            ids=[doc['id']],
            embeddings=[embedding],
            documents=[doc['content']],
            metadatas=[doc['metadata']]
        )
        print(f"Ingested document: {doc['id']}")

if __name__ == "__main__":
    main()
