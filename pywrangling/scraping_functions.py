"""
These functions are designed to add utility to web scraping work.
"""
# %% Importing Packages/Libraries

# Standard Libraries
import time  # Time-related functions
import warnings  # Warnings control
import random  # Generate random numbers

# Data Manipulation Libraries
import pandas as pd  # Data manipulation and analysis

# Selenium Packages for WebDriver
from selenium import webdriver  # Selenium WebDriver for browser automation

# Selenium Packages for Options and Services
from selenium.webdriver.chrome.options import Options  # Chrome options for customization
from selenium.webdriver.chrome.service import Service  # ChromeDriver service
from selenium.webdriver import Chrome  # WebDriver implementation for Chrome


# Selenium Packages for Element Location
from selenium.webdriver.common.by import By  # Locating elements using different strategies

# Selenium Packages for Waiting and Expected Conditions
from selenium.webdriver.support.ui import WebDriverWait  # Waiting for elements to load
from selenium.webdriver.support import expected_conditions as EC  # Expected conditions for waiting

# Selenium Packages for Keyboard Actions
from selenium.webdriver.common.keys import Keys  # Keys for keyboard actions

# Selenium Packages for Exception Handling
from selenium.common.exceptions import NoSuchElementException  # Exception for element not found
from selenium.common.exceptions import NoAlertPresentException  # Exception for no alert present
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, StaleElementReferenceException

# Selenium Packages for Alerts
from selenium.webdriver.common.alert import Alert  # Handling some alert errors

from selenium.webdriver.support.ui import Select



import json

import time
import jwt
from datetime import datetime, timedelta


# %% Functions

def find_and_highlight(element, wait_time=10, background_color="yellow", border_color="red"):
    """
    Highlights a web element on a webpage.

    This function is used for web scraping. It temporarily changes the style of a web element to make it visually stand out.
    The function assumes that the element is part of a Selenium WebDriver browser instance.

    Parameters:
    - element (selenium.webdriver.remote.webelement.WebElement): The web element to be highlighted.
    - wait_time (int, optional): Maximum time to wait for the element to become visible. Defaults to 10 seconds.
    - background_color (str, optional): The background color to use for highlighting. Defaults to yellow.
    - border_color (str, optional): The border color to use for highlighting. Defaults to red.

    Returns:
    - selenium.webdriver.remote.webelement.WebElement: The same web element that was passed in.

    Example:
    ```python
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    chromepath = "C:\\Users\\YourUsername\\path\\to\\chromedriver.exe"
    driver = initialize_browser(chromepath)
    driver.get('http://www.python.org')
    elem = driver.find_element(By.NAME, 'q')  # find the search box
    find_and_highlight(elem, background_color="green", border_color="blue")  # highlight the search box with custom colors
    ```
    """
    
    # Wait until the element is present and visible
    browser = element._parent
    WebDriverWait(browser, wait_time).until(EC.visibility_of(element))
    
    # Define a function to apply a style to the element
    def apply_style(s):
        browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, s)

    # Save the element's original style
    original_style = element.get_attribute('style')

    # Apply the highlight style
    highlight_style = f"background: {background_color}; border: 2px solid {border_color};"
    apply_style(highlight_style)

    # Pause for a moment to let the highlight be seen
    time.sleep(.3)

    # Revert to the original style
    apply_style(original_style)

    # Return the element
    return element



# %%
def initialize_browser(chromepath, extension_path=None, additional_options=None, experimental_options=None):
    """
    Initialize a Selenium WebDriver Chrome browser with specified options.
    
    Parameters:
    - chromepath (str): The file path to the ChromeDriver executable.
    - extension_path (str, optional): The file path to the Chrome extension (.crx file).
    - additional_options (list, optional): A list of additional Chrome options to set.
    - experimental_options (dict, optional): A dictionary of experimental options to set.
    
    Returns:
    - driver (Chrome): An instance of Chrome WebDriver.
    
    Usage Example:
    ```python
    chromepath = "C:\\Users\\YourUsername\\path\\to\\chromedriver.exe"
    additional_options = ["--disable-extensions", "--headless"]
    experimental_options = {"detach": True}
    extension_path = "./exampleOfExtensionDownloadedToFolder.crx"
    driver = initialize_browser(chromepath, extension_path, additional_options, experimental_options)
    driver.get("https://www.google.com")
    ```
    """
 # Set Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    # Add Chrome extension if provided
    if extension_path:
        chrome_options.add_extension(extension_path)
    
    # Add any additional Chrome options if provided
    if additional_options:
        for option in additional_options:
            chrome_options.add_argument(option)

    # Add experimental options if provided
    if experimental_options:
        for key, value in experimental_options.items():
            chrome_options.add_experimental_option(key, value)
    
    # Provide the path to the chromedriver executable
    service = Service(executable_path=chromepath)
    
    # Initialize the Selenium WebDriver with Chrome
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Define and inject the JavaScript function for XPath evaluation
    js_xpath_function = """
    window.getElementByXpath = function(path) {
        return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    }
    """
    driver.execute_script(js_xpath_function)
    
    return driver









# %% A basic credential entering code. 
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
    
    

    
    
  # %%  
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





    
    
   

def find_element_by_text(text, element_type='*', wait_time=10, contains=False, driver=None):
    """
    Finds a web element by its visible text using Selenium.

    Parameters:
    - text (str): The visible text to search for.
    - element_type (str, optional): The type of the HTML element (e.g., 'a' for links, 'div' for divisions). Defaults to '*' (any element).
    - wait_time (int, optional): Maximum time to wait for the element to become visible. Defaults to 10 seconds.
    - contains (bool, optional): Whether to find elements that contain the given text. Defaults to False.
    - driver (selenium.webdriver, optional): The Selenium WebDriver instance.

    Returns:
    - selenium.webdriver.remote.webelement.WebElement: The web element found.

    Example usage:
    >>> element = find_element_by_text("Click Me")
    >>> element.click()
    """

    if contains:
        xpath = f"//{element_type}[contains(text(), '{text}')]"
    else:
        xpath = f"//{element_type}[text()='{text}']"
    
    print(f"Using XPath: {xpath}")
    
    try:
        element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, xpath)))
        #print(f"Element found: {element}")
        return element
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    
    
# Similar to above function but returns a list of all elements. 
def find_elements_by_text(text, element_type='*', wait_time=10, contains=False, driver=None):
   """
   Finds all web elements by their visible text using Selenium.
   
   Parameters:
   - driver (selenium.webdriver): The Selenium WebDriver instance.
   - text (str): The visible text to search for.
   - element_type (str, optional): The type of the HTML element (e.g., 'a' for links, 'div' for divisions). Defaults to '*' (any element).
   - wait_time (int, optional): Maximum time to wait for the element to become visible. Defaults to 10 seconds.
   - contains (bool, optional): Whether to search for elements that contain the given text. Defaults to False.
   
   Returns:
   - List[selenium.webdriver.remote.webelement.WebElement]: List of web elements found.
   
   Example usage:
   >>> elements = find_elements_by_text(driver, "View Case", element_type='a')
   >>> for element in elements:
   >>>     element.click()
   """
   
   if contains:
       xpath = f"//{element_type}[contains(text(), '{text}')]"
   else:
       xpath = f"//{element_type}[text()='{text}']"
       
   elements = WebDriverWait(driver, wait_time).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
   return elements        
  
    
    
def find_element_by_placeholder(text, element_type='input', wait_time=10, contains=False, driver=None):
    """
    Finds a web element by its placeholder attribute using Selenium.
    
    Parameters:
    - text (str): The placeholder text to search for.
    - driver (selenium.webdriver, optional): The Selenium WebDriver instance.
    - element_type (str, optional): The type of the HTML element (e.g., 'input' for input fields). Defaults to 'input'.
    - wait_time (int, optional): Maximum time to wait for the element to become visible. Defaults to 10 seconds.
    - contains (bool, optional): Whether to search for elements that contain the given text. Defaults to False.
    
    Returns:
    - selenium.webdriver.remote.webelement.WebElement: The web element found.
    
    Example usage:
    >>> element = find_element_by_placeholder("Enter your name")
    >>> element.send_keys("John Doe")
    """
    if contains:
        xpath = f"//{element_type}[contains(@placeholder, '{text}')]"
    else:
        xpath = f"//{element_type}[@placeholder='{text}']"
    
    if driver is None:
        try:
            driver = globals()['driver']
        except KeyError:
            raise ValueError("Driver is not initialized. Please initialize the Selenium WebDriver.")
            
    element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, xpath)))
    return element



def find_element_by_title(title, element_type='*', wait_time=10, contains=False, driver=None):
    """
    Finds a web element by its title attribute using Selenium.

    Parameters:
    - title (str): The title attribute value to search for.
    - driver (selenium.webdriver, optional): The Selenium WebDriver instance.
    - element_type (str, optional): The type of the HTML element. Defaults to '*' (any element).
    - wait_time (int, optional): Maximum time to wait for the element to become visible. Defaults to 10 seconds.
    - contains (bool, optional): Whether to search for elements that contain the given title text. Defaults to False.

    Returns:
    - selenium.webdriver.remote.webelement.WebElement: The web element found.

    Example usage:
    >>> element = find_element_by_title("Havai 30")
    >>> print(element.tag_name)
    """
    if contains:
        xpath = f"//{element_type}[contains(@title, '{title}')]"
    else:
        xpath = f"//{element_type}[@title='{title}']"
    
    if driver is None:
        try:
            driver = globals()['driver']
        except KeyError:
            raise ValueError("Driver is not initialized. Please initialize the Selenium WebDriver.")
            
    element = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.XPATH, xpath)))
    return element








def select_from_dropdown(driver, dropdown_id, value, attribute=None, attribute_value=None):
    """
    Selects an option from a dropdown based on the visible text or an attribute.

    Parameters:
    - driver (selenium.webdriver): The WebDriver instance.
    - dropdown_id (str): The ID of the dropdown element.
    - value (str): The visible text of the option to be selected.
    - attribute (str, optional): An additional attribute to match on the option.
    - attribute_value (str, optional): The value of the additional attribute to match.

    Returns:
    - bool: True if selection is successful, False otherwise.

    Example usage:
    >>> select_from_dropdown(driver, "cboHSHearingTypeGroup", "Criminal", "parent", "All Superior Court")
    """
    try:
        dropdown = driver.find_element(By.ID, dropdown_id)
        if attribute and attribute_value:
            options = dropdown.find_elements(By.TAG_NAME, "option")
            for option in options:
                if option.get_attribute("value") == value and option.get_attribute(attribute) == attribute_value:
                    option.click()
                    return True
        else:
            select = Select(dropdown)
            select.select_by_visible_text(value)
            return True
    except Exception as e:
        print(f"An error occurred while selecting from the dropdown: {e}")
        return False






# Sometimes clicks get intercepted because there is an element over it, making it unclickable. 
# In the case that this is a loading screen, this attempts to keep trying until it can click it
def click_with_retry(element, max_attempts=20, wait=1):
    attempts = 0
    while attempts < max_attempts:
        try:
            element.click()
            return True  # Click successful
        except ElementClickInterceptedException:
            time.sleep(wait)  # Wait before retrying
            attempts += 1
    return False  # Click failed after retries


def wait_for_page_load(driver, timeout=30):
    """
    Wait for the page to be completely loaded.

    :param driver: Selenium WebDriver instance.
    :param timeout: Maximum time to wait for page load (in seconds).
    """
    try:
        # Wait for the document.readyState to be 'complete'
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        print("Page loaded successfully")
    except TimeoutException:
        print("Timed out waiting for page to load")











#%% These were put together to get auth tokens for APIs, but we could potentially get anything we would normally see in the network tab when inspecting with these

# Source for this one: https://gist.github.com/rengler33/f8b9d3f26a518c08a414f6f86109863c
def process_browser_logs_for_network_events(logs):
    """
    Return only logs which have a method that start with "Network.response", "Network.request", or "Network.webSocket"
    since we're interested in the network events specifically.
    """
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if (
                "Network.response" in log["method"]
                or "Network.request" in log["method"]
                or "Network.webSocket" in log["method"]
        ):
            yield log
            

def find_bearer_tokens(logs):
    """
    Filters the provided logs for entries that contain bearer tokens
    in the request or response headers.
    """
    bearer_entries = []

    for entry in logs:
        log = json.loads(entry['message'])['message']
        
        # Check if the log entry is related to network events
        if "Network.requestWillBeSent" in log['method']:
            # Extract the request headers
            headers = log.get('params', {}).get('request', {}).get('headers', {})
            
            # Look for the Authorization header
            authorization = headers.get('Authorization', '')
            if 'Bearer' in authorization:
                bearer_entries.append(log)

    return bearer_entries            

# Set up an event listener for network requests
def request_interceptor(request):
    print(request['request']['url'])
    if request['request']['url'].endswith('/api/users'):
        headers = request['request']['headers']
        print(headers.get('Authorization'))
        




def is_token_valid(bearer_token, additional_minutes=0):
    """
    Check if the JWT token is still valid and will remain valid for an additional set of minutes.
    
    :param bearer_token: The JWT token prefixed with "Bearer "
    :param additional_minutes: The number of additional minutes the token should be valid for
    :return: True if the token is valid and False otherwise
    
    Usage:
    bearer_token = "Bearer eyJ0eXAiOiJKV1QiLC..."
    is_valid = is_token_valid_for_additional_minutes(bearer_token, 10)
    if is_valid:
        print("Token is valid for at least another 10 minutes.")
    else:
        print("Token is invalid or expiring soon.")
  
    
    """
    token = bearer_token.split(" ")[1]  # Remove the "Bearer " prefix
    
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = decoded.get('exp', 0)
        current_time = time.time()
        future_time = current_time + (additional_minutes * 60)  # Convert minutes to seconds
        
        return exp_time > future_time
    except jwt.PyJWTError as e:
        print(f"Error decoding token: {e}")
        return False




def get_token_expiration_details(bearer_token):
    """
    Returns the expiration time of the JWT token and the time left until expiration.
    
    :param bearer_token: The JWT token prefixed with "Bearer "
    :return: A tuple containing the expiration datetime (in UTC) and the time left in seconds
    
     
    Usage:

    bearer_token = "Bearer eyJ0eXAiOiJKV1QiLC..."
    expiration_date, time_left = get_token_expiration_details(bearer_token)
    if expiration_date:
        print(f"Token expires on: {expiration_date} UTC, Time left: {time_left}")
    else:
        print("Could not decode token.")
   
    
    """
    token = bearer_token.split(" ")[1]  # Remove the "Bearer " prefix
    
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = decoded.get('exp', 0)
        current_time = time.time()
        time_left = exp_time - current_time  # Time left in seconds
        
        # Convert the exp_time to a datetime object
        exp_date = datetime.utcfromtimestamp(exp_time)
        
        return exp_date, timedelta(seconds=time_left)
    except jwt.PyJWTError as e:
        print(f"Error decoding token: {e}")
        return None, None













