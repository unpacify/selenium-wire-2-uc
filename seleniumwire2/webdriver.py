import logging
from typing import Protocol, TypedDict

# 1. Attempt to import undetected-chromedriver (uc).
#    If missing, we’ll fall back to standard Selenium.
try:
    import undetected_chromedriver as uc
    _UndetectedChrome = uc.Chrome
    _UndetectedChromeOptions = uc.ChromeOptions
    logging.getLogger(__name__).info("Using undetected-chromedriver for Chrome.")
except ImportError:
    from selenium.webdriver import Chrome as _UndetectedChrome
    from selenium.webdriver import ChromeOptions as _UndetectedChromeOptions
    logging.getLogger(__name__).warning("undetected-chromedriver not installed; using standard Selenium Chrome.")

from selenium.webdriver import Edge as _Edge
from selenium.webdriver import EdgeOptions
from selenium.webdriver import Firefox as _Firefox
from selenium.webdriver import FirefoxOptions
from selenium.webdriver import Remote as _Remote
from selenium.webdriver import Safari as _Safari
from selenium.webdriver import SafariOptions
from selenium.webdriver.common.options import BaseOptions
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from seleniumwire2 import backend, utils
from seleniumwire2.inspect import InspectRequestsMixin
from seleniumwire2.options import ProxyConfig, SeleniumWireOptions
from seleniumwire2.server import MitmProxy


class Capabilities(TypedDict):
    proxy: dict
    acceptInsecureCerts: bool


class WebDriverProtocol(Protocol):
    backend: MitmProxy
    def refresh(self) -> None: ...
    def quit(self) -> None: ...


def _set_options(options: BaseOptions, capabilities: Capabilities):
    """
    Applies Selenium Wire 2's proxy config to the driver options.
    Works whether 'options' is undetected-chromedriver ChromeOptions
    or standard ChromeOptions/FirefoxOptions/etc.
    """
    # Chrome / Edge
    if isinstance(options, _UndetectedChromeOptions) or isinstance(options, EdgeOptions):
        # Prevent Chrome/Edge from bypassing the proxy for localhost.
        options.add_argument("--proxy-bypass-list=<-loopback>")
        for key, value in capabilities.items():
            options.set_capability(key, value)

    # Firefox
    elif isinstance(options, FirefoxOptions):
        options.set_preference("network.proxy.allow_hijacking_localhost", True)
        try:
            options.accept_insecure_certs = capabilities["acceptInsecureCerts"]
        except KeyError:
            pass

        # For Selenium 4, we set actual proxy via options.
        try:
            proxy = Proxy()
            proxy.proxy_type = ProxyType.MANUAL
            proxy.http_proxy = capabilities["proxy"]["httpProxy"]
            proxy.ssl_proxy = capabilities["proxy"]["sslProxy"]
            if "noProxy" in capabilities["proxy"]:
                proxy.no_proxy = capabilities["proxy"]["noProxy"]
            options.proxy = proxy
        except KeyError:
            pass

    # Safari
    elif isinstance(options, SafariOptions):
        # Safari does not support auto proxy config, must be done manually
        # but we at least set acceptInsecureCerts
        try:
            options.accept_insecure_certs = capabilities["acceptInsecureCerts"]
        except KeyError:
            pass

    else:
        raise ValueError(f"Unsupported options type: {options.__class__.__name__}")


class DriverCommonMixin:
    """Methods/attributes shared by all WebDriver classes."""

    def _setup_backend(
        self: WebDriverProtocol,
        seleniumwire_options: SeleniumWireOptions,
        webdriver_options: BaseOptions
    ):
        """
        Create and start the Selenium Wire 2 proxy backend (mitmproxy).
        If auto_config is True, build an internal 'capabilities' dict
        with proxy info and call _set_options().
        """
        # 1) Start the proxy
        self.backend = backend.create(seleniumwire_options)

        if seleniumwire_options.auto_config:
            # 2) Build proxy capabilities
            addr, port = utils.urlsafe_address(self.backend.address)
            capabilities: Capabilities = {
                "proxy": {
                    "proxyType": "manual",
                    "httpProxy": f"{addr}:{port}",
                    "sslProxy": f"{addr}:{port}",
                },
                "acceptInsecureCerts": not seleniumwire_options.verify_ssl,
            }
            if seleniumwire_options.exclude_hosts:
                capabilities["proxy"]["noProxy"] = seleniumwire_options.exclude_hosts

            # 3) Apply those capabilities to the options object
            _set_options(webdriver_options, capabilities)
        else:
            # If auto_config=False, just read existing caps from webdriver_options
            capabilities = webdriver_options.to_capabilities()
            _set_options(webdriver_options, capabilities)

    def quit(self: WebDriverProtocol):
        """Shutdown the proxy server, then quit the webdriver."""
        self.backend.shutdown()
        super().quit()  # type: ignore

    def remove_upstream_proxy(self: WebDriverProtocol):
        """Remove upstream proxy from Selenium Wire 2."""
        self.backend.update_server_mode(None)
        self.refresh()

    def set_upstream_proxy(self: WebDriverProtocol, proxy_config: ProxyConfig):
        """Dynamically change the upstream proxy config used by mitmproxy."""
        self.backend.update_server_mode(proxy_config)
        self.refresh()


###############################################################################
# Standard Classes for Other Browsers (Firefox, Edge, Safari, Remote)
###############################################################################

class Firefox(InspectRequestsMixin, DriverCommonMixin, _Firefox):
    """Firefox with Selenium Wire 2."""
    def __init__(self, *args,
                 seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(),
                 **kwargs):
        options = kwargs.get("options", FirefoxOptions())
        kwargs["options"] = options
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


class Edge(InspectRequestsMixin, DriverCommonMixin, _Edge):
    """Edge with Selenium Wire 2."""
    def __init__(self, *args,
                 seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(),
                 **kwargs):
        options = kwargs.get("options", EdgeOptions())
        kwargs["options"] = options
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


class Safari(InspectRequestsMixin, DriverCommonMixin, _Safari):
    """Safari with Selenium Wire 2."""
    def __init__(self, *args,
                 seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(),
                 **kwargs):
        options = kwargs.get("options", SafariOptions())
        kwargs["options"] = options
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


class Remote(InspectRequestsMixin, DriverCommonMixin, _Remote):
    """Remote driver with Selenium Wire 2."""
    def __init__(self, *args,
                 seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(),
                 **kwargs):
        if "options" not in kwargs:
            raise ValueError("Remote driver must be initialized with 'options' kwarg")
        options = kwargs["options"]
        self._setup_backend(seleniumwire_options, options)
        super().__init__(*args, **kwargs)


###############################################################################
# Chrome => Undetected Chrome Driver + Selenium Wire 2
###############################################################################

class Chrome(InspectRequestsMixin, DriverCommonMixin, _UndetectedChrome):
    """
    Chrome with Selenium Wire 2.
    If undetected-chromedriver is installed, uses UC. Otherwise standard Chrome.
    """

    def __init__(self, *args,
                 seleniumwire_options: SeleniumWireOptions = SeleniumWireOptions(),
                 **kwargs):
        # If user passes a specific ChromeOptions, use it; else create default
        options = kwargs.get("options", _UndetectedChromeOptions())
        kwargs["options"] = options

        # 1) Setup the backend (mitmproxy)
        self._setup_backend(seleniumwire_options, options)

        # 2) If auto_config is True, the proxy is set via capabilities
        #    But undetected-chromedriver may ignore desired_capabilities
        #    So we forcibly add the proxy argument ourselves:
        if seleniumwire_options.auto_config:
            addr, port = self.backend.address
            # Make sure to pass the correct address:
            options.add_argument(f"--proxy-server={addr}:{port}")

        super().__init__(*args, **kwargs)


###############################################################################
# Re-export ChromeOptions so user can do:
#   from seleniumwire2.webdriver import ChromeOptions
# and it will be UC's if installed or fallback
###############################################################################
ChromeOptions = _UndetectedChromeOptions
