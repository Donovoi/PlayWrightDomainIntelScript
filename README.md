# 📸 Domain Screenshot & HTML Capture Tool

Welcome to the Domain Screenshot & HTML Capture Tool! This Python module automates the process of capturing screenshots, saving HTML content, and extracting text content from specified domains. This is an efficient way to document the visual and textual content of websites for analysis or archival purposes.

## 🚀 Getting Started

### Prerequisites

Before you can use this module, make sure you have the following installed:

- **Python 3.7+** 🐍
- **Playwright** 🎭

You can install the necessary packages with:

```bash
pip install playwright
```

After installing Playwright, ensure that the required browser binaries are installed:

```bash
python -m playwright install
```

### Project Structure

- `urls.txt` - A text file containing a list of domains you want to capture. Each domain should be on a new line.
- `results/` - The directory where all screenshots, HTML files, and text files will be saved.

### How It Works

This tool works by:

1. **Reading domains** from the `urls.txt` file.
2. **Launching a browser session** using Playwright.
3. **Navigating** to the specified tool's base URL.
4. **Populating all fields** with the domain and triggering the available search functions.
5. **Capturing screenshots**, saving HTML content, and extracting text content from each opened tab.
6. **Saving** all these files into a directory named after each domain inside the `results/` folder.

### Running the Script

To run the script, use the following command:

```bash
python script_name.py
```

Replace `script_name.py` with the actual name of your Python file.

## 📂 Output

For each domain, the tool will create a directory under `results/` named after the domain. Inside this directory, you will find:

- **Screenshots** (`.png`): Full-page screenshots of the web pages.
- **HTML Files** (`.html`): The complete HTML content of the web pages.
- **Text Files** (`.txt`): The extracted text content from the body of the web pages.

## ⚙️ Functions Overview

### `create_dir(domain)`
Creates a directory for the given domain if it doesn't already exist.

### `sanitize_filename(filename)`
Sanitizes the filename by allowing only alphanumeric characters, spaces, periods, and underscores.

### `save_page_content(page, directory, url)`
Saves the screenshot, HTML content, and text content of a page.

### `run(pw)`
Main function that runs the Playwright script, automates browsing, and saves the content of pages.

## 📝 Notes

- The script runs in non-headless mode by default. You can change this by setting `headless=True` in the `browser = pw.chromium.launch(headless=False)` line if you don't need to see the browser in action.
- Adjust the `time.sleep(10)` value to ensure all tabs have enough time to load before capturing content.
- Each domain's directory will contain the saved files using sanitized filenames based on the URL's netloc and path.

## 🛠 Troubleshooting

- **Failed to Save Content**: If you encounter errors related to saving content, ensure that your internet connection is stable and the domains in `urls.txt` are valid and reachable.
- **Browser Binaries**: Make sure that Playwright browser binaries are correctly installed. Use the command `python -m playwright install` if not done already.

## 📬 Contribution & Support

Feel free to contribute by submitting a pull request or reporting issues. If you need help, don't hesitate to reach out!

---

**Happy Browsing!** 🌐✨
