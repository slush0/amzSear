from lxml import html as html_module

try:
    from amzsear.core import build_url, fetch_html
    from amzsear.core.consts import DEFAULT_REGION
    from amzsear.core.AmzProduct import AmzProduct
except ImportError:
    from . import build_url, fetch_html
    from .consts import DEFAULT_REGION
    from .AmzProduct import AmzProduct


class AmzSear(object):
    """
    The AmzSear object is similar to a Python dict, with each item having a
    unique index (ASIN) to reference each AmzProduct.

    The constructor accepts arguments in a hierarchy - higher level arguments
    override lower level ones:

        (query, [page], [region])
                   |
                 (url)
                   |
                (html)
                   |
            (html_element)
                   |
              (products)

    Args:
        query (str): A search query to look up on Amazon.
        page (int or iterable): The page number(s) of the query (defaults to 1).
        region (str): The Amazon region/country to search (defaults to US).
        url (str or iterable): An Amazon search url (not recommended).
        html (str or iterable): The HTML code from an Amazon search page.
        html_element (lxml element or iterable): The lxml root generated from HTML.
        products (list): A list of AmzProducts.

    Note: All arg types can be an iterable of that type. For example,
    page can be an int, list, or range of ints to be searched.
    """

    def __init__(self, query=None, page=1, region=DEFAULT_REGION, url=None, html=None, html_element=None, products=None):
        def get_iter(it):
            if not hasattr(it, '__iter__') or isinstance(it, str):
                return [it]
            else:
                return it

        self._products = []
        self._indexes = []
        self._urls = []

        if query is not None:
            page = get_iter(page)
            url = [build_url(query=query, page_num=p, region=region) for p in page]
        if url is not None:
            url = get_iter(url)
            self._urls = url
            html_element = []
            for u in url:
                elem = fetch_html(build_url(u))
                if elem is not None:
                    html_element.append(elem)
        if html is not None:
            html = get_iter(html)
            html_element = [html_module.fromstring(h) for h in html]
        if html_element is not None:
            html_element = get_iter(html_element)
            products = []
            for html_el in html_element:
                page_products = html_el.cssselect('div[data-asin][data-component-type="s-search-result"]')
                page_products = [x for x in page_products if x.cssselect('h2')]
                page_products = [AmzProduct(elem, region=region) for elem in page_products]
                products.extend(page_products)
        if products is not None:
            products = get_iter(products)
            products = [prod for prod in products if prod.is_valid() and prod._index]
            # Deduplicate by ASIN - keep first occurrence only
            for prod in products:
                if prod._index not in self._indexes:
                    self._products.append(prod)
                    self._indexes.append(prod._index)

    def __repr__(self):
        out = []
        max_index_len = 12  # ASIN is 10 chars + padding
        for index, product in self.items():
            temp_repr = repr(index) + ':' + max_index_len*' '
            temp_repr = temp_repr[:max_index_len] + repr(product)
            temp_repr = temp_repr.replace('\n','\n' + max_index_len*' ')

            out.append(temp_repr)
        out.append('<' + self.__class__.__name__ + ' object>')
        return '\n'.join(out)


    def __iter__(self):
        return iter(self._indexes)

    def __len__(self):
        return len(self._products)

    def __getitem__(self, key):
        return self.get(key, default=None, raise_error=True)

    def _set_repr_max_len(self, val):
        """Set the maximum repr width length for all products."""
        for product in self:
            if hasattr(product, 'REPR_MAX_LEN'):
                product.REPR_MAX_LEN = val

    def get(self, key, default=None, raise_error=False):
        """
        Get the AmzProduct by ASIN.

        Indexing the AmzSear object is equivalent to calling this method
        with raise_error=True.

        Args:
            key (str): The ASIN of the product in the AmzSear object.
            default: The default value if raise_error=False.
            raise_error (bool): If True, raises KeyError if the key is not found.

        Returns:
            The AmzProduct at the key, otherwise the default value.
        """
        key = str(key)
        if key not in self._indexes:
            if raise_error:
                raise KeyError(f'The key {repr(key)} is not a known index')
            else:
                return default

        return self._products[self._indexes.index(key)]

    def rget(self, key, default=None, raise_error=False):
        """
        Relative get - Gets the nth product by position.

        For example, if indexes are ['ABC', 'DEF', 'GHI', 'JKL'],
        calling rget(1) returns the product at 'DEF', and
        rget(-1) returns the product at 'JKL'.

        Args:
            key (int): The relative index of the desired product.
            default: The default value if raise_error=False.
            raise_error (bool): If True, raises IndexError if out of range.

        Returns:
            The AmzProduct at the relative index, otherwise the default value.
        """
        if raise_error:
            return self._products[key]
        else:
            try:
                return self._products[key]
            except IndexError:
                return default

    def aget(self, key, default=None, raise_error=False):
        """
        All get - Gets attribute values from all products.

        Args:
            key (str or list): A single attribute name or a list of attributes.
            default: The default value if attribute is unavailable.
            raise_error (bool): If True, raises ValueError if attribute not found.

        Returns:
            list: List of tuples containing attribute values in product order.
        """
        if not isinstance(key, list):
            key = [key]

        data = []
        for i, k in enumerate(key):
            data.append([])
            curr_out = data[i]

            for index, prod in self.items():
                if hasattr(prod, k):
                    curr_out.append(getattr(prod, k))
                elif raise_error:
                    raise ValueError(f'The key {repr(k)} is not available at index {repr(index)}')
                else:
                    curr_out.append(default)

        return list(zip(*data))

    def items(self):
        """
        Iterate over (index, product) tuples.

        Returns:
            zip: A generator yielding (ASIN, AmzProduct) tuples.
        """
        return zip(self._indexes, self._products)

    def indexes(self):
        """
        Get a list of all indexes (ASINs) in the object.

        Returns:
            list: A list of all the ASIN indexes.
        """
        return list(x for x in self)

    def products(self):
        """
        Get a list of all products in the object.

        Returns:
            list: A list of AmzProduct objects.
        """
        return list(y for x, y in self.items())

    keys = indexes
    values = products

    def to_dataframe(self, recursive=True, flatten=False):
        """
        Convert to a Pandas DataFrame.

        Pandas must be installed for this method to be called.

        Args:
            recursive (bool): See AmzBase.to_dict method.
            flatten (bool): See AmzBase.to_dict method.

        Returns:
            pandas.DataFrame: A dataframe with each product in a row,
                indexed by ASIN.
        """
        from pandas import DataFrame
        return DataFrame(
            [y.to_series(recursive=recursive, flatten=flatten) for x, y in self.items()],
            index=self._indexes
        ) 
