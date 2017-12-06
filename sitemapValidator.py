#!/usr/bin/env python3

# This gets the links of all sitemaps from ifixit.com/sitemap.xml, downloads
# them, and then checks each link response for a 200 code and a matching
# canonical url in the HTML.

from urllib.request import urlopen, urlretrieve
import xml.etree.ElementTree as ET
import re

import getBadSitemapLinks

def get_sitemap(url):
    """Pull down the sitemap XML file at the given url and save to a file"""
    outfile = get_filename_from_sitemap(url)
    print('Downloading ' + outfile + '...')

    urlretrieve(url, outfile)

def get_filename_from_sitemap(sitemap_url):
    """Extract the filename from the sitemap url"""
    matches = re.search('\/([a-z0-9_]+\.xml)$', sitemap_url)

    if matches:
        return matches.group(1)
    return None

def validate_sitemap_index():
    sitemap_index_url = 'https://www.ifixit.com/sitemap.xml'

    with urlopen(sitemap_index_url) as res:
        xml = res.read().decode('utf-8')

    tree = ET.fromstring(xml)
    namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    sitemap_urls = list(map(lambda url_element: url_element.text,
            tree.findall("./sitemap:sitemap/sitemap:loc", namespaces)))
    print(sitemap_urls)

def validate_sitemap():
    sitemap_index_url = 'https://www.ifixit.com/sitemap.xml'

    with urlopen(sitemap_index_url) as res:
        xml = res.read().decode('utf-8')

    tree = ET.fromstring(xml)
    namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    sitemap_urls = list(map(lambda url_element: url_element.text,
            tree.findall("./sitemap:sitemap/sitemap:loc", namespaces)))

    # Download sitemap files
    for url in sitemap_urls:
        get_sitemap(url)

    # Get file names from urls
    sitemap_filenames = list(map(get_filename_from_sitemap, sitemap_urls))

    # Find all urls in the sitemap XML document and write any bad links to file.
    for filename in sitemap_filenames:
        print("Getting bad links for " + filename + " sitemap")
        urls = getBadSitemapLinks.get_urls_from_file(filename)
        getBadSitemapLinks.get_bad_links(urls)

validate_sitemap()
