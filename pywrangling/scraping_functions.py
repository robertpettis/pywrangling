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