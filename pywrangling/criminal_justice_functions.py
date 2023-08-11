# -*- coding: utf-8 -*-
"""
This library is for packages for criminal justice analysis. 
"""
from tqdm import tqdm
import pandas as pd
import openai
import time








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
    """
    import numpy as np
    from tqdm import tqdm

    # Sort by person_id and date
    df = df.sort_values([person_id_col, date_col])

    # Initialize recidivism column to NaN
    df['recidivism'] = np.nan

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

    # Determine the earliest and latest dates we can accurately calculate recidivism for
    earliest_date = df[date_col].min() + pd.DateOffset(years=years)
    latest_date = df[date_col].max() - pd.DateOffset(years=years)

    # Set recidivism to NaN for rows outside the date range we can accurately calculate recidivism for
    df.loc[(df[date_col] < earliest_date) | (df[date_col] > latest_date), 'recidivism'] = np.nan

    return df







# Use chat GPT to populate a column based on another column and a prompt. #####
def count_semicolons(s):
    return s.count(";")

def populate_responses(api_key, initial_prompt, model_name, dataframe, input_col, 
                       batch_size=10, max_tokens=500, max_retries=5, number_of_responses=2):

    openai.api_key = api_key  # Set the API key

    unique_values = dataframe[input_col].unique()
    num_values = len(unique_values)

    output_df = pd.DataFrame(columns=[input_col, 'Response'])  # Empty DataFrame to store results

    for i in tqdm(range(0, num_values, batch_size), total=num_values // batch_size, desc="Processing entries"):
        batch = unique_values[i:i + batch_size]
        prompt = " ; ".join(batch)

        retries = 0
        while retries < max_retries:
            completion = openai.ChatCompletion.create(
                model=model_name,
                messages=[
                    {'role': 'system', 'content': 'You are a helpful assistant with vast legal knowledge.'},
                    {'role': 'user', 'content': initial_prompt},
                    {'role': 'assistant', 'content': 'Yes'},
                    {'role': 'user', 'content': f'{prompt}'}
                ],
                max_tokens=max_tokens,
                n=number_of_responses,
                stop=None,
                temperature=0.5,
            )

            valid_response = None
            for choice in completion.choices:
                response = choice.message.content
                prompt_count = count_semicolons(prompt)
                response_count = count_semicolons(response)
                if prompt_count == response_count:
                    valid_response = response
                    retries = max_retries 
                    break  
            else:
                retries += 1
                time.sleep(21)
                continue

        # Expand the prompts and responses
        prompts = prompt.split(' ; ')
        responses = valid_response.split(' ; ')
        temp_df = pd.DataFrame({input_col: prompts, 'Response': responses})
        output_df = pd.concat([output_df, temp_df], ignore_index=True)
        time.sleep(21)

    # Drop duplicates to ensure unique prompt-response pairs
    output_df = output_df.drop_duplicates(subset=[input_col, 'Response'])

    return output_df









































