
# %% Package Imports
import os  # Provides a way of interacting with the operating system
import re  # Regular expressions library for string manipulation
import pandas as pd

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



def data_to_latex(data, caption="Table", label=None, note=None, 
                  caption_position='above', minipage_size=0.5, 
                  total_row=False, percent_row=False, 
                  total_column=False, percent_column=False, 
                  resize_width=None, comment=None, series_column_name=None):
    """
    Generate a LaTeX table from either a pandas Series or DataFrame.

    Parameters
    ----------
    data : pandas.Series or pandas.DataFrame
        Data to be converted into a LaTeX table. Usually from pandas value_counts() or crosstab() methods.
    caption : str, optional
        Caption for the table. Default is "Table".
    label : str, optional
        Label for the table. Default is None.
    note : str, optional
        Note for the table. Default is None.
    caption_position : str, optional
        Position of the caption, either 'above' or 'below'. Default is 'above'.
    minipage_size : float, optional
        The size of the minipage as a fraction of the line width. Default is 0.5.
    total_row : bool, optional
        Include a total row at the end of the table. Default is False.
    percent_row : bool, optional
        Include a percentage row at the end of the table. Default is False.
    total_column : bool, optional
        Include a total column at the end of the table. Default is False.
    percent_column : bool, optional
        Include a percentage column at the end of the table. Default is False.
    resize_width : str, optional
        A string representing the width to resize the table to, e.g., '0.8\\textwidth'. 
        If None, no resizing is applied. Default is None.
    comment : str, optional
        A comment to be added after the table. Default is None.
    series_column_name : str, optional
        Name of the column represented by the Series (used if data is a Series). Required if data is a Series.

    Returns
    -------
    str
        LaTeX table.
    """

    # Check if data is a Series (value_counts) or DataFrame (crosstab)
    is_series = isinstance(data, pd.Series)
    is_dataframe = isinstance(data, pd.DataFrame)

    # ====== Series Handling (Value Counts) ======
    if is_series:
        if series_column_name is None:
            raise ValueError("series_column_name is required when data is a Series.")

        total_count = data.sum() if percent_row or total_row else None

        formatted_values = []
        for index, count in data.iteritems():
            formatted_count = f"{count:,}"
            if percent_row:
                percent_value = f"{count / total_count:.1%}".replace('%', '\\%')
                formatted_values.append(f"{index} & {formatted_count} & {percent_value}\\\\\n")
            else:
                formatted_values.append(f"{index} & {formatted_count}\\\\\n")
            
            # Add midrule before Total row
            if index == 'Total':
                formatted_values[-1] = "\\midrule\n" + formatted_values[-1]

        headers = f"{series_column_name} & Count"
        headers += " & Percentage" if percent_row else ""

    # ====== DataFrame Handling (Crosstab) ======
    elif is_dataframe:
        if total_column:
            data['Total'] = data.sum(axis=1)
        if total_row:
            data.loc['Total'] = data.sum()

        if percent_column:
            df_percent = data.div(data.sum(axis=1), axis=0) * 100
            df_percent = df_percent.applymap(lambda x: f"{x:.1f}\\%" if isinstance(x, (int, float)) else x)
            data = pd.concat([data, df_percent], axis=1)

        if percent_row:
            df_percent_row = (data.loc['Total'] / data.loc['Total'].sum()) * 100
            data.loc['Percent'] = df_percent_row.apply(lambda x: f"{x:.1f}\\%")

        data = data.applymap(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)

        # Reset index to include it in the table
        data_reset = data.reset_index()

        headers = " & ".join([f"{col}" for col in data_reset.columns])
        formatted_values = []

        for i, row in enumerate(data_reset.itertuples(index=False, name=None)):
            row_string = " & ".join(map(str, row)) + "\\\\"
            
            # Add midrule before Total row
            if row[0] == 'Total' or (total_row and i == len(data_reset) - 2):
                row_string = "\\midrule\n" + row_string

            formatted_values.append(row_string)

    else:
        raise ValueError("Data must be a pandas Series or DataFrame.")

    # ====== Common LaTeX Table Generation ======
    table = "\\begin{table}[H]\n"
    table += "\\begin{center}\n"
    table += f"\\begin{{minipage}}{{{minipage_size}\\linewidth}}\n"
    table += "\\centering\n"

    if resize_width:
        table += f"\\resizebox{{{resize_width}}}{{!}}{{%\n"

    # Dynamic column format based on the number of columns
    column_format = "l" + "r" * (headers.count('&') + 1)
    table += f"\\begin{{tabular}}{{{column_format}}}\n"
    table += "\\hline\n"
    table += f"{headers} \\\\\n"
    table += "\\midrule\n"

    # Add formatted rows to the table
    for value in formatted_values:
        table += f"{value}\n"

    table += "\\hline\n"
    table += "\\hline\n"
    table += "\\end{tabular}\n"

    if resize_width:
        table += "}% end resizebox\n"

    table += "\\end{minipage}\n"

    # Add caption, label, and note
    if caption_position == 'above':
        table += f"\\caption{{{caption}}}\n"
        if label:
            table += f"\\label{{{label}}}\n"
    if note:
        table += "\\vspace{.2cm}\n"
        table += "\\begin{tabular}{@{}p{0.9\\linewidth}@{}}\n"
        table += f"\\small {note}\n"
        table += "\\end{tabular}\n"
        table += "\\vspace{.1cm}\n"
    if caption_position == 'below':
        table += f"\\caption{{{caption}}}\n"
        if label:
            table += f"\\label{{{label}}}\n"

    table += "\\end{center}\n"
    table += "\\end{table}\n"

    # Add the comment if provided
    if comment:
        table += f"% {comment}\n"

    return table







def value_counts_to_latex(value_counts, column_name, order=None, caption="Value Counts", 
                          label=None, note=None, caption_position='above', 
                          total=False, percent=False):
    """
    Generate LaTeX table from pandas value_counts() with options for total and percentage columns.
    THIS FUNCTION IS DEPRECATED AND WILL BE REMOVED IN A FUTURE UPDATE.

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
    caption_position : str, optional
        Position of the caption, either 'above' or 'below'. Default is 'above'.
    total : bool, optional
        Include a total row at the end of the table. Default is False.
    percent : bool, optional
        Include a percentage column in the table. Default is False.

    Returns
    -------
    str
        LaTeX table.

    Examples
    --------
    >>> df['column'].value_counts().pipe(value_counts_to_latex, 'column', total=True, percent=True)
    """
    
    print("WARNING: 'value_counts_to_latex' is deprecated and will be removed in a future update. Please use 'data_to_latex' instead.")

    if percent or total:
        total_count = value_counts.sum()

    formatted_values = []
    for index, count in value_counts.iteritems():
        formatted_count = f"{count:,}"
        if percent:
            percent_value = f"{count / total_count:.1%}".replace('%', '\\%')
            formatted_values.append(f"{index} & {formatted_count} & {percent_value}\\\\\n")
        else:
            formatted_values.append(f"{index} & {formatted_count}\\\\\n")

    table = "\\begin{table}[H]\n"
    table += "\\begin{center}\n"
    table += "\\begin{minipage}{0.5\\linewidth}\n"
    table += "\\centering\n"
    table += "\\begin{tabular}{l c" + (" c" if percent else "") + "}\n"
    table += "\\hline\n"
    headers = f"{column_name} & Count"
    headers += " & Percentage" if percent else ""
    table += headers + "\\\\\\midrule\n"
    
    # Add formatted rows to the table
    for value in formatted_values:
        table += value
    
    if total:
        total_row = f"Total & {total_count:,}"
        total_row += " & 100\\%" if percent else ""
        table += "\\midrule\n"
        table += total_row + "\\\\\n"

    table += "\\hline\n"
    table += "\\hline\n"
    table += "\\end{tabular}\n"

    if note and caption_position == 'below':
        table += "\\vspace{.2cm}\n"
        table += "\\begin{tabular}{@{}p{0.9\\linewidth}@{}}\n"
        table += "\\small " + note + "\n"
        table += "\\end{tabular}\n"
        table += "\\vspace{.1cm}\n"

    if caption_position == 'above':
        table += "\\caption{" + caption + "}\n"
        if label:
            table += "\\label{" + label + "}\n"

    if note and caption_position == 'above':
        table += "\\vspace{.2cm}\n"
        table += "\\begin{tabular}{@{}p{0.9\\linewidth}@{}}\n"
        table += "\\small " + note + "\n"
        table += "\\end{tabular}\n"
        table += "\\vspace{.1cm}\n"

    if caption_position == 'below':
        table += "\\caption{" + caption + "}\n"
        if label:
            table += "\\label{" + label + "}\n"

    table += "\\end{minipage}\n"
    table += "\\end{center}\n"
    table += "\\end{table}\n"
    
    return table




def crosstab_to_latex(df, caption="Crosstab Table", label=None, note=None, 
                      caption_position='above', minipage_size=0.5, 
                      total_row=False, percent_row=False, 
                      total_column=False, percent_column=False, resize_width=None):
    """
    Generate LaTeX table from a pandas crosstab DataFrame with options for total and percentage rows and columns.
    THIS FUNCTION IS DEPRECATED AND WILL BE REMOVED IN A FUTURE UPDATE.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame, usually from pandas crosstab() method.
    caption : str, optional
        Caption for the table. Default is "Crosstab Table".
    label : str, optional
        Label for the table. Default is None.
    note : str, optional
        Note for the table. Default is None.
    caption_position : str, optional
        Position of the caption, either 'above' or 'below'. Default is 'above'.
    minipage_size : float, optional
        The size of the minipage as a fraction of the line width. Default is 0.5.
    total_row : bool, optional
        Include a total row at the end of the table. Default is False.
    percent_row : bool, optional
        Include a percentage row at the end of the table. Default is False.
    total_column : bool, optional
        Include a total column at the end of the table. Default is False.
    percent_column : bool, optional
        Include a percentage column at the end of the table. Default is False.
    resize_width : str, optional
        A string representing the width to resize the table to, e.g., '0.8\\textwidth'. 
        If None, no resizing is applied. Default is None.

    Returns
    -------
    str
        LaTeX table.
    """

    print("WARNING: 'crosstab_to_latex' is deprecated and will be removed in a future update. Please use 'data_to_latex' instead.")

    def format_with_commas(x):
          if isinstance(x, (int, float)):
              return f"{x:,.0f}"
          return x

    def format_with_percent(x):
        if isinstance(x, (int, float)):
            return f"{x:.1f}\\%"
        return x

    if total_column:
        df['Total'] = df.sum(axis=1)
    if total_row:
        df.loc['Total'] = df.sum()

    if percent_column:
        df_percent = df.div(df.sum(axis=1), axis=0) * 100
        df_percent = df_percent.applymap(format_with_percent)
        df = pd.concat([df, df_percent], axis=1)

    if percent_row:
        df_percent_row = (df.loc['Total'] / df.loc['Total']. sum()) * 100
        df.loc['Percent'] = df_percent_row.apply(format_with_percent)

    df = df.applymap(format_with_commas)

    # Reset the index to include it in the table
    df_reset = df.reset_index()

    column_format = "l" + "r" * len(df_reset.columns)
    headers = " & ".join([f"{col}" for col in df_reset.columns])
    body = " \\\\\n".join([" & ".join(map(str, row)) for row in df_reset.itertuples(index=False, name=None)])

    table = "\\begin{table}[H]\n"
    table += "\\begin{center}\n"
    table += f"\\begin{{minipage}}{{{minipage_size}\\linewidth}}\n"
    table += "\\centering\n"

    if resize_width:
        table += f"\\resizebox{{{resize_width}}}{{!}}{{%\n"

    table += f"\\begin{{tabular}}{{{column_format}}}\n"
    table += "\\hline\n"
    table += f"{headers} \\\\\n"
    table += "\\midrule\n"
    table += f"{body} \\\\\n"
    table += "\\hline\n"
    table += "\\hline\n"
    table += "\\end{tabular}\n"

    if resize_width:
        table += "}% end resizebox\n"

    table += "\\end{minipage}\n"
    
    if caption_position == 'above':
        table += f"\\caption{{{caption}}}\n"
        if label:
            table += f"\\label{{{label}}}\n"
    if note:
        table += "\\vspace{.2cm}\n"
        table += "\\begin{tabular}{@{}p{0.9\\linewidth}@{}}\n"
        table += f"\\small {note}\n"
        table += "\\end{tabular}\n"
        table += "\\vspace{.1cm}\n"
    if caption_position == 'below':
        table += f"\\caption{{{caption}}}\n"
        if label:
            table += f"\\label{{{label}}}\n"

    table += "\\end{center}\n"
    table += "\\end{table}\n"

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
