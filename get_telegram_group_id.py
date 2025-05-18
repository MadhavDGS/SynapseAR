#!/usr/bin/env python3
import requests
import json
import time
import sys
import os

# Define colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

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

BOT_TOKEN = '7611464404:AAHng-spGfoE86FwGa_G9JcQy0Hx4TawMMw'

print(f"\n{BOLD}{CYAN}==============================================={RESET}")
print(f"{BOLD}{CYAN}       TELEGRAM GROUP ID FINDER              {RESET}")
print(f"{BOLD}{CYAN}==============================================={RESET}\n")

print_info("This script will help you find your Telegram group ID.")
print_warning("Due to Telegram's privacy restrictions, we'll need to use an alternative method.")

print(f"\n{BOLD}Method 1: Create a group with @RawDataBot{RESET}")
print("1. Create a new Telegram group")
print("2. Add @RawDataBot to the group")
print("3. The bot will instantly display the group's chat_id")
print("4. Note down this chat_id (it will be a negative number)")
print("5. You can remove @RawDataBot after getting the ID")

print(f"\n{BOLD}Method 2: Use a direct method{RESET}")
print("1. Create a new Telegram group")
print("2. Add your bot to the group")
print("3. Make your bot an administrator of the group")
print("4. This gives the bot access to messages")

print(f"\n{BOLD}Which method would you like to use?{RESET}")
print("1. I already have the group ID from @RawDataBot")
print("2. I've made my bot an administrator in the group")
print("3. Help me set up a test with a direct approach")

choice = input(f"\n{BOLD}Enter your choice (1-3): {RESET}")

if choice == "1":
    # User already has the group ID
    chat_id = input(f"\n{BOLD}Enter the group ID you got from @RawDataBot: {RESET}")
    
    try:
        # Validate the chat_id is an integer
        chat_id = int(chat_id)
        
        # Group IDs are typically negative
        if chat_id >= 0:
            print_warning("Group IDs are typically negative numbers. Are you sure this is correct?")
            confirm = input(f"{BOLD}Continue anyway? (y/n): {RESET}").lower() == 'y'
            if not confirm:
                print_info("Exiting. Please try again with the correct group ID.")
                sys.exit(0)
                
        # Update telegram_alerts.py with the group ID
        with open('telegram_alerts.py', 'r') as f:
            content = f.read()
        
        updated_content = content.replace("'YOUR_GROUP_CHAT_ID_HERE'", f"'{chat_id}'")
        
        with open('telegram_alerts.py', 'w') as f:
            f.write(updated_content)
        
        print_success("Updated telegram_alerts.py with your group chat ID.")
        
        # Also save to config file
        config = {"BOT_TOKEN": BOT_TOKEN, "GROUP_CHAT_ID": chat_id}
        with open('telegram_config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        print_success("Saved configuration to telegram_config.json")
        
        # Test sending a message to the group
        test_message = "🔵 *Test Message from Synapse AR*\n\nYour health monitoring system is now connected to Telegram.\nYou will receive alerts here when health metrics exceed thresholds."
        test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        test_params = {
            "chat_id": chat_id,
            "text": test_message,
            "parse_mode": "Markdown"
        }
        
        print_info("Sending test message to your Telegram group...")
        test_response = requests.post(test_url, json=test_params)
        
        if test_response.status_code == 200 and test_response.json().get('ok', False):
            print_success("Sent a test message to your group. Please check Telegram.")
            print_info("You're all set! You can now run the health monitoring system:")
            print_info("python telegram_alerts.py")
        else:
            print_error("Failed to send test message to the group.")
            print_error(f"Error: {test_response.text}")
            print_warning("Make sure your bot is a member of the group and has permission to send messages.")
            
    except ValueError:
        print_error(f"Invalid chat ID: '{chat_id}'. The group ID should be a number.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error updating configuration: {e}")
        sys.exit(1)

elif choice == "2":
    # User made their bot an administrator
    print_info("Checking for updates from your group...")
    
    # Try to get updates from the Telegram API
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url)
        
        if response.status_code != 200:
            print_error(f"Error accessing Telegram API: {response.status_code}")
            print_error(f"Response: {response.text}")
            sys.exit(1)
        
        data = response.json()
        
        if not data['ok']:
            print_error(f"Telegram API error: {data.get('description', 'Unknown error')}")
            sys.exit(1)
        
        updates = data.get('result', [])
        
        if not updates:
            print_warning("No updates found. Make sure:")
            print("1. Your bot has admin privileges in the group")
            print("2. You've sent a message in the group")
            print_info("Let's try to get a group update directly...")
            
            # Since we might not see group updates, let's ask the user for a group title
            group_name = input(f"\n{BOLD}What is the name of your Telegram group? {RESET}")
            
            print_info(f"Let's try to create a group with this bot in '{group_name}'...")
            print_info("Please do the following:")
            print("1. Make sure you've already added the bot to a group with admin privileges")
            print("2. Send a message like '@YourBotName hello' in the group")
            print("3. Then hit Enter to continue")
            
            input(f"\n{BOLD}Press Enter when ready...{RESET}")
            
            # Try again
            print_info("Checking for updates again...")
            response = requests.get(url)
            data = response.json()
            
            if not data['ok']:
                print_error(f"Telegram API error: {data.get('description', 'Unknown error')}")
                sys.exit(1)
            
            updates = data.get('result', [])
            
            if not updates:
                print_error("Still no updates found. Let's try a different approach.")
                print_info("Please use Method 1 with @RawDataBot to get your group ID.")
                sys.exit(1)
        
        # Look for group chat updates
        group_chats = []
        
        for update in updates:
            message = update.get('message', {})
            chat = message.get('chat', {})
            
            # Look for group chats
            if chat.get('type') in ['group', 'supergroup']:
                chat_id = chat.get('id')
                title = chat.get('title', 'Unnamed Group')
                group_chats.append({'id': chat_id, 'title': title})
        
        if not group_chats:
            print_error("No group chats found in the updates.")
            print_info("Please make sure your bot is an admin in the group and try again.")
            sys.exit(1)
        
        # If multiple group chats found, ask user to select one
        selected_chat = None
        
        if len(group_chats) > 1:
            print_info(f"Found {len(group_chats)} groups. Please select which one to use:")
            
            for i, group in enumerate(group_chats):
                print(f"{i+1}. {group['title']} (ID: {group['id']})")
            
            selection = int(input(f"\n{BOLD}Enter selection (1-{len(group_chats)}): {RESET}")) - 1
            
            if 0 <= selection < len(group_chats):
                selected_chat = group_chats[selection]
            else:
                print_error("Invalid selection.")
                sys.exit(1)
        else:
            selected_chat = group_chats[0]
        
        # Display the group ID
        chat_id = selected_chat['id']
        title = selected_chat['title']
        
        print_success(f"Found group: {title}")
        print_success(f"Group ID: {chat_id}")
        
        # Update telegram_alerts.py with the group ID
        try:
            with open('telegram_alerts.py', 'r') as f:
                content = f.read()
            
            updated_content = content.replace("'YOUR_GROUP_CHAT_ID_HERE'", f"'{chat_id}'")
            
            with open('telegram_alerts.py', 'w') as f:
                f.write(updated_content)
            
            print_success("Updated telegram_alerts.py with your group chat ID.")
            
            # Also save to config file
            config = {"BOT_TOKEN": BOT_TOKEN, "GROUP_CHAT_ID": chat_id}
            with open('telegram_config.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            print_success("Saved configuration to telegram_config.json")
            
            # Test sending a message to the group
            test_message = "🔵 *Test Message from Synapse AR*\n\nYour health monitoring system is now connected to Telegram.\nYou will receive alerts here when health metrics exceed thresholds."
            test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            test_params = {
                "chat_id": chat_id,
                "text": test_message,
                "parse_mode": "Markdown"
            }
            
            test_response = requests.post(test_url, json=test_params)
            
            if test_response.status_code == 200 and test_response.json().get('ok', False):
                print_success("Sent a test message to your group. Please check Telegram.")
                print_info("You're all set! You can now run the health monitoring system:")
                print_info("python telegram_alerts.py")
            else:
                print_error("Failed to send test message to the group.")
                print_error(f"Error: {test_response.text}")
        
        except Exception as e:
            print_error(f"Error updating configuration: {e}")
    
    except Exception as e:
        print_error(f"Error: {e}")
        print_info("Please try again later or check your internet connection.")

elif choice == "3":
    # Direct method with manual setup
    print_info("Let's try a direct approach to get your group ID.")
    
    print(f"\n{BOLD}Manual Setup Instructions:{RESET}")
    print("1. Open your Telegram app")
    print("2. Create a new group called 'Synapse AR Alerts' or similar")
    print("3. Add your bot (@" + BOT_TOKEN.split(':')[0] + "_bot) to the group")
    print("4. Make your bot an administrator of the group")
    print("   - In the group, tap the group name at the top")
    print("   - Tap 'Administrators' > 'Add Admin' > select your bot")
    print("   - Enable all permissions for the bot")
    
    input(f"\n{BOLD}Press Enter when you've completed these steps...{RESET}")
    
    # Try to get the bot's info
    try:
        bot_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        bot_response = requests.get(bot_info_url)
        
        if bot_response.status_code != 200:
            print_error(f"Error accessing Telegram API: {bot_response.status_code}")
            sys.exit(1)
            
        bot_data = bot_response.json()
        if bot_data['ok']:
            bot_username = bot_data['result']['username']
            print_info(f"Your bot username is: @{bot_username}")
            
            # Ask for manual input of group information
            print_info("Now we'll manually set up a message to send to your group.")
            group_id = input(f"\n{BOLD}Enter your group ID (if you know it) or press Enter to skip: {RESET}")
            
            if not group_id:
                print_info("No problem. Let's try something different.")
                print_info("We'll set up your bot to send messages to your group anyway.")
                
                # Create a simple user interface for entering group ID
                print(f"\n{BOLD}As a workaround, please try the following:{RESET}")
                print("1. Add @RawDataBot to your group")
                print("2. This bot will show you the group's chat_id immediately")
                print("3. Note down this chat_id (it will be a negative number)")
                print("4. You can remove @RawDataBot after getting the ID")
                
                group_id = input(f"\n{BOLD}Now enter the group ID you got from @RawDataBot: {RESET}")
                
                try:
                    # Validate the chat_id is an integer
                    group_id = int(group_id)
                    
                    # Update telegram_alerts.py with the group ID
                    with open('telegram_alerts.py', 'r') as f:
                        content = f.read()
                    
                    updated_content = content.replace("'YOUR_GROUP_CHAT_ID_HERE'", f"'{group_id}'")
                    
                    with open('telegram_alerts.py', 'w') as f:
                        f.write(updated_content)
                    
                    print_success("Updated telegram_alerts.py with your group chat ID.")
                    
                    # Also save to config file
                    config = {"BOT_TOKEN": BOT_TOKEN, "GROUP_CHAT_ID": group_id}
                    with open('telegram_config.json', 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    print_success("Saved configuration to telegram_config.json")
                    
                    # Test sending a message to the group
                    print_info("Sending a test message to your group...")
                    test_message = "🔵 *Test Message from Synapse AR*\n\nYour health monitoring system is now connected to Telegram.\nYou will receive alerts here when health metrics exceed thresholds."
                    test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    test_params = {
                        "chat_id": group_id,
                        "text": test_message,
                        "parse_mode": "Markdown"
                    }
                    
                    test_response = requests.post(test_url, json=test_params)
                    
                    if test_response.status_code == 200 and test_response.json().get('ok', False):
                        print_success("Sent a test message to your group. Please check Telegram.")
                        print_info("You're all set! You can now run the health monitoring system:")
                        print_info("python telegram_alerts.py")
                    else:
                        print_error("Failed to send test message to the group.")
                        print_error(f"Error: {test_response.text}")
                        print_warning("Make sure your bot is a member of the group and has permission to send messages.")
                    
                except ValueError:
                    print_error(f"Invalid chat ID: '{group_id}'. The group ID should be a number.")
                    sys.exit(1)
            else:
                try:
                    # User provided a group ID
                    group_id = int(group_id)
                    
                    # Update telegram_alerts.py with the group ID
                    with open('telegram_alerts.py', 'r') as f:
                        content = f.read()
                    
                    updated_content = content.replace("'YOUR_GROUP_CHAT_ID_HERE'", f"'{group_id}'")
                    
                    with open('telegram_alerts.py', 'w') as f:
                        f.write(updated_content)
                    
                    print_success("Updated telegram_alerts.py with your group chat ID.")
                    
                    # Also save to config file
                    config = {"BOT_TOKEN": BOT_TOKEN, "GROUP_CHAT_ID": group_id}
                    with open('telegram_config.json', 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    print_success("Saved configuration to telegram_config.json")
                    
                    # Test sending a message to the group
                    print_info("Sending a test message to your group...")
                    test_message = "🔵 *Test Message from Synapse AR*\n\nYour health monitoring system is now connected to Telegram.\nYou will receive alerts here when health metrics exceed thresholds."
                    test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    test_params = {
                        "chat_id": group_id,
                        "text": test_message,
                        "parse_mode": "Markdown"
                    }
                    
                    test_response = requests.post(test_url, json=test_params)
                    
                    if test_response.status_code == 200 and test_response.json().get('ok', False):
                        print_success("Sent a test message to your group. Please check Telegram.")
                        print_info("You're all set! You can now run the health monitoring system:")
                        print_info("python telegram_alerts.py")
                    else:
                        print_error("Failed to send test message to the group.")
                        print_error(f"Error: {test_response.text}")
                        print_warning("Make sure your bot is a member of the group and has permission to send messages.")
                    
                except ValueError:
                    print_error(f"Invalid chat ID: '{group_id}'. The group ID should be a number.")
                    sys.exit(1)
                
        else:
            print_error("Could not retrieve bot information.")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Error: {e}")
        print_info("Please try again later or check your internet connection.")

else:
    print_error("Invalid choice.")
    print_info("Please run the script again and select a valid option (1-3).") 