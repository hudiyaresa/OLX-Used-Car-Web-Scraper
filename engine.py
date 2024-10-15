from sqlalchemy import create_engine, MetaData
import pandas as pd
import json
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time
import math
from bs4 import BeautifulSoup
import datetime
from tqdm import tqdm


def scrape_olx(playwright, keyword, html_path):
    """Scrapes OLX listings based on the keyword provided."""
    browser = None
    try:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        brand, tipe = keyword.split(" ")
        olx_url = f"https://www.olx.co.id/mobil-bekas_c198/q-{brand}-{tipe}"
        page.goto(olx_url)
        time.sleep(5)

        # Fill in the location
        location_input_selector = "#container > header > div > div > div._3nd5v > div > div > div:nth-child(1) > div > div.bGCL7 > input"
        page.fill(location_input_selector, "Indonesia")
        time.sleep(5)
        location_list_selector = "#container > header > div > div > div._3nd5v > div > div > div:nth-child(1) > div > div:nth-child(2) > div > div > div > div > span"
        page.wait_for_selector(location_list_selector)
        page.click(location_list_selector)
        time.sleep(5)

        # Get total listings
        listing_count_selector = "#main_content > div > div > section > div > div > div:nth-child(6) > div._2CyHG > div > div._3eiOr._1xlea > div._1DW26 > div > p > span._351MY"
        total_listings_text = page.inner_text(listing_count_selector)
        total_listings = int(total_listings_text.replace("&nbsp;", "").replace("Iklan", "").strip())
        total_pages = math.ceil(total_listings / 40)

        scraped_data = []
        with tqdm(total=total_pages, desc="Scraping Pages", leave=True) as pbar:
            current_page = 1
            while current_page <= total_pages:
                item_list_selector = "#main_content > div > div > section > div > div > div:nth-child(6) > div._2CyHG > div > div:nth-child(4) > ul > li"
                page.wait_for_selector(item_list_selector)

                listings_on_page = page.locator(item_list_selector).count()
                scraped_data.append(f"Scraped data from page {current_page} with {listings_on_page} items")

                if current_page < total_pages:
                    next_page_button_selector = "#main_content > div > div > section > div > div > div:nth-child(6) > div._2CyHG > div > div:nth-child(4) > ul > li._2xGb5 > div > button"
                    if page.is_visible(next_page_button_selector):
                        page.click(next_page_button_selector)
                        time.sleep(5)
                current_page += 1
                pbar.update(1)

            # Save the HTML content
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as file:
                file.write(html_content)

        print(f"Scraped {len(scraped_data)} cars from {total_pages} pages.")
        print(f"HTML content saved successfully to {html_path}")

    except Exception as e:
        print(f"An error occurred: {e}")
        if browser:
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
            print(f"HTML content saved after error to {html_path}")
    finally:
        if browser:
            browser.close()


def parse_html(html_path, parsed_path):
    """Parses the saved HTML content from OLX and extracts relevant car listings data."""
    with open(html_path, 'r', encoding='utf-8') as html_file:
        soup = BeautifulSoup(html_file.read(), 'html.parser')

    listings = soup.find_all(class_='_3V_Ww')
    parsed_data = []

    for listing in listings:
        title = listing.find('div', class_='_2Gr10').get('title', 'data tidak ditemukan') if listing.find('div', class_='_2Gr10') else 'data tidak ditemukan'
        price = listing.find('span', class_='_1zgtX').text if listing.find('span', class_='_1zgtX') else 'data tidak ditemukan'
        year_mileage = listing.find('div', class_='_21gnE').text if listing.find('div', class_='_21gnE') else 'data tidak ditemukan'
        listing_url = listing.find('a')['href'] if listing.find('a') else 'data tidak ditemukan'
        installment = listing.find('span', class_='_25Fb0').text.strip().replace('Rp', '').replace('.', '') if listing.find('span', class_='_25Fb0') else 0

        location_and_time = listing.find('div', class_='_3VRSm')
        if location_and_time:
            location = location_and_time.contents[0].strip()
            posted_time = location_and_time.find('span').text.strip() if location_and_time.find('span') else 'data tidak ditemukan'
        else:
            location = 'data tidak ditemukan'
            posted_time = 'data tidak ditemukan'

        parsed_data.append({
            'title': title.replace('[OLXmobbi] ', ''),
            'price': price,
            'year_mileage': year_mileage,
            'listing_url': listing_url,
            'location': location,
            'installment': installment if installment else 0,
            'posted_time': posted_time,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    df = pd.DataFrame(parsed_data)
    df.to_csv(parsed_path, index=False)
    print(f"Parsed data saved to {parsed_path}")


def transform_data(parsed_path, transformed_path):
    """Transforms the parsed data for further analysis by cleaning and restructuring it."""
    df = pd.read_csv(parsed_path)

    df['price'] = df['price'].replace('[^0-9]', '', regex=True).astype(float)

    def parse_year_mileage(year_mileage):
        if pd.isna(year_mileage) or not year_mileage:
            return pd.Series(['data tidak ditemukan', 'data tidak ditemukan', 'data tidak ditemukan'])

        year = 'data tidak ditemukan'
        lower_km = 'data tidak ditemukan'
        upper_km = 'data tidak ditemukan'

        try:
            parts = year_mileage.split(' - ')
            if len(parts) == 2:
                year = parts[0].strip()
                km_range = parts[1].strip()

                if km_range.startswith('>'):
                    upper_km = km_range[1:].replace('km', '').replace('.', '').replace(',', '').strip()
                    lower_km = str(int(upper_km) - 5000)
                else:
                    km_parts = km_range.split('-')
                    if len(km_parts) == 2:
                        lower_km, upper_km = km_parts
                        lower_km = lower_km.replace('km', '').replace('.', '').replace(',', '').strip()
                        upper_km = upper_km.replace('km', '').replace('.', '').replace(',', '').strip()
                    else:
                        upper_km = km_range.replace('km', '').replace('.', '').replace(',', '').strip()
                        lower_km = str(int(upper_km) - 5000)
        except Exception as e:
            print(f"Error parsing year_mileage: {e}")

        return pd.Series([year, lower_km, upper_km])

    df[['year', 'lower_km', 'upper_km']] = df['year_mileage'].apply(parse_year_mileage)
    df['listing_url'] = 'https://olx.co.id' + df['listing_url']
    df['location'] = df['location'].str.replace(r'[^\w\s]', '', regex=True)

    df['installment'] = df['installment'].replace('[^0-9]', '', regex=True)
    df['installment'] = pd.to_numeric(df['installment'], errors='coerce') * 1_000_000
    df['installment'] = df['installment'].fillna(0)

    df['posted_time'] = df['posted_time'].apply(lambda x: convert_posted_time(x))
    df.drop(columns=['year_mileage'], inplace=True)
    df.to_csv(transformed_path, index=False)
    print(f"Transformed data saved to {transformed_path}")


def convert_posted_time(posted_time):
    """Converts relative time descriptions into a standard date format."""
    now = datetime.datetime.now()
    month_map = {
        'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr',
        'Mei': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Agu': 'Aug',
        'Sep': 'Sep', 'Okt': 'Oct', 'Nov': 'Nov', 'Des': 'Dec'
    }

    if "Hari ini" in posted_time:
        posted_time = now.strftime('%Y-%m-%d')
    elif "Kemarin" in posted_time:
        posted_time = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        try:
            if "hari yang lalu" in posted_time:
                days_ago = int(posted_time.split()[0])
                posted_time = (now - datetime.timedelta(days=days_ago)).strftime('%Y-%m-%d')
            else:
                day_month = posted_time.split()
                if len(day_month) == 2:
                    day, month_abbr = day_month
                    month = month_map.get(month_abbr, 'data tidak ditemukan')
                    if month == 'data tidak ditemukan':
                        return 'data tidak ditemukan'
                    posted_time = f"{day} {month} {now.year}"
                    posted_time = datetime.datetime.strptime(posted_time, '%d %b %Y').strftime('%Y-%m-%d')
        except ValueError:
            return 'data tidak ditemukan'

    return posted_time


def dw_db_engine():
    """Creates and returns a SQLAlchemy engine for connecting to the database."""
    return create_engine(f"postgresql://{WAREHOUSE_DB_USERNAME}:{WAREHOUSE_DB_PASSWORD}@{WAREHOUSE_DB_HOST}:{WAREHOUSE_DB_PORT}/{WAREHOUSE_DB_NAME}")


def load_data(transformed_data, inserted_path, table_name, db_engine):
    """Loads the transformed data into a database and saves the inserted records as a JSON file."""
    engine = db_engine()

    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)

        table = metadata.tables.get(table_name)
        if table is None:
            raise RuntimeError(f"Table '{table_name}' does not exist in the database.")

        df = pd.read_csv(transformed_data)
        records = df.to_dict(orient='records')

        with engine.begin() as conn:
            conn.execute(table.insert(), records)

        with open(inserted_path, 'w') as f:
            json.dump(records, f)

        print("Data saved successfully to the database and JSON file.")

    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        engine.dispose()


def main():
    """Main function to orchestrate the scraping process."""
    load_dotenv()
    
    # Retrieve database connection details
    global WAREHOUSE_DB_USERNAME, WAREHOUSE_DB_PASSWORD, WAREHOUSE_DB_HOST, WAREHOUSE_DB_PORT, WAREHOUSE_DB_NAME
    WAREHOUSE_DB_USERNAME = os.getenv("WAREHOUSE_DB_USERNAME")
    WAREHOUSE_DB_PASSWORD = os.getenv("WAREHOUSE_DB_PASSWORD")
    WAREHOUSE_DB_HOST = os.getenv("WAREHOUSE_DB_HOST")
    WAREHOUSE_DB_PORT = os.getenv("WAREHOUSE_DB_PORT")
    WAREHOUSE_DB_NAME = os.getenv("WAREHOUSE_DB_NAME")

    brand = input("Enter car brand: ")
    type = input("Enter car type: ")
    keyword = f"{brand} {type}"

    html_path = "scraped_olx.html"
    parsed_path = "parsed_olx.csv"
    transformed_path = "olx_scrape.csv"

    with sync_playwright() as playwright:
        scrape_olx(playwright, keyword, html_path)

    parse_html(html_path, parsed_path)
    transform_data(parsed_path, transformed_path)
    load_data(transformed_path, 'inserted_records.json', "scrape_data", dw_db_engine)

    # Clean up temporary files
    os.remove(html_path)
    os.remove(parsed_path)


if __name__ == "__main__":
    main()
