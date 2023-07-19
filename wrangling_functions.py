"""
This library provides a set of functions designed to simplify common data
wrangling tasks.

It includes functions for renaming columns, moving columns, and replacing
values in a DataFrame based on certain conditions.
"""

import pandas as pd  # Main library for data manipulation
import numpy as np  # Library for numerical operations
import re  # Regular expressions library for string manipulation
import inspect



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







def simple_replace(df, var, value, where):
    """
    Function to mimic Stata's replace command.

    Parameters:
    df (DataFrame): The DataFrame to operate on.
    var (str): The variable (column) to replace values in.
    condition_str (str): A string that represents a condition to be evaluated on the DataFrame.
    value: The value to replace with.

    Returns:
    DataFrame: The DataFrame with values replaced.
    """
    df.loc[df.query(where).index, var] = value
    return df



def replace(df, var, value, where='', flag_var=False , print_result = True):
    """
    Function to mimic Stata's replace command.

    Parameters:
    df (DataFrame): The DataFrame to operate on.
    var (str): The variable (column) to replace values in.
    where (str): A string that represents a condition to be evaluated on the DataFrame.
    value: The value to replace with. This can be a constant value, a column name, or a string representing a relative reference to a value in a column.

    Returns:
    DataFrame: The DataFrame with values replaced.
    """
    
    # TODO: Does not currently handle or statements, isna, notna, len
    # TODO: flag_var and print_result can probably be removed.
    
    
    # Reset index of the DataFrame to ensure that the row-wise operation runs correctly.
    df.reset_index(drop=True, inplace=True)

    def evaluate_value(row):
        # If value is a string that looks like a relative reference, e.g., 'col_name[n-1]'
        if isinstance(value, str) and re.match(r'\w+\[n[+-]\d+\]', value):
            # Extract column name and index shift from the relative reference
            col_name, index_shift = re.match(r'(\w+)\[n([+-]\d+)\]', value).groups()
            index_shift = int(index_shift)
            # If the shifted index is within the DataFrame's index range, get the value from the specified column at the shifted index
            if 0 <= row.name + index_shift < len(df):
                return df.loc[row.name + index_shift, col_name]
            else:
                # If the shifted index is out of range, return NaN
                return np.nan
        # If value is a string that looks like a column name
        elif isinstance(value, str) and re.match(r'\w+', value):
            col_name = re.match(r'(\w+)', value).group(1)
            # If the column name is in the DataFrame's columns, get the value from the specified column at the current index
            if col_name in df.columns:
                return row[col_name]
            else:
                # If the column name is not in the DataFrame's columns, treat the value as a constant value
                return value.strip('"')
        else:
            # If value is not a string, treat it as a constant value
            return value

    def evaluate_where(row):
        # If the where condition is specified
        if where:
            where_evaluated = where
            # Split the where condition into individual conditions by '&'
            conditions = where_evaluated.split(' & ')
            results = []
            for condition in conditions:
                # For each condition, replace relative references with actual values from the DataFrame
                for match in re.findall(r'\w+\[n[+-]\d+\]', condition):
                    col_name, index_shift = re.match(r'(\w+)\[n([+-]\d+)\]', match).groups()
                    index_shift = int(index_shift)
                    # If the shifted index is within the DataFrame's index range, get the value from the specified column at the shifted index
                    if 0 <= row.name + index_shift < len(df):
                        value = df.loc[row.name + index_shift, col_name]
                        if value is not None:
                            condition = condition.replace(match, repr(value))
                        else:
                            # If the value is None, replace the relative reference with NaN
                            condition = condition.replace(match, repr(np.nan))
                    else:
                        # If the shifted index is out of range, replace the relative reference with NaN
                        condition = condition.replace(match, repr(np.nan))
                # Replace column names in the condition with actual values from the DataFrame
                for match in re.findall(r'\w+', condition):
                    if "[" not in match and "]" not in match and '"' not in condition and match in df.columns:
                        value = row[match]
                        if value is not None:
                            condition = condition.replace(match, repr(value))
                # If the condition is empty or only contains spaces, replace it with 'True'
                if not condition or not condition.strip():
                    condition = 'True'
                # Evaluate the condition and add the result to the results list
                try:
                    results.append(eval(condition, {'__builtins__': None}, row.to_dict()))
                except TypeError:
                    results.append(False)
            # If all conditions are True, return True. Otherwise, return False.
            return all(results)
        else:
            # If the where condition is not specified, return True for all rows.
            return True

    df_copy = df.copy()
    # Evaluate the value for each row
    new_values = df_copy.apply(evaluate_value, axis=1)
    # Evaluate the where condition for each row
    where_mask = df_copy.apply(evaluate_where, axis=1)
    
    # Replace the values in the specified column where the where condition is True
    df_copy.loc[where_mask, var] = new_values
    
    # Print the number of rows that were replaced
    num_rows_replaced = where_mask.sum()
    if print_result == True:
        print(f'Replaced values in {num_rows_replaced} rows.')
    
    return df_copy






def how_is_this_not_a_duplicate(df, unique_cols, new_col_name='problematic_cols'):
    """
    This function takes a dataframe and a list of columns that should uniquely identify a row.
    It returns all columns that differ between the rows for that combination of identifiers.

    Parameters:
    df (DataFrame): Input DataFrame
    unique_cols (list): List of columns that should uniquely identify a row
    new_col_name (str): Name of the new column to be added

    Returns:
    DataFrame: DataFrame with an additional column 'problematic_cols' which is 
    a list of the columns preventing the line from being labeled a duplicate.
    """
    # Sort dataframe by unique_cols to ensure all rows with same unique_cols values are grouped together
    df = df.sort_values(by=unique_cols)

    # Identify duplicate rows based on unique_cols
    duplicates = df.duplicated(subset=unique_cols, keep=False)

    # Group by unique_cols and find columns where number of unique values is greater than 1, but only for duplicate rows
    problematic_cols = df[duplicates].groupby(unique_cols).apply(lambda x: x.nunique(dropna=False) > 1)

    # Create a new column in df which is a list of the problematic columns, but only for duplicate rows
    df.loc[duplicates, new_col_name] = df[duplicates].apply(lambda row: ', '.join(problematic_cols.loc[tuple(row[col] if not pd.isna(row[col]) else np.nan for col in unique_cols)].index[problematic_cols.loc[tuple(row[col] if not pd.isna(row[col]) else np.nan for col in unique_cols)]].tolist()), axis=1)

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


###############################################################################
def get_variable_names(*types):
    """
    Retrieve the names of variables of specified types that would be included in Spyder's variable explorer.
    Exclude strings starting with '_' and specific aliases for libraries.

    Parameters:
        *types (type): Variable types to filter. Accepts multiple arguments.

    Returns:
        list: List of variable names matching the specified types.

    Example:
        # Assume the following variables exist in the current scope
        x = 10
        y = 'hello'
        z = [1, 2, 3]

        # Retrieve variable names of type int
        int_vars = get_variable_names(int)
        # Output: ['x']

        # Retrieve variable names of type int and str
        int_str_vars = get_variable_names(int, str)
        # Output: ['x', 'y']

        # Retrieve variable names of type list and dict
        list_dict_vars = get_variable_names(list, dict)
        # Output: ['z']
    """
    # Get the caller's frame
    frame = inspect.currentframe().f_back

    # Get the global variables dictionary
    global_vars = frame.f_globals

    # Aliases to exclude
    aliases_to_exclude = ['pd', 'np', 'timedelta', 'dt']

    # Filter variables by type and exclusion criteria
    result = []
    for var_name, var in global_vars.items():
        if (
            isinstance(var, types)
            and not var_name.startswith('_')
            and var_name not in aliases_to_exclude
        ):
            result.append(var_name)

    return result



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
