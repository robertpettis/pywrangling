"""
These functions provide utility such as sending an email with a given text or sending a text message when conditions are met, etc.

Author: Robert Pettis

"""

# %% Importing required libraries
import sys  # Library for system-specific parameters and functions
import smtplib
from email.mime.text import MIMEText
import xml.etree.ElementTree as ET  # XML parsing library
import pandas as pd  # Data analysis and manipulation tool
import os
from datetime import datetime, time  # For date and time handling
import pytz  # For timezone handling
import inspect

# %% Functions


def find_columns_in_csv(directory: str, search_value: str, case_sensitive: bool = True):
    """
    Searches all CSV files in the given directory for columns that contain the search_value in their names.
    Returns a list of tuples with the file name and the matching column name.
    
    :param directory: Path to the directory containing the CSV files
    :param search_value: Value to search for in column names
    :param case_sensitive: Boolean indicating whether the search should be case-sensitive (default is True)
    :return: List of tuples with the file name and matching column name
    """
    results = []

    # Iterate over all files in the given directory
    for file_name in os.listdir(directory):
        # Check if the file is a CSV file
        if file_name.endswith('.csv'):
            file_path = os.path.join(directory, file_name)
            
            # Attempt to read only the column names of the CSV file with various encodings
            for encoding in ['utf-8', 'ISO-8859-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, nrows=0)
                    break  # Exit the loop if reading was successful
                except UnicodeDecodeError:
                    continue  # Try the next encoding
            
            # Check each column name for the search value
            for column in df.columns:
                if case_sensitive:
                    if search_value in column:
                        results.append((file_name, column))
                else:
                    if search_value.lower() in column.lower():
                        results.append((file_name, column))
    
    return results




def relative_path(relative_path):
    """
    Generate a full file path from a relative path based on the current working directory.
    
    Parameters:
    - relative_path (str): The relative path, using '..' to navigate up directories.

    Returns:
    - str: The absolute path corresponding to the relative path.

    Raises:
    - ValueError: If the current working directory is not set or if the path is invalid.

    Example:
    Suppose your current working directory is `/home/user/projects`, and you want to generate an absolute path to a file located at `../data/file.txt`.

    >>> full_path = relative_path('../data/file.txt')
    >>> print(full_path)
    /home/user/data/file.txt
    
    In this example, the function generates the absolute path `/home/user/data/file.txt` from the relative path `../data/file.txt`.
    """

    # Check if the current working directory is set
    cwd = os.getcwd()
    if not cwd:
        raise ValueError("Current working directory is not set.")
    
    # Generate the full path
    full_path = os.path.abspath(os.path.join(cwd, relative_path))
    
    return full_path



def send_email_or_text(subject, body, sender, recipients, password):
    """   
    # Good info on the app password here:
        https://stackoverflow.com/questions/70261815/smtplib-smtpauthenticationerror-534-b5-7-9-application-specific-password-req


    Parameters
    ----------
    subject : TYPE
        DESCRIPTION.
    body : TYPE
        DESCRIPTION.
    sender : TYPE
        DESCRIPTION.
    recipients : TYPE
        DESCRIPTION.
    password : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")


def testing_function():
    """This funcion is used for testing purposes only.
    """
    print("This is a test function")
    return None



# %% Define the function to fetch command line arguments or default values
# The function aims to provide flexibility in a Python script, allowing it to either accept input parameters from the command line or fall back to predefined default values. 

def fetch_arguments(default_values):
    r"""
    Fetch command-line arguments if available; otherwise, use default values.
    
    Parameters:
    - default_values (list): List of default values to use if no command-line arguments are provided.
    
    Returns:
    - arguments (list): List of arguments fetched from the command-line or default values.
    
    Usage example:
    default_values - [r'C:\Users\pettisr\Desktop\Scramento\Data', 'default_db','default_user']
    args = uf.fetch_arguments(default_values)
    wd, db, user = args

    """
    # Get the number of command-line arguments
    num_args = len(sys.argv) - 1
    
    # Check if command-line arguments are available
    if num_args > 0:
        # Fetch command-line arguments
        arguments = sys.argv[1:num_args+1]
    else:
        # Use default values if command-line arguments are not available
        arguments = default_values
    
    return arguments






# Main goal of this is to load in passwords and usernames from text files, but probably has other uses. 
def load_file_content(file_path):
    """
    Load the contents of a text file into a Python variable.

    Parameters:
    file_path (str): The path to the text file.

    Returns:
    str: The content of the file.

    Example usage:
    content = load_file_content('path/to/file.txt')
    """

    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    # Open and read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()

    return content






# Returns a boolean value. Main usage will be assisting in performing a particular function based on the day. 
def is_time_in_range(day_time_pairs, timezone):
    """
    Check if the current time falls within any of the given day and time pairs.

    Parameters:
    day_time_pairs (dict): A dictionary where keys are days of the week ('Monday', 'Tuesday', ...) and values are lists of tuples with start and end times in HH:MM format.
    timezone (str): The time zone to consider for the current time.

    Returns:
    bool: True if the current time is within any of the specified day and time ranges, otherwise False.
    """
    # Get the current time in the specified timezone
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    current_day = now.strftime('%A')
    current_time = now.time()

    if current_day in day_time_pairs:
        for start_str, end_str in day_time_pairs[current_day]:
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
            
            # Check if the current time falls within the time range
            if start_time <= current_time <= end_time:
                return True
    
    return False







def scan_for_string(directory, extensions, substring):
    """
    Scans the given directory for files with specified extensions
    and checks if they contain a given substring.

    Parameters:
    - directory (str): The path to the directory to scan.
    - extensions (list): A list of file extensions to include.
    - substring (str): The substring to search for in the files.

    Returns:
    - list: A list of file paths that contain the substring.

    Raises:
    - ValueError: If a disallowed file extension is encountered.
    """

    # Define acceptable and disallowed extensions
    acceptable_extensions = {'.sql', '.py', '.do', '.ipynb', '.js', '.html'}
    disallowed_extensions = {'.xlsx', '.xls', '.csv'}

    # Normalize extensions to lower case and ensure they start with a dot
    extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions}

    # Check for disallowed extensions
    for ext in extensions:
        if (ext in disallowed_extensions) | (ext not in acceptable_extensions):
            raise ValueError(f"Extension '{ext}' is disallowed.")

    matching_files = []

    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in extensions:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if substring in f.read():
                            matching_files.append(file_path)
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")

    return matching_files



def print_current_line():
    """
    Prints the line number of the code where this function is called.
    
    This function inspects the call stack to determine the line number 
    of the line where it was invoked and prints it.

    Example:
        # On line 15 of your script, you call the function like this:
        print_current_line()
        # Output: 15
    """
    # Get the frame of the caller (the previous frame)
    caller_frame = inspect.currentframe().f_back
    # Get the line number of the caller
    line_number = caller_frame.f_lineno
    # Print the line number
    print(f"{line_number}")
    return line_number


def cprint(text, text_color="red", bg_color="yellow"):
    # Define color mappings
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }

    # Define background color mappings
    bg_colors = {
        "black": "\033[40m",
        "red": "\033[41m",
        "green": "\033[42m",
        "yellow": "\033[43m",
        "blue": "\033[44m",
        "magenta": "\033[45m",
        "cyan": "\033[46m",
        "white": "\033[47m",
    }

    # Fetch the color codes, default to red text and yellow background
    text_code = colors.get(text_color.lower(), "\033[31m")
    bg_code = bg_colors.get(bg_color.lower(), "\033[43m")
    reset_code = "\033[0m"

    # Print the formatted text
    print(f"{text_code}{bg_code}{text}{reset_code}")
