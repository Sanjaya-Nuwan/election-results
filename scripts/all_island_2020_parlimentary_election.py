import os
import requests
from bs4 import BeautifulSoup
import json
import logging
from electoral_district import lst

BASE_URL = "https://election.adaderana.lk/general-election-2020/"
TIMEOUT = 10
RESULTS_CLASS = 'all-island-results card widget-summery'
PARTY_CLASS = 'ele_result'
SUMMARY_CLASS = 'total-votes-summery'
LOG_FILE = 'scraper.log'
OUTPUT_DIR = '../data/Parliamentary Election Results - All Island - 2020'
JSON_FILENAME = 'All_island_result.json'

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_url(url):
    """Check if the URL is accessible and return the result's container."""
    try:
        res = requests.get(url, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        results_container = soup.find('div', class_=RESULTS_CLASS)
        return results_container
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve URL {url}: {e}")
        return None


def extract_party_data(block):
    """Extract party data from the block."""
    party_short = block.find('div', class_='candi_name').find('span').get_text(strip=True)
    tot_vote_div = block.find('div', class_='tot_vote')
    total_votes = tot_vote_div.find('div', class_='tot_vote_value')
    total_present = tot_vote_div.find('div', class_='tot_vote_present')
    seats = block.find('div', class_="ele_seats").find('span').get_text(strip=True)

    votes = total_votes['data-value']
    percentage = total_present['data-value']

    return {
        "party_short": party_short,
        "party_long": None,
        "votes": int(votes.strip().replace(',', '')),
        "percentage": float(percentage.strip()),
        "seats": int(seats),
        "candidates": [{}]
    }


def scrape_data(results_soup):
    """Scrape election data from the results soup."""
    results = []

    if results_soup:
        party_blocks = results_soup.find_all('div', class_=PARTY_CLASS)
        results = [extract_party_data(block) for block in party_blocks]

        summary_data = extract_summary_data(results_soup)

        election_data = {**summary_data, "results": results}
        save_to_json(election_data, JSON_FILENAME)
        logging.info("Data scraped and saved successfully.")
    else:
        logging.warning('All island scraping unsuccessful')


def extract_summary_data(results_soup):
    """Extract summary data from the results soup."""
    summary_data = {
        "time_stamp": None,
        "polling_division": None,
        "electoral_district": None,
        "electoral_district_id": None,
        "province": None,
        "valid_votes": None,
        "valid_votes_pct": None,
        "rejected_votes": None,
        "rejected_pct": None,
        "total_polled": None,
        "polled_pct": None,
        "registered_electors": None,
    }

    summary_container = results_soup.find('div', class_=SUMMARY_CLASS)

    if summary_container:
        rows = summary_container.find_all('tr')
        summary_data["valid_votes"] = int(rows[0].find_all('td')[0].get_text(strip=True).replace(',', ''))
        summary_data["valid_votes_pct"] = float(rows[0].find_all('td')[1].get_text(strip=True).strip("%").strip())
        summary_data["rejected_votes"] = int(rows[1].find_all('td')[0].get_text(strip=True).replace(',', ''))
        summary_data["rejected_pct"] = float(rows[1].find_all('td')[1].get_text(strip=True).strip("%").strip())
        summary_data["total_polled"] = int(rows[2].find_all('td')[0].get_text(strip=True).replace(',', ''))
        summary_data["polled_pct"] = float(rows[2].find_all('td')[1].get_text(strip=True).strip("%").strip())
        summary_data["registered_electors"] = int(rows[3].find_all('td')[0].get_text(strip=True).replace(',', ''))

    return summary_data


def save_to_json(data, filename):
    """Save the scraped data to a JSON file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(OUTPUT_DIR, filename)

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    all_island_result_soup = check_url(BASE_URL)

    if all_island_result_soup:
        scrape_data(all_island_result_soup)
    else:
        logging.warning("No data scraped due to URL error.")
