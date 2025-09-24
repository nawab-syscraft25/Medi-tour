#!/usr/bin/env python3
"""
Load Testing Script for Medi-Tour API
Tests various endpoints with different load patterns
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any
import argparse


class LoadTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results = []
        
    async def make_request(self, session: aiohttp.ClientSession, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a single HTTP request and measure response time"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with session.request(method, url, **kwargs) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                # Try to read response body
                try:
                    body = await response.text()
                    if response.headers.get('content-type', '').startswith('application/json'):
                        body = await response.json()
                except:
                    body = None
                
                return {
                    'url': url,
                    'method': method,
                    'status': response.status,
                    'response_time': response_time,
                    'success': 200 <= response.status < 300,
                    'error': None,
                    'body_size': len(str(body)) if body else 0
                }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                'url': url,
                'method': method,
                'status': 0,
                'response_time': response_time,
                'success': False,
                'error': str(e),
                'body_size': 0
            }

    async def concurrent_requests(self, endpoint: str, method: str = 'GET', 
                                concurrent_users: int = 10, total_requests: int = 100,
                                **request_kwargs) -> List[Dict[str, Any]]:
        """Execute concurrent requests to an endpoint"""
        
        print(f"🚀 Testing {method} {endpoint}")
        print(f"   Concurrent Users: {concurrent_users}")
        print(f"   Total Requests: {total_requests}")
        
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            # Create batches of concurrent requests
            requests_per_batch = total_requests // concurrent_users
            remaining_requests = total_requests % concurrent_users
            
            start_time = time.time()
            
            for batch in range(concurrent_users):
                batch_requests = requests_per_batch + (1 if batch < remaining_requests else 0)
                
                for _ in range(batch_requests):
                    task = asyncio.create_task(
                        self.make_request(session, method, endpoint, **request_kwargs)
                    )
                    tasks.append(task)
            
            # Execute all requests
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Process results
            valid_results = []
            for result in results:
                if isinstance(result, dict):
                    valid_results.append(result)
                else:
                    # Handle exceptions
                    valid_results.append({
                        'url': f"{self.base_url}{endpoint}",
                        'method': method,
                        'status': 0,
                        'response_time': 0,
                        'success': False,
                        'error': str(result),
                        'body_size': 0
                    })
            
            # Calculate statistics
            response_times = [r['response_time'] for r in valid_results if r['success']]
            success_count = sum(1 for r in valid_results if r['success'])
            error_count = len(valid_results) - success_count
            
            stats = {
                'endpoint': endpoint,
                'method': method,
                'total_requests': len(valid_results),
                'successful_requests': success_count,
                'failed_requests': error_count,
                'success_rate': (success_count / len(valid_results)) * 100 if valid_results else 0,
                'total_time': total_time,
                'requests_per_second': len(valid_results) / total_time if total_time > 0 else 0,
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'median_response_time': statistics.median(response_times) if response_times else 0,
                'p95_response_time': self.percentile(response_times, 95) if response_times else 0,
                'p99_response_time': self.percentile(response_times, 99) if response_times else 0
            }
            
            self.print_results(stats)
            self.results.append(stats)
            
            return valid_results

    def percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of numbers"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def print_results(self, stats: Dict[str, Any]):
        """Print formatted test results"""
        print(f"\n📊 Results for {stats['method']} {stats['endpoint']}")
        print("=" * 60)
        print(f"Total Requests:       {stats['total_requests']}")
        print(f"Successful:          {stats['successful_requests']}")
        print(f"Failed:              {stats['failed_requests']}")
        print(f"Success Rate:        {stats['success_rate']:.2f}%")
        print(f"Total Time:          {stats['total_time']:.2f}s")
        print(f"Requests/Second:     {stats['requests_per_second']:.2f}")
        print(f"Avg Response Time:   {stats['avg_response_time']:.2f}ms")
        print(f"Min Response Time:   {stats['min_response_time']:.2f}ms")
        print(f"Max Response Time:   {stats['max_response_time']:.2f}ms")
        print(f"Median Response:     {stats['median_response_time']:.2f}ms")
        print(f"95th Percentile:     {stats['p95_response_time']:.2f}ms")
        print(f"99th Percentile:     {stats['p99_response_time']:.2f}ms")
        print("=" * 60)

    async def run_load_tests(self, test_config: List[Dict[str, Any]]):
        """Run a series of load tests"""
        print(f"🎯 Starting Load Tests for {self.base_url}")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        for i, test in enumerate(test_config, 1):
            print(f"\n🔄 Running Test {i}/{len(test_config)}")
            await self.concurrent_requests(**test)
            
            # Wait between tests
            if i < len(test_config):
                print("⏳ Waiting 5 seconds before next test...")
                await asyncio.sleep(5)
        
        self.print_summary()

    def print_summary(self):
        """Print overall test summary"""
        print(f"\n🏁 Load Test Summary")
        print("=" * 80)
        
        total_requests = sum(r['total_requests'] for r in self.results)
        total_successful = sum(r['successful_requests'] for r in self.results)
        total_failed = sum(r['failed_requests'] for r in self.results)
        overall_success_rate = (total_successful / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"Total Tests Run:      {len(self.results)}")
        print(f"Total Requests:       {total_requests}")
        print(f"Total Successful:     {total_successful}")
        print(f"Total Failed:         {total_failed}")
        print(f"Overall Success Rate: {overall_success_rate:.2f}%")
        
        # Best and worst performing endpoints
        if self.results:
            best_rps = max(self.results, key=lambda x: x['requests_per_second'])
            worst_rps = min(self.results, key=lambda x: x['requests_per_second'])
            
            print(f"\n🏆 Best Performance:   {best_rps['method']} {best_rps['endpoint']} ({best_rps['requests_per_second']:.2f} req/s)")
            print(f"🐌 Worst Performance:  {worst_rps['method']} {worst_rps['endpoint']} ({worst_rps['requests_per_second']:.2f} req/s)")
        
        print("=" * 80)

    def save_results(self, filename: str):
        """Save results to JSON file"""
        results_data = {
            'test_timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'results': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Results saved to {filename}")


async def main():
    parser = argparse.ArgumentParser(description="Load Test Medi-Tour API")
    parser.add_argument("--url", default="http://165.22.223.163:8000", help="Base URL of the API")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--requests", type=int, default=100, help="Total number of requests per test")
    parser.add_argument("--save", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Initialize load tester
    tester = LoadTester(args.url)
    
    # Define test scenarios
    test_config = [
        # Basic endpoint tests
        {
            'endpoint': '/api/v1/doctors',
            'method': 'GET',
            'concurrent_users': args.users,
            'total_requests': args.requests,
            'params': {'skip': 0, 'limit': 10}
        },
        {
            'endpoint': '/api/v1/hospitals',
            'method': 'GET',
            'concurrent_users': args.users,
            'total_requests': args.requests,
            'params': {'skip': 0, 'limit': 10}
        },
        {
            'endpoint': '/api/v1/treatments',
            'method': 'GET',
            'concurrent_users': args.users,
            'total_requests': args.requests,
            'params': {'skip': 0, 'limit': 10}
        },
        # Filter endpoints
        {
            'endpoint': '/api/filters/locations',
            'method': 'GET',
            'concurrent_users': args.users,
            'total_requests': args.requests
        },
        {
            'endpoint': '/api/filters/treatment-types',
            'method': 'GET',
            'concurrent_users': args.users,
            'total_requests': args.requests
        },
        {
            'endpoint': '/api/filters/specializations',
            'method': 'GET',
            'concurrent_users': args.users,
            'total_requests': args.requests
        },
        # Search with filters
        {
            'endpoint': '/api/v1/treatments',
            'method': 'GET',
            'concurrent_users': args.users // 2,  # Lower load for filtered queries
            'total_requests': args.requests // 2,
            'params': {'location': 'New York', 'treatment_type': 'Cardiology'}
        },
        # High load test
        {
            'endpoint': '/api/v1/doctors',
            'method': 'GET',
            'concurrent_users': args.users * 2,  # Double the users
            'total_requests': args.requests * 2,  # Double the requests
            'params': {'skip': 0, 'limit': 5}
        }
    ]
    
    # Run the tests
    await tester.run_load_tests(test_config)
    
    # Save results if requested
    if args.save:
        tester.save_results(args.save)


if __name__ == "__main__":
    asyncio.run(main())