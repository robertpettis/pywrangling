# -*- coding: utf-8 -*-
"""
Updates needed:
    1) The dates arent right
    2) The graph is avg file modifications per day which is fine
"""

import boto3  # AWS SDK for Python to interact with Amazon S3 and other AWS services
import os  # Provides functions to interact with the operating system
import random  # Provides functions to generate random numbers
import warnings  # Used to issue warning messages
from tqdm import tqdm  # Progress bar library
import pandas as pd 
import tkinter as tk
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil.tz import tzlocal

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


def download_file_from_s3(s3_client, bucket_name, subfolder_path, file_name, destination_directory):
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
        s3_client.download_file(bucket_name, full_file_path, destination_file_path)
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






def s3_filter_processed_files(s3_client, dataframe,  paginator, filename_col, bucket, subdirectory):
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





# def avg_speed(s3, bucket_name, prefix, file_extension):
#     """
#     Plots the average number of files modified per day and prints the average per hour,
#     adjusting for the local time zone of the machine where the script is run.
    
    
#     # Example usage of the function
#     # Initialize S3 client
#     s3 = boto3.client(
#         's3',
#         aws_access_key_id='id',
#         aws_secret_access_key='key'
#     )
    
#     # Set up the paginator for the s3 client
#     paginator = s3.get_paginator('list_objects_v2')
         
#     bucket_name = 'my-bucket'
#     prefix = 'Data/HTML/'  # include trailing slash if specifying a subdirectory
#     file_extension = '.html'  # example file extension
    
#     avg_speed(s3, bucket_name, prefix, file_extension)    
        
    
#     """
#     # List objects in the specified bucket and prefix
#     response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

#     # Check if the request returned any contents
#     if 'Contents' not in response:
#         print("No objects found.")
#         return

#     # Filter files by the specified extension and extract last modified times
#     files = [obj for obj in response['Contents'] if obj['Key'].endswith(file_extension)]
#     times = [obj['LastModified'] for obj in files]

#     # Convert to pandas DataFrame
#     df = pd.DataFrame(times, columns=['LastModified'])

#     # Convert 'LastModified' to UTC and then to local time zone
#     df['LastModified'] = pd.to_datetime(df['LastModified'], utc=True)
#     df['LastModified'] = df['LastModified'].dt.tz_convert(tzlocal())
#     df['LastModified'] = df['LastModified'].dt.tz_localize(None)

#     # Daily average calculations
#     df['Date'] = df['LastModified'].dt.date
#     daily_counts = df.groupby('Date').size()
#     daily_average = daily_counts.mean()

#     # Hourly average per day calculations
#     df['Hour'] = df['LastModified'].dt.hour
#     hourly_avg_per_day = df.groupby(['Date', 'Hour']).size().groupby('Date').mean()

#     # Print daily and hourly grouped data
#     print(f"""
#           Daily Counts:
              
#               {daily_counts}
              
#           Hourly Average By Day
          
#               {hourly_avg_per_day}
          
#           """)

#     # Plot for daily average
#     plt.figure(figsize=(12, 6))
#     daily_counts.plot(kind='line', title='Average File Modifications Per Day', marker='o', markersize=5)

#     # Tilt the x-axis labels and set title font size
#     plt.xticks(rotation=45)
#     plt.title('Average File Modifications Per Day', fontsize=16)  # Adjust font size as needed
    
#     # Highlight today's point if it exists in the data
#     today = datetime.now().date()
#     if today in daily_counts.index:
#         plt.scatter(today, daily_counts.loc[today], color='red', s=100, label='Today')  # s is the size of the marker
    
#     # Set y-axis label position and title
#     plt.ylabel('Average Count', rotation=0, ha='right', fontsize=12)  # Rotate label, right-align, adjust font size
    
#     # Move the y-axis label to the top on the left side
#     ax = plt.gca()
#     ax.yaxis.set_label_coords(0.1, 1.02)
    
#     # Add a horizontal line for the overall average
#     plt.axhline(y=daily_average, color='green', linestyle='--', linewidth=2, label='Overall Avg')
    
#     # Add legend and grid
#     plt.legend()
#     plt.grid(True)
    
#     plt.show()

#     # Plot for hourly average per day
#     plt.figure(figsize=(12, 6))  # New figure for the hourly average per day plot
#     hourly_avg_per_day.plot(kind='bar', title='Average File Modifications Per Hour Per Day')
#     plt.xlabel('Date', fontsize=12)
#     plt.ylabel('Average Hourly Count', rotation=0, ha='right', fontsize=12)
#     plt.xticks(rotation=45)
#     plt.show()
    
#     # Print overall average per hour and per day
#     print(f"Overall average modifications per hour: {hourly_avg_per_day.mean()}")
#     print(f"Overall average modifications per day: {daily_average}")



def upload_file_to_s3(s3_client, bucket_name, subfolder_path, local_file_path):
    """
    Uploads a file from the local file system to a specified path in an S3 bucket.

    Parameters:
    s3_client (boto3.client): The S3 client.
    bucket_name (str): The name of the S3 bucket.
    subfolder_path (str): The path to the subfolder within the bucket where the file will be stored.
    local_file_path (str): The path to the file on the local file system.

    Returns:
    str: The S3 path of the uploaded file or an error message.

    Example:
    s3 = boto3.client('s3', aws_access_key_id='YOUR_ACCESS_KEY', aws_secret_access_key='YOUR_SECRET_KEY')
    upload_file_to_s3(s3, 'my-bucket', 'my/subfolder/', '/path/to/myfile.txt')
    """

    # Extract the file name from the local file path
    file_name = os.path.basename(local_file_path)

    # Ensure the subfolder path ends with a '/'
    if not subfolder_path.endswith('/'):
        subfolder_path += '/'

    # Construct the full S3 path (key) for the file
    s3_path = f"{subfolder_path}{file_name}"

    try:
        # Perform the upload
        s3_client.upload_file(local_file_path, bucket_name, s3_path)
        return f"File uploaded successfully to: s3://{bucket_name}/{s3_path}"
    except Exception as e:
        return f"An error occurred during upload: {e}"

