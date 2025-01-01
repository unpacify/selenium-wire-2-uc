# -*- coding: utf-8 -*-

"""Top-level package for Selenium Wire."""

__author__ = """7x11x13"""
__version__ = "0.3.0"  # Updated version after adding undetected-chromedriver

from mitmproxy.certs import Cert
from mitmproxy.http import Headers

from seleniumwire2.exceptions import SeleniumWireException
from seleniumwire2.options import ProxyConfig, SeleniumWireOptions
from seleniumwire2.webdriver import Chrome, Edge, Firefox, Remote, Safari
from seleniumwire2.undetected_chromedriver import Chrome as UndetectedChrome
from seleniumwire2.undetected_chromedriver import uc as UndetectedChromeOptions

__all__ = [
    "Cert",
    "Headers",
    "SeleniumWireException",
    "ProxyConfig",
    "SeleniumWireOptions",
    "Chrome",
    "Edge",
    "Firefox",
    "Remote",
    "Safari",
    "UndetectedChrome",
    "UndetectedChromeOptions",
]
