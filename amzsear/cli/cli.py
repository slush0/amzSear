try:
    from amzsear import AmzSear, AmzProduct, DetailLevel
    from amzsear.core.consts import DEFAULT_REGION, REGION_CODES, PRODUCT_URL
    from amzsear.core import build_base_url
except ImportError:
    from .amzsear import AmzSear, AmzProduct, DetailLevel
    from .amzsear.core.consts import DEFAULT_REGION, REGION_CODES, PRODUCT_URL
    from .amzsear.core import build_base_url

import argparse
import webbrowser
import json
import sys
import csv

"""
"""
def run(*passed_args):
    parser = get_parser()
    args = parser.parse_args(*passed_args) # the parser defaults to sys args if nothing passed
    args = vars(args)

    # Handle product lookup mode
    if args.get('product'):
        run_product(args)
        return

    # Validate: query is required for search mode
    if not args.get('query'):
        parser.error('query is required (or use --product ASIN)')

    # Handle search mode
    amz_args = {x:y for x,y in args.items() if x not in ['item','output','dont_open','product']}
    out = AmzSear(**amz_args)

    if args['item'] != None:
        # single item selection
        prod = out[args['item']]
        out = AmzSear(products=[prod]) # error raised if not found
        out._urls = [prod.product_url]


    # handle output types
    if args['output'] == 'short':
        print_short(out)
    if args['output'] == 'verbose':
        print_verbose(out)
    elif args['output'] == 'csv':
        print_csv(out)
    elif args['output'] == 'json':
        print_json(out)
    # elif args['output'] == 'quite' --> no output


    if args['dont_open'] != True:
        for url in out._urls:
            webbrowser.open(url)


def run_product(args):
    """Handle product lookup by ASIN."""
    asin = args['product']
    region = args.get('region', DEFAULT_REGION)

    # Create a minimal AmzProduct with just the product_url set
    product = AmzProduct()
    base_url = build_base_url(region)
    product.product_url = PRODUCT_URL % (base_url, asin)
    product._region = region
    product._is_valid = True

    # Fetch BASIC level details
    product.fetch_details(level=DetailLevel.BASIC, region=region)

    # Handle output types
    if args['output'] == 'short':
        print_product_short(product)
    elif args['output'] == 'verbose':
        print_product_verbose(product)
    elif args['output'] == 'csv':
        print_product_csv(product)
    elif args['output'] == 'json':
        print_product_json(product)
    # elif args['output'] == 'quiet' --> no output

    if args['dont_open'] != True:
        webbrowser.open(product.product_url)



def get_parser():
    parser = argparse.ArgumentParser(description='The unofficial Amazon search CLI')

    parser.add_argument('query', type=str, nargs='?', default=None,
        help='The query string to be searched')
    parser.add_argument('-P','--product', type=str, default=None,
        help='Fetch product details by ASIN instead of searching')
    parser.add_argument('-p','--page', type=int,
        help='The page number to be searched (defaults to 1)', default=1)
    parser.add_argument('-i','--item', type=str,
        help='The item index to be displayed (relative to the page)', default=None)
    parser.add_argument('-r','--region', type=str, choices=REGION_CODES,
        default=DEFAULT_REGION, help='The amazon country/region to be searched')

    parser.add_argument('-d','--dont-open', action='store_true',
        help='Stop the page from opening in the default browser')

    parser.add_argument('-o','--output', type=str, choices=['short','verbose','quiet','csv','json'],
        default='short', help='The output type to be displayed (defaults to short)')

    return parser


def print_csv(cls):
    # flattens to list of dicts with index value
    data = [{**v.to_dict(flatten=True),**({'_index' : k})} for k,v in cls.items()]

    # print with all quotes
    writer = csv.DictWriter(sys.stdout, data[0].keys(), quoting=csv.QUOTE_ALL) 
    writer.writeheader()
    writer.writerows(data)

def print_json(cls):
    print(json.dumps({k: v.to_dict() for k,v in cls.items()}))

def print_verbose(cls):
    print(cls)


def print_short(cls):
    fields = ['ASIN','Title','Prices','Rating']

    rows = [{f:f for f in fields}]
    for index, product in cls.items():
        temp_dict = {}

        temp_dict['ASIN'] = product.get_asin() or index[:10]

        # get price in format '$nn.nn-$mm.mm'
        price_tup = {product.prices[k]:product.get_prices(k) for k in product.prices}
        if len(price_tup) > 0:
            price_tup = (min(price_tup, key=lambda x: price_tup[x]), max(price_tup, key=lambda x: price_tup[x]))
            if price_tup[0] == price_tup[-1]:
                temp_dict['Prices'] = price_tup[0] # one price
            else:
                temp_dict['Prices'] = price_tup[0] + ' - ' + price_tup[-1] # range of prices
        else:
            temp_dict['Prices'] = '------------'
        temp_dict['Title'] = product.get('title','----------')[:50] # limit title length
    
        temp_dict['Rating'] = product.get('rating','-----')
        if temp_dict['Rating'] != '-----':
            temp_dict['Rating'] = temp_dict['Rating'].get_star_repr()

        rows.append(temp_dict)

    format_str = []
    for field in fields:
        #get longest in each field into format_str
        format_str.append('{:%d}' % (max(len(x[field]) for x in rows)+ 1))
    format_str = ' '.join(format_str)

    for row in rows:
        print(format_str.format(*[row.get(x,'') for x in fields])) # print in order


# Product output formatters
def print_product_json(product):
    """Output product details as JSON."""
    data = {'asin': product.get_asin()}
    data['product_url'] = product.product_url

    if product.details:
        data['details'] = product.details.to_dict()

    print(json.dumps(data, indent=2))


def print_product_csv(product):
    """Output product details as CSV."""
    data = {'asin': product.get_asin(), 'product_url': product.product_url}

    if product.details:
        details_dict = product.details.to_dict(flatten=True)
        # Flatten lists to strings for CSV
        for k, v in details_dict.items():
            if isinstance(v, list):
                details_dict[k] = '; '.join(str(x) for x in v)
            elif isinstance(v, dict):
                details_dict[k] = json.dumps(v)
        data.update(details_dict)

    writer = csv.DictWriter(sys.stdout, data.keys(), quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows([data])


def print_product_verbose(product):
    """Output full product details."""
    print(f"ASIN: {product.get_asin()}")
    print(f"URL:  {product.product_url}")
    print()

    if product.details:
        print(product.details)
    else:
        print("No details available")


def print_product_short(product):
    """Output product summary."""
    asin = product.get_asin() or 'N/A'
    details = product.details

    print(f"ASIN:   {asin}")

    if details:
        title = details.full_title or 'N/A'
        if len(title) > 70:
            title = title[:67] + '...'
        print(f"Title:  {title}")

        brand = details.brand or 'N/A'
        print(f"Brand:  {brand}")

        if details.average_rating:
            rating_str = f"{details.average_rating:.1f}/5"
            if details.review_count:
                rating_str += f" ({details.review_count:,} reviews)"
            print(f"Rating: {rating_str}")

        if details.about_items:
            print(f"\nAbout this item ({len(details.about_items)} points):")
            for i, item in enumerate(details.about_items[:3], 1):
                text = item[:80] + '...' if len(item) > 80 else item
                print(f"  {i}. {text}")
            if len(details.about_items) > 3:
                print(f"  ... and {len(details.about_items) - 3} more")

        if details.technical_details:
            print(f"\nTechnical details ({len(details.technical_details)} fields)")
    else:
        print("No details available (fetch may have failed)")


if __name__ == '__main__':
    run()
