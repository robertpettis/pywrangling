# TODO: The number of rows replaced needs correction


"""
This library provides a set of functions designed to simplify common data
wrangling tasks.

It includes functions for renaming columns, moving columns, and replacing
values in a DataFrame based on certain conditions.
"""

import pandas as pd  # Main library for data manipulation
import numpy as np  # Library for numerical operations
import re  # Regular expressions library for string manipulation
import math



def rename_columns(df, old_names, new_names=None, prefix=None, suffix=None, remove_prefix=None, remove_suffix=None):
    """
    Rename columns in a DataFrame.

    Parameters:
    df (pd.DataFrame): DataFrame to modify
    old_names (list of str): List of old column names
    new_names (list of str, optional): List of new column names
    prefix (str, optional): Prefix to add to new column names
    suffix (str, optional): Suffix to add to new column names
    remove_prefix (str, optional): Prefix to remove from column names
    remove_suffix (str, optional): Suffix to remove from column names

    Returns:
    pd.DataFrame: Modified DataFrame with renamed columns

    Raises:
    ValueError: If old_names is not provided

    Example without prefix or suffix:
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     'A': [1, 2, 3],
    ...     'B': [4, 5, 6],
    ...     'C': [7, 8, 9]
    ... })
    >>> old_names = ['A', 'B', 'C']
    >>> new_names = ['Column1', 'Column2', 'Column3']
    >>> df = rename_columns(df, old_names, new_names)
    >>> print(df)
       Column1  Column2  Column3
    0        1        4        7
    1        2        5        8
    2        3        6        9

    Example with prefix:
    >>> df = pd.DataFrame({
    ...     'A': [1, 2, 3],
    ...     'B': [4, 5, 6],
    ...     'C': [7, 8, 9]
    ... })
    >>> old_names = ['A', 'B', 'C']
    >>> new_names = ['Column1', 'Column2', 'Column3']
    >>> df = rename_columns(df, old_names, new_names, prefix='prefix_')
    >>> print(df)
       prefix_Column1  prefix_Column2  prefix_Column3
    0               1               4               7
    1               2               5               8
    2               3               6               9

    Example with removing prefix:
    >>> df = pd.DataFrame({
    ...     'prefix_A': [1, 2, 3],
    ...     'prefix_B': [4, 5, 6],
    ...     'prefix_C': [7, 8, 9]
    ... })
    >>> old_names = ['prefix_A', 'prefix_B', 'prefix_C']
    >>> df = rename_columns(df, old_names, remove_prefix='prefix_')
    >>> print(df)
       A  B  C
    0  1  4  7
    1  2  5  8
    2  3  6  9
    """
    # Check if old_names is provided
    if not old_names:
        raise ValueError("old_names must be provided")

    # If old_names or new_names are not list, convert them into list
    if not isinstance(old_names, list):
        old_names = [old_names]
    if new_names and not isinstance(new_names, list):
        new_names = [new_names]

    # If new_names is not provided, use old_names as new_names
    if not new_names:
        new_names = old_names

    # Remove prefix or suffix if provided
    if remove_prefix:
        new_names = [re.sub(f'^{remove_prefix}', '', name) for name in new_names]
    if remove_suffix:
        new_names = [re.sub(f'{remove_suffix}$', '', name) for name in new_names]

    # Add prefix or suffix if provided
    if prefix:
        new_names = [prefix + name for name in new_names]
    if suffix:
        new_names = [name + suffix for name in new_names]

    # Create a dictionary mapping old names to new names
    rename_dict = dict(zip(old_names, new_names))

    # Rename the columns
    df = df.rename(columns=rename_dict)

    return df






def move_column(df, col_to_move, pos='last', ref_col=None):
    """
    This function moves a column in a DataFrame to a specified position.

    Parameters:
    df (pd.DataFrame): DataFrame to modify
    col_to_move (str): Name of the column to move
    pos (str or int, optional): Position to move the column to. Can be 'first', 'last', 'before', 'after', or an integer.
        If 'before' or 'after', ref_col must be provided. Defaults to 'last'.
    ref_col (str, optional): Reference column for 'before' or 'after' positions. Not used for other positions.

    Returns:
    pd.DataFrame: Modified DataFrame
    """
    # Make a list of all columns in the DataFrame
    cols = df.columns.tolist()

    # Remove the column to be moved from the list
    cols.remove(col_to_move)

    # Check the desired position and adjust the list of columns accordingly
    if pos == 'first':
        # If 'first', add the column to the start of the list
        cols = [col_to_move] + cols
    elif pos == 'last':
        # If 'last' (or unspecified), add the column to the end of the list
        cols = cols + [col_to_move]
    elif pos == 'before' and ref_col:
        # If 'before' and a reference column is specified, find the index of the reference column
        # and insert the column to be moved before it
        idx = cols.index(ref_col)
        cols = cols[:idx] + [col_to_move] + cols[idx:]
    elif pos == 'after' and ref_col:
        # Similar to 'before', but insert the column to be moved after the reference column
        idx = cols.index(ref_col)
        cols = cols[:idx + 1] + [col_to_move] + cols[idx + 1:]
    elif isinstance(pos, int):
        # If an integer is given, insert the column to be moved at that position
        # (assuming that the position is 1-indexed as in Stata, hence the -1)
        cols = cols[:pos - 1] + [col_to_move] + cols[pos - 1:]

    # Create a new DataFrame with the columns in the desired order
    return df[cols]





def replace(df, column, new_value, condition):
    """
    Function to replicate Stata's replace functionality.

    Parameters:
    df: pandas DataFrame
    column: str, column name to be modified
    new_value: str or value, new value (could be a column name or a constant value, with optional 'n' notation for shift)
    condition: str, condition to be applied on the column

    Returns:
    pandas.DataFrame: Modified DataFrame with replaced values according to the condition
    """
    
    # Making a deep copy of the DataFrame to ensure the original DataFrame remains unchanged
    df = df.copy()

    # Function to translate 'n' notation to shifted column names
    def translate_n_to_shifted_col_names(condition):
        bracket_contents = re.findall(r'\[n([+-]?\d+)\]', condition)
        groups = re.findall(r'(\w+\[n[+-]?\d+\])', condition)
        shift_dict = {group: group.split('[')[0] + '_shifted_' + bracket_content.replace('-', 'm').replace('+', '')
                      for group, bracket_content in zip(groups, bracket_contents)}
        for group, shifted_col_name in shift_dict.items():
            condition = condition.replace(group, shifted_col_name)
        return condition, shift_dict

    df_condition = df.copy()
    condition_string, shift_dict = translate_n_to_shifted_col_names(condition)
    for original, shifted_col_name in shift_dict.items():
        col = original.split('[')[0]
        shift = -int(re.findall(r'\[n([+-]?\d+)\]', original)[0])  # Negate the shift to align with Python's shift behavior
        df_condition[shifted_col_name] = df[col].shift(shift)

    mask = df_condition.eval(condition_string)

    if isinstance(new_value, str) and '[n' in new_value:
        new_value_shift = -int(re.findall(r'\[n([+-]?\d+)\]', new_value)[0])  # Negate the shift to align with Python's shift behavior
        new_value = re.sub(r'\[n([+-]?\d+)\]', '', new_value)
        new_value = df[new_value].shift(new_value_shift)

    if isinstance(new_value, str) and new_value in df.columns:
        new_value = df[new_value]

    original_column = df[column].copy()
    df.loc[mask, column] = new_value
    replaced_count = (df[column] != original_column).sum()

    print(f'({replaced_count} real changes made)')

    return df




def how_is_this_not_a_duplicate(df, unique_cols, new_col_name='problematic_cols'):
    """
    Identify columns that differ between the rows for a given combination of identifiers.
    Overwrites the existing problematic_cols column if it exists.
    
    Parameters:
    df (DataFrame): Input DataFrame
    unique_cols (list of str or str): Columns that should uniquely identify a row
    new_col_name (str, optional): Name of the new column to be added. Default is 'problematic_cols'.
    
    Returns:
    DataFrame: DataFrame with an additional column, containing a list of columns preventing the row from being labeled a duplicate.
    
    Example:
    >>> df = pd.DataFrame({'ID': [1, 1], 'Name': ['Alice', 'Alice'], 'Age': [25, np.nan]})
    >>> how_is_this_not_a_duplicate(df, unique_cols='ID')
    """
    
    # Make sure unique_cols is a list
    if not isinstance(unique_cols, list):
        unique_cols = [unique_cols]
    
    # If the new column already exists, drop it
    if new_col_name in df.columns:
        df.drop(columns=[new_col_name], inplace=True)
    
    df = df.sort_values(by=unique_cols)
    df_unique_cols_no_nan = df[unique_cols].fillna('')

    duplicates = df_unique_cols_no_nan.duplicated(keep=False)
    result_df = df.copy()
    result_df[new_col_name] = ''
    
    for idx in df[duplicates].index.tolist():
        row = df.loc[idx]
        other_rows = df.loc[duplicates & (df_unique_cols_no_nan == df_unique_cols_no_nan.loc[idx]).all(axis=1)]
        other_rows = other_rows[other_rows.index != idx]
        
        if not other_rows.empty:
            # Check if a column has differing values, considering NaN to be the same as NaN
            cols_diff = ', '.join(
                col for col in df.columns 
                if (
                    (not pd.isna(row[col]) or not pd.isna(other_rows[col].iloc[0])) and 
                    (row[col] != other_rows[col].iloc[0])
                )
            )
            
            if cols_diff:
                result_df.at[idx, new_col_name] = cols_diff
    
    return result_df




def bysort_sequence(df, group_cols, new_col_name, sequence_type='_n'):
    
    """
    Function to generate a sequence number (_n) or the maximum number (_N) within each group of the specified columns.

    Parameters:
    df (pandas.DataFrame): The DataFrame to operate on.
    group_cols (list): The columns to sort and group by.
    new_col_name (str): The name of the new column that will hold the sequence or max number.
    sequence_type (str): The type of sequence, either '_n' for a sequence number or '_N' for the max number in a sequence.

    Returns:
    pandas.DataFrame: The DataFrame with the new column.
    """
    
    # Sort
    df = df.sort_values(group_cols)
    
    # Check the type of sequence required       
    if sequence_type == '_n':
        # If '_n' is specified, generate a sequence number for each group
        df[new_col_name] = df.groupby(group_cols).cumcount() + 1
    elif sequence_type == '_N':
        # If '_N' is specified, generate the maximum number in the sequence for each group
        df[new_col_name] = df.groupby(group_cols)[group_cols[-1]].transform('count')
    else:
        # If an invalid sequence_type is given, print an error message
        print("Invalid sequence_type. Choose either '_n' for a sequence number or '_N' for the max number in a sequence.")
    # Return the DataFrame with the new column
    return df







###############################################################################
def convert_to_units(row, length, unit, conversion_dict):
    if pd.isna(row[unit]):
        return 0
    else:
        return row[length] * conversion_dict[row[unit]]




def count_occurrences_with_offset(df, column, string_to_find, offset=1, inplace=False, new_column_name=None):
    """
    This function counts the occurrences of a given string in each row of a specified column in a dataframe, adds an offset, 
    and appends the results as a new column to the dataframe. Optionally, it can perform the operation in-place.
    
    Parameters:
    df (pd.DataFrame): The pandas dataframe to operate on.
    column (str): The column in the dataframe where the string is to be searched for.
    string_to_find (str): The string to search for in each row of the column.
    offset (int): The number to add to the count of occurrences. Defaults to 1.
    inplace (bool): If True, appends the results as a new column in the existing dataframe. 
                    If False, returns a new dataframe with the appended results. Defaults to False.
    new_column_name (str): The name of the new column that will hold the counts. If not specified, defaults to "{column}_count".

    Returns:
    df (pd.DataFrame): The dataframe with the added column of string occurrence counts (or the original dataframe if inplace=True).

    Example usage:
    >>> df = pd.DataFrame({'instruments': ['Euphonium; Trombone', 'Trumpet', 'Percussion; Euphonium; Clarinet']})
    >>> df_new = count_occurrences_with_offset(df, 'instruments', ';')
    >>> print(df_new)
                        instruments  instruments_count
    0           Euphonium; Trombone                  2
    1                      Trumpet                  1
    2  Percussion; Euphonium; Clarinet               3
    """

    # If no new column name specified, create one based on the searched column
    if not new_column_name:
        new_column_name = f"{column}_count"

    # Count occurrences of string_to_find in each row, add offset and store results in new column
    if inplace:
        df[new_column_name] = df[column].str.count(string_to_find) + offset
    else:
        df = df.copy()
        df[new_column_name] = df[column].str.count(string_to_find) + offset

    return df






def proper_case(df, column):
    """
    Convert the given pandas DataFrame column to proper case.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing the column to convert
    column (str): The column name to convert
    
    Returns:
    pandas.DataFrame: The DataFrame with the converted column
    
    Usage:
    >>> df = pd.DataFrame({"name": ["JASON'S HaT", None, "ANOTHER EXAMPLE"]})
    >>> proper_case(df, 'name')
                 name
    0      Jason's Hat
    1             None
    2  Another Example
    """
    def capitalize(text):
        words = text.split()
        new_words = []
        for word in words:
            word = word.lower()  # Convert to lowercase
            word = word.capitalize()  # Capitalize the first letter
            word = re.sub(r"('\w)", lambda m: m.group(1).lower(), word)  # Correct the internal apostrophe
            new_words.append(word)
        return ' '.join(new_words)
    
    # Apply the capitalize function to each cell in the DataFrame column
    df[column] = df[column].apply(lambda x: capitalize(str(x)) if pd.notna(x) else x)
    return df



def df_slice(df, start_pct, end_pct):
    """
    Get a slice of a DataFrame based on a percentage range.
    
    Parameters:
    - df (DataFrame): The DataFrame to slice.
    - start_pct (float): The starting percentage of the DataFrame slice.
    - end_pct (float): The ending percentage of the DataFrame slice.

    Returns:
    - DataFrame: A DataFrame slice based on the percentage range.
    """
    total_length = len(df)
    start_index = int(total_length * start_pct)
    end_index = int(total_length * end_pct)
    print(f"Dataframe sliced to start at {start_index} and end at {end_index}.")
    return df.iloc[start_index:end_index]





def add_other_row(data, num_rows, new_row_name="Other", sort_column=None, sort_descending=True):
    """
    Modifies the input DataFrame or Series by appending an 'Other' row or item.
    
    For DataFrames, optionally sorts by a specified column before processing, with an option
    to sort in descending order.
    For Series, sorts by values if `sort_column` is truthy, considering `sort_descending` for order.
    
    Keeps the first `num_rows` rows/items as they are (after sorting, if applied),
    sums the remaining rows/items, and appends the sum as a new row/item named `new_row_name`.
    
    Parameters:
    - data: The original pandas DataFrame or Series.
    - num_rows: The number of rows/items to keep from the start.
    - new_row_name: The name of the new row/item to add with the summed values. Defaults to 'Other'.
    - sort_column: Optional; for DataFrames, the column name to sort by before processing. For Series,
      any truthy value triggers sorting by values. Defaults to None.
    - sort_descending: Optional; boolean indicating if sorting should be in descending order. Defaults to True.
    
    Returns:
    - The modified DataFrame or Series with the new 'Other' row/item.
    
    Sample Usage:
    >>> df = pd.DataFrame({'A': [5, 1, 3, 2, 4], 'B': [1, 5, 3, 4, 2]})
    >>> add_other_row(df, 3, sort_column='A', sort_descending=True)
    >>> s = pd.Series([5, 1, 3, 2, 4])
    >>> add_other_row(s, 3, sort_column=True)  # Here, sort_column just needs to be truthy for a Series.
    """
    if isinstance(data, pd.Series):
        if sort_column:  # If sort_column is truthy, sort the Series.
            data = data.sort_values(ascending=not sort_descending)
        top_items = data.iloc[:num_rows]
        others_sum = data.iloc[num_rows:].sum()
        # Use pd.concat to combine the top items with the 'Other' sum
        result = pd.concat([top_items, pd.Series([others_sum], index=[new_row_name])])
    elif isinstance(data, pd.DataFrame):
        if sort_column:
            data = data.sort_values(by=sort_column, ascending=not sort_descending)
        top_rows = data.iloc[:num_rows, :]
        others_sum = data.iloc[num_rows:, :].sum(numeric_only=True)
        others_row = pd.DataFrame([others_sum], index=[new_row_name])
        # Use pd.concat to append 'Other' row to the DataFrame
        result = pd.concat([top_rows, others_row])
    else:
        raise ValueError("Input must be a pandas DataFrame or Series")
    
    return result




def add_total_row(data, total_row_name='Total'):
    """
    Adds a 'Total' row to a pandas Series or DataFrame.
    
    For a DataFrame, it sums all rows for each column and appends this as a new row named `total_row_name`.
    For a Series, it sums all items and appends this sum as a new item with the index `total_row_name`.
    
    Parameters:
    - data: The original pandas DataFrame or Series.
    - total_row_name: The name of the new row/item to add with the total values. Default is 'Total'.
    
    Returns:
    - The modified DataFrame or Series with the new 'Total' row/item.
    
    Sample Usage:
    >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    >>> add_total_row(df)
    >>> s = pd.Series([1, 2, 3])
    >>> add_total_row(s)
    """
    if isinstance(data, pd.Series):
        total_sum = data.sum()
        # Use pd.concat to append 'Total' item to the Series
        result = pd.concat([data, pd.Series([total_sum], index=[total_row_name])])
    elif isinstance(data, pd.DataFrame):
        total_sum = data.sum(numeric_only=True)
        # Create a DataFrame for the 'Total' row to maintain dtype consistency
        total_row = pd.DataFrame([total_sum], index=[total_row_name])
        # Use pd.concat to append 'Total' row to the DataFrame
        result = pd.concat([data, total_row], ignore_index=False)
    else:
        raise ValueError("Input must be a pandas DataFrame or Series")
    
    return result


def move_row(df, row_to_move, pos='last', ref_row=None):
    """
    Move a row in a DataFrame to a specified position without altering the original index.

    Parameters:
    df (pd.DataFrame): DataFrame to modify.
    row_to_move: Index label of the row to move. Can be int or string based on DataFrame's index.
    pos (str or int, optional): Position to move the row to. Can be 'first', 'last', 'before', 'after', or an integer
        indicating the position in the index list. If 'before' or 'after', ref_row must be provided. Defaults to 'last'.
    ref_row: Reference row index label for 'before' or 'after' positions. Required if pos is 'before' or 'after'.

    Returns:
    pd.DataFrame: DataFrame with the row moved to the specified position, maintaining original index.
    """
    # Ensure handling of both integer-based and label-based indices
    if isinstance(row_to_move, int) and isinstance(df.index, pd.RangeIndex):
        row_label = df.index[row_to_move]
    else:
        row_label = row_to_move
    
    # Extract the row to be moved
    row = df.loc[[row_label]]
    
    # Drop the row from its current position
    df_copy = df.drop(row_label)
    
    if pos == 'first':
        # Concatenate the row at the beginning
        new_df = pd.concat([row, df_copy], sort=False)
    elif pos == 'last':
        # Concatenate the row at the end
        new_df = pd.concat([df_copy, row], sort=False)
    elif (pos == 'before' or pos == 'after') and ref_row is not None:
        # Find the insertion point for 'before' or 'after'
        all_rows = df_copy.index.tolist()
        ref_index = all_rows.index(ref_row)
        if pos == 'before':
            new_index = all_rows[:ref_index] + [row_label] + all_rows[ref_index:]
        else:  # pos == 'after'
            new_index = all_rows[:ref_index + 1] + [row_label] + all_rows[ref_index + 1:]
        new_df = df.reindex(new_index)
    elif isinstance(pos, int):
        # Handle integer position
        all_rows = df_copy.index.tolist()
        all_rows.insert(pos, row_label)
        new_df = df.reindex(all_rows)
    else:
        new_df = df  # If position not recognized, return original DataFrame
    
    return new_df


