"""
AmzProductDetails class for storing detailed product information
fetched from Amazon product pages.
"""

try:
    from amzsear.core.AmzBase import AmzBase
except ImportError:
    from .AmzBase import AmzBase


class AmzProductDetails(AmzBase):
    """
    Contains detailed product information fetched from an Amazon product page.

    All fields return None if not available (graceful defaults).

    Attributes:
        full_title (str): Complete product title
        brand (str): Brand/manufacturer name
        brand_url (str): URL to brand's Amazon store
        about_items (list): "About this item" bullet points
        technical_details (dict): Technical specifications table
        product_description (str): Product description text
        image_urls (list): URLs to all product images
        reviews_summary (str): AI-generated reviews summary (if available)
        star_distribution (dict): Rating distribution {5: percentage, 4: percentage, ...}
        review_count (int): Total number of reviews
        average_rating (float): Average star rating
    """

    full_title = None
    brand = None
    brand_url = None
    about_items = None
    technical_details = None
    product_description = None
    image_urls = None
    reviews_summary = None
    star_distribution = None
    review_count = None
    average_rating = None

    _all_attrs = [
        'full_title', 'brand', 'brand_url', 'about_items',
        'technical_details', 'product_description', 'image_urls',
        'reviews_summary', 'star_distribution', 'review_count', 'average_rating'
    ]

    def __init__(self, html_element=None):
        """
        Initialize AmzProductDetails.

        Args:
            html_element: lxml HTML element from product page (optional)
        """
        if html_element is not None:
            self._parse_from_html(html_element)

    def _parse_from_html(self, root):
        """
        Parse product details from HTML element.

        Args:
            root: lxml HTML root element
        """
        import re

        try:
            from amzsear.core.selectors import (
                PRODUCT_TITLE, BRAND_LINK, FEATURE_BULLETS,
                PRODUCT_DESCRIPTION, PRODUCT_DESCRIPTION_ALT,
                TECH_DETAILS_TABLE, TECH_DETAILS_ROWS,
                PRODUCT_DETAILS_TABLE, PRODUCT_DETAILS_TABLE_ALT,
                IMAGE_GALLERY, MAIN_IMAGE, IMAGE_THUMB_LIST,
                REVIEW_COUNT, RATING_STARS, STAR_HISTOGRAM,
                CUSTOMER_REVIEWS_SUMMARY
            )
        except ImportError:
            from .selectors import (
                PRODUCT_TITLE, BRAND_LINK, FEATURE_BULLETS,
                PRODUCT_DESCRIPTION, PRODUCT_DESCRIPTION_ALT,
                TECH_DETAILS_TABLE, TECH_DETAILS_ROWS,
                PRODUCT_DETAILS_TABLE, PRODUCT_DETAILS_TABLE_ALT,
                IMAGE_GALLERY, MAIN_IMAGE, IMAGE_THUMB_LIST,
                REVIEW_COUNT, RATING_STARS, STAR_HISTOGRAM,
                CUSTOMER_REVIEWS_SUMMARY
            )

        # Full title
        title_elem = root.cssselect(PRODUCT_TITLE)
        if title_elem:
            self.full_title = title_elem[0].text_content().strip()

        # Brand
        brand_elem = root.cssselect(BRAND_LINK)
        if brand_elem:
            self.brand = brand_elem[0].text_content().strip()
            # Remove "Visit the X Store" prefix if present
            if self.brand.startswith('Visit the '):
                self.brand = self.brand.replace('Visit the ', '').replace(' Store', '')
            elif self.brand.startswith('Brand: '):
                self.brand = self.brand.replace('Brand: ', '')
            href = brand_elem[0].get('href')
            if href:
                self.brand_url = href

        # About this item bullet points
        bullet_elems = root.cssselect(FEATURE_BULLETS)
        if bullet_elems:
            self.about_items = []
            for elem in bullet_elems:
                text = elem.text_content().strip()
                if text and text not in ['About this item']:
                    self.about_items.append(text)

        # Technical details
        self.technical_details = {}

        # Try multiple selectors for tech details
        for selector in [TECH_DETAILS_ROWS, PRODUCT_DETAILS_TABLE, PRODUCT_DETAILS_TABLE_ALT]:
            rows = root.cssselect(selector)
            if rows:
                for row in rows:
                    cells = row.cssselect('th, td')
                    if len(cells) >= 2:
                        key = cells[0].text_content().strip()
                        value = cells[1].text_content().strip()
                        # Clean up common artifacts
                        key = re.sub(r'[\u200e\u200f]', '', key).strip()
                        value = re.sub(r'[\u200e\u200f]', '', value).strip()
                        if key and value:
                            self.technical_details[key] = value

        if not self.technical_details:
            self.technical_details = None

        # Product description
        desc_elem = root.cssselect(PRODUCT_DESCRIPTION)
        if not desc_elem:
            desc_elem = root.cssselect(PRODUCT_DESCRIPTION_ALT)
        if desc_elem:
            self.product_description = desc_elem[0].text_content().strip()

        # Image URLs
        self.image_urls = []
        for selector in [IMAGE_GALLERY, IMAGE_THUMB_LIST, MAIN_IMAGE]:
            img_elems = root.cssselect(selector)
            for img in img_elems:
                src = img.get('src') or img.get('data-old-hires') or img.get('data-a-dynamic-image')
                if src and src not in self.image_urls:
                    # Skip tiny placeholder images
                    if 'sprite' not in src.lower() and 'transparent' not in src.lower():
                        self.image_urls.append(src)

        if not self.image_urls:
            self.image_urls = None

        # Reviews summary (AI-generated)
        summary_elem = root.cssselect(CUSTOMER_REVIEWS_SUMMARY)
        if summary_elem:
            self.reviews_summary = summary_elem[0].text_content().strip()

        # Review count
        count_elem = root.cssselect(REVIEW_COUNT)
        if count_elem:
            count_text = count_elem[0].text_content().strip()
            # Extract number from text like "1,234 ratings" or "1,234 global ratings"
            match = re.search(r'[\d,]+', count_text)
            if match:
                self.review_count = int(match.group().replace(',', ''))

        # Average rating
        rating_elem = root.cssselect(RATING_STARS)
        if rating_elem:
            rating_text = rating_elem[0].get('title', '') or rating_elem[0].text_content()
            match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', rating_text)
            if match:
                self.average_rating = float(match.group(1))

        # Star distribution
        histogram = root.cssselect(STAR_HISTOGRAM)
        if histogram:
            self.star_distribution = {}
            for row in histogram:
                text = row.text_content()
                # Match patterns like "5 star 85%"
                match = re.search(r'(\d)\s*star\s*(\d+)%', text)
                if match:
                    stars = int(match.group(1))
                    percentage = int(match.group(2))
                    self.star_distribution[stars] = percentage

        if not self.star_distribution:
            self.star_distribution = None

        # Mark as valid if we got at least a title
        if self.full_title:
            self._is_valid = True
