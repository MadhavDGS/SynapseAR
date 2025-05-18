# Synapse AR Telegram Health Alerts

This system integrates the Synapse AR health monitoring system with Telegram to send real-time health alerts when critical thresholds are exceeded.

## Features

- **Real-time health monitoring** - Connects to your Synapse AR system to monitor vital signs
- **Automated alerts** - Sends immediate alerts to a Telegram group when health metrics exceed thresholds
- **Multiple alert types**:
  - High temperature (above 38°C)
  - High heart rate (above 120 BPM)
  - Low heart rate (below 50 BPM)
  - Low SpO2 (below 95%)
  - Fall detection

## Requirements

- Python 3.6 or higher
- The Synapse AR system running on the same machine
- Synapse Web Server running (synapse_web.py)
- A Telegram account
- Internet connection

## Setup Instructions

### Quick Setup

1. Make sure your Synapse AR system is running
2. Run the setup script:
   ```
   python setup_telegram_alerts.py
   ```
3. Follow the on-screen instructions to:
   - Create a Telegram bot
   - Create a Telegram group
   - Configure alert thresholds
   - Set patient information

### Manual Setup

If you prefer to set up the system manually:

1. **Create a Telegram Bot**:
   - Open Telegram and search for "BotFather"
   - Start a chat with BotFather and send `/newbot`
   - Follow the instructions to create your bot
   - BotFather will give you a token - save this for later

2. **Create a Telegram Group**:
   - Create a new group in Telegram
   - Add your bot to the group
   - Send a message in the group
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for "chat" object and find the "id" field - this is your group chat ID

3. **Configure the Alert System**:
   - Open `telegram_alerts.py` in a text editor
   - Replace `YOUR_BOT_TOKEN_HERE` with your bot token
   - Replace `YOUR_GROUP_CHAT_ID_HERE` with your group chat ID
   - Adjust the alert thresholds if needed

4. **Set Patient Information**:
   - Create a file called `user_info.json` with the following structure:
   ```json
   {
       "name": "Patient Name",
       "age": 45,
       "gender": "Gender",
       "medical_conditions": ["Condition 1", "Condition 2"]
   }
   ```

## Running the Alert System

Once the setup is complete, you can run the alert system with:

```
python telegram_alerts.py
```

The system will:
1. Connect to your Synapse AR web server
2. Monitor health data in real-time
3. Send alerts to your Telegram group when thresholds are exceeded

## Alert Thresholds

The default alert thresholds are:

- **High Temperature**: > 38.0°C
- **High Heart Rate**: > 120 BPM
- **Low Heart Rate**: < 50 BPM
- **Low SpO2**: < 95%

You can customize these thresholds by editing the values in `telegram_alerts.py`.

## Telegram Bot Commands

The Telegram bot supports the following commands:

- `/start` - Start the bot
- `/help` - Show help message
- `/status` - Check monitoring status
- `/thresholds` - View alert thresholds
- `/setname [name]` - Set patient name
- `/setinfo [age] [gender]` - Set patient information
- `/addcondition [condition]` - Add medical condition
- `/removecondition [condition]` - Remove medical condition
- `/startmonitoring` - Start health monitoring
- `/stopmonitoring` - Stop health monitoring

## Troubleshooting

- **No alerts are being sent**: Make sure the Synapse AR web server is running and the bot has permission to send messages in the group.
- **Can't connect to web server**: Check that `synapse_web.py` is running properly on port 8081.
- **"Bad Request" error**: Check that your Group Chat ID is correctly entered.
- **Bot not responding to commands**: Make sure the bot is running and has internet connectivity.

## Security Note

This system sends health data to Telegram. Ensure you:
1. Keep your bot token private
2. Only add trusted members to your Telegram group
3. Understand Telegram's data privacy policies 