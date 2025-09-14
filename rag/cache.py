"""Query cache for common questions"""

import json
import os
from typing import Dict, Optional
import hashlib

class QueryCache:
    """Cache for common queries to improve response time"""
    
    def __init__(self, cache_file: str = 'data/common_qa.json'):
        self.cache_file = cache_file
        self.cache = self.load_cache()
        
        # Predefined common Q&A pairs
        self.common_qa = {
            # Setback questions
            "can i build a shed in ar-1": {
                "answer": "Yes, you can build a shed in AR-1 zones. Sheds are considered accessory structures and are permitted.",
                "details": {
                    "distance": "25 feet",
                    "from_point": "side and rear property lines",
                    "zone": "AR-1",
                    "structure_type": "shed/accessory structure",
                    "reference": "Section 5-603"
                },
                "template_type": "setback"
            },
            
            "what's the setback for a barn": {
                "answer": "In AR-1 zones, barns (agricultural structures) must be set back at least 50 feet from all property lines.",
                "details": {
                    "distance": "50 feet",
                    "from_point": "all property lines",
                    "zone": "AR-1",
                    "structure_type": "barn/agricultural structure",
                    "reference": "Section 5-603"
                },
                "template_type": "setback"
            },
            
            "how far from property line for accessory structure": {
                "answer": "Accessory structures in AR-1 must be at least 25 feet from side and rear property lines.",
                "details": {
                    "distance": "25 feet",
                    "from_point": "side and rear property lines",
                    "zone": "AR-1",
                    "structure_type": "accessory structure",
                    "reference": "Section 5-603"
                },
                "template_type": "setback"
            },
            
            # Permit questions
            "do i need a permit for chickens": {
                "answer": "No permit is required for chickens in AR-1 zones on lots of 2 acres or more. Chickens are considered agricultural use.",
                "details": {
                    "required": "No",
                    "permit_type": "Not required",
                    "additional_requirements": "Minimum 2 acre lot required in AR-1",
                    "reference": "Section 5-102"
                },
                "template_type": "permit"
            },
            
            "do i need a permit for a shed": {
                "answer": "Yes, a zoning permit is required for sheds over 200 square feet. Sheds 200 sq ft or smaller are exempt.",
                "details": {
                    "required": "Yes (if over 200 sq ft)",
                    "permit_type": "Zoning Permit",
                    "process": "Submit application with site plan to Planning Department",
                    "reference": "Section 6-101"
                },
                "template_type": "permit"
            },
            
            "permit for fence": {
                "answer": "No permit is required for fences up to 6 feet in height in rear and side yards. Front yard fences over 4 feet need a permit.",
                "details": {
                    "required": "Depends on location and height",
                    "permit_type": "Zoning Permit (if required)",
                    "additional_requirements": "Max 6 ft in rear/side, max 4 ft in front without permit",
                    "reference": "Section 5-900"
                },
                "template_type": "permit"
            },
            
            # Livestock questions
            "are horses allowed on 2 acres": {
                "answer": "Yes, horses are allowed on 2 acres in AR-1. The requirement is 1 horse per acre with a minimum of 2 acres.",
                "details": {
                    "animal_type": "Horses",
                    "allowed": "Yes",
                    "zone": "AR-1",
                    "min_lot_size": "2 acres",
                    "max_number": "2 horses on 2 acres (1 per acre)",
                    "reference": "Section 5-102"
                },
                "template_type": "livestock"
            },
            
            "can i have chickens on 1 acre": {
                "answer": "No, chickens require a minimum of 2 acres in AR-1 zones as they are considered agricultural use.",
                "details": {
                    "animal_type": "Chickens/Poultry",
                    "allowed": "No (lot too small)",
                    "zone": "AR-1",
                    "min_lot_size": "2 acres",
                    "reference": "Section 5-102"
                },
                "template_type": "livestock"
            },
            
            "how many chickens can i have": {
                "answer": "In AR-1 zones with 2+ acres, there is no specific limit on chickens for personal/agricultural use. Commercial operations have different requirements.",
                "details": {
                    "animal_type": "Chickens/Poultry",
                    "allowed": "Yes (with 2+ acres)",
                    "zone": "AR-1",
                    "min_lot_size": "2 acres",
                    "max_number": "No limit for personal use",
                    "requirements": "Must be for personal/agricultural use, not commercial",
                    "reference": "Section 5-102"
                },
                "template_type": "livestock"
            },
            
            # Structure questions
            "maximum shed size without permit": {
                "answer": "Sheds 200 square feet or smaller do not require a permit in AR-1 zones.",
                "details": {
                    "answer": "200 square feet",
                    "explanation": "Accessory structures 200 sq ft or less are exempt from permit requirements",
                    "reference": "Section 6-101"
                },
                "template_type": "simple"
            },
            
            "can i build a pool": {
                "answer": "Yes, pools are permitted in AR-1 zones with proper permits and setbacks. Pools must be at least 10 feet from property lines.",
                "details": {
                    "permitted": "Yes",
                    "required": "Yes",
                    "permit_type": "Building Permit and Zoning Permit",
                    "additional_requirements": "10 ft setback, fencing required",
                    "reference": "Section 5-1000"
                },
                "template_type": "permit"
            },
            
            # Zone questions
            "what can i build in ar-1": {
                "answer": "AR-1 permits single-family dwellings, agricultural uses, and accessory structures like sheds, barns, and garages.",
                "details": {
                    "answer": "Single-family homes, agricultural structures, accessory buildings",
                    "explanation": "AR-1 is Agricultural Rural district allowing residential and agricultural uses",
                    "reference": "Section 3-102"
                },
                "template_type": "simple"
            },
            
            "minimum lot size ar-1": {
                "answer": "The minimum lot size in AR-1 is 3 acres for new subdivisions.",
                "details": {
                    "answer": "3 acres",
                    "explanation": "AR-1 requires minimum 3 acre lots for new subdivisions",
                    "reference": "Section 4-100"
                },
                "template_type": "simple"
            },
            
            # Home business
            "can i run a business from home": {
                "answer": "Yes, home businesses are allowed in AR-1 with a Special Exception permit. Restrictions apply on employees, parking, and signage.",
                "details": {
                    "use_type": "Home Business",
                    "permitted": "Yes (With Special Exception)",
                    "zone": "AR-1",
                    "conditions": "Limited employees, no retail sales, restricted signage",
                    "process": "Apply for Special Exception through Board of Supervisors",
                    "reference": "Section 5-500"
                },
                "template_type": "use"
            },
            
            # Setback specifics
            "shed setback requirements": {
                "answer": "Sheds in AR-1 must be at least 25 feet from side and rear property lines.",
                "details": {
                    "distance": "25 feet",
                    "from_point": "side and rear property lines",
                    "zone": "AR-1",
                    "structure_type": "shed",
                    "reference": "Section 5-603"
                },
                "template_type": "setback"
            },
            
            "garage setback": {
                "answer": "Detached garages in AR-1 must be at least 25 feet from side and rear property lines.",
                "details": {
                    "distance": "25 feet",
                    "from_point": "side and rear property lines",
                    "zone": "AR-1",
                    "structure_type": "detached garage",
                    "reference": "Section 5-603"
                },
                "template_type": "setback"
            },
            
            # Additional common questions
            "fence height limit": {
                "answer": "Fences can be up to 6 feet in rear and side yards, 4 feet in front yards without a permit.",
                "details": {
                    "answer": "6 ft (rear/side), 4 ft (front)",
                    "explanation": "Height limits vary by yard location. Higher fences require permits.",
                    "reference": "Section 5-900"
                },
                "template_type": "simple"
            },
            
            "accessory structure height": {
                "answer": "Accessory structures in AR-1 can be up to 25 feet in height.",
                "details": {
                    "answer": "25 feet maximum",
                    "explanation": "Height limit for accessory structures in agricultural zones",
                    "reference": "Section 5-604"
                },
                "template_type": "simple"
            },
            
            "driveway permit": {
                "answer": "A permit is required for new driveways or driveway modifications that connect to public roads.",
                "details": {
                    "required": "Yes",
                    "permit_type": "VDOT Land Use Permit",
                    "process": "Apply through VDOT for connections to state roads",
                    "reference": "Section 7-400"
                },
                "template_type": "permit"
            },
            
            "beekeeping allowed": {
                "answer": "Yes, beekeeping is allowed in AR-1 zones as an agricultural use on lots of 2 acres or more.",
                "details": {
                    "animal_type": "Bees/Beekeeping",
                    "allowed": "Yes",
                    "zone": "AR-1",
                    "min_lot_size": "2 acres",
                    "requirements": "Hives must be 50 ft from property lines",
                    "reference": "Section 5-102"
                },
                "template_type": "livestock"
            }
        }
    
    def normalize_query(self, query: str) -> str:
        """Normalize query for cache lookup"""
        # Convert to lowercase and remove punctuation
        normalized = query.lower().strip()
        normalized = normalized.replace('?', '').replace('.', '').replace('!', '')
        normalized = normalized.replace(',', '').replace(';', '')
        
        # Remove common filler words
        filler_words = ['the', 'a', 'an', 'is', 'are', 'in', 'on', 'at', 'to', 'for']
        words = normalized.split()
        words = [w for w in words if w not in filler_words or len(words) <= 3]
        
        return ' '.join(words)
    
    def get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        normalized = self.normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def check_cache(self, query: str) -> Optional[Dict]:
        """Check if query exists in cache"""
        normalized = self.normalize_query(query)
        
        # Check predefined common Q&A
        if normalized in self.common_qa:
            return self.common_qa[normalized]
        
        # Check for partial matches
        for cached_query, cached_answer in self.common_qa.items():
            # Check if the key terms match
            if self.is_similar_query(normalized, cached_query):
                return cached_answer
        
        # Check dynamic cache
        cache_key = self.get_cache_key(query)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        return None
    
    def is_similar_query(self, query1: str, query2: str) -> bool:
        """Check if two queries are similar enough to use cached answer"""
        # Extract key terms
        key_terms = ['shed', 'barn', 'setback', 'permit', 'chicken', 'horse', 
                     'fence', 'pool', 'ar-1', 'acre', 'property line', 'garage']
        
        query1_terms = set(word for word in query1.split() if word in key_terms)
        query2_terms = set(word for word in query2.split() if word in key_terms)
        
        # If they share most key terms, consider them similar
        if query1_terms and query2_terms:
            overlap = len(query1_terms & query2_terms)
            total = len(query1_terms | query2_terms)
            if total > 0 and overlap / total >= 0.7:
                return True
        
        return False
    
    def add_to_cache(self, query: str, answer: Dict):
        """Add a query-answer pair to cache"""
        cache_key = self.get_cache_key(query)
        self.cache[cache_key] = answer
        self.save_cache()
    
    def load_cache(self) -> Dict:
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_cache(self):
        """Save cache to file"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)