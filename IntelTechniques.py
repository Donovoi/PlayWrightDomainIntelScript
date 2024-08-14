"""
This module automates the process of capturing screenshots and saving HTML content from domains.
"""

import os
import time
import urllib.parse
from playwright.sync_api import sync_playwright


def create_dir(domain):
    """
    Creates a directory for the given domain if it doesn't exist.
    """
    directory = os.path.join("results", domain)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def sanitize_filename(filename):
    """
    Sanitizes the filename by allowing only alphanumeric characters, spaces, periods, and underscores.
    """
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()


def save_page_content(page, directory, url):
    """
    Saves the screenshot, HTML content, and text content of a page.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        filename = sanitize_filename(
            parsed_url.netloc + parsed_url.path.replace("/", "_"))

        # Save the screenshot
        screenshot_path = os.path.join(directory, f"{filename}.png")
        page.screenshot(path=screenshot_path, full_page=True, timeout=60000)

        # Save the HTML content
        html_path = os.path.join(directory, f"{filename}.html")
        with open(html_path, "w", encoding="utf-8") as html_file:
            html_file.write(page.content())

        # Save the text content
        text_path = os.path.join(directory, f"{filename}.txt")
        with open(text_path, "w", encoding="utf-8") as text_file:
            text_file.write(page.inner_text("body"))
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Failed to save content for URL '{url}': {str(e)}")


def run(pw):
    """
    Main function to run the Playwright script, automate browsing,
    and save the content of pages.
    """
    with open("urls.txt", "r", encoding="utf-8") as f:
        domains = f.read().splitlines()

    for domain in domains:
        # Start a new browser session for each domain
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        base_url = "https://inteltechniques.com/tools/Domain.html"

        directory = create_dir(domain)

        # Go to the base URL and fill all fields
        page.goto(base_url)
        page.fill('input[id="PopAll"]', domain)
        page.click('input[value="Populate All"]')

        # Trigger all search functions in parallel
        for i in range(1, 69):  # 1 to 68 inclusive
            search_function = f"doSearch{i:02d}"
            try:
                print(f"Calling JavaScript function: {search_function}")

                # Call the JavaScript function on the page (opens a new tab)
                page.evaluate(f"{search_function}()")

            except (RuntimeError, ValueError) as e:
                print(f"Function '{search_function}' could not be processed: {str(e)}")

        # Wait for a specific amount of time to allow all tabs to load
        time.sleep(10)  # Wait 10 seconds (adjust if necessary)

        # Ensure all tabs are loaded
        for i in range(1, len(context.pages)):
            try:
                new_page = context.pages[i]
                new_page.wait_for_load_state('networkidle', timeout=60000)
                url = new_page.url
                save_page_content(new_page, directory, url)
            except (OSError, RuntimeError) as e:
                print(f"Failed to save content for tab {i}: {str(e)}")

        # Close the entire browser session
        browser.close()


with sync_playwright() as playwright:
    run(playwright)
