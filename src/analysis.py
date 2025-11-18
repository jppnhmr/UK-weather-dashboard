import os
import src.database as db
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
    
GRAPH_OUTPUT_DIR = "graphs"
os.makedirs(GRAPH_OUTPUT_DIR, exist_ok=True)

class Station:
    def __init__(self, id):
        self.id = id
        self.name = None
        self.lat = None
        self.lon = None
        self.opened = None
        self.url = None
        self.stats = {}

    def add_stat(self, name, val):
        self.stats[name] = val

    def get_stat(self, name):
        return self.stats[name]
    
    def load_details(self):
        data = db.get_station(self.id)
        if data:
            self.id = data[0]
            self.name = data[1]
            self.lon = data[2]
            self.lat = data[3]
            self.opened = data[4]
            self.url = data[5]
            return True
        else:
            return False

    def __repr__(self):
        return f"Station(id={self.id}, name={self.name}, stats={self.stats})"

# Fetch #
def list_stations():
    """
    Returns a list of all stations from the stations table,
    in the form of Station objects.
    """

    query = """
    SELECT id FROM stations
    """

    result = db.select(query)

    if result:
        stations = []
        for station in result:
            new_station = Station(station[0])
            new_station.load_details()
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
def print_stations_by_avg_rain(desc: bool = True):
    
    stations = list_stations()
    if stations is None:
        print("Error fetching stations list")
        return

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

def print_stations_by_avg_temp(desc: bool = True):
    stations = list_stations()
    if stations is None:
        print("Error fetching stations list")
        return
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
# Station-specific Graphs #
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
    file_name = f"{GRAPH_OUTPUT_DIR}/{station_name}_temp_trend.png"
    df = pd.DataFrame(data, columns=['year', 'avg_tmax', 'avg_tmin', 'avg_temp'])
    plt.plot(df['year'], df['avg_temp'], color="black", label="Avg Temp")
    plt.plot(df['year'], df['avg_tmax'], color="red", label="Avg Tmax")
    plt.plot(df['year'], df['avg_tmin'], color="blue", label="Avg Tmin")

    # Trend line for avg_temp
    z = np.polyfit(df['year'], df['avg_temp'], 1)
    p = np.poly1d(z)
    plt.plot(df['year'], p(df['year']), "--", label="Trend Line", color="grey")

    plt.xlabel("Year")
    plt.ylabel("Temperature (ºC)")
    plt.title(f"Annual Temperature Trend for {station_name}")
    plt.legend()
    plt.grid()
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_station_monthly_rainfall(station_id):
    query = """
    SELECT month, 
        AVG(rain) AS avg_rain
    FROM observations
    WHERE station_id = ?
    GROUP BY month
    ORDER BY month;
    """
    params = (station_id,)

    data = db.select(query, params)

    if data is None:
        print("Error fetching rainfall data.")
        return
    station_name = get_station_name(station_id)
    file_name = f"{GRAPH_OUTPUT_DIR}/{station_name}_monthly_rainfall.png"
    df = pd.DataFrame(data, columns=['month', 'avg_rain'])
    df['month_name'] = pd.to_datetime(df['month'], format='%m').dt.strftime('%b')
    plt.bar(df['month_name'], df['avg_rain'], color="blue")

    plt.xlabel("Month")
    plt.ylabel("Average Rainfall (mm)")
    plt.title(f"Average Monthly Rainfall for {station_name}")
    plt.grid(axis='y')
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_station_monthly_sunshine(station_id):
    query = """
    SELECT month, 
        AVG(sun) AS avg_sun
    FROM observations
    WHERE station_id = ?
    GROUP BY month
    ORDER BY month;
    """
    params = (station_id,)

    data = db.select(query, params)

    if data is None:
        print("Error fetching sunshine data.")
        return
    station_name = get_station_name(station_id)
    file_name = f"{GRAPH_OUTPUT_DIR}/{station_name}_monthly_sunshine.png"
    df = pd.DataFrame(data, columns=['month', 'avg_sun'])
    df['month_name'] = pd.to_datetime(df['month'], format='%m').dt.strftime('%b')
    plt.bar(df['month_name'], df['avg_sun'], color="orange")

    plt.xlabel("Month")
    plt.ylabel("Average Sunshine (hours)")
    plt.title(f"Average Monthly Sunshine for {station_name}")
    plt.grid(axis='y')
    plt.savefig(file_name)
    plt.close()

    return file_name

# Overall Graphs #
def plot_overall_temp_trend():
    query = """
    SELECT year, 
        AVG((tmax + tmin) / 2.0) AS avg_temp
    FROM observations
    WHERE tmax IS NOT NULL AND tmin IS NOT NULL
    GROUP BY year
    ORDER BY year;
    """

    data = db.select(query)

    if data is None:
        print("Error fetching temperature data.")
        return
    
    file_name = f"{GRAPH_OUTPUT_DIR}/overall_temp_trend.png"
    df = pd.DataFrame(data, columns=['year', 'avg_temp'])
    plt.scatter(df['year'], df['avg_temp'], color="black", label="Avg Temp")

    # Trend line for avg_temp
    z = np.polyfit(df['year'], df['avg_temp'], 1)
    p = np.poly1d(z)
    plt.plot(df['year'], p(df['year']), "--", label="Trend Line", color="red")
    temp_delta_per_century = z[0] * 100
    sign = '+' if temp_delta_per_century >= 0 else '-'
    # Include trend info box
    plt.annotate(f"Trend: {sign}{temp_delta_per_century:.2f} ºC/century", xy=(0.05, 0.95), xycoords='axes fraction',
                 fontsize=10, ha='left', va='top',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1))

    plt.xlabel("Year")
    plt.ylabel("Temperature (ºC)")
    plt.title(f"Overall Annual Temperature Trend")
    plt.legend()
    plt.grid()
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_overall_monthly_temp():
    query = """
    SELECT month, 
        AVG((tmax + tmin) / 2.0) AS avg_temp
    FROM observations
    WHERE tmax IS NOT NULL AND tmin IS NOT NULL
    GROUP BY month
    ORDER BY month;
    """

    data = db.select(query)

    if data is None:
        print("Error fetching rainfall data.")
        return

    file_name = f"{GRAPH_OUTPUT_DIR}/average_monthly_temp.png"
    df = pd.DataFrame(data, columns=['month', 'avg_temp'])
    df['month_name'] = pd.to_datetime(df['month'], format='%m').dt.strftime('%b')
    plt.bar(df['month_name'], df['avg_temp'], color="red")

    plt.xlabel("Month")
    plt.ylabel("Average Tempurature (°C)")
    plt.title(f"Average Monthly Tempurature Across All Stations")
    plt.grid(axis='y')
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_overall_rainfall_trend():
    query = """
    SELECT year, 
        AVG(rain) AS avg_rain
    FROM observations
    WHERE rain IS NOT NULL
    GROUP BY year
    ORDER BY year;
    """

    data = db.select(query)

    if data is None:
        print("Error fetching temperature data.")
        return
    
    file_name = f"{GRAPH_OUTPUT_DIR}/overall_rainfall_trend.png"
    df = pd.DataFrame(data, columns=['year', 'avg_rain'])
    plt.scatter(df['year'], df['avg_rain'], color="black", label="Avg Rainfall")

    # Trend line for avg_rain
    z = np.polyfit(df['year'], df['avg_rain'], 1)
    p = np.poly1d(z)
    plt.plot(df['year'], p(df['year']), "--", label="Trend Line", color="blue")
    rain_delta_per_century = z[0] * 100
    sign = '+' if rain_delta_per_century >= 0 else '-'
    # Include trend info box
    plt.annotate(f"Trend: {sign}{rain_delta_per_century:.2f} mm/century", xy=(0.05, 0.95), xycoords='axes fraction',
                 fontsize=10, ha='left', va='top',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1))

    plt.xlabel("Year")
    plt.ylabel("Rainfall (mm)")
    plt.title(f"Overall Annual Rainfall Trend")
    plt.legend()
    plt.grid()
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_overall_monthly_rainfall():
    query = """
    SELECT month, 
        AVG(rain) AS avg_rain
    FROM observations
    WHERE rain IS NOT NULL
    GROUP BY month
    ORDER BY month;
    """

    data = db.select(query)

    if data is None:
        print("Error fetching rainfall data.")
        return

    file_name = f"{GRAPH_OUTPUT_DIR}/average_monthly_rainfall.png"
    df = pd.DataFrame(data, columns=['month', 'avg_rain'])
    df['month_name'] = pd.to_datetime(df['month'], format='%m').dt.strftime('%b')
    plt.bar(df['month_name'], df['avg_rain'], color="blue")

    plt.xlabel("Month")
    plt.ylabel("Average Rainfall (mm)")
    plt.title(f"Average Monthly Rainfall Across All Stations")
    plt.grid(axis='y')
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_overall_sunshine_trend():
    query = """
    SELECT year, 
        AVG(sun) AS avg_sun
    FROM observations
    WHERE sun IS NOT NULL
    GROUP BY year
    ORDER BY year;
    """

    data = db.select(query)

    if data is None:
        print("Error fetching sunshine data.")
        return
    
    file_name = f"{GRAPH_OUTPUT_DIR}/overall_sunshine_trend.png"
    df = pd.DataFrame(data, columns=['year', 'avg_sun'])
    plt.scatter(df['year'], df['avg_sun'], color="black", label="Avg Sunshine")

    # Trend line for avg_sun
    z = np.polyfit(df['year'], df['avg_sun'], 1)
    p = np.poly1d(z)
    plt.plot(df['year'], p(df['year']), "--", label="Trend Line", color="orange")
    sun_delta_per_century = z[0] * 100
    sign = '+' if sun_delta_per_century >= 0 else '-'
    # Include trend info box
    plt.annotate(f"Trend: {sign}{sun_delta_per_century:.2f} hours/century", xy=(0.05, 0.95), xycoords='axes fraction',
                 fontsize=10, ha='left', va='top',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1))

    plt.xlabel("Year")
    plt.ylabel("Sunshine (hours)")
    plt.title(f"Overall Annual Sunshine Trend")
    plt.legend()
    plt.grid()
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_overall_monthly_sunshine():
    query = """
    SELECT month, 
        AVG(sun) AS avg_sun
    FROM observations
    WHERE sun IS NOT NULL
    GROUP BY month
    ORDER BY month;
    """

    data = db.select(query)

    if data is None:
        print("Error fetching sunshine data.")
        return

    file_name = f"{GRAPH_OUTPUT_DIR}/average_monthly_sunshine.png"
    df = pd.DataFrame(data, columns=['month', 'avg_sun'])
    df['month_name'] = pd.to_datetime(df['month'], format='%m').dt.strftime('%b')
    plt.bar(df['month_name'], df['avg_sun'], color="orange")

    plt.xlabel("Month")
    plt.ylabel("Average Sunshine (hours)")
    plt.title(f"Average Monthly Sunshine Across All Stations")
    plt.grid(axis='y')
    plt.savefig(file_name)
    plt.close()

    return file_name

def plot_lat_against():
    query = """
    SELECT s.lat,
        AVG(o.rain) AS avg_rain,
        AVG((o.tmax + o.tmin) / 2.0) AS avg_temp,
        AVG(o.sun) AS avg_sun
    FROM stations s
    JOIN observations o ON s.id = o.station_id
    GROUP BY s.id
    ORDER BY s.lat;
    """
    data = db.select(query)

    if data is None:
        print("Error fetching latitude correlation data.")
        return
    
    df = pd.DataFrame(data, columns=['lat', 'avg_rain', 'avg_temp', 'avg_sun'])

    filenames = {}
    filenames['rain'] = f"{GRAPH_OUTPUT_DIR}/lat_rain_correlation.png"

    z = np.polyfit(df['lat'], df['avg_rain'], 1)
    p = np.poly1d(z)
    mm_per_degree = z[0]
    plt.annotate(f"Trend: {mm_per_degree:.2f} mm/degree", xy=(0.05, 0.95), xycoords='axes fraction',
                 fontsize=10, ha='left', va='top',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1))
    plt.plot(df['lat'], p(df['lat']), "--", label="Trend Line", color="red")
    plt.legend()

    plt.scatter(df['lat'], df['avg_rain'], color="blue")
    plt.xlabel("Latitude")
    plt.ylabel("Average Monthly Rainfall (mm)")
    plt.title(f"Latitude vs Average Monthly Rainfall")
    plt.grid()
    plt.savefig(filenames['rain'])
    plt.close()

    filenames['temp'] = f"{GRAPH_OUTPUT_DIR}/lat_temp_correlation.png"

    z = np.polyfit(df['lat'], df['avg_temp'], 1)
    p = np.poly1d(z)
    celsius_per_degree = z[0]
    plt.annotate(f"Trend: {celsius_per_degree:.2f} ºC/degree", xy=(0.05, 0.95), xycoords='axes fraction',
                 fontsize=10, ha='left', va='top',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1))
    plt.plot(df['lat'], p(df['lat']), "--", label="Trend Line", color="red")
    plt.legend()

    plt.scatter(df['lat'], df['avg_temp'], color="red")
    plt.xlabel("Latitude")
    plt.ylabel("Average Monthly Temperature (ºC)")
    plt.title(f"Latitude vs Average Monthly Temperature")
    plt.grid()
    plt.savefig(filenames['temp'])
    plt.close()

    filenames['sun'] = f"{GRAPH_OUTPUT_DIR}/lat_sun_correlation.png"

    z = np.polyfit(df['lat'], df['avg_sun'], 1)
    p = np.poly1d(z)
    hours_per_degree = z[0]
    plt.annotate(f"Trend: {hours_per_degree:.2f} hours/degree", xy=(0.05, 0.95), xycoords='axes fraction',
                 fontsize=10, ha='left', va='top',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1))
    plt.plot(df['lat'], p(df['lat']), "--", label="Trend Line", color="red")
    plt.legend()

    plt.scatter(df['lat'], df['avg_sun'], color="orange")
    plt.xlabel("Latitude")
    plt.ylabel("Average Monthly Sunshine (hours)")
    plt.title(f"Latitude vs Average Monthly Sunshine")
    plt.grid()
    plt.savefig(filenames['sun'])
    plt.close()

    return filenames