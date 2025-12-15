from bs4 import BeautifulSoup
import pandas as pd



#%% Functions

def extract_table_with_text(html_content, search_text, drop_na_columns=True):
    """
    Extracts the first table from an HTML string that contains the specified search text.
    Optionally drops columns that have only NaN values.

    Parameters:
        html_content (str): HTML content as a string.
        search_text (str): The text to search for within tables.
        drop_na_columns (bool): Whether to drop columns that contain only NaN values. Default is True.

    Returns:
        pd.DataFrame: The first DataFrame containing the search text, with optional empty columns removed,
                      or None if not found.

    Example:
        # Extract a table that contains the text "Revenue" from an HTML string:
        html_content = "<html><body>...<table>...</table></body></html>"
        df = extract_table_with_text(html_content, "Revenue", drop_na_columns=True)
        if df is not None:
            print(df)
    """
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all tables
    tables = soup.find_all("table")
    for table in tables:
        if search_text in str(table):
            # Convert the found table to a DataFrame
            df = pd.read_html(str(table))[0]
            # Drop columns with all NaN values if specified
            if drop_na_columns:
                df.dropna(axis=1, how='all', inplace=True)
            return df

    # Return None if no table contains the search text
    return None