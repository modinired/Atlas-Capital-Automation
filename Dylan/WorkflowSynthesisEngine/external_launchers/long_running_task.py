'''
Example of a long-running task with logging and progress.
'''

import time
import logging
import sys

# Configure basic logging to see output in the launcher
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

if __name__ == "__main__":
    logging.info("Starting long-running task...")

    total_steps = 20

    for i in range(total_steps):
        logging.info(f"Processing step {i + 1}/{total_steps}")

        # Simulate some work
        time.sleep(1.5)

        if i == 5:
            logging.warning("This is a warning message at step 6.")
        
        if i == 12:
            logging.error("This is an error message at step 13.")

    logging.info("Long-running task finished successfully!")

