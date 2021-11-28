from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime as dt
import pytz
import logging


LIST_PAGE_SIZE = 7
DETAIL_PAGE_SIZE = 36

class Error:
    WRONG_DATA = 'Некорректные данные!'
    SENSORS_ERROR = 'Некорректная работа сенсоров!'
    CREATE_ERROR = 'Ошибка создания записи!'

logging.basicConfig(filename='arduino_temp_humi.log', level=logging.INFO,
                   format='%(asctime)s %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensor_values.db'
db = SQLAlchemy(app)


def moscow_now():
    return dt.now(tz=pytz.timezone('Europe/Moscow'))

@app.context_processor
def inject_moscow_now():
    return {'moscow_now': moscow_now().date()}

@app.context_processor
def utility_processor():
    def pick_color(red, value, blue):
        red *= 200
        blue *= 200
        green = 255 - (255 * value * 2 / 100)
        alpha =  0.2 * value * 2 / 100
        return f'rgba({red}, {green}, {blue}, {alpha});'
    return {'pick_color': pick_color}



class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, default=1)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    created = db.Column(db.DateTime, default=moscow_now)
    light = db.Column(db.Boolean)


@app.route('/')
def index():
    entry = Entry.query.order_by(Entry.created.desc()).first()
    return render_template('index.html', entry=entry)

@app.route('/list')
def list():
    # список показаний с групировкой по дням
    page = request.args.get('page', 1, type=int)
    entries = (db.session.query(
        Entry.created,
        func.min(Entry.temperature).label('min_temp'),
        func.round(func.avg(Entry.temperature), 1).label('avg_temp'),
        func.max(Entry.temperature).label('max_temp'),
        func.min(Entry.humidity).label('min_humi'),
        func.round(func.avg(Entry.humidity), 1).label('avg_humi'),
        func.max(Entry.humidity).label('max_humi'),
        )
               .group_by(func.strftime('%Y-%m-%d', Entry.created))
               .order_by(Entry.created.desc())
               .paginate(page, LIST_PAGE_SIZE, False))
    return render_template('list.html', entries=entries)

@app.route('/detail/<string:date>')
def detail(date):
    # список показаний за указаную дату(день)
    page = request.args.get('page', 1, type=int)
    entries =  (Entry.query.filter(func.date(Entry.created) == date)
                .paginate(page, DETAIL_PAGE_SIZE, False))
    return render_template('detail.html', entries=entries)

@app.route('/add', methods=['POST'])
def add():
    device_id = request.form.get('device_id')
    temp = request.form.get('temp')
    humi = request.form.get('humi')

    if temp is None or humi is None:
        logging.error(Error.WRONG_DATA)
        return Error.WRONG_DATA, 400
    
    if temp != temp or humi != humi:
        logging.error(Error.SENSORS_ERROR)
        return Error.SENSORS_ERROR, 400
    
    temp = round(float(temp), 1)
    humi = round(float(humi), 1)
        
    new_entry = Entry(device_id=device_id, temperature=temp, humidity=humi)
    
    try:
        db.session.add(new_entry)
        db.session.commit()
        return redirect('/')
    except:
        logging.error(Error.CREATE_ERROR)
        return Error.CREATE_ERROR, 400

if __name__ == '__main__':
    app.run(debug=True)