import os
import urllib.parse
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import time

logging.basicConfig(level=logging.DEBUG)


def create_dir(domain):
    directory = os.path.join("results", domain)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def sanitize_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()


def save_page_content(page, directory, url):
    try:
        parsed_url = urllib.parse.urlparse(url)
        filename = sanitize_filename(
            parsed_url.netloc + parsed_url.path.replace("/", "_"))

        if page.is_closed():
            logging.error(
                "Page is already closed for URL: %s. Cannot save content.", url)
            return

        screenshot_path = os.path.join(directory, "%s.png" % filename)
        page.wait_for_selector("body", timeout=60000)

        retries = 3
        while retries > 0:
            try:
                if not page.is_closed():
                    page.screenshot(path=screenshot_path,
                                    full_page=True, timeout=60000)
                    break
            except (PlaywrightTimeoutError, PlaywrightError) as e:
                retries -= 1
                logging.warning(
                    "Retrying screenshot due to error: %s. Retries left: %d", str(e), retries)

            if retries == 0:
                logging.error(
                    "Failed to take screenshot after retries for URL: %s", url)
                return

        if not page.is_closed():
            html_path = os.path.join(directory, "%s.html" % filename)
            with open(html_path, "w", encoding="utf-8") as html_file:
                html_file.write(page.content())

            text_path = os.path.join(directory, "%s.txt" % filename)
            with open(text_path, "w", encoding="utf-8") as text_file:
                text_file.write(page.inner_text("body"))
        else:
            logging.error("Page closed unexpectedly for URL: %s", url)
    except (OSError, ValueError, RuntimeError, PlaywrightTimeoutError, PlaywrightError) as e:
        logging.error("Failed to save content for URL '%s': %s", url, str(e))


def trigger_all_searches(page, domain, search_functions):
    logging.info("Triggering all search functions for domain: %s", domain)

    for search_function in search_functions:
        function_exists = page.evaluate(
            "typeof %s === 'function'" % search_function)
        if not function_exists:
            logging.warning(
                "Function %s is not defined on the page.", search_function)
            continue

        # Trigger the function with a small delay
        page.evaluate("""
        (function() {{
            try {{
                var domain = '%s';
                %s(domain);
            }} catch (e) {{
                console.error("Error: " + e.message);
            }}
        }})();
        """ % (domain, search_function))

        # Introduce a small delay between each search function call
        time.sleep(0.5)


def capture_pages(context, domain, max_retries=3):
    pages = context.pages[1:]  # Exclude the first page (main page)
    for page in pages:
        retries = max_retries
        while retries > 0:
            try:
                if page.is_closed():
                    logging.warning(
                        "Page is closed unexpectedly. Skipping further retries.")
                    break

                page.wait_for_load_state()
                logging.info("Capturing content for page: %s", page.url)

                # Verify that the page URL is correct before proceeding
                if domain in page.url or domain in page.content():
                    save_page_content(page, create_dir(domain), page.url)
                    break
                else:
                    logging.warning(
                        "Search term '%s' not found on the page or URL is incorrect: %s", domain, page.url)
                    retries -= 1
                    if retries > 0:
                        logging.info("Retrying... (%d retries left)", retries)
                        # Close the problematic page and open a new one
                        if not page.is_closed():
                            page.close()
                        new_page = context.new_page()
                        new_page.goto(page.url, timeout=60000)
                        page = new_page  # Replace the old page with the new one
            except PlaywrightError as e:
                if "ERR_CONNECTION_REFUSED" in str(e):
                    logging.error(
                        "Connection refused for page: %s. Skipping...", page.url)
                    break  # Skip this page if connection is refused
                else:
                    logging.warning(
                        "Timeout or error while loading page: %s", page.url)
                    retries -= 1
                    if retries > 0 and not page.is_closed():
                        logging.info("Retrying... (%d retries left)", retries)
                        page.reload()
            finally:
                if not page.is_closed():
                    page.close()

        if retries == 0:
            logging.error(
                "Failed to capture content after retries for page: %s", page.url)


def process_domain(domain, playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()

    try:
        page = context.new_page()
        logging.info(
            "Navigating to the Intel Techniques page for domain: %s", domain)

        page.goto("https://inteltechniques.com/tools/Domain.html", timeout=60000)
        page.wait_for_load_state('domcontentloaded')

        if page.url == "about:blank":
            logging.error("Page failed to load, URL is still 'about:blank'")
            return

        logging.info("Successfully loaded the page: %s", page.url)

        search_functions = ["doSearch%02d" % i for i in range(1, 69)]

        # Trigger all searches with staggered timing
        trigger_all_searches(page, domain, search_functions)

        # Wait for 20 seconds for pages to load
        page.wait_for_timeout(20000)

        # Capture content from all pages with retry mechanism
        capture_pages(context, domain)

    except PlaywrightTimeoutError as e:
        logging.error("Failed to load the page: %s", str(e))
    finally:
        context.close()
        browser.close()


def run(pw):
    with open("urls.txt", "r", encoding="utf-8") as f:
        domains = f.read().splitlines()

    for domain in domains:
        process_domain(domain, pw)


def main():
    with sync_playwright() as playwright:
        run(playwright)


if __name__ == "__main__":
    main()
