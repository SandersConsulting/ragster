import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time


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


def scrape_site(start_url, exclude_pattern):
    visited = set()
    to_visit = {start_url}
    main_domain = urlparse(start_url).netloc

    scraped_text = ""

    while to_visit:
        url = to_visit.pop()
        visited.add(url)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            }
            response = requests.get(url, headers=headers)
            
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract and print text
            text = soup.get_text(separator=" ", strip=True)
            scraped_text += text
            print(f"Text from {url}:")
            print(text[:500])  # Print first 500 characters of text for demonstration

            # Find and process all links
            for link in soup.find_all("a", href=True):
                absolute_link = urljoin(url, link["href"])
                if is_valid_url(absolute_link, main_domain, exclude_pattern):
                    if url in visited or is_image_url(url):
                        continue
                    else:
                        to_visit.add(absolute_link)

        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")

    return scraped_text


start_url = "https://21st.bio/"
scraped_text = scrape_site(start_url, "")
from datetime import datetime
timestamp = datetime.now()
with open(f"experiments/scraped_text_{timestamp.year}-{timestamp.month}-{timestamp.day}-{timestamp.hour}-{timestamp.minute}.txt", "w") as file:
    file.write(scraped_text)
