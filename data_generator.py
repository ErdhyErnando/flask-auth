import threading
import random
from datetime import datetime
import time  # Import the time module


class RandomDataGenerator:
  """
  This class generates random data every 2 seconds and provides methods
  to access and reset the generated data.
  """

  def __init__(self):
    self.data = None
    self.stop_event = threading.Event()  # Event to signal thread termination

  def generate_data(self):
    while not self.stop_event.is_set():
      self.data = {
          "timestamp": datetime.now().isoformat(),
          "value": random.randint(1, 100)  # Generate random integer between 1 and 100
      }
      time.sleep(2.0)  # Schedule next generation after 2 seconds
      self.stop_event.wait(timeout=2.0)  # Wait for 2 seconds or stop signal

  def start(self):
    """
    Starts the background thread to generate random data.
    """
    self.data_thread = threading.Thread(target=self.generate_data)
    self.data_thread.daemon = True  # Set as daemon thread for clean termination
    self.data_thread.start()

  def stop(self):
    """
    Stops the background thread generating random data.
    """
    self.stop_event.set()  # Signal the thread to stop

  def get_data(self):
    """
    Returns the most recently generated random data, or None if no data has been generated yet.
    """
    return self.data

if __name__ == "__main__":
  generator = RandomDataGenerator()
  generator.start()

  # Simulate some usage of the generated data
  while True:
    data = generator.get_data()
    if data:
      print(f"Generated data: {data}")
    else:
      print("No data generated yet.")
    time.sleep(1)  # Check for data every 1 second

  # Stop the data generation thread (optional, would typically happen on program termination)
  generator.stop()
  generator.data_thread.join()  # Wait for the thread to finish
  print("Data generation stopped.")
