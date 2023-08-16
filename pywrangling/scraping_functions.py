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
    
    
    
    
    
    
def filter_crawled_data(df, s3_client, bucket_name, subfolder_path, variables, separator=None):
    """
    Filters the DataFrame by removing rows corresponding to files found in the specified S3 subfolder and errors/ subfolder.
    
    Parameters:
    df (DataFrame): The DataFrame to filter.
    s3_client (boto3.client): The S3 client.
    bucket_name (str): The S3 bucket name.
    subfolder_path (str): The path to the subfolder to check.
    variables (list): A list of variable names corresponding to filename components.
    separator (str, optional): A separator used if multiple variables are in the filename.

    Returns:
    DataFrame: The filtered DataFrame.

    Example:
    # Single variable usage
    filtered_df = filter_crawled_data(df, s3_client, 'sicuro-sanbernardino', 'Data/Crawl/2023-08-14/', ['case_number'])

    # Multiple variable usage
    filtered_df = filter_crawled_data(df, s3_client, 'sicuro-sanbernardino', 'Data/Crawl/2023-08-14/', ['case_number', 'party_id'], '-')
    """
    # Paginator to handle more than 1000 files
    paginator = s3_client.get_paginator('list_objects_v2')
    operation_parameters = {'Bucket': bucket_name, 'Prefix': subfolder_path}
    page_iterator = paginator.paginate(**operation_parameters)

    # Set to store unique identifiers from filenames
    file_ids = set()

    for page in page_iterator:
        for content in page['Contents']:
            key = content['Key']
            if key.endswith('.html') and not key.endswith('timeout/'):
                # Extract the identifier(s) from the filename
                filename = key.split('/')[-1].replace('.html', '')
                ids = filename.split(separator) if separator else [filename]

                # Map the variables and ids
                file_id = tuple(df[var].astype(str) for var, id_ in zip(variables, ids))
                file_ids.add(file_id)

    # Drop rows from the DataFrame that match the found identifiers
    filter_condition = tuple(df[var].astype(str) for var in variables)
    filtered_df = df[~df[filter_condition].apply(tuple, axis=1).isin(file_ids)]

    return filtered_df

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    