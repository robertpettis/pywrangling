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


import pandas as pd
import warnings
import random



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
def enter_credentials(driver, username, password, 
                      username_locator_type, username_locator_value, 
                      password_locator_type, password_locator_value,
                      timeout=10):
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
    - timeout: The maximum time to wait (in seconds) for the elements to be loaded.

    Example usage:
    enter_credentials(driver, 'my_username', 'my_password', 'xpath', '//input[@name="user"]', 'id', 'password')
    """

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

    # Wait for the username field to be present
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((locator_type_map[username_locator_type], username_locator_value))
    )
    user_elem = find_and_highlight(driver.find_element(locator_type_map[username_locator_type], username_locator_value))
    user_elem.clear()  # Clear any existing values
    user_elem.send_keys(username)  # Enter username

    # Wait for the password field to be present
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((locator_type_map[password_locator_type], password_locator_value))
    )
    pass_elem = find_and_highlight(driver.find_element(locator_type_map[password_locator_type], password_locator_value))
    pass_elem.clear()  # Clear any existing values
    pass_elem.send_keys(password)  # Enter password

    # Submit the form
    pass_elem.submit()
    
    print("Credentials successfully entered.")
    
    

    
    
    
def get_ids(driver, modify_page=False, return_df=True):
    # Initialize an empty dataframe to store the IDs and colors
    df = pd.DataFrame(columns=['ID', 'Color'])
    
    # Get all elements that have an 'id' attribute
    elements_with_ids = driver.find_elements(By.XPATH, "//*[@id]")
    
    # Create a list to store element IDs
    element_ids = []
    
    # Loop to get element IDs
    for element in elements_with_ids:
        element_ids.append(element.get_attribute('id'))
    
    # Loop through IDs to either modify the page, generate a DataFrame, or both
    for element_id in element_ids:
        random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))  # Generate a random color in hex format
        
        if return_df:
            # Append the ID and color to the DataFrame
            df = pd.concat([df, pd.DataFrame({'ID': [element_id], 'Color': [random_color]})], ignore_index=True)
        
        if modify_page:
            # Inject JavaScript to modify the page
            js_code = f"""
                var elem = document.getElementById('{element_id}');
                if (elem) {{
                    elem.innerHTML += '<div style="font-size: 24px; z-index: 9999;">ID = {element_id}</div>';
                    elem.style.backgroundColor = '{random_color}';
                }}
            """
            driver.execute_script(js_code)
    
    if return_df:
        return df





    
    
    
    
    
    
    
    
    
    