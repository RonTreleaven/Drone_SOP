#!/usr/bin/env python3
"""Download data about all active Environment Canada weather stations"""
"""https://github.com/timdaman/canadian-weather-station-downloader"""

### March 26, 2026 - Updated to work with the new Environment Canada API. 
#   The old API was retired in 2024 and the new one is much more difficult to work with. 
#   The new API does not have a single endpoint to get all of the stations. 
#   Instead you have to page through the stations one at a time. This makes the process much slower but it is still possible to get the data. 
#   The new API also does not have a way to get the station metadata in a single request. Instead you have to make a separate request for each station to get the metadata. 
#   This makes the process even slower but it is still possible to get the data. The new API also does not have a way to get the station metadata in a machine readable format. 
#   Instead you have to parse the HTML
#   
# What I changed:
#  Added URL encoding import at GetWeatherStations.py:17.
#  Updated station parsing to collect hidden form inputs and require climate_id at GetWeatherStations.py:120.
# Updated details fetching to accept a station request payload and build the daily-data URL from that payload at GetWeatherStations.py:133.
#  Updated main loop to pass station payloads instead of StationID values at GetWeatherStations.py:159.

## working copy!!!!


from collections import OrderedDict
from csv import DictWriter
from datetime import timedelta, timezone, datetime
from typing import Iterable
from urllib.parse import urlencode

import bs4
import requests

__version__ = '1.0'

"""
This is a small program that downlands data about all of the currently active
weather stations in Canada and exports that in CSV format.

The goal of this script is to produce a CSV suitable to use with Google "My Maps".

Why do I need this? I use weather data to determine if the ice on small lakes
in an area is likely safe to travel on. To do this I process the data of a
weather station hour by hour and imagine a lake is right next to them.

I do not want to use forecast data from the area I am going to as that is
synthesized and may have various biases. I use the data from the nearest
weather station. This program helps im mapping all of the weather active
stations and then visually I can determine which one is best for my
destination.

This program is slow. This is kind to the Weather API and given I plan to
run it once a year so this slowness is not a issue.
"""

"""
Copyright 2021 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# In the Environment Canada API days end when they end in PST
pst = timezone(timedelta(hours=-8))  # UTC -8:00
one_day = timedelta(days=1)
# The APIs do not present data for today until the day is complete.
# As a result we look for stations with data yesterday
today = datetime.now(tz=pst)
yesterday = today - one_day
y_year = yesterday.year
y_month = yesterday.month
y_day = yesterday.day

host = 'https://climate.weather.gc.ca'


def generate_stations(api_host: str = host, year: int = y_year, month: int = y_month, day: int = y_day) \
        -> Iterable[dict[str, str]]:
    """Returns station request payloads for every active station one at a time."""

    start = 0
    interval = 100
    while True:
        station_list_url = f'{api_host}/historical_data/search_historic_data_stations_e.html?' \
                           f'searchType=stnProv&' \
                           f'timeframe=1' \
                           f'&lstProvince=' \
                           f'&StartYear=1840' \
                           f'&EndYear={year}' \
                           f'&optLimit=specDate' \
                           f'&Year={year}' \
                           f'&Month={month}' \
                           f'&Day={day}' \
                           f'&selRowPerPage={interval}' \
                           f'&startRow={start}'
        print(f"Starting at {start} ", end='', flush=True)
        response = requests.get(station_list_url, allow_redirects=True)
        if response.status_code != 200:
            print(f"Server returned error. {response.status_code} {response.content} {station_list_url}")
            exit(1)

        if b'Sorry' in response.content:
            print("Server says data is not available")
            exit(2)

        if b'Your request could not be completed because an error was found' in response.content:
            print("Request error, perhaps the server API has changed?")
            exit(3)

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        base = soup.find(class_='historical-data-results')
        if base is None:
            print("All stations processed!")
            break

        station_list = base.find_all("form")

        for station in station_list:
            payload = {}
            for input_field in station.find_all("input", attrs={'name': True}):
                payload[input_field['name']] = input_field.get('value', '')

            if 'climate_id' not in payload:
                print("!", end='', flush=True)
                continue

            payload['timeframe'] = '2'
            payload.setdefault('Apply', 'Apply')

            print(".", end='', flush=True)
            yield payload
        print("")
        start += interval


def get_station_details(station_request: dict[str, str], api_host: str = host) -> OrderedDict:
    """Given a station request payload, return station metadata."""
    details = OrderedDict()

    details['StationID'] = station_request.get('climate_id', '')
    details['url'] = f"{api_host}/climate_data/daily_data_e.html?{urlencode(station_request)}"

    response = requests.get(details['url'])
    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.content, 'html.parser')

    title_block = soup.select_one("p.table-header").contents
    details['name'] = title_block[0]
    details['province'] = title_block[2]

    for field in ['latitude', 'longitude', 'elevation', 'climateid', 'wmoid', 'tcid']:
        details[field] = soup.select_one(f'div[aria-labelledby={field}]').text.lstrip(' ')
    return details


def main():
    filename = f"canada_weather_station_data_{y_year}-{y_month}-{y_day}.csv"
    print(f'Writing {filename}')
    with open(filename, 'w', newline='') as csv_file:
        first = True
        writer = None
        for station_request in generate_stations():
            details = get_station_details(station_request=station_request)
            if first:
                writer = DictWriter(csv_file, fieldnames=details.keys())
                writer.writeheader()
                first = False
            writer.writerow(details)


if __name__ == '__main__':
    main()