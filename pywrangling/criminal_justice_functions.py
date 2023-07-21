# -*- coding: utf-8 -*-
"""
This library is for packages for criminal justice analysis. 
"""
from tqdm import tqdm
import pandas as pd

###############################################################################
def create_top_charge(df, statute_col, total_charges_col, convicted_col, incarceration_days_col, total_fine_col):
    """
    Creates a new column 'top_charge' in the dataframe.

    Parameters:
    df (pd.DataFrame): Input dataframe.
    statute_col (str): Column in df containing the charges.
    total_charges_col (str): Column in df containing total number of charges.
    convicted_col (str): Column in df containing conviction status (1 if convicted, else 0).
    incarceration_days_col (str): Column in df containing total incarceration time for each charge.
    fine_col (str): Column in df containing total fine amount for each charge.

    Returns:
    df (pd.DataFrame): Dataframe with a new column 'top_charge'.
    """
    import numpy as np

    # Ensure the statutes column is of type string
    df[statute_col] = df[statute_col].astype(str)

    # Filter out rows where total_charges == 1 and convicted == 1
    single_charge_df = df[(df[total_charges_col] == 1) & (df[convicted_col] == 1)].copy()

    # Compute a ranking for each charge based on incarceration time and fine, with higher values indicating higher ranks
    charge_ranks = single_charge_df.groupby(statute_col)[[incarceration_days_col, total_fine_col]].mean().sort_values(by=[incarceration_days_col, total_fine_col], ascending=False).rank(method='min', ascending=False)

    # Define helper function to get top charge
    def get_top_charge(charges):
        # Handle non-string values gracefully
        if not isinstance(charges, str):
            return charges
        charges = charges.split(';')
        ranks = [charge_ranks.loc[charge].sum() if charge in charge_ranks.index else np.inf for charge in charges]
        return charges[np.argmin(ranks)]

    # Apply get_top_charge function to each row
    df['top_charge'] = df[statute_col].apply(get_top_charge)

    return df



# Recidivism Function ########################################################
def recidivism(df, date_col, person_id_col, years, only_convictions=False, conviction_col=None, conviction_value=None):
    """
    Calculate recidivism based on a given number of years and conviction status.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe containing the data.
    date_col : str
        The name of the column containing the dates.
    person_id_col : str
        The name of the column containing the person IDs.
    years : int
        The number of years to consider for recidivism.
    only_convictions : bool, optional
        Whether to only consider rows where the person was convicted.
    conviction_col : str, optional
        The name of the column containing the conviction status.
        Required if only_convictions is True.
    conviction_value : str, optional
        The value in the conviction column that indicates a conviction.
        Required if only_convictions is True.

    Returns
    -------
    df : pandas.DataFrame
        The original dataframe with an additional column `recidivism` indicating recidivism status.

    Usage
    -----
    df = recidivism(df, 'date', 'person_id', 5, only_convictions=True, conviction_col='convicted', conviction_value='Yes')
    
    
    NOTE: The exact semantics of what the function does is that it checks for prior offenses in the past n years. 
    If it is set to have only_convictions=True, then it filters the prior rows such that they onlk
    """
    # Sort by person_id and date
    df = df.sort_values([person_id_col, date_col])

    # Initialize recidivism column to 0
    df['recidivism'] = 0

    # Loop over rows with a progress bar from tqdm
    for i, row in tqdm(df.iterrows(), total=df.shape[0]):
        # Get rows for the same person within given number of years before current date
        mask = ((df[person_id_col] == row[person_id_col]) & 
                (df[date_col] < row[date_col]) & 
                (df[date_col] >= row[date_col] - pd.DateOffset(years=years)))

        # If only considering convictions, further filter the rows
        if only_convictions:
            mask &= (df[conviction_col] == conviction_value)

        # If there are any such rows, set recidivism to 1 for current row
        if df[mask].shape[0] > 0:
            df.at[i, 'recidivism'] = 1

    return df
