import os
import openai
import chromadb
from typing import List, Dict

class ZoningQueryEngine:
    def __init__(self):
        # Use persistent client for embedded mode initially
        self.chroma = chromadb.PersistentClient(path="./chroma_data")

        # Create or get collection
        self.collection = self.chroma.get_or_create_collection(
            name="zoning_codes",
            metadata={"hnsw:space": "cosine"}
        )

        # OpenAI setup
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def search(self, query: str, county: str = None, top_k: int = 5) -> List[Dict]:
        """Search for relevant chunks"""
        # Generate query embedding
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding

        # Build filter
        where_filter = {"county": county} if county else None

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )

        if not results['documents'][0]:
            return []

        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if 'distances' in results else None
            })

        return formatted_results

    def answer_question(self, question: str, county: str) -> Dict:
        """Generate answer with citations"""
        # Search for relevant chunks
        chunks = self.search(question, county, top_k=5)

        if not chunks:
            return {
                'question': question,
                'answer': f"I don't have any zoning information for {county} county yet. Please run the ingest.py script first to load the zoning ordinance.",
                'citations': [],
                'county': county
            }

        # Build context
        context = "\n\n---\n\n".join([
            f"Section: {chunk['metadata'].get('section', 'Unknown')}\n{chunk['text']}"
            for chunk in chunks
        ])

        # Generate answer
        prompt = f"""You are a helpful assistant that answers zoning questions based solely on the provided ordinance text.

Question: {question}

Relevant ordinance sections:
{context}

Instructions:
1. Answer the question based ONLY on the provided text
2. Cite specific section numbers
3. If the answer isn't in the provided text, say so
4. Be concise and direct

Answer:"""

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a zoning code assistant. Answer only based on provided ordinance text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        # Extract citations
        citations = []
        for chunk in chunks[:3]:  # Top 3 most relevant
            citations.append({
                'section': chunk['metadata'].get('section', 'Unknown'),
                'relevance': 1 - (chunk['distance'] if chunk['distance'] else 0)
            })

        return {
            'question': question,
            'answer': answer,
            'citations': citations,
            'county': county,
            'chunks_searched': len(chunks)
        }