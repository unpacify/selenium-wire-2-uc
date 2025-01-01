import logging
from selenium.webdriver import DesiredCapabilities

try:
    import undetected_chromedriver as uc
except ImportError as e:
    raise ImportError(
        "undetected_chromedriver not found. Install it with `pip install undetected-chromedriver`."
    ) from e

from seleniumwire2.inspect import InspectRequestsMixin
from seleniumwire2.webdriver import DriverCommonMixin
from seleniumwire2.utils import urlsafe_address
from seleniumwire2.options import SeleniumWireOptions

log = logging.getLogger(__name__)


class Chrome(InspectRequestsMixin, DriverCommonMixin, uc.Chrome):
    """Extend the undetected_chromedriver Chrome class to integrate Selenium Wire."""

    def __init__(self, *args, seleniumwire_options: SeleniumWireOptions = None, **kwargs):
        if seleniumwire_options is None:
            seleniumwire_options = SeleniumWireOptions()

        # Set up Selenium Wire proxy backend
        config = self._setup_backend(seleniumwire_options)

        # Update desired capabilities if auto_config is enabled
        if seleniumwire_options.auto_config:
            capabilities = kwargs.get("desired_capabilities", DesiredCapabilities.CHROME.copy())
            capabilities.update(config)
            kwargs["desired_capabilities"] = capabilities

        # Configure ChromeOptions
        chrome_options = kwargs.get("options", ChromeOptions())
        addr, port = urlsafe_address(self.backend.address)
        chrome_options.add_argument(f"--proxy-server={addr}:{port}")
        chrome_options.add_argument(
            f"--proxy-bypass-list={','.join(seleniumwire_options.exclude_hosts or ['<-loopback>'])}"
        )
        kwargs["options"] = chrome_options

        log.info("Using undetected-chromedriver with Selenium Wire")

        # Initialize undetected_chromedriver's Chrome class
        super().__init__(*args, **kwargs)


ChromeOptions = uc.ChromeOptions  # Expose ChromeOptions for external use
