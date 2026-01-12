"""amzSear - The unofficial Amazon search CLI & Python API."""

__version__ = '3.0.0'

try:
    from amzsear.core.AmzSear import AmzSear
    from amzsear.core.AmzProduct import AmzProduct
    from amzsear.core.AmzProductDetails import AmzProductDetails
    from amzsear.core.AmzReviews import AmzReviews, AmzReview
    from amzsear.core.selectors import DetailLevel
except ImportError:
    from .core.AmzSear import AmzSear
    from .core.AmzProduct import AmzProduct
    from .core.AmzProductDetails import AmzProductDetails
    from .core.AmzReviews import AmzReviews, AmzReview
    from .core.selectors import DetailLevel

__all__ = [
    '__version__',
    'AmzSear',
    'AmzProduct',
    'AmzProductDetails',
    'AmzReviews',
    'AmzReview',
    'DetailLevel',
]
