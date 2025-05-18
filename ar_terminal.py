#!/usr/bin/env python3
import serial
import serial.tools.list_ports
import time
import os
import sys
import argparse

class ARTerminal:
    def __init__(self, manual_port=None):
        self.ser = None
        self.connected = False
        self.medicines = []
        self.schedule = []
        self.emergency_contact = {"name": "", "number": ""}
        self.manual_port = manual_port
        
    def clear_screen(self):
        """Clear the terminal screen based on OS"""
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            # If clearing fails, just print newlines
            print("\n" * 50)
            
        # Print a message if TERM is not set
        if 'TERM' not in os.environ:
            # Set a default TERM value
            os.environ['TERM'] = 'xterm'
        
    def find_arduino_port(self):
        """Automatically find the Arduino/ESP32 port"""
        # If manual port is specified, use it
        if self.manual_port:
            print(f"Using manually specified port: {self.manual_port}")
            return self.manual_port
            
        ports = list(serial.tools.list_ports.comports())
        
        # First try to find common ESP32 descriptors
        for port in ports:
            if "CP210" in port.description or "CH340" in port.description or "FTDI" in port.description:
                return port.device
        
        # If no ESP32 found, list all ports for manual selection
        if not ports:
            print("No serial ports found.")
            return None
            
        print("Available ports:")
        for i, port in enumerate(ports):
            print(f"{i+1}. {port.device} - {port.description}")
            
        selection = input("Select port number (or press Enter to use first port): ")
        
        if selection.strip() == "":
            return ports[0].device
            
        try:
            index = int(selection) - 1
            if 0 <= index < len(ports):
                return ports[index].device
            else:
                print("Invalid selection. Using first port.")
                return ports[0].device
        except ValueError:
            print("Invalid input. Using first port.")
            return ports[0].device
    
    def connect(self):
        """Connect to the ESP32"""
        port = self.find_arduino_port()
        if not port:
            print("No port selected. Exiting.")
            return False
            
        try:
            self.ser = serial.Serial(port, 115200, timeout=1)
            self.connected = True
            print(f"Connected to {port}")
            time.sleep(2)  # Give time for device to reset
            
            # Clear any pending data
            self.ser.reset_input_buffer()
            
            # Send menu command to get initial menu
            self.send_command("menu")
            return True
            
        except serial.SerialException as e:
            print(f"Error connecting to {port}: {e}")
            return False
    
    def disconnect(self):
        """Close the serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.connected = False
            print("Disconnected from device")
    
    def send_command(self, command):
        """Send a command to the ESP32"""
        if not self.connected or not self.ser:
            print("Not connected to device")
            return ""
            
        # Send command with newline
        self.ser.write((command + "\n").encode('utf-8'))
        
        # Wait for response
        time.sleep(0.5)
        
        # Read response
        response = ""
        while self.ser.in_waiting:
            line = self.ser.readline().decode('utf-8').strip()
            response += line + "\n"
        
        return response
    
    def update_medicine(self, index, name):
        """Update a medicine entry"""
        command = f"med {index} {name}"
        response = self.send_command(command)
        print(response)
        
    def update_schedule(self, index, details):
        """Update a schedule entry"""
        command = f"sch {index} {details}"
        response = self.send_command(command)
        print(response)
        
    def update_emergency(self, name, number):
        """Update emergency contact"""
        command = f"emergency {name} {number}"
        response = self.send_command(command)
        print(response)
    
    def show_main_menu(self):
        """Display the main menu interface"""
        self.clear_screen()
        print("====================================")
        print("        SYNAPSE AR TERMINAL        ")
        print("====================================")
        print("1. View Medicines")
        print("2. View Schedule")
        print("3. Update Medicine")
        print("4. Update Schedule")
        print("5. Update Emergency Contact")
        print("6. Refresh Data")
        print("7. Send Custom Command")
        print("8. Change Serial Port")
        print("0. Exit")
        print("====================================")
        
        choice = input("Select an option: ")
        return choice
    
    def handle_view_medicines(self):
        """Display the medicines list"""
        self.clear_screen()
        print("====================================")
        print("            MEDICINES              ")
        print("====================================")
        
        response = self.send_command("1")
        print(response)
        
        input("Press Enter to continue...")
    
    def handle_view_schedule(self):
        """Display the schedule list"""
        self.clear_screen()
        print("====================================")
        print("             SCHEDULE              ")
        print("====================================")
        
        response = self.send_command("2")
        print(response)
        
        input("Press Enter to continue...")
    
    def handle_update_medicine(self):
        """Update a medicine entry"""
        self.clear_screen()
        print("====================================")
        print("          UPDATE MEDICINE          ")
        print("====================================")
        
        # First show current medicines
        response = self.send_command("1")
        print(response)
        
        index = input("Enter medicine number to update (1-10): ")
        name = input("Enter new medicine name: ")
        
        if index.strip() and name.strip():
            self.update_medicine(index, name)
        else:
            print("Invalid input. Operation cancelled.")
        
        input("Press Enter to continue...")
    
    def handle_update_schedule(self):
        """Update a schedule entry"""
        self.clear_screen()
        print("====================================")
        print("          UPDATE SCHEDULE          ")
        print("====================================")
        
        # First show current schedule
        response = self.send_command("2")
        print(response)
        
        index = input("Enter schedule number to update (1-10): ")
        details = input("Enter new schedule details: ")
        
        if index.strip() and details.strip():
            self.update_schedule(index, details)
        else:
            print("Invalid input. Operation cancelled.")
        
        input("Press Enter to continue...")
    
    def handle_update_emergency(self):
        """Update emergency contact"""
        self.clear_screen()
        print("====================================")
        print("      UPDATE EMERGENCY CONTACT     ")
        print("====================================")
        
        name = input("Enter contact name: ")
        number = input("Enter contact number: ")
        
        if name.strip() and number.strip():
            self.update_emergency(name, number)
        else:
            print("Invalid input. Operation cancelled.")
        
        input("Press Enter to continue...")
    
    def handle_custom_command(self):
        """Send a custom command to the device"""
        self.clear_screen()
        print("====================================")
        print("          CUSTOM COMMAND           ")
        print("====================================")
        print("Available commands:")
        print("- menu: Show menu")
        print("- med [index] [name]: Update medicine")
        print("- sch [index] [details]: Update schedule")
        print("- emergency [name] [number]: Update emergency contact")
        print("====================================")
        
        command = input("Enter command: ")
        
        if command.strip():
            response = self.send_command(command)
            print("\nResponse:")
            print(response)
        else:
            print("No command entered.")
        
        input("Press Enter to continue...")
        
    def handle_change_port(self):
        """Change the serial port"""
        self.clear_screen()
        print("====================================")
        print("         CHANGE SERIAL PORT        ")
        print("====================================")
        
        # Disconnect if connected
        if self.connected:
            self.disconnect()
            
        # List available ports
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No serial ports found.")
            input("Press Enter to continue...")
            return
            
        print("Available ports:")
        for i, port in enumerate(ports):
            print(f"{i+1}. {port.device} - {port.description}")
            
        # Allow manual entry if needed
        print(f"{len(ports)+1}. Enter port manually")
        
        selection = input("\nSelect port number: ")
        
        try:
            index = int(selection) - 1
            if 0 <= index < len(ports):
                self.manual_port = ports[index].device
                print(f"Selected port: {self.manual_port}")
            elif index == len(ports):
                manual_port = input("Enter port path (e.g., /dev/ttyUSB0 or COM3): ")
                if manual_port.strip():
                    self.manual_port = manual_port
                    print(f"Manually set port to: {self.manual_port}")
                else:
                    print("No port entered. Port not changed.")
            else:
                print("Invalid selection. Port not changed.")
        except ValueError:
            print("Invalid input. Port not changed.")
            
        # Try to reconnect
        print("\nAttempting to connect to device...")
        self.connect()
        
        input("Press Enter to continue...")
    
    def run(self):
        """Main application loop"""
        if not self.connect():
            print("Failed to connect. Exiting.")
            return
        
        running = True
        while running:
            choice = self.show_main_menu()
            
            if choice == '1':
                self.handle_view_medicines()
            elif choice == '2':
                self.handle_view_schedule()
            elif choice == '3':
                self.handle_update_medicine()
            elif choice == '4':
                self.handle_update_schedule()
            elif choice == '5':
                self.handle_update_emergency()
            elif choice == '6':
                # Refresh data by sending menu command
                self.clear_screen()
                print("Refreshing data...")
                response = self.send_command("menu")
                print(response)
                input("Press Enter to continue...")
            elif choice == '7':
                self.handle_custom_command()
            elif choice == '8':
                self.handle_change_port()
            elif choice == '0':
                running = False
            else:
                print("Invalid option. Please try again.")
                time.sleep(1)
        
        self.disconnect()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Synapse AR Terminal Interface')
    parser.add_argument('-p', '--port', 
                       help='Manually specify the serial port (e.g., /dev/ttyUSB0 or COM3)')
    return parser.parse_args()

if __name__ == "__main__":
    print("Starting Synapse AR Terminal Interface...")
    
    args = parse_arguments()
    terminal = ARTerminal(manual_port=args.port)
    
    try:
        terminal.run()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        terminal.disconnect()
        print("Goodbye!") 