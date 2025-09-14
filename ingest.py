import os
import hashlib
import json
from typing import List, Dict
import PyPDF2
import tiktoken
import openai
import chromadb
from datetime import datetime

# Import the smart chunker
from rag import OrdinanceChunker

class ZoningIngester:
    def __init__(self):
        # Use persistent client
        self.chroma = chromadb.PersistentClient(path="./chroma_data")

        # Create or get collection
        self.collection = self.chroma.get_or_create_collection(
            name="zoning_codes",
            metadata={"hnsw:space": "cosine"}
        )

        # OpenAI setup
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Use the smart chunker
        self.chunker = OrdinanceChunker()

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI"""
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def ingest_pdf(self, pdf_path: str, county: str):
        """Main ingestion pipeline with smart chunking"""
        print(f"Ingesting {pdf_path} for {county} using RAG v2.0 smart chunker...")

        # Extract text from PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                text += f"\n[Page {page_num + 1}]\n"
                text += page.extract_text()

        # Use smart chunker
        chunks = self.chunker.chunk_by_sections(text, max_tokens=800)
        
        # Optionally merge small related chunks
        chunks = self.chunker.merge_related_chunks(chunks)
        
        print(f"Created {len(chunks)} smart chunks with category detection")

        # Process each chunk with enhanced metadata
        for i, chunk in enumerate(chunks):
            # Generate unique ID based on content and metadata
            chunk_id = hashlib.md5(
                f"{county}_{i}_{chunk.get('section', '')}_{chunk['text'][:100]}".encode()
            ).hexdigest()

            # Generate embedding
            embedding = self.generate_embedding(chunk['text'])

            # Build enhanced metadata
            metadata = {
                'county': county,
                'section': chunk.get('section', 'Unknown'),
                'article': chunk.get('article', 'Unknown'),
                'category': chunk.get('category', 'general'),
                'chunk_index': i,
                'tokens': chunk.get('tokens', 0),
                'ingested_at': datetime.now().isoformat()
            }
            
            # Add extra metadata if available
            if 'metadata' in chunk:
                metadata['section_number'] = chunk['metadata'].get('section_number')
                metadata['has_tables'] = chunk['metadata'].get('has_tables', False)
                metadata['has_lists'] = chunk['metadata'].get('has_lists', False)

            # Add to collection
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[chunk['text']]
            )

            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(chunks)} chunks...")
                # Show sample of detected categories
                if i == 9:
                    categories = [c.get('category', 'unknown') for c in chunks[:10]]
                    print(f"  Sample categories: {', '.join(set(categories))}")

        print(f"Successfully ingested {len(chunks)} chunks for {county}")
        
        # Print category distribution
        category_counts = {}
        for chunk in chunks:
            cat = chunk.get('category', 'general')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print("\nCategory distribution:")
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count} chunks")
    
    def clear_collection(self):
        """Clear the existing collection before re-ingesting"""
        try:
            # Delete the collection if it exists
            self.chroma.delete_collection("zoning_codes")
            print("Cleared existing collection")
            
            # Recreate it
            self.collection = self.chroma.create_collection(
                name="zoning_codes",
                metadata={"hnsw:space": "cosine"}
            )
            print("Created fresh collection")
        except Exception as e:
            print(f"Note: {e}")
            # Collection might not exist, that's okay

if __name__ == "__main__":
    # Set your OpenAI key first
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-...":
        print("Please set your OPENAI_API_KEY environment variable first!")
        print("You can do this in the Replit Secrets panel")
    else:
        ingester = ZoningIngester()
        
        # Check if PDF exists
        pdf_path = "attached_assets/loudoun_zoning_1757731876912.pdf"
        if os.path.exists(pdf_path):
            print("Found Loudoun County zoning PDF!")
            print("Would you like to (re)ingest it with the new RAG v2.0 chunker?")
            print("This will use the smart section-aware chunking.")
            # Uncomment the next lines to actually ingest:
            # ingester.clear_collection()  # Clear old chunks
            # ingester.ingest_pdf(pdf_path, "loudoun")
        else:
            print(f"PDF not found at {pdf_path}")
            print("Please ensure the Loudoun County zoning PDF is uploaded")