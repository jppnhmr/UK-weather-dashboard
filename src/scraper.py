
import database as db

import requests

from bs4 import BeautifulSoup as bs

import pandas as pd
from io import StringIO

# Historic station data
HISTORIC_STATION_DATA_URL = 'https://www.metoffice.gov.uk/research/climate/maps-and-data/historic-station-data'

# --- Scrapping ---
def get_soup(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f"Successful Request to {url}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching: {e}")
    
    return bs(response.text, 'html.parser')

def get_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        text = response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching text: {e}")

    return text

def extract_historic_station_table_data():
    soup = get_soup(HISTORIC_STATION_DATA_URL)

    try:
        table = soup.find("table")
        thead = soup.find("thead")
        tbody = table.find("tbody")

        headers = [th.get_text(strip=True) for th in thead.find_all("th")]
        
        rows = []
        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")

            name = tds[0].get_text(strip=True)
            location = tds[1].get_text(strip=True)
            opened = tds[2].get_text(strip=True)
            link = tds[3].find("a")["href"]

            rows.append([name, location, opened, link])
    except:
        print("Failed to extract historic station table data.")
        exit()

    return headers, rows

def extract_station_data(url):
    lines = get_text(url).splitlines()

    # Find header "yyyy mm ..."
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("yyyy"):
            header_idx = i
            break
    if header_idx is None:
        print(f"Failed to find header in {url} file.")
        exit()
    
    header_line = lines[header_idx]
    units_line = lines[header_idx + 1]

    # only add valid data lines
    data_lines = []
    for line in lines[header_idx + 2:]:
        stripped = line.strip()

        # skip blank lines
        if not stripped:
            continue

        # keep only rows where the first token is a year (4 digits)
        first = stripped.split()[0]
        if first.isdigit() and len(first) == 4:
            data_lines.append(line)
        else:
            # line such as: 'Site Close' reached, stop searching for data
            break

    cleaned = "\n".join([header_line] + data_lines)

    df = pd.read_fwf(StringIO(cleaned))

    return df, units_line

# --- Parsing ---
def parse_location(loc_str):
    lon, lat = [s.strip() for s in loc_str.split(",")]
    return float(lon), float(lat)

def clean_number(x, type):
    if x in ("---", ""):
        return None
    
    try:
        if x[-1] in ("*","#"): # '*' and '#' often appear to add context to values 
            x = x[:-1]   # ignore for now
    except TypeError:
        pass
    
    try:
        if pd.isna(x):
            return None
    except TypeError:
        pass

    if (type == "int"):
        try:
            return int(x)
        except ValueError:
            return None
        
    elif (type == "float"):
        try:
            return float(x)
        except ValueError:
            return None
    
    else:
        print("Invalid type for clean_number funciton.")


# --- SCRAPER ---
if __name__ == "__main__":
    """
    Retrieves Data from met office website, cleans it, then stores it in 
    a local sqlite3 database file.
    """
    print("-"*60)
    print("Beginning...")
    print("-"*60)

    # Create tables if not already created
    db.create_tables()

    headers, stations = extract_historic_station_table_data()

    station_data = []
    # Insert stations
    for station in stations:

        name = station[0]
        lon, lat = parse_location(station[1])
        opened = station[2]
        link = station[3]

        station_id = db.insert_station(name, lon, lat, opened, link)

        df, _ = extract_station_data(link)

        # Insert observations
        for obs in df.itertuples(index=False):
            year = clean_number(getattr(obs, 'yyyy'), "int")
            month = clean_number(getattr(obs, 'mm'), "int")
            af = clean_number(getattr(obs, "af"), "int")

            tmax = clean_number(getattr(obs, "tmax"), "float")
            tmin = clean_number(getattr(obs, "tmin"), "float")
            rain = clean_number(getattr(obs, "rain"), "float")
            sun = clean_number(getattr(obs, "sun"), "float")
            
            db.insert_observation(station_id, year, month, tmax, tmin, af, rain, sun)
        
        print(f"Inserted {len(df)}\tobservations for {name}")

    print("-"*60)
    print("Finished inserting data.")
    print("-"*60)