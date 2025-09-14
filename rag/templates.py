"""Answer formatting templates for consistent responses"""

from typing import Dict, List, Optional

class AnswerFormatter:
    """Format answers using templates for consistency"""
    
    def __init__(self):
        self.templates = {
            'setback': {
                'format': """**Setback Requirements:**
                
**Distance Required:** {distance}
**Measured From:** {from_point}
**Applicable Zone:** {zone}
**Structure Type:** {structure_type}

{additional_notes}

**Reference:** {reference}""",
                'required_fields': ['distance', 'from_point', 'zone', 'structure_type', 'reference']
            },
            
            'permit': {
                'format': """**Permit Requirements:**

**Permit Required:** {required}
**Permit Type:** {permit_type}
{fee_info}
**Application Process:** {process}
{timeline_info}

{additional_requirements}

**Reference:** {reference}""",
                'required_fields': ['required', 'permit_type', 'reference']
            },
            
            'livestock': {
                'format': """**Livestock/Animal Regulations:**

**Animal Type:** {animal_type}
**Allowed:** {allowed}
**Zone:** {zone}
**Minimum Lot Size:** {min_lot_size}
**Maximum Number:** {max_number}

**Additional Requirements:**
{requirements}

**Reference:** {reference}""",
                'required_fields': ['animal_type', 'allowed', 'zone', 'reference']
            },
            
            'use': {
                'format': """**Use Regulations:**

**Use Type:** {use_type}
**Permitted:** {permitted}
**Zone:** {zone}
{conditions}

**Process:**
{process}

**Reference:** {reference}""",
                'required_fields': ['use_type', 'permitted', 'zone', 'reference']
            },
            
            'simple': {
                'format': """**Answer:** {answer}

**Explanation:** {explanation}

**Reference:** {reference}""",
                'required_fields': ['answer', 'reference']
            }
        }
        
        # Keywords to detect template type
        self.template_triggers = {
            'setback': ['setback', 'distance from', 'how far', 'yards', 'feet from'],
            'permit': ['permit', 'approval', 'application', 'need permit', 'authorization'],
            'livestock': ['chicken', 'horse', 'cow', 'livestock', 'animal', 'poultry', 'fowl'],
            'use': ['allowed use', 'permitted use', 'can i use', 'conditional use', 'special exception']
        }
    
    def detect_template_type(self, question: str, answer: str) -> str:
        """Detect which template to use based on question and answer"""
        combined_text = (question + ' ' + answer).lower()
        
        # Check triggers in order of specificity
        for template_type, triggers in self.template_triggers.items():
            for trigger in triggers:
                if trigger in combined_text:
                    return template_type
        
        return 'simple'  # Default template
    
    def extract_fields(self, answer: str, template_type: str) -> Dict[str, str]:
        """Extract structured fields from raw answer text"""
        fields = {}
        
        if template_type == 'setback':
            fields = self.extract_setback_fields(answer)
        elif template_type == 'permit':
            fields = self.extract_permit_fields(answer)
        elif template_type == 'livestock':
            fields = self.extract_livestock_fields(answer)
        elif template_type == 'use':
            fields = self.extract_use_fields(answer)
        else:
            fields = {
                'answer': answer.split('\n')[0] if answer else 'See explanation',
                'explanation': answer,
                'reference': self.extract_reference(answer)
            }
        
        return fields
    
    def extract_setback_fields(self, answer: str) -> Dict[str, str]:
        """Extract setback-specific fields from answer"""
        fields = {
            'distance': 'Not specified',
            'from_point': 'property line',
            'zone': 'Not specified',
            'structure_type': 'accessory structure',
            'additional_notes': '',
            'reference': self.extract_reference(answer)
        }
        
        # Extract distance (look for feet measurements)
        import re
        distance_pattern = r'(\d+)\s*(?:feet|ft|foot)'
        distance_match = re.search(distance_pattern, answer, re.IGNORECASE)
        if distance_match:
            fields['distance'] = f"{distance_match.group(1)} feet"
        
        # Extract zone
        zone_pattern = r'(AR-\d+|R-\d+|TR-\d+)'
        zone_match = re.search(zone_pattern, answer, re.IGNORECASE)
        if zone_match:
            fields['zone'] = zone_match.group(1)
        
        # Extract from point
        if 'side' in answer.lower():
            fields['from_point'] = 'side property line'
        elif 'rear' in answer.lower():
            fields['from_point'] = 'rear property line'
        elif 'front' in answer.lower():
            fields['from_point'] = 'front property line'
        
        # Extract structure type
        if 'shed' in answer.lower():
            fields['structure_type'] = 'shed'
        elif 'barn' in answer.lower():
            fields['structure_type'] = 'barn/agricultural structure'
        elif 'garage' in answer.lower():
            fields['structure_type'] = 'garage'
        
        return fields
    
    def extract_permit_fields(self, answer: str) -> Dict[str, str]:
        """Extract permit-specific fields from answer"""
        fields = {
            'required': 'Yes',
            'permit_type': 'Zoning Permit',
            'fee_info': '',
            'process': 'Submit application to Planning Department',
            'timeline_info': '',
            'additional_requirements': '',
            'reference': self.extract_reference(answer)
        }
        
        # Check if permit is required
        if 'not required' in answer.lower() or 'no permit' in answer.lower():
            fields['required'] = 'No'
        elif 'exempt' in answer.lower():
            fields['required'] = 'No (Exempt)'
        
        # Extract permit type
        if 'building permit' in answer.lower():
            fields['permit_type'] = 'Building Permit'
        elif 'special' in answer.lower() and 'permit' in answer.lower():
            fields['permit_type'] = 'Special Use Permit'
        elif 'zoning permit' in answer.lower():
            fields['permit_type'] = 'Zoning Permit'
        
        # Extract fee info
        import re
        fee_pattern = r'\$(\d+)'
        fee_match = re.search(fee_pattern, answer)
        if fee_match:
            fields['fee_info'] = f"**Fee:** ${fee_match.group(1)}"
        
        return fields
    
    def extract_livestock_fields(self, answer: str) -> Dict[str, str]:
        """Extract livestock-specific fields from answer"""
        fields = {
            'animal_type': 'Not specified',
            'allowed': 'Check regulations',
            'zone': 'Not specified',
            'min_lot_size': 'Not specified',
            'max_number': 'Not specified',
            'requirements': '',
            'reference': self.extract_reference(answer)
        }
        
        # Extract animal type
        animals = ['chickens', 'horses', 'cows', 'goats', 'sheep', 'poultry', 'livestock']
        for animal in animals:
            if animal in answer.lower():
                fields['animal_type'] = animal.capitalize()
                break
        
        # Extract allowed status
        if 'permitted' in answer.lower() or 'allowed' in answer.lower():
            fields['allowed'] = 'Yes'
        elif 'not permitted' in answer.lower() or 'prohibited' in answer.lower():
            fields['allowed'] = 'No'
        
        # Extract lot size requirements
        import re
        acre_pattern = r'(\d+(?:\.\d+)?)\s*acre'
        acre_match = re.search(acre_pattern, answer, re.IGNORECASE)
        if acre_match:
            fields['min_lot_size'] = f"{acre_match.group(1)} acres"
        
        # Extract zone
        zone_pattern = r'(AR-\d+|R-\d+|A-\d+)'
        zone_match = re.search(zone_pattern, answer, re.IGNORECASE)
        if zone_match:
            fields['zone'] = zone_match.group(1)
        
        return fields
    
    def extract_use_fields(self, answer: str) -> Dict[str, str]:
        """Extract use-specific fields from answer"""
        fields = {
            'use_type': 'Not specified',
            'permitted': 'Check regulations',
            'zone': 'Not specified',
            'conditions': '',
            'process': 'Contact Planning Department',
            'reference': self.extract_reference(answer)
        }
        
        # Extract permitted status
        if 'permitted by right' in answer.lower():
            fields['permitted'] = 'Yes (By Right)'
        elif 'special exception' in answer.lower():
            fields['permitted'] = 'Yes (With Special Exception)'
        elif 'conditional use' in answer.lower():
            fields['permitted'] = 'Yes (Conditional)'
        elif 'not permitted' in answer.lower():
            fields['permitted'] = 'No'
        
        return fields
    
    def extract_reference(self, answer: str) -> str:
        """Extract section references from answer"""
        import re
        
        # Look for section references
        section_pattern = r'Section\s+(\d+-\d+)'
        matches = re.findall(section_pattern, answer, re.IGNORECASE)
        
        if matches:
            return f"Section {', '.join(matches)}"
        
        return "See Loudoun County Zoning Ordinance"
    
    def format_answer(self, question: str, answer: str, citations: List[Dict] = None) -> str:
        """Format answer using appropriate template"""
        # Detect template type
        template_type = self.detect_template_type(question, answer)
        
        # Extract fields from answer
        fields = self.extract_fields(answer, template_type)
        
        # Get template
        template = self.templates[template_type]
        
        # Add citations if provided
        if citations and len(citations) > 0:
            citation_text = ', '.join([f"Section {c.get('section', 'Unknown')}" for c in citations[:3]])
            fields['reference'] = citation_text
        
        # Format using template
        try:
            # Only include non-empty optional fields
            format_dict = {}
            for key, value in fields.items():
                if value and value.strip():
                    format_dict[key] = value
                else:
                    format_dict[key] = ''
            
            formatted = template['format'].format(**format_dict)
            
            # Clean up empty lines
            lines = [line for line in formatted.split('\n') if line.strip() or line == '']
            return '\n'.join(lines)
            
        except KeyError:
            # Fallback to simple format if template fails
            return f"**Answer:** {answer}\n\n**Reference:** {fields.get('reference', 'See Zoning Ordinance')}"