import database as db
import pandas as pd


class Station:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.stats = {}

    def add_stat(self, name, val):
        self.stats[name] = val

    def get_stat(self, name):
        return self.stats[name]

def list_stations():
    """
    Returns a list of all stations from the stations table,
    in the form of Station objects.
    """

    query = """
    SELECT id, name FROM stations
    """

    result = db.select(query)

    if result:
        stations = []
        for station in result:
            new_station = Station(station[0], station[1])
            stations.append(new_station)
        return stations
    else:
        print("Failed to list stations.")
        return None

def station_avg_rain(station_id):
    """
    Returns the average rain for a given station
    """
    query = """
    SELECT AVG(rain)
    FROM observations 
    WHERE station_id = ?;
    """
    params = (station_id,)
    
    data = db.select(query, params)
    
    return data[0][0]

def print_stations_by_avg_rain(desc: bool):
    
    stations = list_stations()
    if stations is None:
        print("Error fetching stations list")
        exit()

    # Get average rainfall for each station
    for station in stations:
        station.add_stat("avg_rain", station_avg_rain(station.id))

    # Sort by rainfall
    sorted_stations = sorted(
        stations, 
        key=lambda x: x.stats.get('avg_rain'),
        reverse=desc)

    print("-"*60)
    print(f"Average, Total Monthly Rainfall per Station")
    print("-"*60)
    for station in sorted_stations:
        print(f" {station.get_stat('avg_rain'):.2f}\t{station.name}")


if __name__ == "__main__":
    print_stations_by_avg_rain(True)
