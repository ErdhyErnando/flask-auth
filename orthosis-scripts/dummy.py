import time

# Get the start time
start_time = time.time()

# Loop until 10 seconds have passed
while time.time() - start_time < 5:
  # Get the current time
  current_time = time.strftime("%H:%M:%S")

  # Print the number and time
  print(f"{current_time} - 1")

  time.sleep(1)  # Pause for 1 second
