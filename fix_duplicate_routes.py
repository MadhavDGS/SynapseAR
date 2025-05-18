#!/usr/bin/env python3
import re

# Path to the synapse_web.py file
input_file = 'synapse_web.py'
output_file = 'synapse_web_fixed.py'

# Read the file content
with open(input_file, 'r') as f:
    content = f.read()

# Create a pattern to match the first occurrence of the duplicate route
# This is looking for @app.route('/api/sensor_data'...) section including the function definition
first_route_pattern = r'@app\.route\(\'/api/sensor_data\'.*?def api_sensor_data\(\):.*?return jsonify\({.*?}\), 500\s+\n'
pattern = re.compile(first_route_pattern, re.DOTALL)

# Find the first match
match = pattern.search(content)

if match:
    # Get the matched text
    matched_text = match.group(0)
    print(f"Found duplicate route definition. Removing first occurrence...")
    
    # Replace only the first occurrence with an empty string
    fixed_content = content.replace(matched_text, '', 1)
    
    # Write the fixed content to the output file
    with open(output_file, 'w') as f:
        f.write(fixed_content)
    
    print(f"Successfully created fixed version at {output_file}")
    print("Please review and then rename it to synapse_web.py if everything looks correct.")
else:
    print("Pattern not found. Make sure the route format matches what's expected.") 