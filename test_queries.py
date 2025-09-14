#!/usr/bin/env python3
"""
RAG v2.0 Test Suite for Loudoun County Zoning System
Tests 20 common real-world questions to ensure accuracy
"""

import os
import sys
import json
import time
from typing import Dict, List
from query_engine import ZoningQueryEngine

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class ZoningTestSuite:
    """Test suite for validating RAG v2.0 improvements"""
    
    def __init__(self):
        self.engine = ZoningQueryEngine()
        self.test_results = []
        self.county = "loudoun"
        
        # Define 20 real test questions with expected content
        self.test_questions = [
            {
                "id": 1,
                "question": "Can I build a shed in AR-1?",
                "expected_keywords": ["yes", "allowed", "permitted", "accessory structure"],
                "should_not_contain": ["definition of agriculture"],
                "category": "permit"
            },
            {
                "id": 2,
                "question": "What's the setback for a barn?",
                "expected_keywords": ["50 feet", "property line", "agricultural structure"],
                "should_not_contain": ["unknown"],
                "category": "setback"
            },
            {
                "id": 3,
                "question": "Do I need a permit for chickens?",
                "expected_keywords": ["2 acres", "no permit", "agricultural"],
                "should_not_contain": ["unknown"],
                "category": "permit"
            },
            {
                "id": 4,
                "question": "How far from property line for accessory structure?",
                "expected_keywords": ["25 feet", "side", "rear", "property line"],
                "should_not_contain": ["unknown"],
                "category": "setback"
            },
            {
                "id": 5,
                "question": "Are horses allowed on 2 acres?",
                "expected_keywords": ["yes", "allowed", "1 horse per acre", "2 horses"],
                "should_not_contain": ["prohibited", "not allowed"],
                "category": "livestock"
            },
            {
                "id": 6,
                "question": "Can I have chickens on 1 acre?",
                "expected_keywords": ["no", "2 acres", "minimum", "required"],
                "should_not_contain": ["yes", "allowed"],
                "category": "livestock"
            },
            {
                "id": 7,
                "question": "Do I need a permit for a shed?",
                "expected_keywords": ["200 square feet", "permit", "required"],
                "should_not_contain": ["unknown"],
                "category": "permit"
            },
            {
                "id": 8,
                "question": "How many chickens can I have?",
                "expected_keywords": ["2 acres", "personal use", "agricultural"],
                "should_not_contain": ["prohibited"],
                "category": "livestock"
            },
            {
                "id": 9,
                "question": "What's the minimum lot size in AR-1?",
                "expected_keywords": ["3 acres", "minimum", "lot size"],
                "should_not_contain": ["unknown"],
                "category": "zoning"
            },
            {
                "id": 10,
                "question": "Can I run a business from home?",
                "expected_keywords": ["special exception", "home business", "permit"],
                "should_not_contain": ["prohibited"],
                "category": "use"
            },
            {
                "id": 11,
                "question": "Shed setback requirements",
                "expected_keywords": ["25 feet", "property line", "accessory structure"],
                "should_not_contain": ["unknown"],
                "category": "setback"
            },
            {
                "id": 12,
                "question": "Garage setback",
                "expected_keywords": ["25 feet", "property line", "detached"],
                "should_not_contain": ["unknown"],
                "category": "setback"
            },
            {
                "id": 13,
                "question": "Maximum shed size without permit",
                "expected_keywords": ["200 square feet", "exempt", "no permit"],
                "should_not_contain": ["unknown"],
                "category": "permit"
            },
            {
                "id": 14,
                "question": "Can I build a pool?",
                "expected_keywords": ["yes", "permit", "10 feet", "setback"],
                "should_not_contain": ["prohibited"],
                "category": "permit"
            },
            {
                "id": 15,
                "question": "Fence height limit",
                "expected_keywords": ["6 feet", "rear", "4 feet", "front"],
                "should_not_contain": ["unknown"],
                "category": "structure"
            },
            {
                "id": 16,
                "question": "Permit for fence",
                "expected_keywords": ["6 feet", "4 feet", "height", "permit"],
                "should_not_contain": ["unknown"],
                "category": "permit"
            },
            {
                "id": 17,
                "question": "What can I build in AR-1?",
                "expected_keywords": ["single-family", "agricultural", "accessory"],
                "should_not_contain": ["commercial", "industrial"],
                "category": "use"
            },
            {
                "id": 18,
                "question": "Accessory structure height",
                "expected_keywords": ["25 feet", "height", "maximum"],
                "should_not_contain": ["unknown"],
                "category": "structure"
            },
            {
                "id": 19,
                "question": "Driveway permit",
                "expected_keywords": ["permit", "VDOT", "required"],
                "should_not_contain": ["not required"],
                "category": "permit"
            },
            {
                "id": 20,
                "question": "Beekeeping allowed",
                "expected_keywords": ["yes", "allowed", "2 acres", "50 feet"],
                "should_not_contain": ["prohibited"],
                "category": "livestock"
            }
        ]
    
    def check_answer_quality(self, answer: str, expected_keywords: List[str], 
                            should_not_contain: List[str]) -> Dict:
        """Check if answer contains expected content"""
        answer_lower = answer.lower()
        
        # Check for expected keywords
        found_keywords = []
        missing_keywords = []
        for keyword in expected_keywords:
            if keyword.lower() in answer_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Check for unwanted content
        unwanted_found = []
        for unwanted in should_not_contain:
            if unwanted.lower() in answer_lower:
                unwanted_found.append(unwanted)
        
        # Calculate score
        score = len(found_keywords) / len(expected_keywords) if expected_keywords else 0
        if unwanted_found:
            score *= 0.5  # Penalty for unwanted content
        
        return {
            'score': score,
            'found_keywords': found_keywords,
            'missing_keywords': missing_keywords,
            'unwanted_found': unwanted_found,
            'passed': score >= 0.7 and not unwanted_found
        }
    
    def run_single_test(self, test_case: Dict) -> Dict:
        """Run a single test question"""
        print(f"\n{BLUE}Test #{test_case['id']}: {test_case['question']}{RESET}")
        
        start_time = time.time()
        
        try:
            # Get answer from the engine
            result = self.engine.answer_question(test_case['question'], self.county)
            
            response_time = time.time() - start_time
            
            # Check answer quality
            quality = self.check_answer_quality(
                result['answer'],
                test_case['expected_keywords'],
                test_case['should_not_contain']
            )
            
            # Prepare test result
            test_result = {
                'id': test_case['id'],
                'question': test_case['question'],
                'category': test_case['category'],
                'answer': result['answer'][:200] + '...' if len(result['answer']) > 200 else result['answer'],
                'full_answer': result['answer'],
                'citations': result.get('citations', []),
                'cached': result.get('cached', False),
                'response_time': response_time,
                'quality': quality,
                'passed': quality['passed']
            }
            
            # Print result
            if test_result['passed']:
                print(f"{GREEN}✓ PASSED{RESET} (Score: {quality['score']:.2f}, Time: {response_time:.2f}s)")
                if test_result['cached']:
                    print(f"  {YELLOW}(Cached response){RESET}")
            else:
                print(f"{RED}✗ FAILED{RESET} (Score: {quality['score']:.2f}, Time: {response_time:.2f}s)")
                if quality['missing_keywords']:
                    print(f"  Missing: {', '.join(quality['missing_keywords'])}")
                if quality['unwanted_found']:
                    print(f"  {RED}Unwanted: {', '.join(quality['unwanted_found'])}{RESET}")
            
            return test_result
            
        except Exception as e:
            print(f"{RED}✗ ERROR: {str(e)}{RESET}")
            return {
                'id': test_case['id'],
                'question': test_case['question'],
                'category': test_case['category'],
                'error': str(e),
                'passed': False
            }
    
    def run_all_tests(self):
        """Run all test questions"""
        print(f"\n{BOLD}=== RAG v2.0 Test Suite ==={RESET}")
        print(f"Testing {len(self.test_questions)} common zoning questions\n")
        
        total_time = 0
        passed = 0
        failed = 0
        cached_count = 0
        
        # Run each test
        for test_case in self.test_questions:
            result = self.run_single_test(test_case)
            self.test_results.append(result)
            
            if result['passed']:
                passed += 1
            else:
                failed += 1
            
            if result.get('cached'):
                cached_count += 1
            
            total_time += result.get('response_time', 0)
        
        # Print summary
        print(f"\n{BOLD}=== Test Summary ==={RESET}")
        print(f"Total Tests: {len(self.test_questions)}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"Success Rate: {passed/len(self.test_questions)*100:.1f}%")
        print(f"\nPerformance:")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Average Time: {total_time/len(self.test_questions):.2f}s")
        print(f"  Cached Responses: {cached_count}")
        
        # Category breakdown
        category_stats = {}
        for result in self.test_results:
            cat = result.get('category', 'unknown')
            if cat not in category_stats:
                category_stats[cat] = {'passed': 0, 'failed': 0}
            
            if result['passed']:
                category_stats[cat]['passed'] += 1
            else:
                category_stats[cat]['failed'] += 1
        
        print(f"\n{BOLD}Category Breakdown:{RESET}")
        for cat, stats in category_stats.items():
            total = stats['passed'] + stats['failed']
            success_rate = stats['passed'] / total * 100 if total > 0 else 0
            print(f"  {cat}: {stats['passed']}/{total} passed ({success_rate:.0f}%)")
        
        # Save detailed results
        self.save_results()
        
        return passed == len(self.test_questions)
    
    def save_results(self):
        """Save detailed test results to file"""
        results_file = 'test_results.json'
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_tests': len(self.test_questions),
                'passed': sum(1 for r in self.test_results if r['passed']),
                'failed': sum(1 for r in self.test_results if not r['passed']),
                'results': self.test_results
            }, f, indent=2)
        
        print(f"\n{BLUE}Detailed results saved to {results_file}{RESET}")
    
    def run_quick_test(self):
        """Run a quick test with just 5 questions"""
        print(f"\n{BOLD}=== Quick Test (5 questions) ==={RESET}\n")
        
        quick_tests = self.test_questions[:5]
        
        for test_case in quick_tests:
            result = self.run_single_test(test_case)
            if not result['passed']:
                print(f"\n  {YELLOW}Sample answer excerpt:{RESET}")
                print(f"  {result.get('answer', 'No answer')[:150]}...")

def main():
    """Main entry point"""
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "sk-...":
        print(f"{RED}ERROR: Please set your OPENAI_API_KEY environment variable!{RESET}")
        print("You can do this in the Replit Secrets panel")
        sys.exit(1)
    
    # Create test suite
    suite = ZoningTestSuite()
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        suite.run_quick_test()
    else:
        # Run all tests
        all_passed = suite.run_all_tests()
        
        if all_passed:
            print(f"\n{GREEN}{BOLD}🎉 All tests passed! RAG v2.0 is working perfectly!{RESET}")
        else:
            print(f"\n{YELLOW}Some tests failed. Review the results above for details.{RESET}")
            print(f"Run with --quick flag for a quick test of 5 questions")

if __name__ == "__main__":
    main()