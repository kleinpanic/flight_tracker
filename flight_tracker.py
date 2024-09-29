import requests
import pandas as pd
import sqlite3
import tkinter as tk
from tkinter import ttk
import folium
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Function to fetch flight data from OpenSky Network API with retries and a timeout
def get_flight_data():
    url = "https://opensky-network.org/api/states/all"
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        columns = [
            "icao24", "callsign", "origin_country", "time_position", "last_contact",
            "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
            "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
            "spi", "position_source"
        ]
        df = pd.DataFrame(data["states"], columns=columns)
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error
    except ValueError as e:
        print(f"Error processing data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

# Function to store flight data in SQLite database
def store_flight_data(df):
    if df.empty:
        print("No data to store")
        return
    try:
        conn = sqlite3.connect('flights.db')
        df.to_sql('flights', conn, if_exists='replace', index=False)
        conn.close()
    except sqlite3.Error as e:
        print(f"Error storing data: {e}")

# Function to create a map using Folium
def create_map(df):
    if df.empty:
        print("No data to create map")
        return
    try:
        m = folium.Map(location=[20, 0], zoom_start=2)
        for i, row in df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=row['callsign'],
                ).add_to(m)
        m.save('flights_map.html')
        print("Map has been saved as flights_map.html")
    except Exception as e:
        print(f"Error creating map: {e}")

# Function to display information about a specific flight
def display_specific_flight_data(df, icao24):
    specific_flight = df[df['icao24'] == icao24]
    if specific_flight.empty:
        print(f"No data available for flight with ICAO24: {icao24}")
    else:
        print(specific_flight)

# Function to list available ICAO24 identifiers and callsigns
def list_available_flights(df):
    if df.empty:
        print("No data available")
        return
    available_flights = df[['icao24', 'callsign']].dropna().drop_duplicates()
    print("Available ICAO24 identifiers and callsigns:")
    print(available_flights)

# CLI user interaction
def main():
    print("Welcome to the Flight Tracker!")
    flight_data = get_flight_data()
    store_flight_data(flight_data)

    if flight_data.empty:
        print("Unable to fetch flight data. Please check your network connection and try again later.")
        return

    list_available_flights(flight_data)

    icao24 = input("Enter the ICAO24 identifier of the flight you want to track: ").strip().lower()
    display_specific_flight_data(flight_data, icao24)

    while True:
        show_map = input("Do you want to see a map of the flights? (yes/no): ").strip().lower()
        if show_map in ['yes', 'no']:
            break
        else:
            print("Invalid input, please enter 'yes' or 'no'.")

    if show_map == 'yes':
        create_map(flight_data)

    while True:
        show_gui = input("Do you want to see the flight data in a GUI? (yes/no): ").strip().lower()
        if show_gui in ['yes', 'no']:
            break
        else:
            print("Invalid input, please enter 'yes' or 'no'.")

    if show_gui == 'yes':
        start_gui()

# Function to start the GUI
def start_gui():
    def show_flight_data():
        flight_data = get_flight_data()
        store_flight_data(flight_data)
        create_map(flight_data)
        tree.delete(*tree.get_children())  # Clear existing data in the treeview
        for i, row in flight_data.iterrows():
            tree.insert("", "end", values=list(row))

    # GUI setup using Tkinter
    root = tk.Tk()
    root.title("Flight Tracker")

    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True)

    # Fetch initial flight data
    flight_data = get_flight_data()

    columns = list(flight_data.columns)
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.pack(fill="both", expand=True)

    button = ttk.Button(root, text="Refresh Data", command=show_flight_data)
    button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
