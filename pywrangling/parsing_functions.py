from bs4 import BeautifulSoup
import pandas as pd



#%% Functions
def extract_table_with_text(html_content, search_text):
    """
    Extracts the first table from an HTML string that contains the specified search text,
    and drops any columns that have only NaN values.

    Parameters:
        html_content (str): HTML content as a string.
        search_text (str): The text to search for within tables.

    Returns:
        pd.DataFrame: The first DataFrame containing the search text with empty columns removed, 
                      or None if not found.

    Example:
        # Extract a table that contains the text "Revenue" from an HTML string:
        html_content = "<html><body>...<table>...</table></body></html>"
        df = extract_table_with_text(html_content, "Revenue")
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
            # Drop columns with all NaN values
            df.dropna(axis=1, how='all', inplace=True)
            return df

    # Return None if no table contains the search text
    return None