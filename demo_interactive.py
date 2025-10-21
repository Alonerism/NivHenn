#!/usr/bin/env python3
"""
Demo of interactive analyzer with simulated user input
"""
import subprocess
import sys

# Simulate user input:
# 1. Select listings: 1,2 (first two listings)
# 2. For listing 1: Select agents 1,2,5 (Investment, Location, Construction)
# 3. For listing 2: Select agents all
# 4. Confirm: yes

user_inputs = [
    "1,2",      # Select first two listings
    "1,2,5",    # Agents for listing 1
    "all",      # Agents for listing 2  
    "y"         # Confirm
]

input_string = "\n".join(user_inputs) + "\n"

print("🎬 Running interactive analyzer with simulated input...")
print(f"Simulated inputs: {user_inputs}")
print("=" * 80)
print()

# Run the interactive analyzer with simulated input
process = subprocess.Popen(
    [".venv/bin/python", "interactive_analyzer.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

output, _ = process.communicate(input=input_string, timeout=120)
print(output)

sys.exit(process.returncode)
