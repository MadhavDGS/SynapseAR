#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import requests

# Define colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header():
    """Print a styled header for the setup script"""
    print(f"\n{BOLD}{CYAN}==============================================={RESET}")
    print(f"{BOLD}{CYAN}       SYNAPSE AR TELEGRAM ALERTS SETUP       {RESET}")
    print(f"{BOLD}{CYAN}==============================================={RESET}\n")

def print_step(step_number, step_name):
    """Print a styled step header"""
    print(f"\n{BOLD}{GREEN}Step {step_number}: {step_name}{RESET}")
    print(f"{GREEN}---------------------------------------{RESET}")

def print_info(text):
    """Print information text"""
    print(f"{CYAN}ℹ️ {text}{RESET}")

def print_warning(text):
    """Print warning text"""
    print(f"{YELLOW}⚠️ {text}{RESET}")

def print_error(text):
    """Print error text"""
    print(f"{RED}❌ {text}{RESET}")

def print_success(text):
    """Print success text"""
    print(f"{GREEN}✅ {text}{RESET}")

def check_dependencies():
    """Check if required Python packages are installed"""
    print_step(1, "Checking dependencies")
    
    required_packages = ['telebot', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_info(f"Package '{package}' is installed.")
        except ImportError:
            missing_packages.append(package)
            print_error(f"Package '{package}' is not installed.")
    
    if missing_packages:
        print_warning("Installing missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print_success(f"Successfully installed '{package}'.")
            except subprocess.CalledProcessError:
                print_error(f"Failed to install '{package}'.")
                return False
    else:
        print_success("All required packages are installed.")
    
    return True

def check_synapse_web_server():
    """Check if the Synapse AR web server is running"""
    print_step(2, "Checking Synapse AR web server")
    
    try:
        response = requests.get('http://localhost:8081/api/sensor_data', timeout=5)
        if response.status_code == 200:
            print_success("Synapse AR web server is running.")
            return True
        else:
            print_error(f"Synapse AR web server returned status code {response.status_code}.")
            return False
    except requests.exceptions.RequestException:
        print_error("Could not connect to Synapse AR web server. Make sure it's running at http://localhost:8081.")
        print_info("You can start the server by running: python synapse_web.py")
        return False

def setup_telegram_bot():
    """Guide the user through setting up their Telegram bot"""
    print_step(3, "Setting up Telegram Bot")
    
    print_info("To use Telegram alerts, you need to create a Telegram bot and get its token.")
    print_info("You also need to create a Telegram group and add your bot to it.")
    
    print("\nHere's how to create a Telegram bot:")
    print("1. Open Telegram and search for 'BotFather'")
    print("2. Start a chat with BotFather and send the command: /newbot")
    print("3. Follow the instructions to create your bot")
    print("4. BotFather will give you a token, which you'll need to enter below")
    
    print("\nHere's how to create a Telegram group and get its ID:")
    print("1. Create a new group in Telegram")
    print("2. Add your bot to the group")
    print("3. Send a message in the group")
    print("4. Visit https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
    print("5. Look for 'chat' object and find the 'id' field - this is your group chat ID")
    
    token = input(f"\n{BOLD}Enter your Telegram Bot Token:{RESET} ")
    group_id = input(f"\n{BOLD}Enter your Telegram Group Chat ID:{RESET} ")
    
    # Validate the token and group ID
    if not token or not group_id:
        print_error("Bot token and group chat ID cannot be empty.")
        return False
    
    # Save the token and group ID to a configuration file
    config = {
        "BOT_TOKEN": token,
        "GROUP_CHAT_ID": group_id
    }
    
    try:
        with open('telegram_config.json', 'w') as f:
            json.dump(config, f, indent=4)
        print_success("Telegram configuration saved successfully.")
        
        # Update the token and group ID in the telegram_alerts.py file
        with open('telegram_alerts.py', 'r') as f:
            content = f.read()
        
        content = content.replace("'YOUR_BOT_TOKEN_HERE'", f"'{token}'")
        content = content.replace("'YOUR_GROUP_CHAT_ID_HERE'", f"'{group_id}'")
        
        with open('telegram_alerts.py', 'w') as f:
            f.write(content)
        
        print_success("Updated telegram_alerts.py with your bot token and group chat ID.")
        return True
    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        return False

def configure_alert_thresholds():
    """Allow the user to customize alert thresholds"""
    print_step(4, "Configuring Alert Thresholds")
    
    # Default thresholds
    thresholds = {
        "TEMP_HIGH_THRESHOLD": 38.0,
        "HR_HIGH_THRESHOLD": 120,
        "HR_LOW_THRESHOLD": 50,
        "SPO2_LOW_THRESHOLD": 95
    }
    
    print_info("You can customize the thresholds for health alerts. Press Enter to keep the default value.")
    
    # Get user input for each threshold
    thresholds["TEMP_HIGH_THRESHOLD"] = float(input(f"\n{BOLD}High Temperature Threshold{RESET} (default: 38.0°C): ") or thresholds["TEMP_HIGH_THRESHOLD"])
    thresholds["HR_HIGH_THRESHOLD"] = int(input(f"{BOLD}High Heart Rate Threshold{RESET} (default: 120 BPM): ") or thresholds["HR_HIGH_THRESHOLD"])
    thresholds["HR_LOW_THRESHOLD"] = int(input(f"{BOLD}Low Heart Rate Threshold{RESET} (default: 50 BPM): ") or thresholds["HR_LOW_THRESHOLD"])
    thresholds["SPO2_LOW_THRESHOLD"] = int(input(f"{BOLD}Low SpO2 Threshold{RESET} (default: 95%): ") or thresholds["SPO2_LOW_THRESHOLD"])
    
    # Update the thresholds in the telegram_alerts.py file
    try:
        with open('telegram_alerts.py', 'r') as f:
            content = f.read()
        
        for key, value in thresholds.items():
            # Find and replace the threshold values
            if isinstance(value, int):
                content = content.replace(f"{key} = {int(float(thresholds[key]))}", f"{key} = {value}")
            else:
                content = content.replace(f"{key} = {float(thresholds[key])}", f"{key} = {value}")
        
        with open('telegram_alerts.py', 'w') as f:
            f.write(content)
        
        print_success("Alert thresholds updated successfully.")
        return True
    except Exception as e:
        print_error(f"Failed to update thresholds: {e}")
        return False

def setup_patient_info():
    """Set up patient information"""
    print_step(5, "Setting up Patient Information")
    
    user_info = {
        "name": "Patient",
        "age": 45,
        "gender": "Not specified",
        "medical_conditions": ["None specified"]
    }
    
    print_info("You can set up basic patient information for alerts.")
    
    user_info["name"] = input(f"\n{BOLD}Patient Name{RESET} (default: Patient): ") or user_info["name"]
    
    age_input = input(f"{BOLD}Patient Age{RESET} (default: 45): ")
    if age_input:
        try:
            user_info["age"] = int(age_input)
        except ValueError:
            print_warning("Invalid age input. Using default value.")
    
    user_info["gender"] = input(f"{BOLD}Patient Gender{RESET} (default: Not specified): ") or user_info["gender"]
    
    conditions_input = input(f"{BOLD}Medical Conditions{RESET} (comma-separated, default: None specified): ")
    if conditions_input:
        user_info["medical_conditions"] = [condition.strip() for condition in conditions_input.split(",")]
    
    # Save user info to file
    try:
        with open('user_info.json', 'w') as f:
            json.dump(user_info, f, indent=4)
        print_success("Patient information saved successfully.")
        return True
    except Exception as e:
        print_error(f"Failed to save patient information: {e}")
        return False

def run_alert_system():
    """Run the Telegram alert system"""
    print_step(6, "Running the Telegram Alert System")
    
    print_info("The setup is complete. You can now run the Telegram alert system.")
    print_info("The system will monitor health data from Synapse AR and send alerts to your Telegram group.")
    
    run_now = input(f"\n{BOLD}Do you want to run the system now? (y/n):{RESET} ").lower() == 'y'
    
    if run_now:
        print_info("Starting the Telegram alert system...")
        print_info("Press Ctrl+C to stop.")
        
        try:
            # Run the telegram_alerts.py script
            subprocess.run([sys.executable, "telegram_alerts.py"])
        except KeyboardInterrupt:
            print_info("\nTelegram alert system stopped.")
    else:
        print_info("You can run the system later with the command: python telegram_alerts.py")
    
    print_success("Setup completed successfully!")
    return True

def main():
    """Main function to run the setup script"""
    print_header()
    
    print_info("This script will help you set up Telegram alerts for the Synapse AR system.")
    print_info("Alerts will be sent when health metrics exceed specified thresholds.")
    print_warning("Make sure the Synapse AR web server is running before proceeding.")
    
    proceed = input(f"\n{BOLD}Proceed with setup? (y/n):{RESET} ").lower() == 'y'
    
    if not proceed:
        print_info("Setup cancelled.")
        return
    
    # Run setup steps
    if check_dependencies():
        if check_synapse_web_server():
            if setup_telegram_bot():
                if configure_alert_thresholds():
                    if setup_patient_info():
                        run_alert_system()
    
    print_info("Setup complete. You can run the alert system with: python telegram_alerts.py")

if __name__ == "__main__":
    main() 