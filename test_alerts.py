#!/usr/bin/env python3
import os
import json
import time
import requests
import argparse
import random
from datetime import datetime

# Define the API endpoint URL
API_URL = 'http://localhost:8081/api/sensor_data'

def print_colored(text, color_code):
    """Print text with color"""
    print(f"\033[{color_code}m{text}\033[0m")

def print_info(text):
    """Print information text in cyan"""
    print_colored(f"ℹ️ {text}", 96)

def print_warning(text):
    """Print warning text in yellow"""
    print_colored(f"⚠️ {text}", 93)

def print_error(text):
    """Print error text in red"""
    print_colored(f"❌ {text}", 91)

def print_success(text):
    """Print success text in green"""
    print_colored(f"✅ {text}", 92)

def check_api_available():
    """Check if the Synapse web API is available"""
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            print_success("API is available.")
            return True
        else:
            print_error(f"API returned status code {response.status_code}.")
            return False
    except requests.exceptions.RequestException:
        print_error("Could not connect to API. Is the Synapse Web Server running?")
        return False

def simulate_high_temperature():
    """Simulate high temperature (>38°C)"""
    print_info("Simulating high temperature...")
    
    # Generate a high temperature between 38.5 and 40.0°C
    temp = round(random.uniform(38.5, 40.0), 1)
    print_warning(f"Temperature: {temp}°C")
    
    # Update the vital signs on the server
    try:
        response = requests.post('http://localhost:8081/update_vital_signs', json={
            'temperature': temp,
            'heartRate': 80,
            'heartRateAvg': 82,
            'spo2': 98,
            'spo2Avg': 97,
            'validReadings': True,
            'fallDetected': False
        })
        
        if response.status_code == 200:
            print_success("Vital signs updated.")
            return True
        else:
            print_error(f"Failed to update vital signs: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error updating vital signs: {e}")
        return False

def simulate_high_heart_rate():
    """Simulate high heart rate (>120 BPM)"""
    print_info("Simulating high heart rate...")
    
    # Generate a high heart rate between 120 and 150 BPM
    hr = random.randint(120, 150)
    hr_avg = random.randint(120, hr)
    
    print_warning(f"Heart Rate: {hr} BPM, Average: {hr_avg} BPM")
    
    # Update the vital signs on the server
    try:
        response = requests.post('http://localhost:8081/update_vital_signs', json={
            'temperature': 37.0,
            'heartRate': hr,
            'heartRateAvg': hr_avg,
            'spo2': 98,
            'spo2Avg': 97,
            'validReadings': True,
            'fallDetected': False
        })
        
        if response.status_code == 200:
            print_success("Vital signs updated.")
            return True
        else:
            print_error(f"Failed to update vital signs: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error updating vital signs: {e}")
        return False

def simulate_low_heart_rate():
    """Simulate low heart rate (<50 BPM)"""
    print_info("Simulating low heart rate...")
    
    # Generate a low heart rate between 30 and 49 BPM
    hr = random.randint(30, 49)
    hr_avg = random.randint(30, hr)
    
    print_warning(f"Heart Rate: {hr} BPM, Average: {hr_avg} BPM")
    
    # Update the vital signs on the server
    try:
        response = requests.post('http://localhost:8081/update_vital_signs', json={
            'temperature': 37.0,
            'heartRate': hr,
            'heartRateAvg': hr_avg,
            'spo2': 98,
            'spo2Avg': 97,
            'validReadings': True,
            'fallDetected': False
        })
        
        if response.status_code == 200:
            print_success("Vital signs updated.")
            return True
        else:
            print_error(f"Failed to update vital signs: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error updating vital signs: {e}")
        return False

def simulate_low_spo2():
    """Simulate low SpO2 (<95%)"""
    print_info("Simulating low SpO2...")
    
    # Generate a low SpO2 between 85 and 94%
    spo2 = random.randint(85, 94)
    spo2_avg = random.randint(85, spo2)
    
    print_warning(f"SpO2: {spo2}%, Average: {spo2_avg}%")
    
    # Update the vital signs on the server
    try:
        response = requests.post('http://localhost:8081/update_vital_signs', json={
            'temperature': 37.0,
            'heartRate': 80,
            'heartRateAvg': 82,
            'spo2': spo2,
            'spo2Avg': spo2_avg,
            'validReadings': True,
            'fallDetected': False
        })
        
        if response.status_code == 200:
            print_success("Vital signs updated.")
            return True
        else:
            print_error(f"Failed to update vital signs: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error updating vital signs: {e}")
        return False

def simulate_fall_detection():
    """Simulate fall detection"""
    print_info("Simulating fall detection...")
    
    # Update the vital signs on the server with fall detected
    try:
        response = requests.post('http://localhost:8081/update_vital_signs', json={
            'temperature': 37.0,
            'heartRate': 90,
            'heartRateAvg': 92,
            'spo2': 97,
            'spo2Avg': 96,
            'validReadings': True,
            'fallDetected': True
        })
        
        if response.status_code == 200:
            print_success("Fall detection triggered.")
            return True
        else:
            print_error(f"Failed to update vital signs: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error updating vital signs: {e}")
        return False

def reset_vital_signs():
    """Reset vital signs to normal values"""
    print_info("Resetting vital signs to normal values...")
    
    # Update the vital signs on the server with normal values
    try:
        response = requests.post('http://localhost:8081/update_vital_signs', json={
            'temperature': 36.8,
            'heartRate': 75,
            'heartRateAvg': 72,
            'spo2': 99,
            'spo2Avg': 98,
            'validReadings': True,
            'fallDetected': False
        })
        
        if response.status_code == 200:
            print_success("Vital signs reset to normal.")
            return True
        else:
            print_error(f"Failed to update vital signs: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error updating vital signs: {e}")
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test the Telegram alert system by simulating abnormal vital signs.')
    parser.add_argument('--scenario', choices=['high_temp', 'high_hr', 'low_hr', 'low_spo2', 'fall', 'all', 'reset'], 
                       help='The scenario to simulate')
    parser.add_argument('--delay', type=int, default=60, 
                       help='Delay in seconds between scenarios when running "all" (default: 60)')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    print("\n=================================================")
    print("       SYNAPSE AR TELEGRAM ALERT TEST TOOL       ")
    print("=================================================\n")
    
    print_info("This tool simulates abnormal vital signs to test the Telegram alert system.")
    print_info("Make sure the Synapse Web Server and Telegram Alert System are running.")
    
    # Check if the API is available
    if not check_api_available():
        print_error("Cannot connect to Synapse Web Server. Exiting.")
        return
    
    # Run the selected scenario
    if args.scenario == 'high_temp':
        simulate_high_temperature()
    elif args.scenario == 'high_hr':
        simulate_high_heart_rate()
    elif args.scenario == 'low_hr':
        simulate_low_heart_rate()
    elif args.scenario == 'low_spo2':
        simulate_low_spo2()
    elif args.scenario == 'fall':
        simulate_fall_detection()
    elif args.scenario == 'reset':
        reset_vital_signs()
    elif args.scenario == 'all' or args.scenario is None:
        # If no scenario is specified or 'all' is selected, run all scenarios
        if args.scenario is None:
            # Interactive mode if no arguments provided
            print("\nSelect a scenario to simulate:")
            print("1. High Temperature (>38°C)")
            print("2. High Heart Rate (>120 BPM)")
            print("3. Low Heart Rate (<50 BPM)")
            print("4. Low SpO2 (<95%)")
            print("5. Fall Detection")
            print("6. Run All Scenarios")
            print("7. Reset to Normal Values")
            print("0. Exit")
            
            choice = input("\nEnter your choice (0-7): ")
            
            if choice == '1':
                simulate_high_temperature()
            elif choice == '2':
                simulate_high_heart_rate()
            elif choice == '3':
                simulate_low_heart_rate()
            elif choice == '4':
                simulate_low_spo2()
            elif choice == '5':
                simulate_fall_detection()
            elif choice == '6':
                run_all_scenarios(args.delay)
            elif choice == '7':
                reset_vital_signs()
            elif choice == '0':
                print_info("Exiting.")
                return
            else:
                print_error("Invalid choice. Exiting.")
                return
        else:
            run_all_scenarios(args.delay)
    else:
        print_error(f"Unknown scenario: {args.scenario}")
        return

def run_all_scenarios(delay):
    """Run all test scenarios with a delay between each"""
    print_info(f"Running all scenarios with {delay} seconds delay between each...")
    
    # Reset to ensure we start with clean state
    reset_vital_signs()
    time.sleep(5)  # Short delay before starting
    
    # High temperature
    simulate_high_temperature()
    print_info(f"Waiting {delay} seconds before next scenario...")
    time.sleep(delay)
    
    # High heart rate
    simulate_high_heart_rate()
    print_info(f"Waiting {delay} seconds before next scenario...")
    time.sleep(delay)
    
    # Low heart rate
    simulate_low_heart_rate()
    print_info(f"Waiting {delay} seconds before next scenario...")
    time.sleep(delay)
    
    # Low SpO2
    simulate_low_spo2()
    print_info(f"Waiting {delay} seconds before next scenario...")
    time.sleep(delay)
    
    # Fall detection
    simulate_fall_detection()
    print_info(f"Waiting {delay} seconds before resetting...")
    time.sleep(delay)
    
    # Reset to normal values
    reset_vital_signs()
    
    print_success("All scenarios completed.")

if __name__ == "__main__":
    main() 