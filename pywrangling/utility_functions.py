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

# %% Functions

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






# %% Convert XML to a dataframe

# I imagine different structures may not work, but this is a start. I won't 
# Advertise this in the readme though. 

def xml_file_to_dataframe(file_path):
    """
    Convert any XML file to a pandas DataFrame.

    Parameters:
    - file_path (str): The path to the XML file.

    Returns:
    - df (DataFrame): The resulting pandas DataFrame.
    """

    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Assuming that all children of the root have the same structure,
    # get the list of attribute names (columns) from the first grandchild
    if len(root) == 0 or len(root[0]) == 0:
        return pd.DataFrame()  # Return an empty DataFrame if there are no children or grandchildren

    columns = list(root[0][0].attrib.keys())

    # Extract data from the XML
    data = []
    for child in root:
        for grandchild in child:
            row_data = []
            for col in columns:
                value = grandchild.get(col)
                # Try to convert the value to an integer, if not leave it as is
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    pass
                row_data.append(value)
            data.append(row_data)

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data, columns=columns)

    return df










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









