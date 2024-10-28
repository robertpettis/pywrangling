from bs4 import BeautifulSoup
import pandas as pd

def extract_table_with_text(html_file, search_text):
    """
    Extracts the first table from an HTML file that contains the specified search text.

    Parameters:
        html_file (str): Path to the HTML file to parse.
        search_text (str): The text to search for within tables.

    Returns:
        pd.DataFrame: The first DataFrame containing the search text, or None if not found.

    Example:
        # Extract a table that contains the text "Revenue" from an HTML file:
        df = extract_table_with_text("financial_report.html", "Revenue")
        if df is not None:
            print(df)

        # Extract a table that mentions "User Data" from an HTML file:
        user_data_table = extract_table_with_text("user_info.html", "User Data")
        if user_data_table is not None:
            user_data_table.to_csv("user_data.csv", index=False)

        # If the specified text is not found:
        missing_table = extract_table_with_text("report.html", "Nonexistent Text")
        if missing_table is None:
            print("No table found containing the specified text.")
    """
    # Load the HTML document
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find all tables
    tables = soup.find_all("table")
    for table in tables:
        if search_text in str(table):
            # Convert the found table to a DataFrame
            return pd.read_html(str(table))[0]

    # Return None if no table contains the search text
    return None