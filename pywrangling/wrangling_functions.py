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
from typing import Callable, Literal


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






# def move_column(df, col_to_move, pos='last', ref_col=None):
#     """
#     This function moves a column in a DataFrame to a specified position.

#     Parameters:
#     df (pd.DataFrame): DataFrame to modify
#     col_to_move (str): Name of the column to move
#     pos (str or int, optional): Position to move the column to. Can be 'first', 'last', 'before', 'after', or an integer.
#         If 'before' or 'after', ref_col must be provided. Defaults to 'last'.
#     ref_col (str, optional): Reference column for 'before' or 'after' positions. Not used for other positions.

#     Returns:
#     pd.DataFrame: Modified DataFrame
#     """
#     # Make a list of all columns in the DataFrame
#     cols = df.columns.tolist()

#     # Remove the column to be moved from the list
#     cols.remove(col_to_move)

#     # Check the desired position and adjust the list of columns accordingly
#     if pos == 'first':
#         # If 'first', add the column to the start of the list
#         cols = [col_to_move] + cols
#     elif pos == 'last':
#         # If 'last' (or unspecified), add the column to the end of the list
#         cols = cols + [col_to_move]
#     elif pos == 'before' and ref_col:
#         # If 'before' and a reference column is specified, find the index of the reference column
#         # and insert the column to be moved before it
#         idx = cols.index(ref_col)
#         cols = cols[:idx] + [col_to_move] + cols[idx:]
#     elif pos == 'after' and ref_col:
#         # Similar to 'before', but insert the column to be moved after the reference column
#         idx = cols.index(ref_col)
#         cols = cols[:idx + 1] + [col_to_move] + cols[idx + 1:]
#     elif isinstance(pos, int):
#         # If an integer is given, insert the column to be moved at that position
#         # (assuming that the position is 1-indexed as in Stata, hence the -1)
#         cols = cols[:pos - 1] + [col_to_move] + cols[pos - 1:]

#     # Create a new DataFrame with the columns in the desired order
#     return df[cols]

def move_column(df, columns_to_move, pos='last', ref_col=None, return_renamed=False):
    """
    Moves one or more columns to a specified position in a DataFrame, ensuring no duplicate column names.

    Parameters:
    df (pd.DataFrame): DataFrame to modify.
    columns_to_move (str or list of str): Name or list of names of the columns to move.
    pos (str or int, optional): Position to move the column(s) to. Can be:
        - 'first': move to the beginning
        - 'last': move to the end (default)
        - 'before': move before another column (requires ref_col)
        - 'after': move after another column (requires ref_col)
        - int: 1-based index like Stata (1 = first)
    ref_col (str, optional): Reference column used with 'before' or 'after'.
    return_renamed (bool, optional): If True, returns (df, renamed_dict).

    Returns:
    pd.DataFrame or (pd.DataFrame, dict): Reordered DataFrame, with optional renamed column log.
    """
    from collections import Counter

    # Normalize single string input
    if isinstance(columns_to_move, str):
        columns_to_move = [columns_to_move]

    # Deduplicate columns
    counts = Counter()
    new_cols = []
    renamed = {}

    for col in df.columns:
        counts[col] += 1
        if counts[col] == 1:
            new_cols.append(col)
        else:
            new_name = f"{col}.{counts[col]-1}"
            new_cols.append(new_name)
            renamed[col] = renamed.get(col, []) + [new_name]

    if renamed:
        print("⚠️  Duplicate column names found and renamed:")
        for base, new_versions in renamed.items():
            print(f"   • '{base}' → {', '.join(new_versions)}")

    df.columns = new_cols
    cols = df.columns.tolist()

    # Keep only existing columns from the requested list
    columns_to_move = [col for col in columns_to_move if col in cols]

    # Remove columns to move from current order
    cols = [col for col in cols if col not in columns_to_move]

    # Insert at desired location
    if pos == 'first':
        cols = columns_to_move + cols
    elif pos == 'last':
        cols = cols + columns_to_move
    elif pos == 'before':
        if not ref_col or ref_col not in cols:
            raise ValueError(f"Reference column '{ref_col}' not found for 'before'.")
        idx = cols.index(ref_col)
        cols = cols[:idx] + columns_to_move + cols[idx:]
    elif pos == 'after':
        if not ref_col or ref_col not in cols:
            raise ValueError(f"Reference column '{ref_col}' not found for 'after'.")
        idx = cols.index(ref_col)
        cols = cols[:idx + 1] + columns_to_move + cols[idx + 1:]
    elif isinstance(pos, int):
        idx = max(0, min(pos - 1, len(cols)))
        cols = cols[:idx] + columns_to_move + cols[idx:]
    else:
        raise ValueError(f"Invalid 'pos' argument: {pos}")

    result = df.loc[:, cols]
    return (result, renamed) if return_renamed else result




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

    # Handling string comparisons separately
    eval_condition = re.sub(r"\s*==\s*'(\w+)'\s*", r" == '\1' ", condition_string)
    mask = df_condition.eval(eval_condition)
    
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





def proper_case(df, column, strip_spaces=True):
    """
    Convert the given pandas DataFrame column to proper case.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing the column to convert
    column (str): The column name to convert
    strip_spaces (bool, optional): Whether to strip leading and trailing spaces (default is True)
    
    Returns:
    pandas.DataFrame: The DataFrame with the converted column
    
    Usage:
    >>> df = pd.DataFrame({"name": [" JASON'S HaT ", None, " ANOTHER EXAMPLE  "]})
    >>> proper_case(df, 'name')
                 name
    0      Jason's Hat
    1             None
    2  Another Example
    """
    def capitalize(text):
        text = text.strip() if strip_spaces else text  # Strip spaces if enabled
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




def find_columns_with_substring(df, substring, case_sensitive=True):
    """
    Returns a list of column names where at least one value in the column contains the specified substring.

    Args:
    df (pd.DataFrame): The DataFrame to search through.
    substring (str): The substring to search for in the column values.

    Returns:
    list: A list of column names where values contain the substring.
    """
    # Adjust case sensitivity in the search
    if case_sensitive:
        matching_columns = [col for col in df.columns if df[col].astype(str).str.contains(substring).any()]
    else:
        matching_columns = [col for col in df.columns if df[col].astype(str).str.contains(substring, case=False).any()]
    return matching_columns




def drop_horizontal_duplicates(
    df: pd.DataFrame,
    *,
    keep: Literal["first", "last"] = "first",
    normalise: Callable[[object], object] | None = None,
) -> pd.DataFrame:
    """
    Replace values that appear more than once *within the same row* by
    ``pd.NA`` (leaving only the copy indicated by *keep*).

    Parameters
    ----------
    df : DataFrame
        The frame to clean.
    keep : {'first', 'last'}, default 'first'
        Which duplicate to keep in each row.
    normalise : callable, optional
        Function applied to every cell before comparison.
        Handy when you want equality to ignore case/spacing, e.g.::

            normalise=lambda x: str(x).strip().lower() if pd.notna(x) else x

    Returns
    -------
    DataFrame
        A copy of *df* with horizontal duplicates masked out.

    Examples
    --------
    >>> import pandas as pd, numpy as np
    >>> df = pd.DataFrame({
    ...     "A": ["foo", "foo", "bar"],
    ...     "B": ["foo", "baz", "bar"],
    ...     "C": ["foo", "qux", "bar"],
    ... })
    >>> df
         A    B    C
    0  foo  foo  foo
    1  foo  baz  qux
    2  bar  bar  bar

    Keep the first occurrence in each row (default) ▶
    >>> drop_horizontal_duplicates(df)
         A    B    C
    0  foo  <NA> <NA>
    1  foo  baz  qux
    2  bar  <NA> <NA>

    Keep the last occurrence instead ▶
    >>> drop_horizontal_duplicates(df, keep="last")
         A    B    C
    0  <NA> <NA> foo
    1  foo  baz  qux
    2  <NA> <NA> bar
    """
    # Work on a copy so the original is untouched
    out = df.copy()

    def _row_dedup(row: pd.Series) -> pd.Series:
        vals = row if normalise is None else row.map(normalise)
        mask = vals.duplicated(keep=keep)
        return row.mask(mask, pd.NA)

    return out.apply(_row_dedup, axis=1)





def safe_left_merge(
        left: pd.DataFrame,
        right: pd.DataFrame,
        on,                          # cols or list of cols
        *,                           # force kwargs below to be named
        validate='one_to_one',       # or 'one_to_many', etc.
        error_on_collision=True,    # whether to error if columns collide
        msg: str = None,
        **kwargs
    ) -> pd.DataFrame:
    """
    Left-merge that asserts row-count is preserved.

    By default:
    - If a collision would happen, allow it but restore original left columns.
      (The left-hand columns stay unchanged, right-hand colliding columns are dropped.)

    If `error_on_collision=True`:
    - Raise an error if any columns outside the `on` keys would collide.

    Parameters
    ----------
    left, right : DataFrame
        The two DataFrames to merge.
    on : str or list of str
        Column(s) to join on.
    validate : str, optional
        Pandas built-in integrity check.
    error_on_collision : bool, default False
        If True, raise ValueError if a collision would happen.
    msg : str, optional
        Custom message for assertion error.
    kwargs : keyword arguments
        Any other arguments to pass to `pd.merge`.

    Returns
    -------
    merged : DataFrame
        The merged DataFrame.

    Examples
    --------
    >>> import pandas as pd
    >>> import pywrangling.wrangling_functions as wf
    >>>
    >>> left = pd.DataFrame({'id': [1, 2], 'val': ['a', 'b']})
    >>> right = pd.DataFrame({'id': [1, 2], 'val': ['c', 'd'], 'other': [10, 20]})
    >>>
    >>> # Default behavior: collisions allowed, left wins
    >>> merged = wf.safe_left_merge(left, right, on='id')
    >>> print(merged)
       id val  other
    0   1   a     10
    1   2   b     20
    >>>
    >>> # Force strict behavior: collision raises an error
    >>> merged = wf.safe_left_merge(left, right, on='id', error_on_collision=True)
    Traceback (most recent call last):
        ...
    ValueError: Cannot merge: these columns would collide and require suffixes: ['val']
    """
    # Determine join keys
    on_cols = on if isinstance(on, list) else [on]
    left_nonkey = set(left.columns) - set(on_cols)
    right_nonkey = set(right.columns) - set(on_cols)

    # Identify collisions
    collisions = left_nonkey & right_nonkey
    if collisions and error_on_collision:
        raise ValueError(
            f"Cannot merge: these columns would collide and require suffixes: {sorted(collisions)}"
        )

    before = len(left)
    merged = pd.merge(
        left,
        right,
        how='left',
        on=on,
        validate=validate,
        suffixes=('_x', '_y'),  # allow suffixing temporarily
        **kwargs
    )
    after = len(merged)

    # If collisions occurred, restore left columns
    if collisions:
        for col in collisions:
            merged.rename(columns={f"{col}_x": col}, inplace=True)
            merged.drop(columns=[f"{col}_y"], inplace=True)

    assert after == before, (
        msg or
        f"Row count changed after merge on {on}: {before:,} → {after:,}"
    )
    return merged



def column_values_contain(df: pd.DataFrame, value, case_sensitive=False):
    """
    Returns a list of column names in the DataFrame that contain the specified value.
    
    Parameters:
    - df (pd.DataFrame): The DataFrame to search.
    - value: The value to search for.
    - case_sensitive (bool): Whether the match should be case-sensitive. Defaults to True.
    
    Returns:
    - List[str]: A list of column names containing the value.
    """
    result = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_string_dtype(series):
            if case_sensitive and series.str.contains(str(value), na=False).any():
                result.append(col)
            elif not case_sensitive and series.str.contains(str(value), case=False, na=False).any():
                result.append(col)
        else:
            if (series == value).any():
                result.append(col)
    return result



def column_name_contains(df: pd.DataFrame, value: str, case_sensitive: bool = False):
    """
    Returns a list of column names that contain the given value.

    Parameters:
    - df: The DataFrame to check.
    - value: Substring to look for in column names.
    - case_sensitive: If False (default), performs case-insensitive match.

    Returns:
    - List of column names that contain the value.
    """
    if not case_sensitive:
        value = value.lower()
        return [col for col in df.columns if value in col.lower()]
    else:
        return [col for col in df.columns if value in col]




# ##############################################################################
# 🧩🧩🧩 METHODS SECTION 🧩🧩🧩
# ##############################################################################





"""
🚨🚨🚨
If a future version of pandas introduces its own method called values_and_percent, this monkey-patched version could conflict with it, potentially leading to unexpected results.

Same is true with any other monkey-patched method.
🚨🚨🚨
"""

def values_and_percent(self, decimals=2, include_total=False, separator_char='-'):
    """
    Calculate value counts and percentages of the Series.

    Parameters:
        decimals (int): Decimal places for percentages.
        include_total (bool): Whether to print total row.
        separator_char (str): Character for separator line.

    Returns:
        pd.DataFrame or None
    """
    import io

    counts = self.value_counts(dropna=False)
    percentages = (counts / len(self) * 100).round(decimals)
    df = pd.DataFrame({'Count': counts, 'Percentage': percentages})

    if include_total:
        # Capture the formatted table
        buffer = io.StringIO()
        df.to_string(buf=buffer)
        table_str = buffer.getvalue()
        lines = table_str.splitlines()

        # Print the table
        for line in lines:
            print(line)

        # Separator
        width = len(lines[0])
        print(separator_char * width)

        # Locate column positions
        header = lines[0]
        count_start = header.index("Count")
        pct_start = header.index("Percentage")

        # Format total line to match exact spacing
        total_label = ""
        total_count = str(counts.sum())
        total_pct = f"{percentages.sum():.{decimals}f}"

        total_line = (
            f"{total_label:<{count_start}}"
            f"{total_count:>{pct_start - count_start-2}}"
            f"{total_pct:>{width - pct_start+2}}"
        )

        print(total_line)
        return None

    return df



# Attach to pandas Series
pd.Series.values_and_percent = values_and_percent



