#!/usr/bin/env python3
"""
RAG System Testing Suite
========================

This script systematically tests the RAG (Retrieval-Augmented Generation) system
under different conditions to diagnose issues and record various interaction scenarios.

Author: AI Assistant
Date: 2025-08-12
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rag_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RAGSystemTester:
    """Comprehensive RAG system testing suite"""
    
    def __init__(self):
        self.base_urls = {
            'ollama': 'http://localhost:11434',
            'ai_service': 'http://localhost:8001',
            'app_server': 'http://localhost:3001',
            'react_client': 'http://localhost:3000'
        }
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log_test_result(self, test_name: str, status: str, details: Dict[str, Any]):
        """Log test result with timestamp"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'status': status,
            'details': details
        }
        self.test_results.append(result)
        logger.info(f"Test: {test_name} - Status: {status}")
        if details.get('error'):
            logger.error(f"Error details: {details['error']}")
    
    def test_service_connectivity(self) -> Dict[str, bool]:
        """Test basic connectivity to all services"""
        logger.info("=== Testing Service Connectivity ===")
        connectivity_results = {}
        
        for service_name, url in self.base_urls.items():
            try:
                if service_name == 'ollama':
                    response = self.session.get(f"{url}/api/tags")
                elif service_name == 'ai_service':
                    response = self.session.get(f"{url}/api/status")
                else:
                    response = self.session.get(url)
                
                is_connected = response.status_code == 200
                connectivity_results[service_name] = is_connected
                
                self.log_test_result(
                    f"connectivity_{service_name}",
                    "PASS" if is_connected else "FAIL",
                    {
                        'url': url,
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds()
                    }
                )
                
            except Exception as e:
                connectivity_results[service_name] = False
                self.log_test_result(
                    f"connectivity_{service_name}",
                    "FAIL",
                    {
                        'url': url,
                        'error': str(e)
                    }
                )
        
        return connectivity_results
    
    def test_ollama_models(self) -> Dict[str, Any]:
        """Test Ollama model availability and functionality"""
        logger.info("=== Testing Ollama Models ===")
        
        try:
            # Check available models
            response = self.session.get(f"{self.base_urls['ollama']}/api/tags")
            if response.status_code != 200:
                self.log_test_result("ollama_models_list", "FAIL", 
                                   {'error': f'Status code: {response.status_code}'})
                return {'available': False}
            
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            self.log_test_result("ollama_models_list", "PASS", 
                               {'models': available_models})
            
            # Test specific models
            required_models = ['mxbai-embed-large', 'qwen2']
            model_tests = {}
            
            for model in required_models:
                model_available = any(model in m for m in available_models)
                model_tests[model] = model_available
                
                if model_available:
                    # Test model generation
                    try:
                        test_payload = {
                            "model": model,
                            "prompt": "Hello, this is a test.",
                            "stream": False
                        }
                        
                        gen_response = self.session.post(
                            f"{self.base_urls['ollama']}/api/generate",
                            json=test_payload
                        )
                        
                        if gen_response.status_code == 200:
                            self.log_test_result(f"ollama_model_{model}_generation", "PASS",
                                               {'response_time': gen_response.elapsed.total_seconds()})
                        else:
                            self.log_test_result(f"ollama_model_{model}_generation", "FAIL",
                                               {'status_code': gen_response.status_code})
                    except Exception as e:
                        self.log_test_result(f"ollama_model_{model}_generation", "FAIL",
                                           {'error': str(e)})
                else:
                    self.log_test_result(f"ollama_model_{model}_availability", "FAIL",
                                       {'error': 'Model not found in available models'})
            
            return {
                'available': True,
                'models': available_models,
                'required_models_status': model_tests
            }
            
        except Exception as e:
            self.log_test_result("ollama_models_test", "FAIL", {'error': str(e)})
            return {'available': False, 'error': str(e)}
    
    def test_ai_service_endpoints(self) -> Dict[str, Any]:
        """Test AI Service API endpoints"""
        logger.info("=== Testing AI Service Endpoints ===")
        
        endpoints_to_test = [
            {'path': '/api/status', 'method': 'GET', 'name': 'status'},
            {'path': '/api/health', 'method': 'GET', 'name': 'health'},
            {'path': '/docs', 'method': 'GET', 'name': 'docs'},
        ]
        
        endpoint_results = {}
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{self.base_urls['ai_service']}{endpoint['path']}"
                
                if endpoint['method'] == 'GET':
                    response = self.session.get(url)
                else:
                    response = self.session.post(url)
                
                is_working = response.status_code in [200, 201]
                endpoint_results[endpoint['name']] = {
                    'working': is_working,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
                
                self.log_test_result(
                    f"ai_service_endpoint_{endpoint['name']}",
                    "PASS" if is_working else "FAIL",
                    endpoint_results[endpoint['name']]
                )
                
            except Exception as e:
                endpoint_results[endpoint['name']] = {
                    'working': False,
                    'error': str(e)
                }
                self.log_test_result(
                    f"ai_service_endpoint_{endpoint['name']}",
                    "FAIL",
                    {'error': str(e)}
                )
        
        return endpoint_results
    
    def test_rag_query_scenarios(self) -> Dict[str, Any]:
        """Test various RAG query scenarios"""
        logger.info("=== Testing RAG Query Scenarios ===")
        
        test_queries = [
            {
                'name': 'simple_question',
                'query': 'What is artificial intelligence?',
                'expected_type': 'general_knowledge'
            },
            {
                'name': 'document_specific',
                'query': 'What information is available in the documents?',
                'expected_type': 'document_retrieval'
            },
            {
                'name': 'technical_question',
                'query': 'How does RAG work?',
                'expected_type': 'technical_explanation'
            },
            {
                'name': 'empty_query',
                'query': '',
                'expected_type': 'error_handling'
            },
            {
                'name': 'very_long_query',
                'query': 'This is a very long query ' * 50,
                'expected_type': 'edge_case'
            }
        ]
        
        query_results = {}
        
        for test_query in test_queries:
            try:
                # Test through AI Service API
                payload = {
                    'query': test_query['query'],
                    'max_tokens': 150
                }
                
                response = self.session.post(
                    f"{self.base_urls['ai_service']}/api/query",
                    json=payload
                )
                
                result = {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'query_length': len(test_query['query'])
                }
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        result['response_length'] = len(str(response_data))
                        result['has_answer'] = bool(response_data.get('answer'))
                        result['has_sources'] = bool(response_data.get('sources'))
                        
                        self.log_test_result(
                            f"rag_query_{test_query['name']}",
                            "PASS",
                            result
                        )
                    except json.JSONDecodeError:
                        result['error'] = 'Invalid JSON response'
                        self.log_test_result(
                            f"rag_query_{test_query['name']}",
                            "FAIL",
                            result
                        )
                else:
                    result['error'] = f'HTTP {response.status_code}'
                    try:
                        result['error_details'] = response.text
                    except:
                        pass
                    
                    self.log_test_result(
                        f"rag_query_{test_query['name']}",
                        "FAIL",
                        result
                    )
                
                query_results[test_query['name']] = result
                
            except Exception as e:
                query_results[test_query['name']] = {
                    'error': str(e),
                    'query_length': len(test_query['query'])
                }
                self.log_test_result(
                    f"rag_query_{test_query['name']}",
                    "FAIL",
                    {'error': str(e)}
                )
        
        return query_results
    
    def test_database_connectivity(self) -> Dict[str, Any]:
        """Test ChromaDB and vector database connectivity"""
        logger.info("=== Testing Database Connectivity ===")
        
        try:
            # Test ChromaDB through AI Service
            response = self.session.get(f"{self.base_urls['ai_service']}/api/database/status")
            
            if response.status_code == 200:
                db_status = response.json()
                self.log_test_result("database_connectivity", "PASS", db_status)
                return {'connected': True, 'details': db_status}
            else:
                self.log_test_result("database_connectivity", "FAIL", 
                                   {'status_code': response.status_code})
                return {'connected': False, 'status_code': response.status_code}
                
        except Exception as e:
            self.log_test_result("database_connectivity", "FAIL", {'error': str(e)})
            return {'connected': False, 'error': str(e)}
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        logger.info("=== Generating Test Report ===")
        
        report_lines = [
            "RAG System Test Report",
            "=" * 50,
            f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Tests: {len(self.test_results)}",
            ""
        ]
        
        # Summary statistics
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        report_lines.extend([
            "Test Summary:",
            f"  PASSED: {passed_tests}",
            f"  FAILED: {failed_tests}",
            f"  SUCCESS RATE: {(passed_tests / len(self.test_results) * 100):.1f}%",
            ""
        ])
        
        # Detailed results
        report_lines.append("Detailed Results:")
        report_lines.append("-" * 30)
        
        for result in self.test_results:
            status_symbol = "✓" if result['status'] == 'PASS' else "✗"
            report_lines.append(f"{status_symbol} {result['test_name']}: {result['status']}")
            
            if result['status'] == 'FAIL' and result['details'].get('error'):
                report_lines.append(f"    Error: {result['details']['error']}")
        
        report_content = "\n".join(report_lines)
        
        # Save report to file
        report_file = f"logs/rag_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs('logs', exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Test report saved to: {report_file}")
        return report_content
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        logger.info("Starting Comprehensive RAG System Test")
        logger.info("=" * 60)
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Run all test suites
        connectivity = self.test_service_connectivity()
        ollama_status = self.test_ollama_models()
        ai_endpoints = self.test_ai_service_endpoints()
        database_status = self.test_database_connectivity()
        rag_queries = self.test_rag_query_scenarios()
        
        # Generate and display report
        report = self.generate_test_report()
        print("\n" + report)
        
        # Return summary for programmatic use
        return {
            'connectivity': connectivity,
            'ollama': ollama_status,
            'ai_service': ai_endpoints,
            'database': database_status,
            'rag_queries': rag_queries,
            'total_tests': len(self.test_results),
            'passed': len([r for r in self.test_results if r['status'] == 'PASS']),
            'failed': len([r for r in self.test_results if r['status'] == 'FAIL'])
        }

def main():
    """Main execution function"""
    print("RAG System Testing Suite")
    print("=" * 40)
    
    tester = RAGSystemTester()
    results = tester.run_comprehensive_test()
    
    # Print final summary
    print(f"\nFinal Summary:")
    print(f"Tests Passed: {results['passed']}/{results['total_tests']}")
    print(f"Success Rate: {(results['passed'] / results['total_tests'] * 100):.1f}%")
    
    if results['failed'] > 0:
        print(f"\n⚠️  {results['failed']} tests failed. Check logs for details.")
        return 1
    else:
        print(f"\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    exit(main())
