"""
These functions are designed to add utility to web scraping work.
"""
import time


# Selenium Packages
from selenium import webdriver  # Selenium WebDriver for browser automation
from selenium.webdriver.chrome.options import Options  # Chrome options for customization
from selenium.webdriver.common.by import By  # Locating elements using different strategies
from selenium.webdriver.support.ui import WebDriverWait  # Waiting for elements to load
from selenium.webdriver.support import expected_conditions as EC  # Expected conditions for waiting
from selenium.webdriver.common.keys import Keys  # Keys for keyboard actions
from selenium.common.exceptions import NoSuchElementException  # Exception for element not found
from selenium.webdriver.chrome.service import Service  # ChromeDriver service
from selenium.webdriver.common.alert import Alert #Handling some alert errors
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import TimeoutException

import boto3 
import pandas as pd
import warnings

def find_and_highlight(element):
    """
    Highlights a web element on a webpage.

    This function is used for web scraping. It temporarily changes the style of a web element to make it visually stand out.
    The function assumes that the element is part of a Selenium WebDriver browser instance.

    Parameters:
    element (selenium.webdriver.remote.webelement.WebElement): The web element to be highlighted.

    Returns:
    selenium.webdriver.remote.webelement.WebElement: The same web element that was passed in.

    Example:
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    driver = webdriver.Firefox()
    driver.get('http://www.python.org')
    elem = driver.find_element(By.NAME, 'q')  # find the search box
    find_and_highlight(elem)  # highlight the search box
    """
    # Get the parent browser instance
    browser = element._parent

    # Define a function to apply a style to the element
    def apply_style(s):
        browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, s)

    # Save the element's original style
    original_style = element.get_attribute('style')

    # Apply the highlight style
    apply_style("background: yellow; border: 2px solid red;")

    # Pause for a moment to let the highlight be seen
    time.sleep(.3)

    # Revert to the original style
    apply_style(original_style)

    # Return the element
    return element







# Initialize a browser with basic settings
def initialize_browser(chromepath):
    # Set Chrome options for full screen
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    # Provide the path to the chromedriver executable
    service = Service(executable_path=chromepath)
    driver = webdriver.Chrome(service=service,options=chrome_options)
    
    return driver


# A basic credential entering code. 
# A potential update would be to add an argument for a wait 
def enter_credentials(driver, username, password, 
                      username_locator_type, username_locator_value, 
                      password_locator_type, password_locator_value):
    """
    Enter credentials into a web form.

    Parameters:
    - driver: The selenium WebDriver object.
    - username: The user's username.
    - password: The user's password.
    - username_locator_type: Type of locator for username (e.g., 'id', 'xpath', 'css selector', etc.)
    - username_locator_value: The value of the locator for the username input field.
    - password_locator_type: Type of locator for password.
    - password_locator_value: The value of the locator for the password input field.

    Example usage:
    enter_credentials(driver, 'my_username', 'my_password', 'xpath', '//input[@name="user"]', 'id', 'password')
    """

    # Map locator types to their corresponding selenium By attributes
    locator_type_map = {
        'id': By.ID,
        'xpath': By.XPATH,
        'css selector': By.CSS_SELECTOR,
        'name': By.NAME,
        'class name': By.CLASS_NAME,
        'tag name': By.TAG_NAME,
        'link text': By.LINK_TEXT,
        'partial link text': By.PARTIAL_LINK_TEXT
    }

    # Send username
    user_elem = find_and_highlight(driver.find_element(locator_type_map[username_locator_type], username_locator_value))
    user_elem.clear()  # Clear any existing values
    user_elem.send_keys(username)  # Enter username
        
    # Send password
    pass_elem = find_and_highlight(driver.find_element(locator_type_map[password_locator_type], password_locator_value))
    pass_elem.clear()  # Clear any existing values
    pass_elem.send_keys(password)  # Enter password

    # Submit the form
    pass_elem.submit()
    
    
    
    

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

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    