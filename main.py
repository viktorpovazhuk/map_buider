import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import math
from geopy.exc import GeocoderUnavailable, GeocoderServiceError
import time
import folium


def read_locations_file(path: str):
    """
    Read locations from file
    """
    with open(file=path, encoding='cp1252') as f:
        for _ in range(14):
            next(f)
        lines = f.readlines()

    locations = []

    for line in lines:
        title_location = line.strip().split("\t")
        title_location = list(filter(None, title_location))
        title_location = tuple(title_location[:2])
        locations.append(title_location)

    df = pd.DataFrame(locations, columns=['Title', 'Place'])

    return df


def filter_films(df: pd.DataFrame, year: str):
    """
    Filter unsuitable films
    """
    df = df[df['Title'].str.contains(year) &
            (df['Place'].str.contains('Federal') == False)]
    df.reset_index(drop=True, inplace=True)

    return df


def find_coordinates(df: pd.DataFrame):
    df['Lon'], df['Lat'] = 0, 0
    df = df.astype({'Lon': 'float64', 'Lat': 'float64'}, copy=False)

    geolocator = Nominatim(user_agent="geo_loc")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.5)

    # req_nums = 0

    for idx in df.index:
        place = df.iloc[idx, :]['Place']

        try:
            if check_and_set_exist_coordinates(df, place, idx):
                continue

            location = geolocator.geocode(place)
            # req_nums += 1

            if location == None:
                place = place[place.find(',') + 2:]

                if check_and_set_exist_coordinates(df, place, idx):
                    continue

                location = geolocator.geocode(place)
                # req_nums += 1

            if location == None:
                df.at[idx, 'Lon'], df.at[idx, 'Lat'] = 0, 0
                continue

            df.at[idx, 'Place'] = place
            df.at[idx, 'Lon'] = location.longitude
            df.at[idx, 'Lat'] = location.latitude
            # print(location.longitude, location.latitude)

        except (GeocoderUnavailable, GeocoderServiceError, Exception) as exc:
            with open('fatal_erros.txt', 'a') as f:
                f.write(f'{place}: {str(exc)} \n')

    # print('req nums: ' + str(req_nums))

    return df


def check_and_set_exist_coordinates(df: pd.DataFrame, place: str, idx: int):
    cur_df = df.iloc[:idx, :]
    exist_places = cur_df.loc[cur_df['Place'] == place]

    if len(exist_places) != 0:
        df.at[idx, 'Place'] = place
        df.at[idx, 'Lon'] = exist_places.iloc[0]['Lon']
        df.at[idx, 'Lat'] = exist_places.iloc[0]['Lat']

        # print(f'duplicate: {place}, index: {idx}')

        return True
    else:
        return False


def calculate_distances(df: pd.DataFrame, set_lat: float, set_lon: float):
    df['Distance'] = 0
    df = df.astype({'Distance': 'float64'}, copy=False)

    set_lon, set_lat = math.radians(set_lon), math.radians(set_lat)
    earth_rad = 6371

    for idx in df.index:
        cur_lon = math.radians(df.iloc[idx, :]['Lon'])
        cur_lat = math.radians(df.iloc[idx, :]['Lat'])
        df.at[idx, 'Distance'] = (2 * earth_rad * math.asin(math.sqrt(
            math.sin((cur_lat - set_lat) / 2) ** 2 +
            math.cos(set_lat) * math.cos(cur_lat)
            * math.sin((cur_lon - set_lon) / 2) ** 2)))

    return df


def generate_map_file(df: pd.DataFrame, set_coordinates: tuple):
    mp = folium.Map(location=list(set_coordinates))

    fg = folium.FeatureGroup(name="Films locations")
    for _, (lt, ln, title) in df[['Lat', 'Lon', 'Title']].iterrows():
        fg.add_child(folium.Marker(location=[float(lt), float(ln)],
                                   popup=title, icon=folium.Icon()))
    mp.add_child(fg)

    mp.add_child(folium.LayerControl())

    mp.save('nearby_movies_map.html')


def create_map(year: str, set_coordinates: str):
    set_coordinates = tuple(map(float, set_coordinates.split(',')))

    df = read_locations_file('data/locations.list')

    year = '2006'

    df = filter_films(df, year)

    # limit df
    df = df.iloc[:100, :]

    # start = time.time()
    df = find_coordinates(df)
    # fin = time.time()

    # print('seconds: ' + str((fin - start) / 60))

    df = calculate_distances(df, *set_coordinates)
    df.sort_values(by=['Distance'], inplace=True)

    generate_map_file(df[:10], set_coordinates)


if __name__ == '__main__':
    movies_year = input(
        'Please enter a year you would like to have a map for: ')
    set_coordinates = input('Please enter your location (format: lat, long): ')
    print('Map is generating...')
    print('Please wait...')
    create_map(movies_year, set_coordinates)
    print('Finished. Please have look at the map nearby_movies_map.html')
