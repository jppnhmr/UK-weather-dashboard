from fastapi import FastAPI

import src.analysis as analysis; 
from src.analysis import Station
import src.database as db

app = FastAPI(title="UK Weather Dashboard")

@app.get("/")
def root():
    return {"message": "Welcome to the UK Weather Dashboard API - use /docs for API documentation."}

@app.get("/stations")
def get_stations():
    stations = analysis.list_stations()
    if stations is None:
        return {"stations": []}
    else:
        return {
            "stations": [{"id": station.id, "name": station.name} for station in stations]
        }

@app.get("/station/{station_id}")
def get_station_info(station_id: int):

    station = Station(station_id)
    if (not station.load_details()):
        return {"error": "Station not found."}

    filenames = {}
    filenames['temp_trend'] = analysis.plot_station_temp_trend(station.id)
    filenames['monthly_rainfall'] = analysis.plot_station_monthly_rainfall(station.id)
    filenames['monthly_sunshine'] = analysis.plot_station_monthly_sunshine(station.id)

    return {
        "details": {
            "id": station.id,
            "name": station.name,
            "lon": station.lon,
            "lat": station.lat,
            "opened": station.opened,
            "data_url": station.url
        },
        "graphs": filenames
    }

@app.get("/overall")
def get_overall_info():
    filenames = {}
    filenames['avg_temp_trend'] = analysis.plot_overall_temp_trend()
    filenames['total_rainfall'] = analysis.plot_overall_monthly_rainfall()
    filenames['total_sunshine'] = analysis.plot_overall_monthly_sunshine()

    return {
        "graphs": filenames
    }

@app.get("/overall/latitude")
def get_overall_latitude_info():
    filenames = analysis.plot_lat_against()

    return {
        "graphs": filenames
    }