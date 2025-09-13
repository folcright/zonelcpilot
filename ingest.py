import os
import hashlib
import json
from typing import List, Dict
import PyPDF2
import tiktoken
import openai
import chromadb
from datetime import datetime

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
        self.encoding = tiktoken.encoding_for_model("gpt-4")

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Smart chunking that respects section boundaries"""
        chunks = []
        lines = text.split('\n')
        current_chunk = []
        current_size = 0
        current_section = "Unknown"

        for line in lines:
            # Detect section headers
            if any(marker in line for marker in ['Section', 'SECTION', '§', 'Article']):
                if line.strip():
                    current_section = line.strip()

            tokens = len(self.encoding.encode(line))

            if current_size + tokens > chunk_size and current_chunk:
                chunk_text = '\n'.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'section': current_section,
                    'tokens': current_size
                })

                # Overlap
                overlap_lines = current_chunk[-5:]
                current_chunk = overlap_lines + [line]
                current_size = len(self.encoding.encode('\n'.join(current_chunk)))
            else:
                current_chunk.append(line)
                current_size += tokens

        # Last chunk
        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'section': current_section,
                'tokens': current_size
            })

        return chunks

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI"""
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def ingest_pdf(self, pdf_path: str, county: str):
        """Main ingestion pipeline"""
        print(f"Ingesting {pdf_path} for {county}...")

        # Extract text from PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                text += f"\n[Page {page_num + 1}]\n"
                text += page.extract_text()

        # Chunk the text
        chunks = self.chunk_text(text)
        print(f"Created {len(chunks)} chunks")

        # Process each chunk
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{county}_{i}_{chunk['text'][:100]}".encode()).hexdigest()

            embedding = self.generate_embedding(chunk['text'])

            metadata = {
                'county': county,
                'section': chunk['section'],
                'chunk_index': i,
                'tokens': chunk['tokens'],
                'ingested_at': datetime.now().isoformat()
            }

            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[chunk['text']]
            )

            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(chunks)} chunks...")

        print(f"Successfully ingested {len(chunks)} chunks for {county}")

if __name__ == "__main__":
    # Set your OpenAI key first
    os.environ["OPENAI_API_KEY"] = "sk-..."  # You'll update this in Replit

    ingester = ZoningIngester()
    # ingester.ingest_pdf("loudoun_zoning.pdf", "loudoun")
    print("Ready to ingest PDFs. Upload a PDF and uncomment the line above.")