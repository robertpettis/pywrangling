"""
These functions provide utility such as sending an email with a given text or sending a text message when conditions are met, etc.

Author: Robert Pettis

"""

# %% Importing required libraries
import sys  # Library for system-specific parameters and functions
import smtplib
from email.mime.text import MIMEText
import pandas as pd  # Data analysis and manipulation tool
import os
import datetime
import time
import json
import yaml
import pytz  # For timezone handling
import inspect
import csv
import xml.etree.ElementTree as ET

# %% Functions




def find_bad_csv_line(
    filename: str,
    has_header: bool = True,
    return_as_dataframe: bool = False,
    encoding: str = 'utf-8'
):
    """
    Reads a CSV file line by line using the built-in csv module and checks
    whether each row has the same number of columns as the first (header) row.
    If a row is found with a mismatched column count (commonly due to an
    unescaped comma), this function returns information about the offending
    row.

    Parameters
    ----------
    filename : str
        The path to the CSV file to be read.
    has_header : bool, optional
        If True, treat the first row as the header row (column names).
        If False, the function will generate generic column names for the row
        comparison. Default is True.
    return_as_dataframe : bool, optional
        If True, return a tuple: (raw_line_text, df), where df is a DataFrame
        showing how the values line up under column names (including potential
        "Extra_XXX" columns for overflow). If False, only the raw line text is
        returned. Default is False.

    Returns
    -------
    str or tuple or None
        - If return_as_dataframe=False, returns the raw text of the offending row.
        - If return_as_dataframe=True, returns a tuple: (raw_line_text, df).
        - Returns None if no mismatched rows are detected.

    Examples
    --------
    1) Basic usage returning only the raw line:
    >>> bad_line = find_bad_csv_line_csv_module("some_file.csv")
    >>> if bad_line is not None:
    ...     print("Offending row text:", bad_line)

    2) If you also want a DataFrame for debugging:
    >>> result = find_bad_csv_line_csv_module("some_file.csv", return_as_dataframe=True)
    >>> if result is not None:
    ...     bad_line, bad_df = result
    ...     print("Raw line:", bad_line)
    ...     print("DataFrame showing misalignment:")
    ...     print(bad_df)
    """


    # Read the entire file as a list of lines for raw access
    try:
        with open(filename, 'r', encoding=encoding) as f:
            lines = f.readlines()
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(f"Could not decode file with encoding '{encoding}'. Try 'windows-1252' or 'latin1'.") from e

    # Use the csv module on the same file again to parse
    with open(filename, 'r', encoding=encoding) as f:
        reader = csv.reader(f)

        try:
            first_row = next(reader)
        except StopIteration:
            print("File is empty, no bad lines.")
            return None

        if has_header:
            header = first_row
            expected_num_cols = len(header)
            line_number = 1
        else:
            header = [f"col_{i+1}" for i in range(len(first_row))]
            expected_num_cols = len(header)
            line_number = 1
            if len(first_row) != expected_num_cols:
                print(f"Potentially bad row at line {line_number}.")
                raw_line_text = lines[line_number - 1].rstrip('\n')
                return _build_return(raw_line_text, header, return_as_dataframe)

        for row in reader:
            line_number += 1
            if len(row) != expected_num_cols:
                print(f"Potentially bad row at line {line_number}.")
                raw_line_text = lines[line_number - 1].rstrip('\n')
                return _build_return(raw_line_text, header, return_as_dataframe, row)

    print("No mismatched rows found.")
    return None



def _build_return(raw_line_text, header, return_as_dataframe, row=None):
    """
    Helper function to either return the raw line or build a DataFrame
    if return_as_dataframe is True. 'row' is the list of parsed columns for the
    mismatched line if available.
    """
    if not return_as_dataframe:
        return raw_line_text

    # If we need a dataframe, we have to handle:
    # 1) If row is shorter or equal in length -> we fill in None if needed
    # 2) If row is longer -> we create "Extra_###" column names
    row = row or []

    # If there's more data than columns, add extra "Extra_#" columns
    if len(row) > len(header):
        extra_count = len(row) - len(header)
        extra_headers = [f"Extra_{i+1}" for i in range(extra_count)]
        augmented_header = header + extra_headers
        data_dict = {}
        # Fill out normal columns
        for h, val in zip(header, row[:len(header)]):
            data_dict[h] = [val]
        # Fill out the extra columns
        for eh, val in zip(extra_headers, row[len(header):]):
            data_dict[eh] = [val]
    else:
        # If there's fewer items in row than header, fill missing with None
        data_dict = {}
        for i, h in enumerate(header):
            if i < len(row):
                data_dict[h] = [row[i]]
            else:
                data_dict[h] = [None]
        augmented_header = list(data_dict.keys())

    df = pd.DataFrame(data_dict, columns=augmented_header)
    return (raw_line_text, df)




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
    #now = datetime.now(tz)    #Started getting an error for this. Perhaps there was an update. 
    now = datetime.datetime.now(tz)
    current_day = now.strftime('%A')
    current_time = now.time()

    if current_day in day_time_pairs:
        for start_str, end_str in day_time_pairs[current_day]:
            start_time = datetime.datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.datetime.strptime(end_str, "%H:%M").time()

            
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



def cprint(text, text_color="red", bg_color="yellow", bold=True, animate=False, total_time=2.0):
    """
    Prints colored text to the console with optional background color, bold formatting,
    and optional animated typing effect over a total duration.

    Args:
        text (str): The text string to print.
        text_color (str or tuple, optional): Text color as a name (e.g., "red") or an (R, G, B) tuple.
                                             Defaults to "red".
        bg_color (str or tuple, optional): Background color as a name (e.g., "yellow") or an (R, G, B) tuple.
                                           Defaults to "yellow".
        bold (bool, optional): If True, displays bold text. Defaults to True.
        animate (bool, optional): If True, prints text with a typing animation. Defaults to False.
        total_time (float, optional): Total duration (in seconds) for the animated output. Only used if animate=True.

    Examples:
        # Using named colors without animation
        >>> cprint("Hello, world!", text_color="blue", bg_color="white")

        # Using RGB tuples with animation over 3 seconds
        >>> cprint("Animating with RGB colors...", text_color=(0, 255, 180), bg_color=(30, 30, 30),
        ...        bold=False, animate=True, total_time=3.0)
    """
    
    color_map = {
            # Basic Colors
            "black": (0, 0, 0), "red": (255, 0, 0), "green": (0, 128, 0), "yellow": (255, 255, 0),
            "blue": (0, 0, 255), "magenta": (255, 0, 255), "cyan": (0, 255, 255), "white": (255, 255, 255),
    
            # Extended Colors
            "pink": (255, 192, 203), "orange": (255, 165, 0), "sky blue": (135, 206, 235),
            "burnt orange": (204, 85, 0), "navy blue": (0, 0, 128), "lime green": (50, 205, 50),
            "gold": (255, 215, 0), "turquoise": (64, 224, 208), "violet": (143, 0, 255),
            "teal": (0, 128, 128), "coral": (255, 127, 80), "lavender": (230, 230, 250),
            "cobalt blue": (0, 71, 171), "electric indigo": (111, 0, 255), "bright green": (0, 255, 0),
    
            # Specialty Added Colors
            "cosmic latte": (255, 248, 231),
            "web du bois red": (184, 45, 73),
            "web du bois blue": (88, 100, 152),
            "web du bois brown": (107, 79, 58),
            "web du bois yellow": (231, 182, 44),
            "web du bois pink": (208, 150, 142),
            "cobalt blue": (37, 69, 213),
            "american red": (178, 34, 52),
            "american blue": (60, 59, 110),
            "sc blue": (0, 51, 102),
            "cider": (158, 110, 88),
            "slimer": (136, 183, 47),
            "1987 leonardo": (56, 108, 238),
            "1987 michaelangelo": (253, 95, 0),
            "1987 donatello": (81, 29, 110),
            "1987 raphael": (177, 0, 24),
            "deadpool": (107, 6, 20),
            "link hyrule warriors": (73, 124, 38),
            "link botw": (3, 146, 150),
            "tng command red": (146, 15, 9),
            "tng medical blue": (45, 129, 146),
            "tng gold": (206, 151, 70),
            "tng troi liner": (171, 149, 184),
            "tng warp lights": (178, 192, 255),
            "dayflower fresh": (110, 145, 246),
            "dayflower aged": (127, 143, 191),
            "indigo": (75, 0, 130),
            "prussian blue": (0, 49, 83),
            "red lead": (227, 66, 52),
            "red ochre": (125, 78, 87),
            "safflower pale": (255, 209, 220),
            "safflower red": (255, 99, 112),
            "orpiment": (255, 215, 0),
            "turmeric": (255, 196, 12),
            "amur cork tree": (255, 211, 0),
            "gamboge": (228, 155, 15),
            "yellow ochre": (204, 119, 34)
        }

    def is_valid_rgb(rgb):
        return (isinstance(rgb, tuple) and len(rgb) == 3 and
                all(isinstance(x, int) and 0 <= x <= 255 for x in rgb))

    def get_rgb(color_input, default_rgb):
        if is_valid_rgb(color_input):
            return color_input
        elif isinstance(color_input, str):
            return color_map.get(color_input.lower(), default_rgb)
        return default_rgb

    r_text, g_text, b_text = get_rgb(text_color, color_map["red"])
    r_bg, g_bg, b_bg = get_rgb(bg_color, color_map["yellow"])

    text_ansi_code = f"\033[38;2;{r_text};{g_text};{b_text}m"
    bg_ansi_code = f"\033[48;2;{r_bg};{g_bg};{b_bg}m"
    bold_code = "\033[1m" if bold else ""
    reset_code = "\033[0m"
    prefix = f"{bold_code}{text_ansi_code}{bg_ansi_code}"
    suffix = reset_code

    if animate and text:
        delay = total_time / len(text)
        for char in text:
            sys.stdout.write(f"{prefix}{char}{suffix}")
            sys.stdout.flush()
            time.sleep(delay)
        print()
    else:
        print(f"{prefix}{text}{suffix}")




def sleep_with_count(seconds, refresh_rate=0.1, count_up=False, text_color="cyan", bold=True):
    """
    Sleep for a given number of seconds while displaying a live countdown or count-up in the terminal.

    The display is updated in-place (like a progress bar), with optional color.

    Args:
        seconds (float): Number of seconds to sleep.
        refresh_rate (float, optional): How often to update the display (in seconds). Default is 0.1.
        count_up (bool, optional): If True, counts up from 0 to `seconds`.
                                   If False (default), counts down from `seconds` to 0.
        text_color (str or tuple, optional): Color of the countdown text. Can be a string
                                             (e.g., "yellow", "pink") which will be resolved
                                             to an RGB value, or an RGB tuple directly
                                             (e.g., (255, 255, 0) for pure yellow).
                                             Default is "cyan".
        bold (bool, optional): If True, display bold text. Default is True.

    Example usage:

    >>> sleep_with_count(5) # Default cyan
    >>> sleep_with_count(5, count_up=True, text_color="yellow") # Will now be true yellow
    >>> sleep_with_count(10, refresh_rate=0.5, text_color=(0, 255, 0)) # Pure green via RGB tuple
    >>> sleep_with_count(7, text_color="orange") # Will now be true orange
    """

    # --- ANSI color definitions as RGB tuples ---
    # These RGB values will be converted to 24-bit ANSI codes before printing.
    # This ensures consistent color rendering if your terminal supports 24-bit color.
    colors_rgb = {
        "black": (0, 0, 0),
        "red": (255, 0, 0),
        "green": (0, 128, 0), # Standard green
        "bright green": (0, 255, 0), # A more vibrant green, often associated with 'green'
        "yellow": (255, 255, 0), # Pure yellow
        "blue": (0, 0, 255),
        "magenta": (255, 0, 255),
        "cyan": (0, 255, 255),
        "white": (255, 255, 255),
        "pink": (255, 192, 203),        # Common RGB for Pink
        "orange": (255, 165, 0),        # Common RGB for Orange
        "sky blue": (135, 206, 235),    # Confirmed working RGB for Sky Blue
        "burnt orange": (204, 85, 0),   # Common RGB for Burnt Orange
        "navy blue": (0, 0, 128),       # Common RGB for Navy Blue
        "lime green": (50, 205, 50),    # Confirmed working RGB for Lime Green
        "gold": (255, 215, 0),          # Common RGB for Gold
        "turquoise": (64, 224, 208),    # Common RGB for Turquoise
        "violet": (143, 0, 255),        # Common RGB for Violet
        "teal": (0, 128, 128),          # Common RGB for Teal
        "coral": (255, 127, 80),        # Common RGB for Coral
        "lavender": (230, 230, 250),    # Common RGB for Lavender
        "cobalt blue": (0, 71, 171),    # Common RGB for Cobalt Blue
        "electric indigo": (111, 0, 255), # Common RGB for Electric Indigo
    }

    # Determine the RGB tuple for the requested color
    selected_rgb = None
    if isinstance(text_color, tuple) and len(text_color) == 3:
        # If it's already an RGB tuple, use it directly
        selected_rgb = text_color
    elif isinstance(text_color, str):
        # Look up the named color in our RGB dictionary
        selected_rgb = colors_rgb.get(text_color.lower())

    # Fallback to default cyan RGB if color not found or invalid
    if selected_rgb is None:
        selected_rgb = colors_rgb.get("cyan", (0, 255, 255)) # Default to cyan RGB if "cyan" also missing

    # Construct the 24-bit True Color ANSI escape code
    r, g, b = selected_rgb
    text_code = f"\033[38;2;{r};{g};{b}m"

    bold_code = "\033[1m" if bold else ""
    reset_code = "\033[0m"

    start_time = time.time()
    end_time = start_time + seconds

    while True:
        now = time.time()
        elapsed = now - start_time
        remaining = end_time - now

        if remaining <= 0:
            break

        if count_up:
            text = f"Sleeping: {elapsed:.1f}/{seconds} seconds elapsed... "
        else:
            text = f"Sleeping: {remaining:.1f} seconds remaining... "

        # Print with color and overwrite line
        sys.stdout.write(f"\r{bold_code}{text_code}{text}{reset_code}")
        sys.stdout.flush()
        time.sleep(refresh_rate)

    # Final message
    sys.stdout.write(f"\r{bold_code}{text_code}Done sleeping!                               {reset_code}\n")





def load_dict_from_file(filepath):
    """
    Loads a structured data file (.json, .yaml/.yml, or .xml) into a Python dictionary.

    Parameters:
    filepath (str): The path to the file.

    Returns:
    dict: Parsed data as a dictionary.
    """
    ext = os.path.splitext(filepath)[1].lower()
    with open(filepath, 'r', encoding='utf-8') as file:
        if ext == '.json':
            return json.load(file)
        elif ext in ('.yaml', '.yml'):
            return yaml.safe_load(file)
        elif ext == '.xml':
            tree = ET.parse(file)
            root = tree.getroot()
            return {root.tag: _xml_to_dict(root)}
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

def _xml_to_dict(element):
    """
    Recursively converts an XML element and its children into a dictionary.
    """
    # Convert children
    children = list(element)
    if children:
        result = {}
        for child in children:
            child_dict = _xml_to_dict(child)
            if child.tag in result:
                # Promote to list if tag repeats
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        return result
    else:
        # Include attributes and text
        if element.attrib:
            return {**element.attrib, '_text': element.text.strip() if element.text else ''}
        return element.text.strip() if element.text else ''



def _xml_to_dict(element):
    """
    Recursively converts an XML element and its children into a dictionary.
    """
    # Convert children
    children = list(element)
    if children:
        result = {}
        for child in children:
            child_dict = _xml_to_dict(child)
            if child.tag in result:
                # Promote to list if tag repeats
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        return result
    else:
        # Include attributes and text
        if element.attrib:
            return {**element.attrib, '_text': element.text.strip() if element.text else ''}
        return element.text.strip() if element.text else ''