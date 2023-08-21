# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 14:51:31 2023

@author: Owner
"""

import boto3  # AWS SDK for Python to interact with Amazon S3 and other AWS services
import os  # Provides functions to interact with the operating system
import random  # Provides functions to generate random numbers
import pandas as pd  # Data analysis library to handle data frames
import warnings  # Used to issue warning messages



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

    Example:
    downloaded_files = download_files_from_s3(s3_client, 'sicuro-sanbernardino', 'Data/Crawl/2023-08-14/', ['.csv', ''], '/path/to/save', sample_size=100)
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

    def sanitize_filename(filename):
        # Replace or remove any characters that might be invalid in Windows filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    downloaded_files = []
    for file_key in file_keys:
        file_name = os.path.basename(file_key)
        file_name = sanitize_filename(file_name)  # Sanitize the filename
        local_path = os.path.join(save_path, file_name)
        s3_client.download_file(bucket_name, file_key, local_path)
        downloaded_files.append(local_path)

    return downloaded_files

























