"""
AmzReview and AmzReviews classes for storing customer review data
fetched from Amazon product review pages.
"""
import re

try:
    from amzsear.core.AmzBase import AmzBase
except ImportError:
    from .AmzBase import AmzBase


class AmzReview(AmzBase):
    """
    Represents a single customer review.

    Attributes:
        reviewer (str): Reviewer's display name
        rating (float): Star rating (1-5)
        title (str): Review title
        date (str): Review date
        text (str): Full review text
        verified (bool): Whether this is a verified purchase
        helpful_count (int): Number of people who found this helpful
        images (list): URLs to images attached to review
    """

    reviewer = None
    rating = None
    title = None
    date = None
    text = None
    verified = None
    helpful_count = None
    images = None

    _all_attrs = [
        'reviewer', 'rating', 'title', 'date',
        'text', 'verified', 'helpful_count', 'images'
    ]

    def __init__(self, html_element=None):
        """
        Initialize AmzReview.

        Args:
            html_element: lxml HTML element for a single review (optional)
        """
        super().__init__()
        if html_element is not None:
            self._parse_from_html(html_element)

    def _parse_from_html(self, elem):
        """
        Parse review data from HTML element.

        Args:
            elem: lxml HTML element for a single review
        """
        try:
            from amzsear.core.selectors import (
                REVIEW_TITLE, REVIEW_RATING, REVIEW_DATE,
                REVIEW_BODY, REVIEW_AUTHOR, REVIEW_VERIFIED,
                REVIEW_HELPFUL, REVIEW_IMAGES
            )
        except ImportError:
            from .selectors import (
                REVIEW_TITLE, REVIEW_RATING, REVIEW_DATE,
                REVIEW_BODY, REVIEW_AUTHOR, REVIEW_VERIFIED,
                REVIEW_HELPFUL, REVIEW_IMAGES
            )

        # Reviewer name
        author_elem = elem.cssselect(REVIEW_AUTHOR)
        if author_elem:
            self.reviewer = author_elem[0].text_content().strip()

        # Rating
        rating_elem = elem.cssselect(REVIEW_RATING)
        if rating_elem:
            rating_text = rating_elem[0].text_content()
            match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', rating_text)
            if match:
                self.rating = float(match.group(1))

        # Title
        title_elem = elem.cssselect(REVIEW_TITLE)
        if title_elem:
            # Title often includes rating text, extract just the title
            title_text = title_elem[0].text_content().strip()
            # Remove rating prefix like "5.0 out of 5 stars"
            title_text = re.sub(r'^\d+\.?\d*\s*out\s*of\s*5\s*stars?\s*', '', title_text)
            self.title = title_text.strip()

        # Date
        date_elem = elem.cssselect(REVIEW_DATE)
        if date_elem:
            date_text = date_elem[0].text_content().strip()
            # Extract date from text like "Reviewed in the United States on December 3, 2024"
            match = re.search(r'on\s+(.+)$', date_text)
            if match:
                self.date = match.group(1).strip()
            else:
                self.date = date_text

        # Review text
        body_elem = elem.cssselect(REVIEW_BODY)
        if body_elem:
            self.text = body_elem[0].text_content().strip()

        # Verified purchase
        verified_elem = elem.cssselect(REVIEW_VERIFIED)
        self.verified = len(verified_elem) > 0

        # Helpful count
        helpful_elem = elem.cssselect(REVIEW_HELPFUL)
        if helpful_elem:
            helpful_text = helpful_elem[0].text_content()
            match = re.search(r'([\d,]+)\s*people?\s*found', helpful_text)
            if match:
                self.helpful_count = int(match.group(1).replace(',', ''))
            elif 'One person' in helpful_text:
                self.helpful_count = 1
            else:
                self.helpful_count = 0
        else:
            self.helpful_count = 0

        # Review images
        img_elems = elem.cssselect(REVIEW_IMAGES)
        if img_elems:
            self.images = []
            for img in img_elems:
                src = img.get('src')
                if src:
                    self.images.append(src)
            if not self.images:
                self.images = None

        # Mark as valid if we have at least text or title
        if self.text or self.title:
            self._is_valid = True


class AmzReviews(AmzBase):
    """
    Collection of customer reviews for a product.

    Attributes:
        reviews (list): List of AmzReview objects
        total_count (int): Total number of reviews
        feature_ratings (dict): Feature-specific ratings (e.g., {"Sound quality": 4.5})
    """

    reviews = None
    total_count = None
    feature_ratings = None

    _all_attrs = ['reviews', 'total_count', 'feature_ratings']

    def __init__(self, html_element=None):
        """
        Initialize AmzReviews.

        Args:
            html_element: lxml HTML element from reviews page (optional)
        """
        super().__init__()
        if html_element is not None:
            self._parse_from_html(html_element)

    def _parse_from_html(self, root):
        """
        Parse reviews from HTML element.

        Args:
            root: lxml HTML root element from reviews page
        """
        try:
            from amzsear.core.selectors import REVIEW_ITEM, REVIEW_COUNT
        except ImportError:
            from .selectors import REVIEW_ITEM, REVIEW_COUNT

        # Parse individual reviews
        review_elems = root.cssselect(REVIEW_ITEM)
        if review_elems:
            self.reviews = []
            for elem in review_elems:
                review = AmzReview(elem)
                if review.is_valid():
                    self.reviews.append(review)

        if not self.reviews:
            self.reviews = []

        # Total count
        count_elem = root.cssselect(REVIEW_COUNT)
        if count_elem:
            count_text = count_elem[0].text_content()
            match = re.search(r'[\d,]+', count_text)
            if match:
                self.total_count = int(match.group().replace(',', ''))

        # Feature ratings (these are often in a separate widget)
        # Look for feature rating buttons
        feature_buttons = root.cssselect('[data-hook="cr-insights-widget-aspects"] button')
        if feature_buttons:
            self.feature_ratings = {}
            for btn in feature_buttons:
                text = btn.text_content()
                # Extract feature and count, e.g., "Sound quality (2K)"
                match = re.match(r'([^(]+)\s*\(([^)]+)\)', text)
                if match:
                    feature = match.group(1).strip()
                    count = match.group(2).strip()
                    self.feature_ratings[feature] = count

        if not self.feature_ratings:
            self.feature_ratings = None

        # Mark as valid if we have reviews
        if self.reviews:
            self._is_valid = True

    def __len__(self):
        """Return number of reviews."""
        return len(self.reviews) if self.reviews else 0

    def __iter__(self):
        """Iterate over reviews."""
        return iter(self.reviews) if self.reviews else iter([])
