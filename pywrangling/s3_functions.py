# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 14:51:31 2023

@author: Owner
"""

import boto3  # AWS SDK for Python to interact with Amazon S3 and other AWS services
import os  # Provides functions to interact with the operating system
import random  # Provides functions to generate random numbers
import warnings  # Used to issue warning messages
from tqdm import tqdm  # Progress bar library
import pandas as pd 
import tkinter as tk



"""The main use for this is to collect the names of files already crawled so that an inturrupted crawl doesnt start from scratch."""

def s3_glob(s3_client, bucket_name, subfolder_path, extensions):
    """
    Returns a DataFrame with names of all files with given extensions or no extension from the specified S3 bucket and subfolder.
    
    Parameters:
    s3_client (boto3.client): The S3 client.
    bucket_name (str): The S3 bucket name.
    subfolder_path (str): The path to the subfolder to check.
    extensions (list): A list of file extensions to look for, including an empty string '' for files without extensions.

    Returns:
    DataFrame: A DataFrame containing the filenames.

    Example:
    filenames_df = s3_glob(s3_client, 'sicuro-sanbernardino', 'Data/Crawl/2023-08-14/', ['.html', ''])
    """
    # Paginator to handle more than 1000 files
    paginator = s3_client.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name, 'Prefix': subfolder_path}
    page_iterator = paginator.paginate(**operation_parameters)

    filenames = []
    found_subfolder = False
    
    for page in page_iterator:
        if 'Contents' in page:  # Check if the 'Contents' key exists
            found_subfolder = True  # Subfolder exists if there are contents
            for content in page['Contents']:
                key = content['Key']
                file_name = key.split('/')[-1]

                # Check if the file matches one of the extensions or has no extension
                if any(file_name.endswith(ext) for ext in extensions) or ('.' not in file_name and '' in extensions):
                    filenames.append(file_name)

    if not found_subfolder:
        warnings.warn(f"Subfolder path {subfolder_path} not found in bucket {bucket_name}")

    filenames_df = pd.DataFrame({'filename': filenames})

    return filenames_df



def download_files_from_s3(s3_client, bucket_name, subfolder_path, extensions, save_path='.', sample_size=None):
    """
    Download files with specified extensions from a given S3 bucket and subfolder, with an option to download a random sample.

    Parameters:
    s3_client (boto3.client): The S3 client.
    bucket_name (str): The S3 bucket name.
    subfolder_path (str): The path to the subfolder within the bucket.
    extensions (list): A list of file extensions to look for, including an empty string '' for files without extensions.
    save_path (str, optional): Path to the local folder where files will be saved.
    sample_size (int, optional): Number of files to randomly sample, None for all files.

    Returns:
    list: List of downloaded file paths.
    """

    # Ensure the save path exists
    os.makedirs(save_path, exist_ok=True)

    # Paginator to handle more than 1000 files
    paginator = s3_client.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name, 'Prefix': subfolder_path}
    page_iterator = paginator.paginate(**operation_parameters)

    file_keys = []
    found_subfolder = False

    for page in page_iterator:
        if 'Contents' in page:  # Check if the 'Contents' key exists
            found_subfolder = True  # Subfolder exists if there are contents
            for content in page['Contents']:
                key = content['Key']
                file_name = key.split('/')[-1]

                # Check if the file matches one of the extensions or has no extension
                if any(file_name.endswith(ext) for ext in extensions) or ('.' not in file_name and '' in extensions):
                    file_keys.append(key)

    if not found_subfolder:
        warnings.warn(f"Subfolder path {subfolder_path} not found in bucket {bucket_name}")

    # Randomly sample the files if sample_size is specified
    if sample_size is not None:
        file_keys = random.sample(file_keys, sample_size)

    # Define a function to sanitize filenames
    def sanitize_filename(filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    downloaded_files = []
    # Iterate through file keys with a progress bar
    for file_key in tqdm(file_keys, desc='Downloading files', unit='file'):
        file_name = os.path.basename(file_key)
        file_name = sanitize_filename(file_name)  # Sanitize the filename
        local_path = os.path.join(save_path, file_name)
        s3_client.download_file(bucket_name, file_key, local_path)
        downloaded_files.append(local_path)

    return downloaded_files


def download_file_from_s3(s3_instance, bucket_name, subfolder_path, file_name, destination_directory):
    """
    Download a file from an S3 bucket to a specified local directory.

    Parameters:
    s3_instance (boto3.client): An instance of boto3 S3 client.
    bucket_name (str): Name of the S3 bucket.
    subfolder_path (str): Path of the subfolder inside the bucket.
    file_name (str): Name of the file to be downloaded.
    destination_directory (str): Local directory to which the file will be downloaded.

    Returns:
    str: Path of the downloaded file or an error message.

    Example:
    s3 = boto3.client('s3')
    download_file_from_s3(s3, 'mybucket', 'data/subfolder', 'myfile.csv', '/local/path')
    """

    # Check for missing values
    if not all([bucket_name, subfolder_path, file_name, destination_directory]):
        return "Missing one or more required parameters."

    # Construct the full file path in the S3 bucket
    full_file_path = os.path.join(subfolder_path, file_name)

    # Construct the full path for the destination file
    destination_file_path = os.path.join(destination_directory, file_name)

    try:
        # Download the file
        s3_instance.download_file(bucket_name, full_file_path, destination_file_path)
        return destination_file_path
    except Exception as e:
        return f"An error occurred: {e}"







def get_aws_credentials():
    """
    Create a GUI window to get AWS access and secret keys from the user.

    :return: aws_access_key (str), aws_secret_key (str)
        The AWS access and secret keys entered by the user.

    Example usage:
    aws_access_key, aws_secret_key = get_aws_credentials()
    print(f"AWS Access Key: {aws_access_key}\nAWS Secret Key: {aws_secret_key}")
    """

    # Creating main window
    root = tk.Tk()
    root.title("Enter AWS Credentials")

    # Labels
    tk.Label(root, text="Enter AWS Access Key:").grid(row=0)
    tk.Label(root, text="Enter AWS Secret Access Key:").grid(row=1)

    # Entry fields
    access_key_entry = tk.Entry(root, show="*")
    secret_key_entry = tk.Entry(root, show="*")
    access_key_entry.grid(row=0, column=1)
    secret_key_entry.grid(row=1, column=1)

    # Dictionary to store values
    aws_keys = {}

    # Function to retrieve values and close window
    def retrieve_values():
        aws_keys['access_key'] = access_key_entry.get()
        aws_keys['secret_key'] = secret_key_entry.get()
        root.quit()

    # Button to submit
    tk.Button(root, text="Submit", command=retrieve_values).grid(row=2, columnspan=2)

    # Start GUI loop
    root.mainloop()
    root.destroy()

    return aws_keys['access_key'], aws_keys['secret_key']






def s3_filter_processed_files(dataframe, s3_client, paginator, filename_col, bucket, subdirectory):
    """
    Drops rows from the DataFrame where the filename already exists in the S3 bucket.

    Parameters:
    - dataframe (pandas.DataFrame): DataFrame containing the filenames.
    - filename_col (str): Name of the column in the DataFrame that contains the filenames.
    - bucket (str): The name of the S3 bucket.
    - subdirectory (str): The subdirectory in the S3 bucket.

    Returns:
    - pandas.DataFrame: The filtered DataFrame.

    Example usage:
    filtered_df = filter_processed_files(df, 'FILENAME', 'my-bucket', 'my/subdirectory')
    """

    prefix = f"{subdirectory}/" if subdirectory else ""

    # Set to store filenames found in S3
    existing_files = set()

    # Iterate over pages of objects in S3
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            filename = obj['Key'].split('/')[-1]
            existing_files.add(filename)

    # Drop rows where the filename exists in S3
    return dataframe[~dataframe[filename_col].isin(existing_files)]









