from urllib.request import urlopen
from urllib.error import HTTPError
from datetime import datetime
from time import sleep
import logging
import os
import json
import configparser


path = os.path.abspath(os.path.dirname(__file__))

cfg = configparser.ConfigParser()
cfg.read(path + '/settings.ini')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s : %(levelname)s : %(message)s',
    filename=f'{path}/log.log',
    filemode='a',
    )


def get_data(url: str):
    """ завантажує дані з інтернету у локальний файл """
    url = url.strip()
    tmp = ""

    try:
        tmp = json.loads(urlopen(url).read().decode('utf-8'))
    except HTTPError as e:
        logging.error("HTTPError:\ne")
        return None

    with open(path + '/data.json', 'w') as fh:
        tmp['last_update_time'] = datetime.now().timestamp()
        fh.write(json.dumps(tmp))


def load_data():
    """ читає файл з погодою та декодує в json """
    with open(path + '/data.json', 'r') as fh:
        data = json.load(fh)
    return data


def from_wmo(wmo: int):
    return cfg['FORECAST'][str(wmo)]


def weather_data(d: dict):
    res = []
    for i, j in enumerate(d['time']):
        time = datetime.fromtimestamp(d['time'][i])
        temp = d['temperature_2m'][i]
        wmo = d['weathercode'][i]
        wind = d['windspeed_10m'][i]
        res.append((time, temp, from_wmo(wmo), wind))
    return res


if __name__ == "__main__":
    next_update = datetime.now().timestamp()
    lat = cfg["LOCATION"]["latitude"]
    long = cfg["LOCATION"]["longitude"]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&hourly=temperature_2m,weathercode,windspeed_10m,winddirection_10m&daily=sunrise,sunset&timeformat=unixtime&timezone=Europe%2FLondon"
    now = datetime.now().timestamp()

    if not os.path.exists(path + "/data.json"):
        get_data(url)
    data = load_data()

    if data['last_update_time'] + 3600 < now:
        get_data(url)
        data = load_data()

    weather = weather_data(data['hourly'])
    for i, j in enumerate(weather):
        if weather[i][0] < datetime.now() < weather[i+1][0]:
            s = f'{j[1]}℃ {j[2]}, wind: {j[3]} km/h'
            next_update = weather[i+1][0].timestamp()
            print(s)
            with open(path + '/weather.txt', 'w') as fh:
                fh.write(s)
    logging.info(f"weather: {s}")

