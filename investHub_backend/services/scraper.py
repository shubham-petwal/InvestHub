import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import random
import re

def read_urls_from_excel(file_path: str) -> List[str]:
    """Read URLs from first column in Excel file"""
    try:
        # Read Excel file and get first column
        df = pd.read_excel(file_path)
        # Get the first column values, dropping any NaN values
        urls = df.iloc[:, 0].dropna().tolist()
        
        # Process URLs to ensure they have http:// or https://
        processed_urls = []
        for url in urls:
            # Strip any whitespace
            url = url.strip()
            # Add http:// if no protocol is specified
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            processed_urls.append(url)
            
        # print("Processed URLs:", processed_urls)  # For debugging
        return processed_urls
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return []

def extract_company_name(url: str) -> str:
    try:
        # Remove http://, https://, and www.
        cleaned_url = re.sub(r'https?://(www\.)?', '', url.lower())
        # Get the domain part (before the next slash or end of string)
        domain = cleaned_url.split('/')[0]
        # Get the part before the last dot (remove .com, .org, etc.)
        company_name = domain.split('.')[-2]
        # Clean up and capitalize
        company_name = company_name.replace('-', ' ').replace('_', ' ').title()
        return company_name
    except Exception as e:
        print(f"Error extracting company name from {url}: {e}")
        return "Unknown Company"

def scrape_website(url: str) -> Dict:
    """Scrape data from a single website"""
    try:
        print("the url is: ",url)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Example: Extract text from paragraphs
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        
        company_name = extract_company_name(url)
        print(f"Successfully scraped: {company_name}")
        return {
            "company_name": company_name,
            "url": url,
            "text": text
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return {
            "company_name": "Unknown Company",
            "url": url,
            "error": str(e)
        }

def scrape_all_websites(file_path: str) -> List[Dict]:
    """Scrape data from all websites listed in Excel file"""
    urls = read_urls_from_excel(file_path)
    print("The total length of urls are: ", len(urls))
    print(f"Found {len(urls)} URLs to scrape")
    results = []
    
    for url in range(1):
        print(f"Scraping: {url}")
        result = scrape_website("https://www.coinbase.com/ventures")
        results.append(result)
    print("The results are: ", results)
    
    return results 