import yaml
import math
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import time

#TODO:
# make it click around instead of subpages


def is_valid_url(url, main_domain, exclude_pattern):
    parsed = urlparse(url)
    return (
        bool(parsed.netloc)
        and parsed.netloc.endswith(main_domain)
        and not url.startswith(exclude_pattern)
    )


def is_image_url(url):
    # Check if URL is an image (png, jpg, jpeg, etc.)
    return url.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg"))


def scrape_site(urls, exclude_pattern, output_path):
    visited = set()
    to_visit = set(urls)
    main_domain = urlparse(urls[0]).netloc

    scraped_text = ""

    while to_visit:
        url = to_visit.pop()
        visited.add(url)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            }
            last_request =  datetime.now()
            response = requests.get(url, headers=headers)
            if response.status_code > 200:
                print(f"Request failed for {url}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract and print text
            text = soup.get_text(separator="\n", strip=True) + "\n"
            scraped_text += text
            print(f"Text from {url}:")
            print(text[:500])  # Print first 500 characters of text for demonstration

            # follow progress
            with open(output_path, "wb") as file:
                file.write(scraped_text.encode("utf-8"))


            # Find and process all links
            for link in soup.find_all("a", href=True):
                absolute_link = urljoin(url, link["href"])
                if is_valid_url(absolute_link, main_domain, exclude_pattern):
                    if url in visited or is_image_url(url):
                        continue
                    else:
                        to_visit.add(absolute_link)

            # ensure we don't make more than 1 request per 10 seconds
            if datetime.now() - last_request < timedelta(seconds=10):
                time.sleep(math.ceil(10 - (datetime.now()-last_request).total_seconds()) )

            

        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")

    return scraped_text


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Scrape content of config-provided urls')

    # Required positional argument
    parser.add_argument('--page_name', '-pn', default="lovdata", type=str, help='Page name to find correct config')
    args = parser.parse_args()

    page_name = args.page_name
    # Load the YAML file
    with open(Path().cwd() / "configs" / f'{page_name}_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    start_timestamp = datetime.now()
    output_path = f"experiments/scraped_{page_name}_{start_timestamp.year}-{start_timestamp.month}-{start_timestamp.day}-{start_timestamp.hour}-{start_timestamp.minute}.txt"
    scraped_text = scrape_site(config['urls'], " ", output_path=output_path)
    
    
