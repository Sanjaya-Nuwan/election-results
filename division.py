import os

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs
from elctoral_district import lst

base_url = "https://election.adaderana.lk/general-election-2020/division_result.php"
timeout = 10


def check_url(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')

    results_container = soup.find('div', class_='division-results card widget-summery')

    if results_container:
        return results_container
    else:
        return None


def scrape_data(results_soup, province, dist_id, div_id):
    # parsed_url = urlparse(url)
    # query_params = parse_qs(parsed_url.query)
    # electoral_district = query_params.get('dist_id', [None])[0]
    # polling_division = query_params.get('div_id', [None])[0]

    # res = requests.get(url)
    # soup = BeautifulSoup(res.content, 'html.parser')
    #
    # results_container = soup.find('div', class_='division-results card widget-summery')

    results = []

    if results_soup:
        party_blocks = results_soup.find_all('div', class_='dis_ele_result_block')

        for block in party_blocks:
            party_short = block.find('div', class_='ele_party').find('span').get_text(strip=True)
            party_long = block.find('div', class_='ele_party').get_text(strip=True).replace(party_short, '').strip()

            vote_data = block.find('div', class_='ele_value').get_text(strip=True)

            percentage, votes = vote_data.split('%')
            percentage = percentage.strip()
            votes = votes.strip().replace(',', '')

            results.append({
                "party_short": party_short,
                "party_long": party_long,
                "votes": int(votes),
                "percentage": float(percentage),
                "seats": None,
                "candidates": [{
                }]
            })
    else:
        print(f'{dist_id} scraping unsuccessfully')

    time_stamp = None
    electoral_district_id = None
    valid_votes = None
    valid_votes_pct = None
    rejected_votes = None
    rejected_pct = None
    total_polled = None
    polled_pct = None
    registered_electors = None

    if results_soup:
        summary_container = results_soup.find('div', class_='total-votes-summery')

        if summary_container:
            rows = summary_container.find_all('tr')

            valid_votes = int(rows[0].find_all('td')[0].get_text(strip=True).replace(',', ''))
            valid_votes_pct = float(rows[0].find_all('td')[1].get_text(strip=True).strip("%").strip())

            rejected_votes = int(rows[1].find_all('td')[0].get_text(strip=True).replace(',', ''))
            rejected_pct = float(rows[1].find_all('td')[1].get_text(strip=True).strip("%").strip())

            total_polled = int(rows[2].find_all('td')[0].get_text(strip=True).replace(',', ''))
            polled_pct = float(rows[2].find_all('td')[1].get_text(strip=True).strip("%").strip())

            registered_electors = int(rows[3].find_all('td')[0].get_text(strip=True).replace(',', ''))

    else:
        print(f'{dist_id} scraping unsuccessfully')
    election_data = {
        "time_stamp": time_stamp,
        "polling_division": div_id,
        "electoral_district": dist_id,
        "electoral_district_id": electoral_district_id,
        "province": province,
        "valid_votes": valid_votes,
        "valid_votes_pct": valid_votes_pct,
        "rejected_votes": rejected_votes,
        "rejected_pct": rejected_pct,
        "total_polled": total_polled,
        "polled_pct": polled_pct,
        "registerd_electors": registered_electors,
        "results": results
    }

    main_dir = f'division results/{province}'
    os.makedirs(main_dir, exist_ok=True)

    folder_path = os.path.join(main_dir, dist_id)
    os.makedirs(folder_path, exist_ok=True)

    file_name = f'{div_id}.json'
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, "w") as file:
        json.dump(election_data, file, indent=4)


for pvce in lst:
    province_name = pvce["name"]
    districts = pvce["districts"]

    for dist_id, divisions in districts.items():
        for div_id in divisions:
            url = f"{base_url}?dist_id={dist_id}&div_id={div_id}"

            try:
                response = requests.get(url, timeout=timeout)

                if response.status_code == 200:
                    results_container_soup = check_url(url)
                    if results_container_soup:
                        scrape_data(results_container_soup, province_name, dist_id, div_id)
                        print(f'{div_id} is working')
                    else:
                        print(f'{div_id} url is not working')
                        with open('division results/error_division_list.txt', 'a') as err_log:
                            err_log.write(f'({dist_id})/ {div_id} url is not working \n')
                else:
                    print(f"Failed with status {response.status_code}: {dist_id} -> {div_id}")

            except requests.exceptions.RequestException as e:
                print(f"Request failed for dist_id={dist_id}, div_id={div_id}. Error: {e}")
            continue
