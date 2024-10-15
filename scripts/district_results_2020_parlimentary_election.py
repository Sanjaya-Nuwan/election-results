import os
import requests
from bs4 import BeautifulSoup
import json
from electoral_district import lst

base_url = "https://election.adaderana.lk/general-election-2020/district_result.php"
timeout = 10


def check_url(url, property_name, class_name):
    """Check the URL and return the container based on HTML properties."""
    try:
        res = requests.get(url, timeout=timeout)
        res.raise_for_status()  # Raise HTTPError for bad responses
        soup = BeautifulSoup(res.content, 'html.parser')
        return soup.find(property_name, class_=class_name)
    except requests.exceptions.RequestException as e:
        print(f"Request failed for URL: {url}. Error: {e}")
        return None


def extract_candidates(dist_name, party_short):
    """Extract candidates and their votes for a given party."""
    url_for_candidates = build_url(dist_name)
    soup = BeautifulSoup(requests.get(url_for_candidates).content, 'html.parser')

    h2_tag = soup.find('h2', text=lambda x: x and f'Preferential Votes - {dist_name}' in x)
    if not h2_tag:
        print(f'No Preferential Votes section found for {dist_name}')
        return []

    card_body = h2_tag.find_next('div', class_='card-body')
    if not card_body:
        return []

    p_tags = card_body.find_all('p')
    votes_list = []

    for p in p_tags:
        party_strong_tag = p.find('strong')
        if party_strong_tag and party_strong_tag.get_text().replace('\xa0', ' ').replace(':',
                                                                                         '').strip() == party_short:
            vote_data = p.get_text().split('\n')[1:]  # Skip the party name
            for entry in vote_data:
                if '-' in entry:
                    name, votes = map(str.strip, entry.split('-'))
                    votes_list.append({"name": name, "votes": votes})

    return votes_list


def scrape_data(results_soup, province, dist_name):
    """Scrape party and voting data for a district."""
    results = []

    if results_soup:
        party_blocks = results_soup.find_all('div', class_='dis_ele_result')

        for block in party_blocks:
            party_short = block.find('div', class_='ele_party').find('span').get_text(strip=True)
            party_long = block.find('div', class_='ele_party').get_text(strip=True).replace(party_short, '').strip()
            seats_count = block.find('div', class_='ele_seats').find('span').get_text(strip=True)
            vote_data = block.find('div', class_='ele_value').get_text(strip=True)

            percentage, votes = vote_data.split('%')
            percentage = percentage.strip()
            votes = votes.strip().replace(',', '')

            candidates_votes_list = extract_candidates(dist_name, party_short)

            results.append({
                "party_short": party_short,
                "party_long": party_long,
                "votes": int(votes),
                "percentage": float(percentage),
                "seats": int(seats_count),
                "candidates": candidates_votes_list
            })

        save_vote_summary(dist_name, province, results)
    else:
        print(f'{dist_name} scraping unsuccessful')


def build_url(dist_name):
    """Build URL for a given district."""
    return f"{base_url}?dist_id={dist_name}"


def save_vote_summary(dist_name, province, results):
    """Save vote summary data into a JSON file."""
    url_for_summary = build_url(dist_name)
    results_soup = check_url(url_for_summary, 'div', "total-votes-summery")

    if results_soup:
        rows = results_soup.find_all('tr')

        valid_votes = int(rows[0].find_all('td')[0].get_text(strip=True).replace(',', ''))
        valid_votes_pct = float(rows[0].find_all('td')[1].get_text(strip=True).strip("%").strip())
        rejected_votes = int(rows[1].find_all('td')[0].get_text(strip=True).replace(',', ''))
        rejected_pct = float(rows[1].find_all('td')[1].get_text(strip=True).strip("%").strip())
        total_polled = int(rows[2].find_all('td')[0].get_text(strip=True).replace(',', ''))
        polled_pct = float(rows[2].find_all('td')[1].get_text(strip=True).strip("%").strip())
        registered_electors = int(rows[3].find_all('td')[0].get_text(strip=True).replace(',', ''))

        election_data = {
            "time_stamp": None,
            "polling_division": None,
            "electoral_district": dist_name,
            "electoral_district_id": None,
            "province": province,
            "valid_votes": valid_votes,
            "valid_votes_pct": valid_votes_pct,
            "rejected_votes": rejected_votes,
            "rejected_pct": rejected_pct,
            "total_polled": total_polled,
            "polled_pct": polled_pct,
            "registered_electors": registered_electors,
            "results": results
        }

        save_to_json(province, dist_name, election_data)
    else:
        print(f'{dist_name} scraping unsuccessful')


def save_to_json(province, dist_name, data):
    """Save data into a JSON file."""
    main_dir = f'../data/Parliamentary Election Results - Districts - 2020/{province}'
    os.makedirs(main_dir, exist_ok=True)

    file_name = f'{main_dir}/{dist_name}.json'
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    for pvce in lst:
        province_name = pvce["name"]
        districts = pvce["districts"]

        for district_name, divisions in districts.items():
            url = build_url(district_name)
            results_container_soup = check_url(url, 'div', "district district-summery")

            if results_container_soup:
                scrape_data(results_container_soup, province_name, district_name)
                print(f'{district_name} is working')
            else:
                print(f'{district_name} URL is not working')
                with open('../data/error_district_list.txt', 'a') as err_log:
                    err_log.write(f'{district_name} URL is not working\n')
