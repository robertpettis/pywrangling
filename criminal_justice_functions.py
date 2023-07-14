# -*- coding: utf-8 -*-
"""
This library is for packages for criminal justice analysis. 
"""

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
