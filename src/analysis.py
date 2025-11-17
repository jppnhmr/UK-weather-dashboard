import database as db
import pandas as pd
import matplotlib.pyplot as plt

GRAPH_OUTPUT_DIR = "graphs"

class Station:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.stats = {}

    def add_stat(self, name, val):
        self.stats[name] = val

    def get_stat(self, name):
        return self.stats[name]

# Fetch #
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

def get_station_name(station_id):
    """
    Returns the name of a station given its ID
    """
    query = """
    SELECT name FROM stations WHERE id = ?;
    """
    params = (station_id,)

    data = db.select(query, params)

    if data:
        return data[0][0]
    else:
        return None

# CLI Output #
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
    print(f"Average, Monthly Rainfall (mm) per Station")
    print("-"*60)
    for station in sorted_stations:
        print(f" {station.get_stat('avg_rain'):.2f}\t{station.name}")

def print_stations_by_avg_temp(desc: bool):
    stations = list_stations()
    if stations is None:
        print("Error fetching stations list")
        exit()

    # Get average temperature for each station
    for station in stations:
        query = """
        SELECT AVG((tmax + tmin) / 2.0)
        FROM observations 
        WHERE station_id = ?;
        """
        params = (station.id,)
        
        data = db.select(query, params)
        station.add_stat("avg_temp", data[0][0])

    # Sort by temperature
    sorted_stations = sorted(
        stations, 
        key=lambda x: x.stats.get('avg_temp'),
        reverse=desc)

    print("-"*60)
    print(f"Average, Monthly Temperature (ºC) per Station")
    print("-"*60)
    for station in sorted_stations:
        print(f" {station.get_stat('avg_temp'):.2f}\t{station.name}")

# Graphing #
def plot_station_temp_trend(station_id):
    query = """
    SELECT year, 
        AVG(tmax) AS avg_tmax,
        AVG(tmin) AS avg_tmin,
        AVG((tmax + tmin) / 2.0) AS avg_temp
    FROM observations
    WHERE station_id = ?
    GROUP BY year
    ORDER BY year;
    """
    params = (station_id,)

    data = db.select(query, params)

    if data is None:
        print("Error fetching temperature data.")
        return
    station_name = get_station_name(station_id)
    df = pd.DataFrame(data, columns=['year', 'avg_tmax', 'avg_tmin', 'avg_temp'])
    plt.plot(df['year'], df['avg_temp'], color="black", label="Avg Temp")
    plt.plot(df['year'], df['avg_tmax'], color="red", label="Avg Tmax")
    plt.plot(df['year'], df['avg_tmin'], color="blue", label="Avg Tmin")

    plt.xlabel("Year")
    plt.ylabel("Temperature (ºC)")
    plt.title(f"Temperature Trend for {station_name}")
    plt.legend()
    plt.grid()
    plt.savefig(f"{GRAPH_OUTPUT_DIR}/{station_name}_temp_trend.png")

if __name__ == "__main__":
    #print_stations_by_avg_rain(True)
    #print_stations_by_avg_temp(True)
    plot_station_temp_trend(13)
