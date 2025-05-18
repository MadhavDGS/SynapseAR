#!/usr/bin/env python3
import os
import time
import json
import logging
import telebot
from telebot import types
import threading
import requests
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


BOT_TOKEN = '7611464404:AAHng-spGfoE86FwGa_G9JcQy0Hx4TawMMw'
GROUP_CHAT_ID = '-4736660190'


TEMP_HIGH_THRESHOLD = 38.0       # Alert when temperature exceeds 38.0°C
HR_HIGH_THRESHOLD = 120          # Alert when heart rate exceeds 120 BPM
HR_LOW_THRESHOLD = 50            # Alert when heart rate is below 50 BPM
SPO2_LOW_THRESHOLD = 95          # Alert when SpO2 falls below 95%

# Alert cooldown periods (in seconds)
TEMP_ALERT_COOLDOWN = 300        # 5 minutes between temperature alerts
HR_ALERT_COOLDOWN = 180          # 3 minutes between heart rate alerts
SPO2_ALERT_COOLDOWN = 300        # 5 minutes between SpO2 alerts
FALL_ALERT_COOLDOWN = 60         # 1 minute between fall alerts

# Store last alert times
last_alerts = {
    'temp_high': 0,
    'hr_high': 0,
    'hr_low': 0,
    'spo2_low': 0,
    'fall': 0
}

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

class TelegramAlertSystem:
    def __init__(self):
        self.running = False
        self.thread = None
        self.sensor_data = {
            "heartRate": 0,
            "heartRateAvg": 0,
            "spo2": 0,
            "spo2Avg": 0,
            "temperature": 0,
            "fallDetected": False,
            "validReadings": False,
            "last_updated": None
        }
        self.user_info = {
            "name": "Patient",
            "age": 45,
            "gender": "Not specified",
            "medical_conditions": ["None specified"]
        }
        
        # Attempt to load user info from file
        try:
            if os.path.exists('user_info.json'):
                with open('user_info.json', 'r') as f:
                    self.user_info = json.load(f)
                logger.info("Loaded user information from file")
        except Exception as e:
            logger.error(f"Error loading user info: {e}")
    
    def save_user_info(self):
        """Save user information to a file"""
        try:
            with open('user_info.json', 'w') as f:
                json.dump(self.user_info, f, indent=4)
            logger.info("Saved user information to file")
        except Exception as e:
            logger.error(f"Error saving user info: {e}")
    
    def get_sensor_data(self):
        """Get the latest sensor data from Synapse AR web server"""
        try:
            response = requests.get('http://localhost:8081/api/sensor_data')
            if response.status_code == 200:
                data = response.json()
                if 'sensor_data' in data:
                    self.sensor_data = data['sensor_data']
                    logger.debug(f"Retrieved sensor data: {self.sensor_data}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error getting sensor data: {e}")
            return False
    
    def check_alerts(self):
        """Check if any health metrics exceed alert thresholds"""
        current_time = time.time()
        
        # Check if readings are valid
        if not self.sensor_data.get('validReadings', False):
            return
        
        # Check temperature
        if self.sensor_data['temperature'] > TEMP_HIGH_THRESHOLD:
            if current_time - last_alerts['temp_high'] > TEMP_ALERT_COOLDOWN:
                self.send_temperature_alert()
                last_alerts['temp_high'] = current_time
        
        # Check heart rate
        if self.sensor_data['heartRateAvg'] > HR_HIGH_THRESHOLD:
            if current_time - last_alerts['hr_high'] > HR_ALERT_COOLDOWN:
                self.send_high_hr_alert()
                last_alerts['hr_high'] = current_time
        elif self.sensor_data['heartRateAvg'] < HR_LOW_THRESHOLD and self.sensor_data['heartRateAvg'] > 20:
            if current_time - last_alerts['hr_low'] > HR_ALERT_COOLDOWN:
                self.send_low_hr_alert()
                last_alerts['hr_low'] = current_time
        
        # Check SpO2
        if self.sensor_data['spo2Avg'] < SPO2_LOW_THRESHOLD and self.sensor_data['spo2Avg'] > 0:
            if current_time - last_alerts['spo2_low'] > SPO2_ALERT_COOLDOWN:
                self.send_spo2_alert()
                last_alerts['spo2_low'] = current_time
        
        # Check for fall detection with improved handling
        fall_detected = False
        
        # Properly check the fallDetected field with type awareness
        if 'fallDetected' in self.sensor_data:
            fall_value = self.sensor_data['fallDetected']
            
            # Handle different possible data types for the fall detection value
            if isinstance(fall_value, bool):
                fall_detected = fall_value
            elif isinstance(fall_value, int) or isinstance(fall_value, float):
                fall_detected = fall_value > 0
            elif isinstance(fall_value, str):
                fall_detected = fall_value.lower() in ('yes', 'true', '1', 'y')
            
            # Log for debugging
            logger.info(f"Fall detection check: raw={fall_value}, type={type(fall_value).__name__}, interpreted={fall_detected}")
        
        if fall_detected:
            # Log that fall was detected
            logger.info(f"Fall detected in sensor data: {fall_detected}")
            
            if current_time - last_alerts['fall'] > FALL_ALERT_COOLDOWN:
                # Log attempt to send fall alert
                logger.info("Attempting to send fall alert due to detected fall")
                self.send_fall_alert()
                last_alerts['fall'] = current_time
    
    def send_temperature_alert(self):
        """Send high temperature alert to Telegram group"""
        temp = self.sensor_data['temperature']
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🔴 *HIGH TEMPERATURE ALERT* 🔴\n\n"
            f"Patient: {self.user_info['name']}\n"
            f"Temperature: *{temp:.1f}°C*\n"
            f"Time: {timestamp}\n\n"
            f"❗ Temperature exceeds safe threshold of {TEMP_HIGH_THRESHOLD}°C"
        )
        
        self.send_telegram_message(message)
        logger.info(f"Sent high temperature alert: {temp:.1f}°C")
    
    def send_high_hr_alert(self):
        """Send high heart rate alert to Telegram group"""
        hr = self.sensor_data['heartRateAvg']
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🔴 *HIGH HEART RATE ALERT* 🔴\n\n"
            f"Patient: {self.user_info['name']}\n"
            f"Heart Rate: *{hr} BPM*\n"
            f"Time: {timestamp}\n\n"
            f"❗ Heart rate exceeds safe threshold of {HR_HIGH_THRESHOLD} BPM"
        )
        
        self.send_telegram_message(message)
        logger.info(f"Sent high heart rate alert: {hr} BPM")
    
    def send_low_hr_alert(self):
        """Send low heart rate alert to Telegram group"""
        hr = self.sensor_data['heartRateAvg']
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🔴 *LOW HEART RATE ALERT* 🔴\n\n"
            f"Patient: {self.user_info['name']}\n"
            f"Heart Rate: *{hr} BPM*\n"
            f"Time: {timestamp}\n\n"
            f"❗ Heart rate below safe threshold of {HR_LOW_THRESHOLD} BPM"
        )
        
        self.send_telegram_message(message)
        logger.info(f"Sent low heart rate alert: {hr} BPM")
    
    def send_spo2_alert(self):
        """Send low SpO2 alert to Telegram group"""
        spo2 = self.sensor_data['spo2Avg']
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🔴 *LOW OXYGEN SATURATION ALERT* 🔴\n\n"
            f"Patient: {self.user_info['name']}\n"
            f"SpO2: *{spo2}%*\n"
            f"Time: {timestamp}\n\n"
            f"❗ Oxygen saturation below safe threshold of {SPO2_LOW_THRESHOLD}%"
        )
        
        self.send_telegram_message(message)
        logger.info(f"Sent low SpO2 alert: {spo2}%")
    
    def send_fall_alert(self):
        """Send fall detection alert to Telegram group"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🚨 *FALL DETECTED* 🚨\n\n"
            f"Patient: {self.user_info['name']}\n"
            f"Time: {timestamp}\n\n"
            f"❗ Fall detected! Immediate assistance may be required."
        )
        
        result = self.send_telegram_message(message)
        if result:
            logger.info("Successfully sent fall detection alert")
        else:
            logger.error("Failed to send fall detection alert")
    
    def send_telegram_message(self, message):
        """Send a message to the Telegram group"""
        try:
            bot.send_message(
                GROUP_CHAT_ID,
                message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def monitoring_loop(self):
        """Main monitoring loop to check for health alerts"""
        logger.info("Starting health monitoring for Telegram alerts")
        
        while self.running:
            try:
                # Get latest sensor data
                if self.get_sensor_data():
                    # Debug log the received data for troubleshooting 
                    logger.info(f"Current sensor data: {self.sensor_data}")
                    
                    # Check for alert conditions
                    self.check_alerts()
                
                # Wait before next check
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait longer after an error
    
    def start(self):
        """Start the monitoring thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.monitoring_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Health monitoring thread started")
            
            # Send a startup message to the group
            startup_msg = (
                f"🟢 *Synapse AR Health Monitor Started* 🟢\n\n"
                f"Monitoring health data for: {self.user_info['name']}\n"
                f"Alerts configured for:\n"
                f"• High temperature (>{TEMP_HIGH_THRESHOLD}°C)\n"
                f"• High heart rate (>{HR_HIGH_THRESHOLD} BPM)\n"
                f"• Low heart rate (<{HR_LOW_THRESHOLD} BPM)\n"
                f"• Low SpO2 (<{SPO2_LOW_THRESHOLD}%)\n"
                f"• Fall detection\n\n"
                f"Bot is now active and will send alerts when critical thresholds are exceeded."
            )
            self.send_telegram_message(startup_msg)
            
            return True
        return False
    
    def stop(self):
        """Stop the monitoring thread"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=2.0)
            logger.info("Health monitoring thread stopped")
            
            # Send a shutdown message to the group
            shutdown_msg = "🔴 *Synapse AR Health Monitor Stopped* 🔴\n\nHealth monitoring has been deactivated."
            self.send_telegram_message(shutdown_msg)
            
            return True
        return False

# Bot command handlers
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle the /start command"""
    bot.reply_to(message, 
        "Welcome to Synapse AR Health Monitor!\n\n"
        "This bot will send health alerts to the configured group chat.\n"
        "Use /help to see available commands."
    )

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Handle the /help command"""
    help_text = (
        "Synapse AR Health Monitor Commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/status - Check monitoring status\n"
        "/thresholds - View alert thresholds\n"
        "/setname [name] - Set patient name\n"
        "/setinfo [age] [gender] - Set patient information\n"
        "/addcondition [condition] - Add medical condition\n"
        "/removecondition [condition] - Remove medical condition\n"
        "/startmonitoring - Start health monitoring\n"
        "/stopmonitoring - Stop health monitoring\n"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['status'])
def handle_status(message):
    """Handle the /status command"""
    if alert_system.running:
        status = "🟢 Monitoring Active"
    else:
        status = "🔴 Monitoring Inactive"
    
    sensor_status = "Not available"
    last_update = "Never"
    
    if alert_system.sensor_data['last_updated']:
        sensor_status = "Connected" if alert_system.sensor_data['validReadings'] else "Invalid readings"
        update_time = datetime.datetime.fromtimestamp(alert_system.sensor_data['last_updated'])
        last_update = update_time.strftime("%Y-%m-%d %H:%M:%S")
    
    status_text = (
        f"*Synapse AR Monitor Status*\n\n"
        f"Monitor: {status}\n"
        f"Sensor Status: {sensor_status}\n"
        f"Last Update: {last_update}\n\n"
        f"Current Readings:\n"
        f"• Heart Rate: {alert_system.sensor_data['heartRateAvg']} BPM\n"
        f"• SpO2: {alert_system.sensor_data['spo2Avg']}%\n"
        f"• Temperature: {alert_system.sensor_data['temperature']:.1f}°C\n"
    )
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['thresholds'])
def handle_thresholds(message):
    """Handle the /thresholds command"""
    thresholds_text = (
        "*Alert Thresholds*\n\n"
        f"• High Temperature: > {TEMP_HIGH_THRESHOLD}°C\n"
        f"• High Heart Rate: > {HR_HIGH_THRESHOLD} BPM\n"
        f"• Low Heart Rate: < {HR_LOW_THRESHOLD} BPM\n"
        f"• Low SpO2: < {SPO2_LOW_THRESHOLD}%\n"
    )
    
    bot.reply_to(message, thresholds_text, parse_mode='Markdown')

@bot.message_handler(commands=['setname'])
def handle_set_name(message):
    """Handle the /setname command"""
    try:
        # Extract the name from the message
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a name. Example: /setname John Doe")
            return
        
        name = parts[1].strip()
        alert_system.user_info['name'] = name
        alert_system.save_user_info()
        
        bot.reply_to(message, f"Patient name set to: {name}")
    except Exception as e:
        logger.error(f"Error handling setname command: {e}")
        bot.reply_to(message, "Failed to set name. Please try again.")

@bot.message_handler(commands=['setinfo'])
def handle_set_info(message):
    """Handle the /setinfo command"""
    try:
        # Extract age and gender from the message
        parts = message.text.split(' ')
        if len(parts) < 3:
            bot.reply_to(message, "Please provide age and gender. Example: /setinfo 45 Male")
            return
        
        age = parts[1].strip()
        gender = parts[2].strip()
        
        alert_system.user_info['age'] = age
        alert_system.user_info['gender'] = gender
        alert_system.save_user_info()
        
        bot.reply_to(message, f"Patient information updated: Age {age}, Gender {gender}")
    except Exception as e:
        logger.error(f"Error handling setinfo command: {e}")
        bot.reply_to(message, "Failed to set information. Please try again.")

@bot.message_handler(commands=['addcondition'])
def handle_add_condition(message):
    """Handle the /addcondition command"""
    try:
        # Extract the condition from the message
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a medical condition. Example: /addcondition Diabetes")
            return
        
        condition = parts[1].strip()
        
        # Initialize medical_conditions if it doesn't exist
        if 'medical_conditions' not in alert_system.user_info:
            alert_system.user_info['medical_conditions'] = []
        
        # Remove "None specified" if it exists
        if "None specified" in alert_system.user_info['medical_conditions']:
            alert_system.user_info['medical_conditions'].remove("None specified")
        
        # Add the condition if it's not already in the list
        if condition not in alert_system.user_info['medical_conditions']:
            alert_system.user_info['medical_conditions'].append(condition)
            alert_system.save_user_info()
            bot.reply_to(message, f"Added medical condition: {condition}")
        else:
            bot.reply_to(message, f"Medical condition '{condition}' already exists.")
    except Exception as e:
        logger.error(f"Error handling addcondition command: {e}")
        bot.reply_to(message, "Failed to add condition. Please try again.")

@bot.message_handler(commands=['removecondition'])
def handle_remove_condition(message):
    """Handle the /removecondition command"""
    try:
        # Extract the condition from the message
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a medical condition. Example: /removecondition Diabetes")
            return
        
        condition = parts[1].strip()
        
        # Check if medical_conditions exists and remove the condition
        if 'medical_conditions' in alert_system.user_info and condition in alert_system.user_info['medical_conditions']:
            alert_system.user_info['medical_conditions'].remove(condition)
            
            # Add "None specified" if the list is empty
            if len(alert_system.user_info['medical_conditions']) == 0:
                alert_system.user_info['medical_conditions'].append("None specified")
            
            alert_system.save_user_info()
            bot.reply_to(message, f"Removed medical condition: {condition}")
        else:
            bot.reply_to(message, f"Medical condition '{condition}' not found.")
    except Exception as e:
        logger.error(f"Error handling removecondition command: {e}")
        bot.reply_to(message, "Failed to remove condition. Please try again.")

@bot.message_handler(commands=['startmonitoring'])
def handle_start_monitoring(message):
    """Handle the /startmonitoring command"""
    if alert_system.start():
        bot.reply_to(message, "Health monitoring started. Alerts will be sent to the configured group.")
    else:
        bot.reply_to(message, "Health monitoring is already running.")

@bot.message_handler(commands=['stopmonitoring'])
def handle_stop_monitoring(message):
    """Handle the /stopmonitoring command"""
    if alert_system.stop():
        bot.reply_to(message, "Health monitoring stopped.")
    else:
        bot.reply_to(message, "Health monitoring is not running.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other messages"""
    bot.reply_to(message, "I don't understand that command. Type /help to see available commands.")

if __name__ == "__main__":
    # Create and start the alert system
    alert_system = TelegramAlertSystem()
    
    # Start health monitoring
    alert_system.start()
    
    try:
        logger.info("Starting Telegram bot polling...")
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
    finally:
        # Make sure to stop the monitoring thread when the bot stops
        alert_system.stop() 