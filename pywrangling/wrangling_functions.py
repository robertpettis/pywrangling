"""
This library provides a set of functions designed to simplify common data
wrangling tasks.

It includes functions for renaming columns, moving columns, and replacing
values in a DataFrame based on certain conditions.
"""

import pandas as pd  # Main library for data manipulation
import numpy as np  # Library for numerical operations
import re  # Regular expressions library for string manipulation




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

    The function supports 'n' notation to indicate shift operation in pandas. For example, 'B[n-1]' is translated to 'B.shift(-1)'.
    The 'n' notation supports both positive and negative integers.

    Example:
    Suppose we have a DataFrame 'df' with columns 'A', 'B', 'C', and 'D'.
    We want to replace values in column 'A' where B equals 'mouse' or the previous row of B equals 'dog' and the next row of C is greater than -0.4.
    We want to replace these values with the value in column 'B' from two rows ahead. Here's how we can do it:

    condition = "(B == 'mouse') | (B[n-1] == 'dog') & (C[n+1] > -0.4)"
    new_value = 'B[n+2]'
    df_modified = replace(df, 'A', new_value, condition)
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
        shift = int(re.findall(r'\[n([+-]?\d+)\]', original)[0])
        df_condition[shifted_col_name] = df[col].shift(shift)

    mask = df_condition.eval(condition_string)

    if isinstance(new_value, str) and '[n' in new_value:
        new_value_shift = -int(re.findall(r'\[n([+-]?\d+)\]', new_value)[0])
        new_value = re.sub(r'\[n([+-]?\d+)\]', '', new_value)
        new_value = df[new_value].shift(new_value_shift)

    if isinstance(new_value, str) and new_value in df.columns:
        new_value = df[new_value]

    original_column = df[column].copy()
    df.loc[mask, column] = new_value
    replaced_count = (df[column] != original_column).sum()

    print(f'({replaced_count} real changes made)')

    return df





def how_is_this_not_a_duplicate(df, unique_cols, new_col_name='problematic_cols', nan_placeholder='NaN_placeholder'):
    """
    This function takes a dataframe and a list of columns that should uniquely identify a row.
    It returns all columns that differ between the rows for that combination of identifiers.

    Parameters:
    df (DataFrame): Input DataFrame
    unique_cols (list): List of columns that should uniquely identify a row
    new_col_name (str): Name of the new column to be added
    nan_placeholder (str): Placeholder value for NaN in unique columns

    Returns:
    DataFrame: DataFrame with an additional column 'problematic_cols' which is 
    a list of the columns preventing the line from being labeled a duplicate.
    """
    # Sort dataframe by unique_cols to ensure all rows with same unique_cols values are grouped together
    df = df.sort_values(by=unique_cols)

    # Replace NaN values with the specified placeholder in the unique_cols
    df_unique_cols_no_nan = df[unique_cols].fillna(nan_placeholder)

    # Identify duplicate rows based on unique_cols without NaN values
    duplicates = df_unique_cols_no_nan.duplicated(keep=False)

    # Group by unique_cols without NaN values and find columns where number of unique values is greater than 1
    problematic_cols = df[duplicates].groupby(df_unique_cols_no_nan.loc[duplicates].to_records(index=False)).apply(lambda x: x.nunique(dropna=False) > 1)

    # Create a new column in df which is a list of the problematic columns, but only for duplicate rows
    df.loc[duplicates, new_col_name] = df[duplicates].apply(lambda row: ', '.join(problematic_cols.loc[tuple(row[col] if not pd.isna(row[col]) else nan_placeholder for col in unique_cols)].index[problematic_cols.loc[tuple(row[col] if not pd.isna(row[col]) else nan_placeholder for col in unique_cols)]].tolist()), axis=1)

    return df






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
    >>> df = pd.DataFrame({"name": ["JASON'S HaT"]})
    >>> proper_case(df, 'name')
           name
    0  Jason's Hat
    """
    df[column] = df[column].apply(lambda x: re.sub(r"(\b\w+)", lambda m: m.group(1).capitalize(), str(x)))
    return df











