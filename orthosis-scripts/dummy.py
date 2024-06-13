import time

# Loop forever
while True:
  # Get the current time
  current_time = time.strftime("%H:%M:%S")

  # Print the number and time
  print(f"{current_time} - 1")

  time.sleep(1)  # Pause for 1 second
