import urllib.parse
from datetime import datetime as dt

import pytz
from flask import Blueprint

MONTHS = ['Январь', 'Февраль', 'Март',
          'Апрель', 'Май', 'Июнь',
          'Июль','Август', 'Сентябрь',
          'Октябрь', 'Ноябрь', 'Декабрь']


bp = Blueprint('utils', __name__, template_folder='templates', static_folder='static')


def moscow_now():
    return dt.now(tz=pytz.timezone('Europe/Moscow'))

@bp.app_context_processor
def inject_moscow_now():
    return {'moscow_now': moscow_now().date()}

@bp.app_context_processor
def utility_processor():
    def day_of_month(value):
        return MONTHS[int(value) - 1]
    return {'day_of_month': day_of_month}

@bp.app_context_processor
def utility_processor():
    def query_update(request, **kwargs):
        updated = request.args.copy()
        for key, value in kwargs.items():
            if value != 0:
                updated[key] = value
            else:
                updated.pop(key)
        return f'?{urllib.parse.urlencode(updated, doseq=True)}'
    return {'query_update': query_update}
    
@bp.app_context_processor
def utility_processor():
    def pick_color(red, value, blue):
        red *= 200
        blue *= 200
        green = round(255 - (255 * value * 2 / 100))
        green = max(0, min(green, 255))
        alpha =  round(0.2 * value * 2 / 100, 2)
        return f'rgba({red}, {green}, {blue}, {alpha});'
    return {'pick_color': pick_color}
