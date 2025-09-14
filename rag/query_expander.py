"""Query expansion module for improving retrieval accuracy"""

import re
from typing import List, Set, Dict

class QueryExpander:
    """Expands queries with synonyms and related terms"""
    
    def __init__(self):
        # Term mappings from user language to ordinance language
        self.term_mappings = {
            # Structures
            'shed': ['accessory structure', 'accessory building', 'outbuilding', 'storage structure'],
            'barn': ['agricultural structure', 'farm building', 'livestock shelter', 'accessory structure'],
            'garage': ['accessory structure', 'vehicle storage', 'carport'],
            'pool': ['swimming pool', 'pool structure', 'recreational facility'],
            'fence': ['fence', 'fencing', 'enclosure', 'barrier'],
            'deck': ['deck', 'patio', 'outdoor structure'],
            'gazebo': ['accessory structure', 'pavilion', 'outdoor structure'],
            
            # Animals
            'chickens': ['poultry', 'fowl', 'domestic fowl', 'birds', 'hens'],
            'horses': ['equine', 'livestock', 'large animals', 'horses'],
            'cows': ['cattle', 'bovine', 'livestock', 'large animals'],
            'goats': ['goats', 'livestock', 'small livestock'],
            'pigs': ['swine', 'hogs', 'livestock'],
            'bees': ['beekeeping', 'apiary', 'honeybees'],
            
            # Distances/Measurements
            'setback': ['setback', 'yard requirement', 'distance', 'minimum distance'],
            'property line': ['property line', 'lot line', 'boundary', 'property boundary'],
            'how far': ['setback', 'distance', 'minimum distance', 'required distance'],
            'distance': ['setback', 'separation', 'spacing', 'buffer'],
            
            # Permits/Approvals
            'permit': ['permit', 'approval', 'authorization', 'certificate', 'license'],
            'allowed': ['permitted', 'allowed', 'permissible', 'authorized'],
            'can i': ['permitted', 'allowed', 'may', 'permissible'],
            'do i need': ['required', 'necessary', 'must', 'shall'],
            
            # Zones
            'ar-1': ['AR-1', 'Agricultural Rural-1', 'Agricultural Rural 1'],
            'ar-2': ['AR-2', 'Agricultural Rural-2', 'Agricultural Rural 2'],
            'residential': ['residential', 'R-1', 'R-2', 'R-3', 'dwelling'],
            
            # Actions
            'build': ['construct', 'erect', 'establish', 'install'],
            'add': ['construct', 'install', 'establish', 'place'],
            'put up': ['erect', 'construct', 'install'],
            'have': ['keep', 'maintain', 'house', 'raise'],
            'raise': ['keep', 'raise', 'maintain', 'house'],
            
            # Size/Area
            'acre': ['acre', 'acreage', 'lot size', 'parcel size'],
            'square feet': ['square feet', 'sq ft', 'square footage', 'area'],
            'size': ['area', 'dimensions', 'square footage', 'lot size']
        }
        
        # Common question patterns
        self.question_patterns = {
            'setback': r'(how far|what.{0,10}setback|distance.{0,10}from)',
            'permit': r'(do i need.{0,10}permit|permit.{0,10}required|need.{0,10}approval)',
            'allowed': r'(can i|am i allowed|is it permitted|are.{0,10}allowed)',
            'size': r'(how big|what size|minimum.{0,10}size|how many.{0,10}acre)'
        }
        
        # Zone-specific expansions
        self.zone_expansions = {
            'ar-1': ['agricultural rural', 'AR-1 district', 'agricultural zoning'],
            'ar-2': ['agricultural rural', 'AR-2 district', 'agricultural zoning'],
            'residential': ['residential district', 'residential zoning', 'R- district']
        }
    
    def expand_query(self, query: str) -> str:
        """Expand a query with related terms"""
        query_lower = query.lower()
        expanded_terms = set()
        
        # Add original query
        expanded_terms.add(query)
        
        # Find and expand mapped terms
        for user_term, ordinance_terms in self.term_mappings.items():
            if user_term in query_lower:
                # Add ordinance language equivalents
                for term in ordinance_terms:
                    expanded_query = query_lower.replace(user_term, term)
                    expanded_terms.add(expanded_query)
        
        # Detect question type and add relevant terms
        question_type = self.detect_question_type(query_lower)
        if question_type:
            expanded_terms.update(self.get_question_specific_terms(question_type, query_lower))
        
        # Join all expanded terms with OR
        return ' OR '.join(expanded_terms)
    
    def detect_question_type(self, query: str) -> str:
        """Detect the type of question being asked"""
        for q_type, pattern in self.question_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return q_type
        return None
    
    def get_question_specific_terms(self, question_type: str, query: str) -> Set[str]:
        """Get additional terms based on question type"""
        terms = set()
        
        if question_type == 'setback':
            terms.update(['yard requirements', 'minimum distance', 'setback requirements'])
            # Check for specific structure mentions
            if 'shed' in query or 'accessory' in query:
                terms.add('accessory structure setback')
            if 'barn' in query:
                terms.add('agricultural structure setback')
                
        elif question_type == 'permit':
            terms.update(['zoning permit', 'building permit', 'permit requirements'])
            
        elif question_type == 'allowed':
            terms.update(['permitted uses', 'allowed uses', 'use regulations'])
            
        elif question_type == 'size':
            terms.update(['minimum lot size', 'area requirements', 'dimensional requirements'])
        
        return terms
    
    def extract_key_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract key entities from the query"""
        entities = {
            'structures': [],
            'animals': [],
            'zones': [],
            'measurements': []
        }
        
        query_lower = query.lower()
        
        # Extract structures
        structure_keywords = ['shed', 'barn', 'garage', 'fence', 'pool', 'deck', 'house', 'building']
        for keyword in structure_keywords:
            if keyword in query_lower:
                entities['structures'].append(keyword)
        
        # Extract animals
        animal_keywords = ['chicken', 'horse', 'cow', 'goat', 'pig', 'sheep', 'bee', 'poultry', 'livestock']
        for keyword in animal_keywords:
            if keyword in query_lower or keyword + 's' in query_lower:
                entities['animals'].append(keyword)
        
        # Extract zones
        zone_pattern = r'\b(AR-\d+|R-\d+|TR-\d+|PD-[A-Z]+)\b'
        zone_matches = re.findall(zone_pattern, query, re.IGNORECASE)
        entities['zones'].extend(zone_matches)
        
        # Extract measurements
        measurement_pattern = r'\b(\d+)\s*(acre|feet|foot|ft|square feet|sq ft)'
        measurement_matches = re.findall(measurement_pattern, query_lower)
        for match in measurement_matches:
            entities['measurements'].append(f"{match[0]} {match[1]}")
        
        return entities
    
    def create_focused_query(self, query: str) -> List[str]:
        """Create multiple focused query variations"""
        queries = [query]  # Start with original
        
        entities = self.extract_key_entities(query)
        
        # Create structure-specific queries
        if entities['structures']:
            for structure in entities['structures']:
                if 'setback' in query.lower():
                    queries.append(f"{structure} setback requirements")
                    queries.append(f"accessory structure setback {structure}")
                if 'permit' in query.lower():
                    queries.append(f"{structure} permit requirements")
        
        # Create animal-specific queries
        if entities['animals']:
            for animal in entities['animals']:
                queries.append(f"{animal} regulations")
                queries.append(f"livestock {animal} requirements")
                if 'permit' in query.lower():
                    queries.append(f"{animal} permit requirements")
        
        # Create zone-specific queries
        if entities['zones']:
            for zone in entities['zones']:
                queries.append(f"{zone} regulations")
                queries.append(f"{zone} permitted uses")
                if entities['structures']:
                    queries.append(f"{zone} {entities['structures'][0]} requirements")
        
        return queries