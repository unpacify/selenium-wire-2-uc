# __init__.py for seleniumwire2.undetected_chromedriver

from .webdriver import Chrome, ChromeOptions  # Import Chrome and ChromeOptions
try:
    import undetected_chromedriver as uc  # Import the undetected_chromedriver module
except ImportError:
    uc = None  # Handle cases where undetected_chromedriver is not installed
