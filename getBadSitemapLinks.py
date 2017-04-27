#!/usr/bin/env python3

# This script takes a sitemap XML filename and visits the URL from each <loc>
# tag.
#
# It records the sitemap URL, canonical URL, and response code from each URL
# GET and writes any responses that have a bad response code or
# sitemap/canonical URL mismatch to a JSON file.

import re
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from urllib.request import urlopen
from urllib.error import HTTPError

from multiprocessing import Pool

def get_urls_from_file(filename):
    """Get a list of all URLs from the given XML file"""
    tree = ET.parse(filename)
    namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    root = tree.getroot()
    return list(map(lambda x: x.text,
        root.findall('./sitemap:url/sitemap:loc', namespaces)))

def grab_canonical_from_html(html):
    """Extract the canonical URL from the given HTML document"""
    parsed_dom = BeautifulSoup(html, 'lxml')
    return parsed_dom.find(id='canonical-link').get('href')

def map_url_status(sitemap_url):
    """Map the given sitemap_url into a dictionary of the format
       {'sitemap_url': '...',
        'canonical_url': '...',
        'code': xxx}
    """
    try:
        with urlopen(sitemap_url) as res:
            html = res.read().decode('utf-8')
            return {'sitemap_url': sitemap_url,
                    'canonical_url': grab_canonical_from_html(html),
                    'code': res.code}
    except HTTPError as e:
        print('Error!', e)
        return {'sitemap_url': sitemap_url,
                'canonical_url': '',
                'code': e.code}

def has_bad_response_code(status):
    return status['code'] != 200

def has_url_mismatch(status):
    success_code = status['code'] == 200
    bad_canonical = status['sitemap_url'] != status['canonical_url']

    return success_code and bad_canonical

# For each URL in the sitemap file, return a
#   sitemap_url
#   canonical_url
#   code
#
# Parallelize this because we can.
# NOTE: If you run this from outside of the office you WILL get rate limited.
def get_bad_links(urls):
    with Pool(20) as pool:
        statuses = pool.map(map_url_status, urls)

    # Filter statuses into lists of bad response codes and url mismatches
    bad_code_statuses = list(filter(has_bad_response_code, statuses))
    url_mismatch_statuses = list(filter(has_url_mismatch, statuses))

    # Grab the filename without the .xml extension
    outfile_name = re.search('([a-z0-9_]+)\.xml$', filename).group(1)

    # Write out the list of bad code statuses and url mismatch statuses to their
    # own respective JSON files.
    with open(outfile_name + '-bad-code.json', 'w') as out:
        json.dump(bad_code_statuses, out)

    with open(outfile_name + '-url-mismatch.json', 'w') as out:
        json.dump(url_mismatch_statuses, out)

# This file can be run as a standalone script, or as a module.
# When run as a script, take a filename argument.
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: ./get_bad_sitemap_links.py <sitemap xml file>")
        exit()

    filename = sys.argv[1]
    urls = get_urls_from_file(filename)
    get_statuses(urls)
