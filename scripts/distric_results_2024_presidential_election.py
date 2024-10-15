import os
import requests
from bs4 import BeautifulSoup
import json
from electoral_district import lst

base_url = "https://election.adaderana.lk/presidential-election-2024/district_result.php"
timeout = 10


def check_url(url, property, class_name):
    try:
        res = requests.get(url, timeout=timeout)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        return soup.find(property, class_=class_name)
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return None


def scrape_data(results_soup, province, district_name):
    results = []

    if results_soup:
        party_blocks = results_soup.find_all('div', class_='dis_ele_result')

        for block in party_blocks:
            party_short = block.find('div', class_='ele_party').find('span').get_text(strip=True)
            party_long = block.find('div', class_='ele_party').get_text(strip=True).replace(party_short, '').strip()
            vote_data = block.find('div', class_='ele_value').get_text(strip=True)
            percentage, votes = vote_data.split('%')
            percentage = float(percentage.strip())
            votes = int(votes.strip().replace(',', ''))

            results.append({
                "party_short": party_short,
                "party_long": party_long,
                "votes": votes,
                "percentage": percentage,
                "seats": None,
                "candidates": None
            })

        votes_summary_scrape(district_name, province, results)
    else:
        print(f'{district_name} scraping unsuccessful')


def build_url(district_name):
    return f"{base_url}?dist_id={district_name}"


def extract_candidates(district_name, party_short):
    url_for_candidates = build_url(district_name)

    res = requests.get(url_for_candidates)
    soup = BeautifulSoup(res.content, 'html.parser')

    h2_tag = soup.find('h2', text=lambda x: x and f'Preferential Votes - {district_name}' in x)

    if h2_tag:
        card_body = h2_tag.find_next('div', class_='card-body')
        p_tags = card_body.find_all('p')

        votes_list = []
        for p in p_tags:
            party_strong_tag = p.find('strong')
            if party_strong_tag and party_strong_tag.get_text(strip=True) == party_short:
                vote_data = p.get_text().split('\n')[1:]  # Skip the party name
                for entry in vote_data:
                    if '-' in entry:
                        name, votes = map(str.strip, entry.split('-'))
                        votes_list.append({"name": name, "votes": int(votes.replace(',', ''))})

        return votes_list
    else:
        print('No preferential votes found')
        return None


def votes_summary_scrape(district_name, province, results):
    url_for_summary = build_url(district_name)
    summary_soup = check_url(url_for_summary, 'div', "total-votes-summery")

    election_data = {
        "time_stamp": None,
        "polling_division": None,
        "electoral_district": district_name,
        "electoral_district_id": None,
        "province": province,
        "valid_votes": None,
        "valid_votes_pct": None,
        "rejected_votes": None,
        "rejected_pct": None,
        "total_polled": None,
        "polled_pct": None,
        "registered_electors": None,
        "results": results
    }

    if summary_soup:
        rows = summary_soup.find_all('tr')

        election_data["valid_votes"] = int(rows[0].find_all('td')[0].get_text(strip=True).replace(',', ''))
        election_data["valid_votes_pct"] = float(rows[0].find_all('td')[1].get_text(strip=True).strip("%").strip())

        election_data["rejected_votes"] = int(rows[1].find_all('td')[0].get_text(strip=True).replace(',', ''))
        election_data["rejected_pct"] = float(rows[1].find_all('td')[1].get_text(strip=True).strip("%").strip())

        election_data["total_polled"] = int(rows[2].find_all('td')[0].get_text(strip=True).replace(',', ''))
        election_data["polled_pct"] = float(rows[2].find_all('td')[1].get_text(strip=True).strip("%").strip())

        election_data["registered_electors"] = int(rows[3].find_all('td')[0].get_text(strip=True).replace(',', ''))

    save_election_data(province, district_name, election_data)
    print(f'{district_name} scraping complete')


def save_election_data(province, district_name, election_data):
    main_dir = f'../data/Presidential Election Results - Districts -2024/{province}'
    os.makedirs(main_dir, exist_ok=True)

    file_name = f'{main_dir}/{district_name}.json'
    with open(file_name, "w") as file:
        json.dump(election_data, file, indent=4)


def main():
    for pvce in lst:
        province_name = pvce["name"]
        districts = pvce["districts"]

        for district_name in districts.keys():
            url = build_url(district_name)
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    results_container_soup = check_url(url, 'div', "district district-summery")
                    if results_container_soup:
                        scrape_data(results_container_soup, province_name, district_name)
                        print(f'{district_name} scraping successful')
                    else:
                        print(f'{district_name} data not found')
                        log_error(district_name, 'data not found')
                else:
                    print(f"Failed with status {response.status_code}: {district_name}")
            except requests.exceptions.RequestException as e:
                print(f"Request failed for {district_name}: {e}")
                log_error(district_name, f"request failed: {e}")


def log_error(district_name, message):
    with open('district_results/error_log.txt', 'a') as err_log:
        err_log.write(f"{district_name}: {message}\n")


if __name__ == "__main__":
    main()
