import requests
from bs4 import BeautifulSoup
import json
import time # Import for polite scraping delay

def scrape_page(url, output_filename='ucmerced_data.json'):
    """
    Scrapes a single page, extracts information (e.g., all paragraph text),
    and saves the extracted data to a JSON file.

    Args:
        url (str): The URL of the page to scrape.
        output_filename (str): The name of the JSON file to save data to.
    """
    try:
        # 1. Fetch HTML Content
        # Mimic a common browser user-agent to be polite and avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # 2. Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- DATA EXTRACTION LOGIC ---
        # **Note: This section requires inspection of the actual UC Merced webpage.**
        # Example: Extracting the page title and all paragraph texts
        page_title = soup.find('title').text if soup.find('title') else 'No Title'
        
        # Example: Extract all paragraph text. You'll need to use more specific 
        # selectors (like class names) for a real-world page to target specific data.
        all_paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        
        # Structure the extracted data
        scraped_data = {
            'url': url,
            'title': page_title,
            'paragraphs': all_paragraphs,
            # Add more specific fields here based on your target page (e.g., course names, departments)
        }

        # 3. Save Data to JSON File
        with open(output_filename, 'w', encoding='utf-8') as f:
            # Use json.dump for saving a dictionary to a file
            json.dump(scraped_data, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully scraped {url} and saved data to {output_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Execution ---
if __name__ == "__main__":
    # A starting URL for UC Merced's academic catalog.
    # You would need to check the robots.txt for the specific site you are scraping.
    UCM_URL = 'https://catalog.ucmerced.edu/' 
    OUTPUT_FILE = 'ucmerced_catalog_info.json'
    
    scrape_page(UCM_URL, OUTPUT_FILE)
    
    # Be a polite scraper: add a delay if you were to crawl multiple pages
    # time.sleep(2) 
    
# To scrape multiple pages (a simple "crawler"), you would typically:
# 1. Maintain a list/set of URLs to visit (`to_visit`).
# 2. Maintain a set of already visited URLs (`visited`).
# 3. Modify `scrape_page` to extract new links (e.g., all <a> tags with 'href') 
#    and add them to `to_visit` if they haven't been visited and are within the allowed domain.
# 4. Loop until `to_visit` is empty, calling `scrape_page` (or a modified crawling function)
#    and managing the visited set.