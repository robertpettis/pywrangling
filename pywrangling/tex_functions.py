
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


def value_counts_to_latex(value_counts, column_name, order=None, caption="Value Counts", label=None, note=None):
    """
    Generate LaTeX table from pandas value_counts().

    Parameters
    ----------
    value_counts : pandas.Series
        Value counts, usually from pandas value_counts() method.
    column_name : str
        Name of the column represented by value_counts.
    order : list, optional
        Ordering of the index values. Default is None.
    caption : str, optional
        Caption for the table. Default is "Value Counts".
    label : str, optional
        Label for the table. Default is None.
    note : str, optional
        Note for the table. Default is None.

    Returns
    -------
    str
        LaTeX table.

    Examples
    --------
    >>> df['column'].value_counts().pipe(value_counts_to_latex, 'column')
    """
    # Order value_counts if order list is provided
    if order is not None:
        value_counts = value_counts.reindex(order, fill_value=0)

    table = "\\begin{table}[H]\n"
    table += "\\caption{" + caption + "}\n"
    if label:
        table += "\\label{" + label + "}\n"
    table += "\\begin{center}\n"
    table += "\\begin{minipage}{0.5\\linewidth}\n"  # Begin a minipage
    table += "\\centering\n"
    table += "\\begin{tabular}{l|c}\n"
    table += "\\hline\n"
    table += f"\\textbf{{{column_name}}} & \\textbf{{Count}}\\\\\\hline\\hline\n"
    
    for index, count in value_counts.items():
        formatted_count = format(int(count), ',')
        table += f"{index} & {formatted_count}\\\\\n"
    
    table += "\\hline\n"
    table += "\\end{tabular}\n"

    if note:
        table += "\\vspace{.2cm}\n"
        table += "\\begin{tabular}{@{}p{0.9\\linewidth}@{}}\n"  # Begin a full-width single-column table
        table += "\\small " + note + "\n"
        table += "\\vspace{.1cm}\n"
        table += "\\end{tabular}\n"  # End the full-width single-column table

    table += "\\end{minipage}\n"  # End minipage
    table += "\\end{center}\n"
    table += "\\end{table}\n"
    
    return table







def crosstab_to_latex(crosstab, caption="Crosstab", label=None, note=None, copy_mode=False):
    # Determine the backslash character to use based on the mode
    bs = "\\" if copy_mode else "\\\\"

    table = f"{bs}begin{{table}}[H]\n"
    table += f"{bs}caption{{{caption}}}\n"
    if label:
        table += f"{bs}label{{{label}}}\n"
    table += f"{bs}begin{{center}}\n"
    table += f"{bs}begin{{tabular}}{{l|{'c' * len(crosstab.columns)}}}\n"
    
    # Header
    table += f"{bs}hline\n"
    table += f"{bs}textbf{{}}"
    for column in crosstab.columns:
        table += f" & {bs}textbf{{{column}}}"
    table += f"{bs}{bs}\n{bs}hline{bs}hline\n"
    
    # Rows
    for index, row in crosstab.iterrows():
        table += f"{bs}textbf{{{index}}}"
        for value in row:
            formatted_value = format(value, ',')
            table += f" & {formatted_value}"
        table += f"{bs}{bs}\n"
    
    table += f"{bs}hline\n"
    table += f"{bs}end{{tabular}}\n"
    if note:
        table += f"{bs}begin{{minipage}}{{10cm}}\n"
        table += f"{bs}vspace{{.2cm}}\n"
        table += f"{bs}small {note}\n"
        table += f"{bs}vspace{{.1cm}}\n"
        table += f"{bs}end{{minipage}}\n"
    table += f"{bs}end{{center}}\n"
    table += f"{bs}end{{table}}\n"
    
    return table



def value_count_percentages(data_counts):
    total_count = 0
    for count in data_counts.values():
        total_count += count

    value_percentages = {}
    
    for value, count in data_counts.items():
        percentage = (count / total_count) * 100
        value_percentages[value] = (count, percentage)

    return value_percentages



def panel_table(tables, caption, label, note=None):
    """
    Create a LaTeX panel table from a list of pandas DataFrames.

    Parameters:
    - tables (list): A list of dictionaries where the keys are the panel names and the values are pandas DataFrames.
    - caption (str): The table caption.
    - label (str): The table label.
    - note (str, optional): A note to include at the bottom of the table.

    Returns:
    str: A string representing the LaTeX panel table.

    Usage:
    >>> tables = [{"Panel A: Ever Incarcerated": df1}, {"Panel B: County Jail": df2}]
    >>> panel_table(tables, "Incarceration and Probation", "tab: incarcerated")
    """
    latex_table = r"\begin{table}[H]"
    latex_table += f"\n\caption{{{caption}}}"
    latex_table += f"\n\label{{{label}}}"
    latex_table += "\n\\begin{center}"
    latex_table += "\n\\begin{tabular}{ll}"
    
    for table_dict in tables:
        for panel_name, df in table_dict.items():
            latex_table += f"\n\hline \multicolumn{{2}}{{c}}{{{panel_name}}} \\ [0.5ex] \hline"
            for index, row in df.iterrows():
                latex_table += f"\n{index}\t&\t{row[0]} \\\\"
            latex_table += "\n\hline"
    
    if note:
        latex_table += "\n\\begin{minipage}{8cm}"
        latex_table += "\n\vspace{.1cm}"
        latex_table += f"\n\small {note}"
        latex_table += "\n\vspace{.1cm}"
        latex_table += "\n\end{minipage}"
    
    latex_table += "\n\end{center}"
    latex_table += "\n\end{table}"
    
    return latex_table



# Given folder path
#folder_path = "D:\\Dropbox\\Placer DA\\Tables"

#process_tex_files(folder_path)
