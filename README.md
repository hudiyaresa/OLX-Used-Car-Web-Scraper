

# OLX Car Listings Scraper

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Functions Overview](#functions-overview)
6. [Credits](#credits)
7. [Disclaimer](#disclaimer)

## Introduction
This script is designed to scrape car listings from OLX Indonesia based on specified keywords. It utilizes Playwright for web scraping, BeautifulSoup for HTML parsing, and Pandas for data manipulation and storage.

## Features
- Scrapes car listings based on brand and type.
- Parses and transforms HTML content into structured CSV data.
- Loads transformed data into a PostgreSQL database.
- Provides detailed logs and error handling.

## Installation
To set up the project, create a `requirements.txt` file and install the dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage
1. Clone the repository and navigate to the project directory.
2. Set up your database connection details in a `.env` file.
3. Run the script and follow the prompts to enter the car brand and type.

```bash
python script.py
```

## Functions Overview
- `scrape_olx(playwright, keyword, html_path)`: Scrapes OLX listings based on the provided keyword.
- `parse_html(html_path, parsed_path)`: Parses the saved HTML content and extracts relevant car listing data.
- `transform_data(parsed_path, transformed_path)`: Cleans and restructures the parsed data for further analysis.
- `convert_posted_time(posted_time)`: Converts relative time descriptions into a standard date format.
- `load_data(transformed_data, inserted_path, table_name, db_engine)`: Loads transformed data into the database.

## Credits
This project was developed with assistance from Pacmann Academy.

## Disclaimer
This script is intended for educational purposes only and is not for commercial use. Users are encouraged to explore the terms and conditions of OLX Indonesia before using this script.
