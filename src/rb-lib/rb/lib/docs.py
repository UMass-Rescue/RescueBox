import requests
import logging
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)

BASE_WIKI_URL = "https://github.com/UMass-Rescue/RescueBox/wiki"


def get_wiki_page_links():
    """
    Fetches all subpage links from the GitHub Wiki main page.
    """
    try:
        response = requests.get(BASE_WIKI_URL, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all links to subpages (they contain '/RescueBox/wiki/' in href)
        wiki_links = soup.find_all("a", href=True)

        # Extract the full URLs of each wiki page
        page_urls = [
            BASE_WIKI_URL
            + "/"
            + link["href"].split("/")[-1]  # Append page name to base URL
            for link in wiki_links
            if "/RescueBox/wiki/" in link["href"]
        ]

        return page_urls

    except requests.RequestException as e:
        logger.debug("Error fetching wiki page links: %s", e)
        return []


def download_wiki_page(url):
    """
    Downloads and extracts markdown content from a given GitHub wiki page.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract markdown content (GitHub wikis use `markdown-body` class)
        wiki_content_div = soup.find("div", class_="markdown-body")

        if not wiki_content_div:
            logger.debug("Warning: No markdown content found on %s", url)
            return None

        return wiki_content_div.get_text().strip()

    except requests.RequestException as e:
        logger.error("Error downloading %s %s", url, e)
        return None

def get_rescuebox_code():
    import os
    dir_path = os.path.join("src")
    file_data = {}
    for root, _, files in os.walk(dir_path):
        for filename in files:
            if not str(filename).endswith('.py') or 'lib' in str(filename):
                continue
            filepath = os.path.join(root, filename)
            with open(filepath, 'r') as file:
                file_data[filepath] = file.readlines()
    return file_data


def download_all_wiki_pages():
    """
    Fetches all wiki pages and extracts their markdown content.
    """
    wiki_pages = get_wiki_page_links()
    wiki_data = {}

    for page_url in wiki_pages:
        page_name = page_url.split("/")[-1]  # Extract the page name
        if page_name == '_history':
            continue
        logger.debug("Fetching: %s", page_name)
        markdown_text = download_wiki_page(page_url)

        if markdown_text:
            parts = markdown_text.split('\n')
            wiki_data[page_name] = parts

    return wiki_data


# Example Usage
all_wiki_content = download_all_wiki_pages()

