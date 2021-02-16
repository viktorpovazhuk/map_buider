import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import math
import sys
from geopy.exc import GeocoderUnavailable, GeocoderServiceError

def read_locations_file(path: str):
    with open(file="data/locations.list", encoding='cp1252') as f:
    for _ in range(14):
        next(f)
    lines = f.readlines()

    locations = []

    for line in lines:
        line = line.strip()
        loc = line.split("\t")
        loc = list(filter(None, loc))
        loc = tuple(loc[:2])
        locations.append(loc)

    df = pd.DataFrame(locations, columns=['Title', 'Place'])



year = '2006'
df_year = df[df['Title'].str.contains(year)]
df_year = df_year.iloc[:1000, :]
df_year.reset_index(drop=True, inplace=True)

# print(len(df_year))
# print(df_year.head(10))
# sys.exit()

df_year['Lon'], df_year['Lat'], df_year['Distance'] = 0, 0, 0
df_year = df_year.astype({'Lon': 'float64', 'Lat': 'float64', 'Distance': 'float64'}, copy=False)

geolocator = Nominatim(user_agent="geo_loc")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)

req_nums = 0

for idx in df_year.index:
    place = df_year.iloc[idx, :]['Place']
    # print(place)
    
    try:
    
        cur_df = df_year.iloc[:idx, :]
        exist_place = cur_df.loc[cur_df['Place'] == place]
        if len(exist_place) != 0:
            df_year.at[idx, 'Place'] = place
            df_year.at[idx, 'Lon'] = exist_place.iloc[0]['Lon']
            df_year.at[idx, 'Lat'] = exist_place.iloc[0]['Lat']
            continue
        location = geolocator.geocode(place)
        req_nums += 1
        if location == None:
            place = place[place.find(',') + 2:]
            cur_df = df_year.iloc[:idx, :]
            exist_place = cur_df.loc[cur_df['Place'] == place]
            if len(exist_place) != 0:
                df_year.at[idx, 'Place'] = place
                df_year.at[idx, 'Lon'] = exist_place.iloc[0]['Lon']
                df_year.at[idx, 'Lat'] = exist_place.iloc[0]['Lat']
                continue
            location = geolocator.geocode(place)
        if location == None:
            delete raw
            continue
        df_year.at[idx, 'Place'] = place
        df_year.at[idx, 'Lon'] = location.longitude
        df_year.at[idx, 'Lat'] = location.latitude
        # print(location.longitude, location.latitude)
    
    except (GeocoderUnavailable, GeocoderServiceError) as exc:
        print(exc)
        print(place)

print(len(df_year))
print(df_year.head(10))
print('req nums: ' + str(req_nums))
sys.exit()

set_lon, set_lat = math.radians(49.83826), math.radians(24.02324)
earth_rad = 6371

for idx in df_year.index:
    cur_lon = math.radians(df_year.iloc[idx, :]['Lon'])
    cur_lat = math.radians(df_year.iloc[idx, :]['Lat'])
    df_year.at[idx, 'Distance'] = 2 * earth_rad * math.asin(math.sqrt(math.sin((cur_lat - set_lat) / 2) ** 2 +
    math.cos(set_lat) * math.cos(cur_lat) * math.sin((cur_lon - set_lon) / 2) ** 2))

df_year.sort_values(by=['Distance'], inplace=True)

print(df_year.iloc[:5, :])


# ex_lon, ex_lat = math.radians(50.83826), math.radians(24.02324)

# distance = 2 * earth_rad * math.asin(math.sqrt(math.sin((ex_lat - set_lat) / 2) ** 2 +
# math.cos(set_lat) * math.cos(ex_lat) * math.sin((ex_lon - set_lon) / 2) ** 2))

