from pywrangling.utility_functions import cprint

# Test the cprint function
cprint("My name is Robert!")  # Default colors
cprint("Hello in green text!", text_color="green")
cprint("Error with white text on red background!", text_color="white", bg_color="red")
cprint("Notice with red text on blue background!", bg_color="blue")
cprint("Notice with white text on magenta background!", text_color="white", bg_color="magenta")
cprint("Notice with red text on cyan background!", bg_color="cyan")





# %%Text styles
BOLD = '\033[1m'
ITALIC = '\033[3m'  # May not work in all terminals
UNDERLINE = '\033[4m'
STRIKETHROUGH = '\033[9m'

# Reset
# Individual reset codes
RESET_BOLD = '\033[22m'        # Resets bold/intensity
RESET_ITALIC = '\033[23m'      # Resets italic
RESET_UNDERLINE = '\033[24m'   # Resets underline
RESET_STRIKETHROUGH = '\033[29m'  # Resets strikethrough

# General reset for everything
RESET = '\033[0m'


# Example usage
print(f"{BOLD}This is bold text!{RESET}")
print(f"{ITALIC}This is italic text!{RESET}")
print(f"{UNDERLINE}This is underlined text!{RESET}")
print(f"{STRIKETHROUGH}This is strikethrough text!{RESET}")

# Example 1: Bold text with custom colors
cprint(f"This is {BOLD}bold {RESET_BOLD} red on yellow text!", text_color="red", bg_color="yellow") ## 

# Example 2: Underlined text with custom colors
cprint(f"This is {UNDERLINE}underlined{RESET_UNDERLINE} white on blue text!{RESET}", text_color="white", bg_color="blue")

# Example 3: Strikethrough text with green background
cprint(f"{STRIKETHROUGH}This is strikethrough text on a green background!{RESET}", text_color="white", bg_color="green")

# Example 4: Italicized text with magenta background
cprint(f"{ITALIC}This is italicized red text on a magenta background!{RESET}", text_color="red", bg_color="magenta")



# %% Animations
import time
import itertools

# Spinning loader animation
spinner = itertools.cycle(['-', '\\', '|', '/'])
for _ in range(20):
    print(f"\rLoading... {next(spinner)}", end="")
    time.sleep(0.1)





# %% Table like output

from tabulate import tabulate

data = [["Alice", 24], ["Bob", 27], ["Charlie", 22]]
print(tabulate(data, headers=["Name", "Age"], tablefmt="grid"))




#%% Gradient text

def gradient_text(text):
    colors = [31, 32, 33, 34, 35, 36]  # Red, Green, Yellow, Blue, Magenta, Cyan
    result = ""
    for i, char in enumerate(text):
        result += f"\033[{colors[i % len(colors)]}m{char}"
    return result + "\033[0m"

print(gradient_text("Python Gradient!"))





# %% Sounds

print('\a')  # May need speaker enabled






# %% Logging
import logging
import os

# Define log file path
log_file = r"Z:\Programming\Python\pywrangling\app.log"

# Function to set up logging
def setup_logger(log_file, append_mode=True):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all logs

    # Clear existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Choose mode: append ('a') or overwrite ('w')
    mode = 'a' if append_mode else 'w'

    # Set up file handler with the chosen mode
    file_handler = logging.FileHandler(log_file, mode=mode)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Step 1: Write initial log entries (INFO, WARNING, ERROR)
logger = setup_logger(log_file, append_mode=False)  # Overwrite to start fresh
logger.info("Initial INFO log entry.")
logger.warning("Initial WARNING log entry.")
logger.error("Initial ERROR log entry.")

# Close handlers to simulate ending the script
for handler in logger.handlers:
    handler.close()
    logger.removeHandler(handler)

# Step 2: Append new log entries (DEBUG, CRITICAL)
logger = setup_logger(log_file, append_mode=True)  # Append to the existing file
logger.debug("Appended DEBUG log entry.")
logger.critical("Appended CRITICAL log entry.")


# %% Manual Progress Bar
import time

for i in range(10001):
    print(f"\rLoading... {i/100}%", end="")
    time.sleep(0.001)

