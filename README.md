# Sri Lanka Election Data Scraper

This repository contains Python scripts to scrape election data from different websites and for various elections held in Sri Lanka. The scraped data includes results, candidate information, vote summaries, and more.

## Project Overview

The goal of this project is to automate the extraction of election results from online sources to organize them into structured formats (like JSON) for further analysis. The data can be used for election result tracking, reporting, or visualization.

## Features

- Scrapes Presidential and General (Parliamentary) election data from multiple sources.
- Extracts detailed results, including party names, votes, percentages, and seats won.
- Retrieves preferential vote data for individual candidates where available.
- Saves the scraped data in structured JSON files organized by province and district.

## Repository Structure
The repository is organized to keep files and results easily accessible and scalable as new elections are added.

### Folder Structure

├── data/                                                                               
│   ├── Presidential-Election-2024/
│   │   └── {province}/{district}.json
│   ├── General-Election-2020/
│   │   └── {province}/{district}.json
├── scripts/                          
│   ├── presidential_2024_scrape.py   
│   ├── general_2020_scrape.py       
├── electoral_district.py             
├── README.md                         


### File Naming Convention

1. Scripts:

 - Each script is named based on the election type and year, for example, presidential_2024_scrape.py for the 2024 presidential -  election and general_2020_scrape.py for the 2020 general election.
 - Scripts scraping the same data but from different sources are named accordingly (e.g., source1, source2).

2. Data Output:

 - Output files are saved under the data/ directory, organized by election type and year.
 - Each province and district has its own JSON file containing the results.


## How to Use

### Prerequisites

- Python 3.x
- Required Python packages: requests, BeautifulSoup4

## Error Handling

- If any scraping process fails (e.g., due to a broken URL), the script logs the failed districts in error_district_list.txt under the data/ folder for further debugging.

