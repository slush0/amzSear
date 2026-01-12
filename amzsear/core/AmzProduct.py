import re
from urllib import request
from lxml import html as html_module

try:
    from amzsear.core.AmzBase import AmzBase
    from amzsear.core import requires_valid_data, capture_exception, build_url, build_base_url
    from amzsear.core.AmzRating import AmzRating
    from amzsear.core.AmzProductDetails import AmzProductDetails
    from amzsear.core.AmzReviews import AmzReviews
    from amzsear.core.selectors import DetailLevel
    from amzsear.core.consts import PRODUCT_URL, REVIEWS_URL, QA_URL, DETAIL_HEADERS, DEFAULT_REGION
except ImportError:
    from .AmzBase import AmzBase
    from . import requires_valid_data, capture_exception, build_url, build_base_url
    from .AmzRating import AmzRating
    from .AmzProductDetails import AmzProductDetails
    from .AmzReviews import AmzReviews
    from .selectors import DetailLevel
    from .consts import PRODUCT_URL, REVIEWS_URL, QA_URL, DETAIL_HEADERS, DEFAULT_REGION
"""
    The AmzProduct class extends the AmzBase class and, as such the following
    attributes are available to be called as an index call or as an attribute:

        title (str): The name of the product.
        product_url (str) A url directly to the product's Amazon page.
        image_url (str) A url to the product's default image.
        rating (AmzRating) An AmzRating object.
        prices (dict) A dictionary of prices, with the price type as a key and
          a string for the price value (see get_prices method to get float values).
        extra_attributes (dict) Any extra information that can be extracted
          from the product.
        subtext (list) A list of strings under the title, typically the author's
          name and/or the date of publication.

    This class should usually not be instantiated directly (rather be used in
    an (AmzSear object) but can be created by passing an HTML element to
    the constructor. If nothing is passed, an empty AmzProduct object is
    created.

    Optional Args:
        html_element (LXML root): A root for an HTML tree derived from an element on an Amazon search page.
"""
class AmzProduct(AmzBase):
    title = None
    product_url = None
    image_url = None
    rating = None
    prices = None
    extra_attributes = None
    subtext = None
    details = None  # AmzProductDetails object (populated by fetch_details)
    reviews = None  # AmzReviews object (populated by fetch_details)
    _region = DEFAULT_REGION  # Region for URL building

    _all_attrs = ['title','product_url','image_url','rating','prices',
        'extra_attributes', 'subtext', 'details', 'reviews']

    def __init__(self, html_element=None):
        if html_element != None:
            html_dict = self._get_from_html(html_element)
            for k,v in html_dict.items():
                setattr(self, k, v)
            if len(html_dict) > 0:
                self._is_valid = True

    """
        Private method - used in to initialise fields from HTML

        Returns:
            dict: A dict of fields with extracted data
    """
    @capture_exception(IndexError,default={})
    def _get_from_html(self, root):
        d = {}

        title_root = [x for x in root.cssselect('a') if len(x.cssselect('h2')) > 0][0]
        d['title'] = ''.join([x.text_content() for x in title_root.cssselect('h2')])
        d['product_url'] = build_url(title_root.get('href'))
        for elem in title_root.getparent().getparent().cssselect('div[class="a-row a-spacing-none"]'):
            temp_subtext = ''.join([x.text_content() for x in elem.cssselect('span[class*="a-size-small"]')])
            if len(temp_subtext) > 0:
                d['subtext'] = d.get('subtext',[]) + [temp_subtext]


        d['image_url'] = root.cssselect('img[src]')[0].get('src')
        d['rating'] = AmzRating(root) or None

        d['prices'] = {}
        price_names = root.cssselect('h3[data-attribute]')
        price_text = root.cssselect('span[class^="a"]')
        price_text = filter(lambda x: re.match('^[^a-z\-]+$',str(x.text)) and
            re.search('[\.\,]',str(x.text)) and re.search('\d',str(x.text)), price_text)

        for i, el in enumerate(price_text):
            if i >= len(price_names):
                price_key = str(len(d['prices'])) # defaults to a number if no name for price type
            else:
                price_key = price_names[i].text
            d['prices'][price_key] = el.text

        extras = root.cssselect('div[class="a-fixed-left-grid-inner"] > div > span')
        extras = [re.sub('\s+',' ', x.text_content().strip()) for x in extras]
        d['extra_attributes'] = dict(list(zip(extras,extras[1:]))[::2])

        # _index is not used explicitly in _all_attrs but can be referenced elsewhere
        d['_index'] = root.get('id','').split('_')[-1]

        # clean up before returning
        return dict(map(lambda k: (k, d[k].strip() if isinstance(d[k],str) else d[k]), d)) 


    """
        Gets a list of floats from the dictionary of price text. A key can be passed
        to explicitly specify the prices to select. If the key is None, all prices keys
        are used.

        Optional Args:
            key (str or list): A key or list of keys to in the price dictionary.

        Returns:
            list: List of floats for the subset of price specified.
    """
    @requires_valid_data(default=[])
    def get_prices(self, key=None):
        keys = []
        if key == None:
            keys = self.prices.keys()
        elif isinstance(key,list):
            keys = key
        else:
            keys = [key]

        prices = []
        for k in keys:
            if k not in self.prices:
                raise KeyError(k)
            prices += [re.sub(',','',x) for x in re.findall('[\d.,]+', self.prices[k])]

        return sorted(map(float,prices))
        
    def get_asin(self):
        result = re.search('(?:/|%2F)dp(?:/|%2F)([A-Z0-9]{10})', self.product_url)
        if result is not None:
            result = result.group(1)
        return result

    def _fetch_html(self, url):
        """
        Fetch HTML content from a URL.

        Args:
            url: The URL to fetch

        Returns:
            lxml HTML element or None on failure
        """
        try:
            req = request.Request(url, headers=DETAIL_HEADERS)
            response = request.urlopen(req)
            html_content = response.read()
            return html_module.fromstring(html_content)
        except Exception:
            return None

    def fetch_details(self, level=None, region=None):
        """
        Fetch detailed product information from Amazon.

        This method makes HTTP requests to Amazon to retrieve additional
        product information beyond what's available in search results.

        Args:
            level: DetailLevel enum specifying how much detail to fetch:
                - DetailLevel.SEARCH (0): No request, use existing data
                - DetailLevel.BASIC (1): Fetch product page (title, brand, specs, etc.)
                - DetailLevel.REVIEWS (2): Also fetch reviews page
                - DetailLevel.FULL (3): Also fetch Q&A page
            region: Amazon region code (e.g., 'US', 'UK', 'DE'). Defaults to US.

        Returns:
            self: Returns self for method chaining

        Example:
            >>> product = search_results.rget(0)
            >>> product.fetch_details(level=DetailLevel.BASIC)
            >>> print(product.details.brand)
        """
        if level is None:
            level = DetailLevel.BASIC

        if region is not None:
            self._region = region

        asin = self.get_asin()
        if not asin:
            return self

        base_url = build_base_url(self._region)

        # Level 1: Fetch product page details
        if level.value >= DetailLevel.BASIC.value:
            product_url = PRODUCT_URL % (base_url, asin)
            html_elem = self._fetch_html(product_url)
            if html_elem is not None:
                self.details = AmzProductDetails(html_elem)

        # Level 2: Fetch reviews page
        if level.value >= DetailLevel.REVIEWS.value:
            reviews_url = REVIEWS_URL % (base_url, asin)
            html_elem = self._fetch_html(reviews_url)
            if html_elem is not None:
                self.reviews = AmzReviews(html_elem)

        # Level 3: Q&A would be fetched here (not implemented yet)
        # if level.value >= DetailLevel.FULL.value:
        #     qa_url = QA_URL % (base_url, asin)
        #     ...

        return self


