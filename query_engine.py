import os
import openai
import chromadb
from typing import List, Dict, Optional

# Import RAG v2.0 modules
from rag import QueryExpander, AnswerFormatter, QueryCache

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
        
        # Initialize RAG v2.0 components
        self.query_expander = QueryExpander()
        self.answer_formatter = AnswerFormatter()
        self.cache = QueryCache()

    def search(self, query: str, county: str = None, top_k: int = 5) -> List[Dict]:
        """Search for relevant chunks with query expansion"""
        # Expand query for better retrieval
        expanded_query = self.query_expander.expand_query(query)
        
        # Generate query embedding from expanded query
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=expanded_query
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
    
    def search_multiple_queries(self, queries: List[str], county: str = None, top_k: int = 3) -> List[Dict]:
        """Search with multiple query variations"""
        all_results = {}
        seen_chunks = set()
        
        for query in queries[:3]:  # Limit to 3 variations to control costs
            chunks = self.search(query, county, top_k)
            for chunk in chunks:
                # Use text hash as unique identifier
                chunk_id = hash(chunk['text'][:100])
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    all_results[chunk_id] = chunk
        
        # Sort by relevance (distance)
        sorted_results = sorted(all_results.values(), 
                              key=lambda x: x.get('distance', 1.0))
        
        return sorted_results[:top_k]

    def answer_question(self, question: str, county: str) -> Dict:
        """Generate answer with citations using RAG v2.0 improvements"""
        
        # Step 1: Check cache for common questions
        cached_answer = self.cache.check_cache(question)
        if cached_answer:
            # Format cached answer using template
            template_type = cached_answer.get('template_type', 'simple')
            if 'details' in cached_answer:
                # Use template formatter for structured response
                formatted_answer = self._format_cached_answer(cached_answer)
                return {
                    'question': question,
                    'answer': formatted_answer,
                    'citations': [{'section': cached_answer['details'].get('reference', 'Cached')}],
                    'county': county,
                    'cached': True
                }
            else:
                return {
                    'question': question,
                    'answer': cached_answer['answer'],
                    'citations': [],
                    'county': county,
                    'cached': True
                }
        
        # Step 2: Create multiple query variations for better retrieval
        query_variations = self.query_expander.create_focused_query(question)
        
        # Step 3: Search with expanded queries
        chunks = self.search_multiple_queries(query_variations, county, top_k=5)
        
        if not chunks:
            # Try one more time with just the expanded original query
            chunks = self.search(question, county, top_k=5)
        
        if not chunks:
            return {
                'question': question,
                'answer': f"I don't have any zoning information for {county} county yet. Please run the ingest.py script first to load the zoning ordinance.",
                'citations': [],
                'county': county
            }

        # Step 4: Build context from retrieved chunks
        context = self._build_enhanced_context(chunks)
        
        # Step 5: Generate answer with better prompt
        answer = self._generate_answer(question, context)
        
        # Step 6: Format answer using templates
        formatted_answer = self.answer_formatter.format_answer(question, answer, 
                                                              self._extract_citations(chunks))
        
        # Step 7: Cache if it's a good answer
        if len(answer) > 50:  # Only cache substantive answers
            self.cache.add_to_cache(question, {
                'answer': formatted_answer,
                'template_type': self.answer_formatter.detect_template_type(question, answer)
            })
        
        return {
            'question': question,
            'answer': formatted_answer,
            'citations': self._extract_citations(chunks),
            'county': county,
            'chunks_searched': len(chunks)
        }
    
    def _format_cached_answer(self, cached_data: Dict) -> str:
        """Format cached answer using appropriate template"""
        template_type = cached_data.get('template_type', 'simple')
        details = cached_data.get('details', {})
        
        if template_type == 'setback':
            return f"""**Setback Requirements:**
            
**Distance Required:** {details.get('distance', 'Not specified')}
**Measured From:** {details.get('from_point', 'property line')}
**Applicable Zone:** {details.get('zone', 'AR-1')}
**Structure Type:** {details.get('structure_type', 'accessory structure')}

**Reference:** {details.get('reference', 'Loudoun County Zoning Ordinance')}"""
        
        elif template_type == 'permit':
            answer = f"""**Permit Requirements:**

**Permit Required:** {details.get('required', 'Yes')}
**Permit Type:** {details.get('permit_type', 'Zoning Permit')}"""
            
            if details.get('additional_requirements'):
                answer += f"\n\n{details['additional_requirements']}"
            
            answer += f"\n\n**Reference:** {details.get('reference', 'Loudoun County Zoning Ordinance')}"
            return answer
        
        elif template_type == 'livestock':
            return f"""**Livestock/Animal Regulations:**

**Animal Type:** {details.get('animal_type', 'Not specified')}
**Allowed:** {details.get('allowed', 'Check regulations')}
**Zone:** {details.get('zone', 'AR-1')}
**Minimum Lot Size:** {details.get('min_lot_size', 'Not specified')}
**Maximum Number:** {details.get('max_number', 'Not specified')}

{details.get('requirements', '')}

**Reference:** {details.get('reference', 'Loudoun County Zoning Ordinance')}"""
        
        else:
            return cached_data['answer']
    
    def _build_enhanced_context(self, chunks: List[Dict]) -> str:
        """Build context with better structure"""
        context_parts = []
        
        # Group chunks by section if possible
        sections = {}
        for chunk in chunks:
            section = chunk['metadata'].get('section', 'General')
            if section not in sections:
                sections[section] = []
            sections[section].append(chunk['text'])
        
        # Build context with section grouping
        for section, texts in sections.items():
            context_parts.append(f"=== {section} ===")
            for text in texts:
                context_parts.append(text)
            context_parts.append("")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer with improved prompt"""
        # Extract entities from question for better prompting
        entities = self.query_expander.extract_key_entities(question)
        
        # Build focused prompt based on question type
        prompt = self._build_focused_prompt(question, context, entities)
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Loudoun County zoning code expert. Answer based ONLY on the provided ordinance text. Be specific and cite section numbers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def _build_focused_prompt(self, question: str, context: str, entities: Dict) -> str:
        """Build a focused prompt based on question type"""
        base_prompt = f"""Question: {question}

Relevant ordinance sections:
{context}

"""
        
        # Add specific instructions based on entities
        if entities['structures']:
            base_prompt += f"\nFocus on regulations for: {', '.join(entities['structures'])}"
        
        if entities['animals']:
            base_prompt += f"\nFocus on regulations for: {', '.join(entities['animals'])}"
        
        if entities['zones']:
            base_prompt += f"\nSpecific to zone(s): {', '.join(entities['zones'])}"
        
        base_prompt += """

Instructions:
1. Answer based ONLY on the provided ordinance text
2. If asking about distances/setbacks, provide specific measurements
3. If asking about permits, clearly state if required or not
4. If asking about animals/livestock, include lot size requirements
5. Cite specific section numbers (e.g., Section 5-603)
6. If the information is not in the provided text, say so

Answer:"""
        
        return base_prompt
    
    def _extract_citations(self, chunks: List[Dict]) -> List[Dict]:
        """Extract citations from chunks"""
        citations = []
        seen_sections = set()
        
        for chunk in chunks[:3]:  # Top 3 most relevant
            section = chunk['metadata'].get('section', 'Unknown')
            if section not in seen_sections:
                seen_sections.add(section)
                citations.append({
                    'section': section,
                    'relevance': 1 - (chunk.get('distance', 0) if chunk.get('distance') else 0)
                })
        
        return citations