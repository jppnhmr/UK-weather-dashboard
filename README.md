# UK Weather Dashboard
Python Dashboard for UK weather. 
Uses SQLite database and BeautifulSoup4 for web scraping.

Gets data from:
https://www.metoffice.gov.uk/research/climate/maps-and-data/historic-station-data

## Installation
> pip install -r requirements.txt
## Usage
To scrape data and store in database:
> python -m src.scraper

To run API locally:
> uvicorn src.api:app

then go to [localhost:8000](http://localhost:8000/)

## TODO
- Web interface for API
- Expand API endpoints:
    - Overall graphs
    - Overall trends
- Gather more data sources
