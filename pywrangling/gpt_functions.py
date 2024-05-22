# -*- coding: utf-8 -*-
"""
Created on Tue May 21 17:47:22 2024

@author: Owner
"""
from tqdm import tqdm
import pandas as pd
import openai
import time


def populate_responses(api_key, initial_prompt, model_name, dataframe, input_col, max_tokens=500, max_retries=5, number_of_responses=2):

    openai.api_key = api_key  # Set the API key

    unique_values = dataframe[input_col].unique()
    num_values = len(unique_values)

    output_df = pd.DataFrame(columns=[input_col, 'Response'])  # Empty DataFrame to store results

    for value in tqdm(unique_values, total=num_values, desc="Processing entries"):
        retries = 0
        while retries < max_retries:
            try:
                completion = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {'role': 'system', 'content': 'You are a helpful assistant with vast legal knowledge.'},
                        {'role': 'user', 'content': initial_prompt},
                        {'role': 'assistant', 'content': 'Yes'},
                        {'role': 'user', 'content': f'{value}'}
                    ],
                    max_tokens=max_tokens,
                    n=number_of_responses,
                    stop=None,
                    temperature=0.5,
                )

                valid_response = completion.choices[0].message.content if completion.choices else None
                if valid_response:
                    temp_df = pd.DataFrame({input_col: [value], 'Response': [valid_response]})
                    output_df = pd.concat([output_df, temp_df], ignore_index=True)
                    break  # Exit the retry loop if we get a valid response
            except openai.error.OpenAIError as e:
                if "ServiceUnavailableError" in str(e):
                    print("Server unavailable. Retrying after a longer pause...")
                    time.sleep(60)  # Sleep for 60 seconds before retrying
                    retries += 1
            else:
                retries += 1
                time.sleep(21)

    return output_df

