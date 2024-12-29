# seleniumwire2/undetected_chromedriver/webdriver.py

import logging

from selenium.webdriver import DesiredCapabilities

try:
    import undetected_chromedriver as uc
except ImportError as e:
    raise ImportError(
        'undetected_chromedriver not found. '
        'Install it with `pip install undetected_chromedriver`.'
    ) from e

# IMPORTANT: Adjust these imports from 'seleniumwire' to 'seleniumwire2'
from seleniumwire2.inspect import InspectRequestsMixin
from seleniumwire2.utils import urlsafe_address
from seleniumwire2.webdriver import DriverCommonMixin

log = logging.getLogger(__name__)


class Chrome(InspectRequestsMixin, DriverCommonMixin, uc.Chrome):
    """
    Extends the undetected_chromedriver Chrome webdriver
    to provide Selenium Wire 2 functionality (request interception, etc.).
    """

    def __init__(self, *args, seleniumwire_options=None, **kwargs):
        """
        Initialize an undetected-chromedriver Chrome instance
        that also runs through Selenium Wire 2's proxy.
        """
        if seleniumwire_options is None:
            seleniumwire_options = {}

        # The crucial piece: set up Selenium Wire 2’s proxy backend.
        config = self._setup_backend(seleniumwire_options)

        if seleniumwire_options.get('auto_config', True):
            capabilities = kwargs.get('desired_capabilities')
            if capabilities is None:
                capabilities = DesiredCapabilities.CHROME
            capabilities = capabilities.copy()
            capabilities.update(config)

            kwargs['desired_capabilities'] = capabilities

        # Try to retrieve ChromeOptions from kwargs; else create a fresh one.
        try:
            chrome_options = kwargs['options']
        except KeyError:
            chrome_options = ChromeOptions()

        log.info('Using undetected_chromedriver with Selenium Wire 2')

        # Point the browser at Selenium Wire 2's local proxy
        addr, port = urlsafe_address(self.backend.address())
        chrome_options.add_argument(f'--proxy-server={addr}:{port}')
        chrome_options.add_argument(
            f"--proxy-bypass-list={','.join(seleniumwire_options.get('exclude_hosts', ['<-loopback>']))}"
        )

        kwargs['options'] = chrome_options

        # Initialize uc.Chrome
        super().__init__(*args, **kwargs)


ChromeOptions = uc.ChromeOptions
