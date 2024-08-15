import os
import time
import urllib.parse
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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

        if not page.is_closed():
            screenshot_path = os.path.join(directory, f"{filename}.png")
            page.wait_for_selector("body", timeout=60000)

            retries = 3
            while retries > 0:
                try:
                    page.screenshot(path=screenshot_path,
                                    full_page=True, timeout=60000)
                    break
                except PlaywrightTimeoutError as e:
                    retries -= 1
                    print(f"Retrying screenshot due to error: {str(e)}")
                    if retries == 0:
                        print(
                            f"Failed to take screenshot after retries for URL: {url}")
                        return

            html_path = os.path.join(directory, f"{filename}.html")
            with open(html_path, "w", encoding="utf-8") as html_file:
                html_file.write(page.content())

            text_path = os.path.join(directory, f"{filename}.txt")
            with open(text_path, "w", encoding="utf-8") as text_file:
                text_file.write(page.inner_text("body"))
        else:
            print(f"Page closed before content could be saved for URL: {url}")
    except (OSError, ValueError, RuntimeError, PlaywrightTimeoutError) as e:
        print(f"Failed to save content for URL '{url}': {str(e)}")


def run_search(page, domain, search_function):
    print(
        f"Running search with function: {search_function} for domain: {domain}")

    for _ in range(3):  # Allow up to 3 retries
        try:
            # Directly use the domain in the JavaScript function
            script = f"""
            (function() {{
                var domain = '{domain}';
                if (typeof {search_function} === 'function') {{
                    {search_function}(domain);
                }} else {{
                    throw new Error('Function {search_function} is not defined.');
                }}
            }})();
            """
            page.evaluate(script)

            # Wait for the new page or tab to open
            new_page = page.context.wait_for_event('page')
            new_page.wait_for_load_state()

            print(f"New Page URL: {new_page.url}")  # Debugging output
            time.sleep(5)  # Wait for the page to fully load

            # Check if the domain is in the new page content
            if domain not in new_page.content():
                print(
                    f"Search term '{domain}' not found on the new page: {new_page.url}. Retrying...")
                continue  # Retry if the term isn't found

            # Save the new page content
            save_page_content(new_page, create_dir(domain), new_page.url)
            return  # Exit if successful

        except (OSError, RuntimeError, PlaywrightTimeoutError) as e:
            print(f"Failed to process page: {str(e)}. Retrying...")
            continue  # Retry the loop on failure

    print(f"Failed to find search term '{domain}' after multiple attempts.")


def run(pw):
    with open("urls.txt", "r", encoding="utf-8") as f:
        domains = f.read().splitlines()

    for domain in domains:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()

        page = context.new_page()

        # Load the base page before attempting to evaluate JavaScript functions
        base_url = "https://inteltechniques.com/tools/Domain.html"
        page.goto(base_url)
        # Ensure the page is fully loaded
        page.wait_for_selector("body", timeout=10000)

        for i in range(1, 69):
            search_function = f"doSearch{i:02d}"
            try:
                function_exists = page.evaluate(
                    f"typeof {search_function} === 'function'")
                if function_exists:
                    print(f"Calling JavaScript function: {search_function}")
                    run_search(page, domain, search_function)
                else:
                    print(
                        f"Function {search_function} is not defined on the page.")
            except (RuntimeError, ValueError) as e:
                print(
                    f"Function '{search_function}' could not be processed: {str(e)}")

        browser.close()


with sync_playwright() as playwright:
    run(playwright)
