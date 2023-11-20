# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 12:47:14 2023

@author: Owner
"""

import tkinter as tk  # Standard GUI library for creating graphical user
import math



def get_percentages():
    """
    Create a GUI window to get START_PERCENTAGE and END_PERCENTAGE from the user.

    :return: start_percentage (float), end_percentage (float)
        The starting and ending percentages entered by the user.

    Example usage:
    start_percentage, end_percentage = get_percentages()
    print(f"Start Percentage: {start_percentage}\nEnd Percentage: {end_percentage}")
    """

    # Creating main window
    root = tk.Tk()
    root.title("Enter Percentages")

    # Labels
    tk.Label(root, text="Enter Starting Percentage:").grid(row=0)
    tk.Label(root, text="Enter Ending Percentage:").grid(row=1)

    # Entry fields
    start_entry = tk.Entry(root)
    end_entry = tk.Entry(root)
    start_entry.grid(row=0, column=1)
    end_entry.grid(row=1, column=1)

    # Dictionary to store values
    percentages = {}

    # Function to retrieve values and close window
    def retrieve_values():
        percentages['start'] = float(start_entry.get())
        percentages['end'] = float(end_entry.get())
        root.quit()

    # Button to submit
    tk.Button(root, text="Submit", command=retrieve_values).grid(row=2, columnspan=2)

    # Start GUI loop
    root.mainloop()
    root.destroy()

    return percentages['start'], percentages['end']

def filter_by_percentage(df, low_perc, high_perc):
    """
    Filters a DataFrame to only include rows within the given percentile range.

    Parameters:
    - df (pd.DataFrame): The DataFrame to filter.
    - low_perc (float): The lower percentile to start the filter.
    - high_perc (float): The upper percentile to end the filter.

    Returns:
    - pd.DataFrame: A DataFrame containing only the rows within the specified percentile range.

    Example:
    >>> df = pd.DataFrame({'A': range(1, 101)})
    >>> filtered_df = filter_by_percentage(df, 20, 40)
    """
    n = len(df)
    low_idx = math.ceil((low_perc / 100) * n)
    high_idx = math.ceil((high_perc / 100) * n)

    # Make sure indices do not overlap
    low_idx = min(low_idx, high_idx)
    high_idx = max(low_idx, high_idx)

    return df.iloc[low_idx:high_idx].reset_index(drop=True)




# Requires a paginator to be set up!
# I have duplicated this in the s3 functions library (mainly because duplicating it bothers me less than not putting this with s3 or not putting it with filtering functions)
def s3_filter_processed_files(dataframe, s3_client, paginator, filename_col, bucket, subdirectory):
    """
    Drops rows from the DataFrame where the filename already exists in the S3 bucket.

    Parameters:
    - dataframe (pandas.DataFrame): DataFrame containing the filenames.
    - filename_col (str): Name of the column in the DataFrame that contains the filenames.
    - bucket (str): The name of the S3 bucket.
    - subdirectory (str): The subdirectory in the S3 bucket.

    Returns:
    - pandas.DataFrame: The filtered DataFrame.

    Example usage:
    filtered_df = filter_processed_files(df, 'FILENAME', 'my-bucket', 'my/subdirectory')
    """

    prefix = f"{subdirectory}/" if subdirectory else ""

    # Set to store filenames found in S3
    existing_files = set()

    # Iterate over pages of objects in S3
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            filename = obj['Key'].split('/')[-1]
            existing_files.add(filename)

    # Drop rows where the filename exists in S3
    return dataframe[~dataframe[filename_col].isin(existing_files)]






