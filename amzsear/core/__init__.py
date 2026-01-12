from functools import wraps
from urllib import parse

import requests
from lxml import html as html_module

try:
    from amzsear.core.consts import (QUERY_BUILD_DICT, BASE_URL, DEFAULT_REGION,
        REGION_CODES, SEARCH_URL, REQUEST_HEADERS)
except ImportError:
    from .consts import (QUERY_BUILD_DICT, BASE_URL, DEFAULT_REGION,
        REGION_CODES, SEARCH_URL, REQUEST_HEADERS)


def requires_valid_data(default=None):
    """Decorator for valid data in an object, returns default if not valid."""
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kws):
            if hasattr(self, '_is_valid') and self._is_valid:
                return f(self, *args, **kws)
            else:
                return default
        return wrapper
    return decorator


def capture_exception(error, default=None):
    """Decorator to capture exception and return a default instead."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kws):
            try:
                return f(*args, **kws)
            except error:
                return default
        return wrapper
    return decorator


def build_url(url=None, query='', page_num=1, region=DEFAULT_REGION):
    """Build a URL based on a query."""
    if url is None:
        # Build from query, page_num and region
        base = build_base_url(region)
        url = SEARCH_URL % (base, parse.quote(query), page_num)

    if url.startswith('/'):
        url = build_base_url(region) + url

    parsed_obj = parse.urlparse(url)
    query_dict = parse.parse_qs(parsed_obj.query)

    # Update the query dict
    query_dict.update(QUERY_BUILD_DICT)

    parsed_obj = parsed_obj._replace(query=parse.urlencode(query_dict, doseq=True))
    return parsed_obj.geturl()


def build_base_url(region=DEFAULT_REGION):
    """Build base URL based on region."""
    find_region = region.upper()
    if find_region not in REGION_CODES:
        raise ValueError(f'{repr(region)} is not a known Amazon region')

    return BASE_URL + REGION_CODES[find_region]


class FetchError(Exception):
    """Raised when fetching a URL fails."""
    pass


def fetch_html(url):
    """
    Fetch HTML content from a URL and return parsed lxml element.

    Args:
        url: The URL to fetch

    Returns:
        lxml HTML element

    Raises:
        FetchError: If the fetch fails (network error, 404, etc.)
    """
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
        return html_module.fromstring(response.content)
    except requests.RequestException as e:
        raise FetchError(f"Failed to fetch {url}: {e}") from e
