import requests

API_KEY = 'cdb4dc7326b69ab1b44830e3aca84d87'
CITY = 'Saint Petersburg'


def get_weather():
    response = requests.get('http://api.openweathermap.org/data/2.5/weather',
                            params={'q': CITY, 'lang': 'ru', 'units': 'metric', 'appid': API_KEY})
    
    if response.status_code != 200:
        return

    data = response.json()
    city = data['name']
    icon_code = data['weather'][0]['icon']
    icon_url = f'http://openweathermap.org/img/wn/{icon_code}@2x.png'
    temp  = data['main']['temp']
    temp = round(int(temp))
    humi = data['main']['humidity']

    return {'city': city, 'icon_url': icon_url, 'temp': temp, 'humidity': humi}
