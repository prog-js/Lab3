#!/usr/bin/env python3
import requests
import json
import sys
import argparse
import time

def run_scenario(base_url, scenario_file):
    with open(scenario_file, 'r') as f:
        config = json.load(f)
    
    passed = 0
    failed = 0
    
    for scenario in config['scenarios']:
        print(f"\n📋 Запуск: {scenario['name']}")
        
        url = f"{base_url}{scenario['endpoint']}"
        
        try:
            if scenario['method'] == 'GET':
                resp = requests.get(url, timeout=30)
            elif scenario['method'] == 'POST':
                resp = requests.post(url, json=scenario.get('payload', {}), timeout=30)
            
            if resp.status_code == scenario['expected_status']:
                print(f"  ✅ Status OK: {resp.status_code}")
                passed += 1
            else:
                print(f"  ❌ Status Error: expected {scenario['expected_status']}, got {resp.status_code}")
                failed += 1
                continue
            
            if 'expected_fields' in scenario:
                data = resp.json()
                for field in scenario['expected_fields']:
                    if field in data:
                        print(f"  ✅ Field '{field}' present")
                    else:
                        print(f"  ❌ Field '{field}' missing")
                        failed += 1
            
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            failed += 1
    
    print(f"\n📊 Результаты: passed={passed}, failed={failed}")
    return failed == 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8000')
    parser.add_argument('--scenario', default='scenario.json')
    args = parser.parse_args()
    
    success = run_scenario(args.url, args.scenario)
    sys.exit(0 if success else 1)