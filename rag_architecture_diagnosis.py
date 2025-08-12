#!/usr/bin/env python3
"""
RAG Architecture Diagnosis & Verification Tool
==============================================

This tool systematically checks every component of the RAG pipeline
to identify where the "Sorry, something went wrong." error is coming from.

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
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rag_diagnosis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RAGArchitectureDiagnostic:
    """Comprehensive RAG architecture diagnostic tool"""
    
    def __init__(self):
        self.base_urls = {
            'ollama': 'http://localhost:11434',
            'ai_service': 'http://localhost:8001',
            'app_server': 'http://localhost:3001',
            'react_client': 'http://localhost:3000'
        }
        self.test_results = {}
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
    def log_result(self, test_name: str, status: str, details: Dict[str, Any]):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'status': status,
            'details': details
        }
        self.test_results[test_name] = result
        
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        logger.info(f"{status_symbol} {test_name}: {status}")
        
        if status == "FAIL" and details.get('error'):
            logger.error(f"   Error: {details['error']}")
        elif details.get('info'):
            logger.info(f"   Info: {details['info']}")
    
    def test_1_service_connectivity(self):
        """Test 1: Basic service connectivity"""
        logger.info("=" * 60)
        logger.info("TEST 1: Service Connectivity Check")
        logger.info("=" * 60)
        
        connectivity_results = {}
        
        # Test Ollama
        try:
            response = self.session.get(f"{self.base_urls['ollama']}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                connectivity_results['ollama'] = True
                self.log_result("ollama_connectivity", "PASS", {
                    'status_code': response.status_code,
                    'models_available': len(models),
                    'model_names': model_names
                })
            else:
                connectivity_results['ollama'] = False
                self.log_result("ollama_connectivity", "FAIL", {
                    'status_code': response.status_code
                })
        except Exception as e:
            connectivity_results['ollama'] = False
            self.log_result("ollama_connectivity", "FAIL", {'error': str(e)})
        
        # Test AI Service
        try:
            response = self.session.get(f"{self.base_urls['ai_service']}/api/status")
            if response.status_code == 200:
                connectivity_results['ai_service'] = True
                self.log_result("ai_service_connectivity", "PASS", {
                    'status_code': response.status_code,
                    'response': response.text[:200]
                })
            else:
                connectivity_results['ai_service'] = False
                self.log_result("ai_service_connectivity", "FAIL", {
                    'status_code': response.status_code,
                    'response': response.text[:200]
                })
        except Exception as e:
            connectivity_results['ai_service'] = False
            self.log_result("ai_service_connectivity", "FAIL", {'error': str(e)})
        
        # Test App Server
        try:
            response = self.session.get(f"{self.base_urls['app_server']}")
            connectivity_results['app_server'] = response.status_code in [200, 404]  # 404 is OK for API server
            self.log_result("app_server_connectivity", "PASS" if connectivity_results['app_server'] else "FAIL", {
                'status_code': response.status_code
            })
        except Exception as e:
            connectivity_results['app_server'] = False
            self.log_result("app_server_connectivity", "FAIL", {'error': str(e)})
        
        return connectivity_results
    
    def test_2_ollama_models(self):
        """Test 2: Ollama model availability and functionality"""
        logger.info("=" * 60)
        logger.info("TEST 2: Ollama Models Check")
        logger.info("=" * 60)
        
        try:
            # Check available models
            response = self.session.get(f"{self.base_urls['ollama']}/api/tags")
            if response.status_code != 200:
                self.log_result("ollama_models_check", "FAIL", {
                    'error': f'Cannot get model list: HTTP {response.status_code}'
                })
                return False
            
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            # Check required models
            required_models = ['mxbai-embed-large', 'qwen2']
            missing_models = []
            
            for required in required_models:
                found = any(required in model for model in available_models)
                if not found:
                    missing_models.append(required)
            
            if missing_models:
                self.log_result("ollama_models_check", "FAIL", {
                    'available_models': available_models,
                    'missing_models': missing_models,
                    'error': f'Missing required models: {missing_models}'
                })
                return False
            
            # Test model generation
            test_model = 'qwen2'
            try:
                test_payload = {
                    "model": test_model,
                    "prompt": "Hello, this is a test. Please respond briefly.",
                    "stream": False
                }
                
                gen_response = self.session.post(
                    f"{self.base_urls['ollama']}/api/generate",
                    json=test_payload,
                    timeout=30
                )
                
                if gen_response.status_code == 200:
                    gen_data = gen_response.json()
                    self.log_result("ollama_generation_test", "PASS", {
                        'model': test_model,
                        'response_length': len(gen_data.get('response', '')),
                        'response_preview': gen_data.get('response', '')[:100]
                    })
                    return True
                else:
                    self.log_result("ollama_generation_test", "FAIL", {
                        'model': test_model,
                        'status_code': gen_response.status_code,
                        'error': gen_response.text[:200]
                    })
                    return False
                    
            except Exception as e:
                self.log_result("ollama_generation_test", "FAIL", {
                    'model': test_model,
                    'error': str(e)
                })
                return False
                
        except Exception as e:
            self.log_result("ollama_models_check", "FAIL", {'error': str(e)})
            return False
    
    def test_3_ai_service_endpoints(self):
        """Test 3: AI Service API endpoints"""
        logger.info("=" * 60)
        logger.info("TEST 3: AI Service Endpoints Check")
        logger.info("=" * 60)
        
        endpoints = [
            {'path': '/api/status', 'method': 'GET', 'name': 'status'},
            {'path': '/api/health', 'method': 'GET', 'name': 'health'},
            {'path': '/docs', 'method': 'GET', 'name': 'docs'},
        ]
        
        all_passed = True
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_urls['ai_service']}{endpoint['path']}"
                
                if endpoint['method'] == 'GET':
                    response = self.session.get(url)
                else:
                    response = self.session.post(url)
                
                if response.status_code in [200, 201]:
                    self.log_result(f"ai_service_{endpoint['name']}", "PASS", {
                        'status_code': response.status_code,
                        'response_length': len(response.text),
                        'content_type': response.headers.get('content-type', 'unknown')
                    })
                else:
                    self.log_result(f"ai_service_{endpoint['name']}", "FAIL", {
                        'status_code': response.status_code,
                        'error': response.text[:200]
                    })
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"ai_service_{endpoint['name']}", "FAIL", {
                    'error': str(e)
                })
                all_passed = False
        
        return all_passed
    
    def test_4_database_connection(self):
        """Test 4: ChromaDB connection and data"""
        logger.info("=" * 60)
        logger.info("TEST 4: Database Connection Check")
        logger.info("=" * 60)
        
        try:
            # Try to get database status through AI service
            response = self.session.get(f"{self.base_urls['ai_service']}/api/health")
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check if database info is in health response
                db_info = health_data.get('database', {})
                if db_info:
                    self.log_result("database_connection", "PASS", {
                        'database_info': db_info,
                        'collections': db_info.get('collections', []),
                        'total_documents': db_info.get('total_documents', 0)
                    })
                    return True
                else:
                    self.log_result("database_connection", "FAIL", {
                        'error': 'No database info in health response',
                        'health_response': health_data
                    })
                    return False
            else:
                self.log_result("database_connection", "FAIL", {
                    'error': f'Health endpoint failed: HTTP {response.status_code}',
                    'response': response.text[:200]
                })
                return False
                
        except Exception as e:
            self.log_result("database_connection", "FAIL", {'error': str(e)})
            return False
    
    def test_5_rag_query_pipeline(self):
        """Test 5: Complete RAG query pipeline"""
        logger.info("=" * 60)
        logger.info("TEST 5: RAG Query Pipeline Test")
        logger.info("=" * 60)
        
        test_queries = [
            {
                'name': 'simple_test',
                'query': 'Hello, can you help me?',
                'expected': 'Should get a response'
            },
            {
                'name': 'document_query',
                'query': 'What security guidelines are available?',
                'expected': 'Should retrieve relevant documents'
            },
            {
                'name': 'empty_query',
                'query': '',
                'expected': 'Should handle empty query gracefully'
            }
        ]
        
        all_passed = True
        
        for test_query in test_queries:
            try:
                payload = {
                    'question': test_query['query']
                }
                
                # Test through AI Service directly
                response = self.session.post(
                    f"{self.base_urls['ai_service']}/ask",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        self.log_result(f"rag_query_{test_query['name']}", "PASS", {
                            'query': test_query['query'],
                            'status_code': response.status_code,
                            'has_answer': bool(response_data.get('answer')),
                            'answer_length': len(str(response_data.get('answer', ''))),
                            'has_sources': bool(response_data.get('sources')),
                            'response_preview': str(response_data)[:200]
                        })
                    except json.JSONDecodeError as e:
                        self.log_result(f"rag_query_{test_query['name']}", "FAIL", {
                            'query': test_query['query'],
                            'error': f'Invalid JSON response: {str(e)}',
                            'raw_response': response.text[:200]
                        })
                        all_passed = False
                else:
                    self.log_result(f"rag_query_{test_query['name']}", "FAIL", {
                        'query': test_query['query'],
                        'status_code': response.status_code,
                        'error': response.text[:200]
                    })
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"rag_query_{test_query['name']}", "FAIL", {
                    'query': test_query['query'],
                    'error': str(e)
                })
                all_passed = False
        
        return all_passed
    
    def test_6_frontend_backend_integration(self):
        """Test 6: Frontend-Backend integration"""
        logger.info("=" * 60)
        logger.info("TEST 6: Frontend-Backend Integration Test")
        logger.info("=" * 60)
        
        try:
            # Test the actual API endpoint that frontend uses
            payload = {
                'question': 'Test question from frontend integration test'
            }
            
            # Test through App Server (which should proxy to AI Service)
            response = self.session.post(
                f"{self.base_urls['app_server']}/api/ask",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    self.log_result("frontend_backend_integration", "PASS", {
                        'status_code': response.status_code,
                        'response_data': response_data,
                        'integration_working': True
                    })
                    return True
                except json.JSONDecodeError:
                    self.log_result("frontend_backend_integration", "FAIL", {
                        'error': 'Invalid JSON from app server',
                        'raw_response': response.text[:200]
                    })
                    return False
            else:
                self.log_result("frontend_backend_integration", "FAIL", {
                    'status_code': response.status_code,
                    'error': response.text[:200],
                    'app_server_issue': True
                })
                return False
                
        except Exception as e:
            self.log_result("frontend_backend_integration", "FAIL", {
                'error': str(e),
                'connection_issue': True
            })
            return False
    
    def generate_diagnosis_report(self):
        """Generate comprehensive diagnosis report"""
        logger.info("=" * 60)
        logger.info("GENERATING DIAGNOSIS REPORT")
        logger.info("=" * 60)
        
        report_lines = [
            "RAG Architecture Diagnosis Report",
            "=" * 50,
            f"Diagnosis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Tests: {len(self.test_results)}",
            ""
        ]
        
        # Summary statistics
        passed_tests = len([r for r in self.test_results.values() if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results.values() if r['status'] == 'FAIL'])
        
        report_lines.extend([
            "Test Summary:",
            f"  PASSED: {passed_tests}",
            f"  FAILED: {failed_tests}",
            f"  SUCCESS RATE: {(passed_tests / len(self.test_results) * 100):.1f}%",
            ""
        ])
        
        # Critical issues
        critical_failures = []
        for test_name, result in self.test_results.items():
            if result['status'] == 'FAIL':
                critical_failures.append({
                    'test': test_name,
                    'error': result['details'].get('error', 'Unknown error')
                })
        
        if critical_failures:
            report_lines.append("CRITICAL ISSUES FOUND:")
            report_lines.append("-" * 30)
            for failure in critical_failures:
                report_lines.append(f"❌ {failure['test']}")
                report_lines.append(f"   Error: {failure['error']}")
            report_lines.append("")
        
        # Detailed results
        report_lines.append("Detailed Test Results:")
        report_lines.append("-" * 30)
        
        for test_name, result in self.test_results.items():
            status_symbol = "✅" if result['status'] == 'PASS' else "❌"
            report_lines.append(f"{status_symbol} {test_name}: {result['status']}")
            
            if result['details'].get('info'):
                report_lines.append(f"    Info: {result['details']['info']}")
            if result['details'].get('error'):
                report_lines.append(f"    Error: {result['details']['error']}")
        
        # Recommendations
        report_lines.extend([
            "",
            "RECOMMENDATIONS:",
            "-" * 20
        ])
        
        if any('ollama' in name and result['status'] == 'FAIL' for name, result in self.test_results.items()):
            report_lines.append("• Fix Ollama service and model issues")
        
        if any('ai_service' in name and result['status'] == 'FAIL' for name, result in self.test_results.items()):
            report_lines.append("• Check AI Service logs for errors")
        
        if any('database' in name and result['status'] == 'FAIL' for name, result in self.test_results.items()):
            report_lines.append("• Verify ChromaDB connection and data loading")
        
        if any('integration' in name and result['status'] == 'FAIL' for name, result in self.test_results.items()):
            report_lines.append("• Check App Server to AI Service communication")
        
        report_content = "\n".join(report_lines)
        
        # Save report to file
        report_file = f"logs/rag_diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Diagnosis report saved to: {report_file}")
        print("\n" + report_content)
        
        return report_content, critical_failures
    
    def run_complete_diagnosis(self):
        """Run complete RAG architecture diagnosis"""
        logger.info("Starting Complete RAG Architecture Diagnosis")
        logger.info("=" * 80)
        
        # Run all tests
        test_1_result = self.test_1_service_connectivity()
        test_2_result = self.test_2_ollama_models()
        test_3_result = self.test_3_ai_service_endpoints()
        test_4_result = self.test_4_database_connection()
        test_5_result = self.test_5_rag_query_pipeline()
        test_6_result = self.test_6_frontend_backend_integration()
        
        # Generate report
        report, critical_failures = self.generate_diagnosis_report()
        
        # Return summary
        return {
            'total_tests': len(self.test_results),
            'passed': len([r for r in self.test_results.values() if r['status'] == 'PASS']),
            'failed': len([r for r in self.test_results.values() if r['status'] == 'FAIL']),
            'critical_failures': critical_failures,
            'all_tests_passed': len(critical_failures) == 0
        }

def main():
    """Main execution function"""
    print("RAG Architecture Diagnosis Tool")
    print("=" * 50)
    
    diagnostic = RAGArchitectureDiagnostic()
    results = diagnostic.run_complete_diagnosis()
    
    print(f"\nFinal Summary:")
    print(f"Tests Passed: {results['passed']}/{results['total_tests']}")
    print(f"Success Rate: {(results['passed'] / results['total_tests'] * 100):.1f}%")
    
    if results['critical_failures']:
        print(f"\n❌ {len(results['critical_failures'])} critical issues found!")
        print("The RAG pipeline has problems that need to be fixed.")
        return 1
    else:
        print(f"\n✅ All tests passed! RAG architecture is healthy.")
        return 0

if __name__ == "__main__":
    exit(main())
