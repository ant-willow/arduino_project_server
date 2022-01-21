import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
CITY = 'Saint Petersburg'


def get_weather():
    response = requests.get('http://api.openweathermap.org/data/2.5/weather',
                            params={'q': CITY, 'lang': 'ru', 'units': 'metric', 'appid': API_KEY})
    
    if response.status_code != 200:
        return

    data = response.json()
    city_name = data['name']
    icon_code = data['weather'][0]['icon']
    icon_url = f'http://openweathermap.org/img/wn/{icon_code}@2x.png'
    temp  = data['main']['temp']
    temp = round(int(temp))
    humi = data['main']['humidity']
    pressure = data['main']['pressure']
    pressure_mmhg = round(pressure * 0.75006157818041)
    return {'city': city_name, 'icon_url': icon_url,
            'temp': temp, 'humidity': humi, 'pressure': pressure_mmhg}
