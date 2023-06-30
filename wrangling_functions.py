"""This library will make my life easier by including functions for regular 
tasks."""

import re
import numpy as np 


def rename_columns(df, old_names, new_names):
    """
    Rename columns in a DataFrame.

    Parameters:
    df (pd.DataFrame): DataFrame to modify
    old_names (list of str): List of old column names
    new_names (list of str): List of new column names

    Returns:
    pd.DataFrame: Modified DataFrame with renamed columns
    """
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
    cols = df.columns.tolist()
    cols.remove(col_to_move)

    if pos == 'first':
        cols = [col_to_move] + cols
    elif pos == 'last':
        cols = cols + [col_to_move]
    elif pos == 'before' and ref_col:
        idx = cols.index(ref_col)
        cols = cols[:idx] + [col_to_move] + cols[idx:]
    elif pos == 'after' and ref_col:
        idx = cols.index(ref_col)
        cols = cols[:idx + 1] + [col_to_move] + cols[idx + 1:]
    elif isinstance(pos, int):
        cols = cols[:pos - 1] + [col_to_move] + cols[pos - 1:]

    return df[cols]






# def replace(df, var, value, where):
#     """
#     Function to mimic Stata's replace command.

#     Parameters:
#     df (DataFrame): The DataFrame to operate on.
#     var (str): The variable (column) to replace values in.
#     condition_str (str): A string that represents a condition to be evaluated on the DataFrame.
#     value: The value to replace with.

#     Returns:
#     DataFrame: The DataFrame with values replaced.
#     """
#     df.loc[df.query(where).index, var] = value
#     return df



def replace(df, var, value, where=''):
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

    def evaluate_value(row):
        if isinstance(value, str) and re.match(r'\w+\[n[+-]\d+\]', value):
            col_name, index_shift = re.match(r'(\w+)\[n([+-]\d+)\]', value).groups()
            index_shift = int(index_shift)
            if 0 <= row.name + index_shift < len(df):
                return df.loc[row.name + index_shift, col_name]
            else:
                return np.nan
        elif isinstance(value, str) and re.match(r'\w+', value):
            col_name = re.match(r'(\w+)', value).group(1)
            if col_name in df.columns:
                return row[col_name]
            else:
                return value.strip('"')
        else:
            return value

    def evaluate_where(row):
        if where:
            where_evaluated = where
            for match in re.findall(r'epros\["\w+"\]\[n[+-]\d+\]', where):
                col_name, index_shift = re.match(r'epros\["(\w+)"\]\[n([+-]\d+)\]', match).groups()
                index_shift = int(index_shift)
                if 0 <= row.name + index_shift < len(df):
                    value = df.loc[row.name + index_shift, col_name]
                    if value is not None:
                        where_evaluated = where_evaluated.replace(match, repr(value))
                    else:
                        where_evaluated = where_evaluated.replace(match, repr(np.nan))
                else:
                    where_evaluated = where_evaluated.replace(match, repr(np.nan))
            for match in re.findall(r'epros\["\w+"\]', where):
                col_name = re.match(r'epros\["(\w+)"\]', match).group(1)
                value = row[col_name]
                if value is not None:
                    where_evaluated = where_evaluated.replace(match, repr(value))
            if not where_evaluated or not where_evaluated.strip():
                where_evaluated = 'True'
            try:
                return eval(where_evaluated, {'__builtins__': None}, row.to_dict())
            except TypeError:
                return False
        else:
            return False



    df_copy = df.copy()
    new_values = df_copy.apply(evaluate_value, axis=1)
    where_mask = df_copy.apply(evaluate_where, axis=1)
    df_copy.loc[where_mask, var] = new_values
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
    DataFrame: DataFrame with an additional column 'problematic_cols' which is a list of the problematic columns.
    """
    # Identify duplicate rows based on unique_cols
    duplicates = df.duplicated(subset=unique_cols, keep=False)

    # Group by unique_cols and find columns where number of unique values is greater than 1, but only for duplicate rows
    problematic_cols = df[duplicates].groupby(unique_cols).apply(lambda x: x.nunique() > 1)

    # Create a new column in df which is a list of the problematic columns, but only for duplicate rows
    df.loc[duplicates, new_col_name] = df[duplicates].apply(lambda row: problematic_cols.loc[tuple(row[col] for col in unique_cols)].index[problematic_cols.loc[tuple(row[col] for col in unique_cols)]].tolist(), axis=1)

    return df



