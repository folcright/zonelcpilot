"""Smart section-aware chunker for zoning ordinances"""

import re
from typing import List, Dict
import tiktoken

class OrdinanceChunker:
    """Smart chunker that preserves section structure and adds metadata"""
    
    def __init__(self):
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        self.section_pattern = re.compile(r'Section\s+(\d+-\d+)', re.IGNORECASE)
        self.article_pattern = re.compile(r'Article\s+(\d+)', re.IGNORECASE)
        
        # Category detection keywords
        self.category_keywords = {
            'setback': ['setback', 'yard', 'distance', 'feet from', 'property line', 'boundary'],
            'permit': ['permit', 'approval', 'certificate', 'application', 'license', 'authorization'],
            'use': ['permitted use', 'allowed use', 'conditional use', 'special exception', 'prohibited'],
            'livestock': ['animal', 'livestock', 'poultry', 'horse', 'chicken', 'fowl', 'cattle', 'sheep'],
            'structure': ['building', 'structure', 'accessory', 'shed', 'barn', 'garage', 'dwelling'],
            'density': ['density', 'lot size', 'minimum area', 'acre', 'square feet'],
            'height': ['height', 'stories', 'feet tall', 'maximum height'],
            'parking': ['parking', 'vehicle', 'driveway', 'garage']
        }
    
    def detect_category(self, text: str) -> str:
        """Detect the primary category of a chunk based on keywords"""
        text_lower = text.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return 'general'
    
    def chunk_by_sections(self, text: str, max_tokens: int = 800) -> List[Dict]:
        """Split text by sections while preserving headers and context"""
        chunks = []
        lines = text.split('\n')
        
        current_section = None
        current_article = None
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            # Check for article header
            article_match = self.article_pattern.search(line)
            if article_match:
                current_article = f"Article {article_match.group(1)}"
            
            # Check for section header
            section_match = self.section_pattern.search(line)
            if section_match:
                # Save previous chunk if exists
                if current_chunk and current_tokens > 100:  # Minimum chunk size
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'section': current_section,
                        'article': current_article,
                        'category': self.detect_category(chunk_text),
                        'tokens': current_tokens,
                        'metadata': {
                            'section_number': self.extract_section_number(current_section),
                            'has_tables': self.has_tables(chunk_text),
                            'has_lists': self.has_lists(chunk_text)
                        }
                    })
                
                # Start new section
                current_section = line.strip()
                current_chunk = [line]
                current_tokens = len(self.encoding.encode(line))
            else:
                # Add line to current chunk
                line_tokens = len(self.encoding.encode(line))
                
                # Check if adding this line would exceed max tokens
                if current_tokens + line_tokens > max_tokens and current_chunk:
                    # Save current chunk
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'section': current_section,
                        'article': current_article,
                        'category': self.detect_category(chunk_text),
                        'tokens': current_tokens,
                        'metadata': {
                            'section_number': self.extract_section_number(current_section),
                            'has_tables': self.has_tables(chunk_text),
                            'has_lists': self.has_lists(chunk_text)
                        }
                    })
                    
                    # Start new chunk with section header for context
                    if current_section:
                        current_chunk = [current_section, line]
                        current_tokens = len(self.encoding.encode(current_section)) + line_tokens
                    else:
                        current_chunk = [line]
                        current_tokens = line_tokens
                else:
                    current_chunk.append(line)
                    current_tokens += line_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'section': current_section,
                'article': current_article,
                'category': self.detect_category(chunk_text),
                'tokens': current_tokens,
                'metadata': {
                    'section_number': self.extract_section_number(current_section),
                    'has_tables': self.has_tables(chunk_text),
                    'has_lists': self.has_lists(chunk_text)
                }
            })
        
        return chunks
    
    def extract_section_number(self, section_header: str) -> str:
        """Extract section number from header"""
        if not section_header:
            return None
        match = self.section_pattern.search(section_header)
        return match.group(1) if match else None
    
    def has_tables(self, text: str) -> bool:
        """Check if chunk contains table data"""
        # Simple heuristic: multiple lines with consistent spacing/tabs
        lines = text.split('\n')
        tab_lines = sum(1 for line in lines if '\t' in line or '  ' in line)
        return tab_lines > 3
    
    def has_lists(self, text: str) -> bool:
        """Check if chunk contains numbered or bulleted lists"""
        patterns = [
            r'^\s*\d+\.',  # Numbered lists
            r'^\s*\([a-z]\)',  # Letter lists (a), (b), etc.
            r'^\s*[•·\-\*]',  # Bullet points
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    def merge_related_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Merge small related chunks when appropriate"""
        merged = []
        i = 0
        
        while i < len(chunks):
            current = chunks[i]
            
            # Check if next chunk should be merged
            if i + 1 < len(chunks):
                next_chunk = chunks[i + 1]
                
                # Merge if same section and combined size is reasonable
                if (current['section'] == next_chunk['section'] and 
                    current['tokens'] + next_chunk['tokens'] < 1200):
                    
                    # Merge chunks
                    merged_text = current['text'] + '\n\n' + next_chunk['text']
                    merged_chunk = {
                        'text': merged_text,
                        'section': current['section'],
                        'article': current['article'],
                        'category': self.detect_category(merged_text),
                        'tokens': current['tokens'] + next_chunk['tokens'],
                        'metadata': current['metadata']
                    }
                    merged.append(merged_chunk)
                    i += 2  # Skip next chunk since we merged it
                else:
                    merged.append(current)
                    i += 1
            else:
                merged.append(current)
                i += 1
        
        return merged