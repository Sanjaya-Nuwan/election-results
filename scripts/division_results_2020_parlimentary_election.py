import os
import requests
from bs4 import BeautifulSoup
import json
import logging
from electoral_district import lst

# Set up logging
logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
BASE_URL = "https://election.adaderana.lk/general-election-2020/division_result.php"
TIMEOUT = 10
RESULTS_DIR = '../data/Parliamentary Election Results - Divisions - 2020'

def check_url(url):
    """Checks if the URL is valid and returns the results container if found."""
    try:
        res = requests.get(url)
        res.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
        soup = BeautifulSoup(res.content, 'html.parser')
        results_container = soup.find('div', class_='division-results card widget-summery')
        return results_container
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing {url}: {e}")
        return None


def scrape_data(results_soup, province, dist_id, div_id):
    """Scrapes election data from the results soup."""
    results = []

    if results_soup:
        party_blocks = results_soup.find_all('div', class_='dis_ele_result_block')

        for block in party_blocks:
            party_short = block.find('div', class_='ele_party').find('span').get_text(strip=True)
            party_long = block.find('div', class_='ele_party').get_text(strip=True).replace(party_short, '').strip()

            vote_data = block.find('div', class_='ele_value').get_text(strip=True)
            percentage, votes = vote_data.split('%')
            results.append({
                "party_short": party_short,
                "party_long": party_long,
                "votes": int(votes.strip().replace(',', '')),
                "percentage": float(percentage.strip()),
                "seats": None,
                "candidates": [{}]
            })

        summary_data = extract_summary_data(results_soup)
        election_data = compile_election_data(province, dist_id, div_id, results, summary_data)
        save_election_data(province, dist_id, div_id, election_data)
    else:
        logging.warning(f'{dist_id} scraping unsuccessfully')


def extract_summary_data(results_soup):
    """Extracts summary data from the results soup."""
    summary_data = {}
    summary_container = results_soup.find('div', class_='total-votes-summery')

    if summary_container:
        rows = summary_container.find_all('tr')
        summary_data['valid_votes'] = int(rows[0].find_all('td')[0].get_text(strip=True).replace(',', ''))
        summary_data['valid_votes_pct'] = float(rows[0].find_all('td')[1].get_text(strip=True).strip("%").strip())
        summary_data['rejected_votes'] = int(rows[1].find_all('td')[0].get_text(strip=True).replace(',', ''))
        summary_data['rejected_pct'] = float(rows[1].find_all('td')[1].get_text(strip=True).strip("%").strip())
        summary_data['total_polled'] = int(rows[2].find_all('td')[0].get_text(strip=True).replace(',', ''))
        summary_data['polled_pct'] = float(rows[2].find_all('td')[1].get_text(strip=True).strip("%").strip())
        summary_data['registered_electors'] = int(rows[3].find_all('td')[0].get_text(strip=True).replace(',', ''))
    else:
        logging.warning('Summary data not found for the district')

    return summary_data


def compile_election_data(province, dist_id, div_id, results, summary_data):
    """Compiles all election data into a single dictionary."""
    return {
        "time_stamp": None,
        "polling_division": div_id,
        "electoral_district": dist_id,
        "electoral_district_id": None,
        "province": province,
        **summary_data,
        "results": results
    }


def save_election_data(province, dist_id, div_id, election_data):
    """Saves the election data as a JSON file."""
    main_dir = os.path.join(RESULTS_DIR, province)
    os.makedirs(main_dir, exist_ok=True)

    folder_path = os.path.join(main_dir, dist_id)
    os.makedirs(folder_path, exist_ok=True)

    file_name = f'{div_id}.json'
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, "w") as file:
        json.dump(election_data, file, indent=4)
    logging.info(f'Successfully saved data for {div_id} in {file_path}')


def main():
    for pvce in lst:
        province_name = pvce["name"]
        districts = pvce["districts"]

        for dist_id, divisions in districts.items():
            for div_id in divisions:
                url = f"{BASE_URL}?dist_id={dist_id}&div_id={div_id}"

                results_container_soup = check_url(url)
                if results_container_soup:
                    scrape_data(results_container_soup, province_name, dist_id, div_id)
                    logging.info(f'{div_id} is working')
                else:
                    logging.warning(f'{div_id} url is not working')
                    with open('../data/Parliamentary Election Results - Divisions - 2020', 'a') as err_log:
                        err_log.write(f'({dist_id})/ {div_id} url is not working \n')


if __name__ == "__main__":
    main()
