
# %% Package Imports
import os  # Provides a way of interacting with the operating system
import re  # Regular expressions library for string manipulation


# %% FUNCTIONS FOR BRUTE FORCING PROPER FORMATTING IN LATEX FILES 
def add_space_after_ampersand(latex_content):
    """
    Add a space after any & symbol in LaTeX content.
    
    Parameters:
    - latex_content (str): The LaTeX content as a string.
    
    Returns:
    str: The LaTeX content with a space added after any & symbol.
    
    Sample Usage:
    >>> add_space_after_ampersand("Value is 0.31 &0.4")
    "Value is 0.31 & 0.4"
    """
    return re.sub(r'&', r'& ', latex_content)

def add_leading_zero_to_small_numbers(latex_content):
    """
    Add a leading zero to numbers that are less than one if they do not already have one.
    
    Parameters:
    - latex_content (str): The LaTeX content as a string.
    
    Returns:
    str: The LaTeX content with leading zeros added to numbers less than one.
    
    Sample Usage:
    >>> add_leading_zero_to_small_numbers("Value is .31 and .4")
    "Value is 0.31 and 0.4"
    """
    return re.sub(r'(?<=\s|&|\\|,|\()\.(\d+)', r'0.\1', latex_content)

def round_small_numbers(latex_content):
    """
    Round numbers that have more than 3 decimals to have 3 decimals in LaTeX content.
    
    Parameters:
    - latex_content (str): The LaTeX content as a string.
    
    Returns:
    str: The LaTeX content with numbers rounded to 3 decimal places.
    
    Sample Usage:
    >>> round_small_numbers("Value is 0.12345 and 0.6789")
    "Value is 0.123 and 0.679"
    """
    return re.sub(r'(\d+\.\d{4,})', lambda x: f"{round(float(x.group(1)), 3)}", latex_content)



def add_thousands_separators(latex_content):
    """
    Adds commas as thousands separators to integers in LaTeX content.
    
    Parameters:
    latex_content (str): The LaTeX content as a string.
    
    Returns:
    str: The LaTeX content with commas added as a thousands separator to integers.
    
    Sample Usage:
    >>> add_thousands_separators("Value is 1000 and 20000")
    "Value is 1,000 and 20,000"
    """
    return re.sub(r'(?<=\s|&|\\|,|\()(\d{1,3}(?=(\d{3})+(?!\d)))', r'\1,', latex_content)





def format_latex_content(latex_content):
    """
    Format LaTeX content by adding leading zeros, rounding numbers, and adding spaces after ampersands.
    
    Parameters:
    - latex_content (str): The LaTeX content as a string.
    
    Returns:
    str: The formatted LaTeX content.
    
    Sample Usage:
    >>> format_latex_content("Value is .31 and 1000 and 0.12345 &0.6")
    "Value is 0.31 and 1000 and 0.123 & 0.6"
    """
    latex_content = add_space_after_ampersand(latex_content)
    latex_content = add_leading_zero_to_small_numbers(latex_content)
    latex_content = round_small_numbers(latex_content)
    latex_content = add_thousands_separators(latex_content)
    
    return latex_content




def process_tex_files(folder_path):
    """
    Apply LaTeX formatting to all .tex files in a given directory.
    
    Parameters:
    - folder_path (str): The path to the directory containing .tex files.
    
    Sample Usage:
    >>> process_tex_files("D:\\Dropbox\\Placer DA\\Tables")
    """
    
    # Check if the directory exists
    if not os.path.exists(folder_path):
        print(f"The directory {folder_path} does not exist.")
        return

    # Loop through each file in the directory
    for filename in os.listdir(folder_path):
        if filename.endswith(".tex"):
            filepath = os.path.join(folder_path, filename)
            
            # Read the original LaTeX content from the .tex file
            with open(filepath, 'r', encoding='utf-8') as file:
                original_content = file.read()
            
            # Apply formatting
            formatted_content = format_latex_content(original_content)
            
            # Write the formatted LaTeX content back to the .tex file
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(formatted_content)
            
            print(f"Processed {filename}")



# Given folder path
#folder_path = "D:\\Dropbox\\Placer DA\\Tables"

#process_tex_files(folder_path)
