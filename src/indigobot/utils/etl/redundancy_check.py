"""
These functions are meant to read tracked URLs from a specified file, checks for duplicates,
append new unique URLs, and saves the updated list back into the file.
"""

from indigobot.config import TRACKED_URLS_FILE


def check_duplicate(urls):
    """
    Check which URLs are new by comparing with previously tracked URLs and update the tracked list.

    :param urls: List of URLs to check
    :type urls: list[str]
    :return: List of URLs that are not yet tracked
    :rtype: list[str]
    """
    urls_to_load = []

    try:
        tracked_urls = file_to_list()
    except FileNotFoundError:
        tracked_urls = []

    for url in urls:
        if url in tracked_urls:
            continue
        else:
            tracked_urls.append(url)
            urls_to_load.append(url)

    with open(TRACKED_URLS_FILE, "w") as f:
        for line in tracked_urls:
            f.write(f"{line}\n")

    return urls_to_load


def file_to_list():
    """
    Read the tracked URL file and return each line as a list element.

    :return: List of URLs from the tracked URLs file
    :rtype: list[str]
    """
    with open(TRACKED_URLS_FILE, "r") as file:
        lines = file.readlines()
        # Remove newline characters from each line
        return [line.strip() for line in lines]
