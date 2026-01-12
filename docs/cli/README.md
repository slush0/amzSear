## CLI

The amzSear CLI is the main entry point for using the amzSear package. It is similar to the [original version](../../legacy/v1) and backwards has been maintained where possible. However some features had to be changed consequently some CLI commands had to be changed, as discussed [below](#comparison-to-version-1).

The CLI, in it's basic form can still be used in the following way:

```
$ amzsear 'Harry Potter Books'
```

<a name="usage"></a>
##### Usage

The extended amzSear usage can be seen by typing `amzsear` without any additional arguments.

```
usage: amzsear [-h] [-P ASIN] [-p PAGE] [-i ITEM]
               [-r {AU,BR,CA,CN,DE,ES,FR,IN,IT,JP,MX,NL,SG,UK,US}] [-b]
               [-o {short,verbose,quiet,csv,json}]
               [query]
```

###### Args
*query*: The query string to search Amazon.

###### Optional Args
*-h, --help*: Display extended help & usage information.
*-P ASIN, --product ASIN*: Fetch product details by ASIN instead of searching.
*-p NUM, --page NUM*: The page number to be searched (defaults to 1).
*-i ITEM, --item ITEM*: Select item by ASIN or numeric index (0-based position). If no item is specified, the entire page's products will be displayed.
*-r STR, --region STR*: The amazon country/region to be searched (defaults to US). For a list of countries to country code see the [region table](../regions.md).
*-b, --browser*: Open the product page in the default browser.
*-o STR, --output STR*: The output type to be displayed (defaults to short). Output types are as follows:
* *short*: A concise view of the title, price summary and rating.
* *verbose*: The complete amzSear representation taken from the core api representation.
* *quiet*: No output is produced.
* *csv*: A quoted csv of all products with with all fields flattened, including the index.
* *json*: A JSON object of all products with all fields with the product's index as the top-level key.

<a name="comparison-to-version-1"></a>
##### Comparison to Version 1

###### Verbose Argument
In the previous version of amzSear, a verbose option could be displayed by adding the `-v` argument. However this can now be done through the output argument. For example:
```
$ amzsear 'Harry Potter' --output verbose

	OR

$ amzsear 'Harry Potter' -o verbose
```

###### Quiet Argument
Similar to the verbose argument, a quiet option could be used in the previous version of amzSear by adding the `-q` argument. However this can now be done through the output argument. For example:
```
$ amzsear 'Harry Potter' --output quiet

	OR

$ amzsear 'Harry Potter' -o quiet
```

<a name="examples"></a>
##### Examples

###### Example 1
```
$ amzsear 'Harry Potter' -p 1

	OR

$ amzsear 'Harry Potter' --page 1
```
In the above example, the first page of results for the query `Harry Potter` will be displayed. The query `amzsear 'Harry Potter'` would have the same result as the default page number is 1.

###### Example 2
```
$ amzsear 'Harry Potter' -i 0

	OR

$ amzsear 'Harry Potter' -i B00728DYLA
```
This example will display the first item (index 0) or the item with ASIN B00728DYLA. The `-i` flag accepts both numeric index (0-based) and ASIN.

###### Example 3
```
$ amzsear 'Harry Potter' -r ES

	OR
    
$ amzsear 'Harry Potter' --region ES
```
Example 3 will display all results from the `Harry Potter` searching the Spanish Amazon website. 

###### Example 4
```
$ amzsear 'Harry Potter' -b

	OR

$ amzsear 'Harry Potter' --browser
```
This example will display the search results and open the product pages in the default browser. By default, the browser is not opened.

###### Example 5
```
$ amzsear 'Harry Potter' -o csv > harry_amzsear.csv

	OR
    
$ amzsear 'Harry Potter' --output csv > harry_amzsear.csv
```
In this example a csv of all products from the first page of search results is produced and then piped into a csv called `harry_amzsear.csv`.

###### Example 6
```
$ amzsear 'Harry Potter' -p 2 -i B00728DYLA --output json
```
In this example a JSON object of the item with ASIN B00728DYLA on page 2 is displayed.

###### Example 7
```
$ amzsear -P B00006IFHD
```
This example fetches detailed product information directly by ASIN, bypassing search. Returns brand, title, specs, bullet points, and review statistics.



