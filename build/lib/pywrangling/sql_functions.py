# -*- coding: utf-8 -*-
"""
Created on Fri Oct  6 13:00:21 2023

@author: Owner
"""

# %% Module Imports
import mariadb  # MariaDB connector for Python
import pandas as pd  # Data manipulation library
from pathlib import Path
from tqdm import tqdm  # Progress bar library

# %% Custom Functions

def map_dtype(dtype, column=None, df=None):
    """
    Map pandas dtype to SQL data types.

    Parameters:
    dtype (numpy.dtype): The numpy data type
    column (str, optional): The column name. Defaults to None.
    df (DataFrame, optional): The DataFrame. Defaults to None.

    Returns:
    str: Corresponding SQL data type
    """
    if pd.api.types.is_integer_dtype(dtype):
        if dtype == "int8" or dtype == "int16":
            return "SMALLINT"
        elif dtype == "int32":
            return "INT"
        else:  # np.int64
            return "BIGINT"
    elif pd.api.types.is_float_dtype(dtype):
        if dtype == "float16" or dtype == "float32":
            return "REAL"
        else:  # np.float64
            return "FLOAT"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BIT"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "DATETIME"
    else:  # default to NVARCHAR
        if column and df is not None:
            max_length = df[column].astype(str).str.len().max()
            return f"NVARCHAR({max_length})"
        else:
            return "NVARCHAR(255)"


def generate_create_table_sql(table_name, df):
    """
    Generate SQL command for creating a new table.

    Parameters:
    table_name (str): Name of the table to be created
    df (DataFrame): DataFrame containing the data

    Returns:
    str: SQL command for creating the table
    """
    column_defs = [f"`{col}` {map_dtype(dtype, col, df)}" for col, dtype in zip(df.columns, df.dtypes)]
    column_defs_str = ', '.join(column_defs)
    create_table_sql = f"CREATE TABLE `{table_name}` ({column_defs_str})"
    return create_table_sql





# Function to generate SQL for batch insert
def generate_batch_insert_sql(table_name, columns, num_rows):
    columns_str = ', '.join([f"`{col}`" for col in columns])
    values_str = ', '.join(['(' + ', '.join(['%s'] * len(columns)) + ')' for _ in range(num_rows)])
    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES {values_str}"
    return insert_sql





















