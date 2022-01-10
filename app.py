import logging
from datetime import datetime as dt

from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, func

from utils import bp, moscow_now
from weather import get_weather

PAGE_SIZE = 7
DETAIL_PAGE_SIZE = 36


class Error:
    WRONG_DATA = 'Некорректные данные!'
    SENSORS_ERROR = 'Некорректная работа сенсоров!'
    CREATE_ERROR = 'Ошибка создания записи!'

logging.basicConfig(filename='arduino_temp_humi.log', level=logging.INFO,
                   format='%(asctime)s %(levelname)s - %(message)s')

app = Flask(__name__)
app.register_blueprint(bp)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensor_values.db'
db = SQLAlchemy(app)


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, default=1)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    created = db.Column(db.DateTime, default=moscow_now)
    light = db.Column(db.Boolean)


@app.route('/')
def index():
    entry = Entry.query.order_by(Entry.created.desc()).filter(Entry.device_id == 1).first()
    entry2 = Entry.query.order_by(Entry.created.desc()).filter(Entry.device_id == 2).first()
    return render_template('index.html', entry=entry, entry2=entry2, weather=get_weather())


@app.route('/daily/')
def daily():
    # список показаний с групировкой по дням
    page = request.args.get('page', 1, type=int)
    year = request.args.get('year', moscow_now().date().year)
    month = request.args.get('month', moscow_now().date().month)
    device_id = request.args.get('device_id', 1)
    table = request.args.get('table', False) 
   
    entries = (db.session.query(
        Entry.created,
        func.min(Entry.temperature).label('min_temp'),
        func.round(func.avg(Entry.temperature), 1).label('avg_temp'),
        func.max(Entry.temperature).label('max_temp'),
        func.min(Entry.humidity).label('min_humi'),
        func.round(func.avg(Entry.humidity), 1).label('avg_humi'),
        func.max(Entry.humidity).label('max_humi'))
               .filter(extract('year', Entry.created) == year, 
                       extract('month', Entry.created) == month,
                       Entry.device_id == device_id)
               .group_by(func.strftime('%Y-%m-%d', Entry.created)) 
               )

    available_months = (db.session.query(
        extract('month', Entry.created))
              .group_by(func.strftime('%m', Entry.created))
              .filter(extract('year', Entry.created) == year)
              .all())
    available_years = (db.session.query(
        extract('year', Entry.created),
        extract('month', Entry.created))
             .group_by(func.strftime('%Y', Entry.created))
             .order_by(Entry.created.desc())
             .all())

    data = {'available_years': available_years,'available_months': available_months,
            'year': year, 'month': month, 'device_id': device_id}
    
    if not table:
        chart_data = [{'min_t': n.min_temp, 'avg_t': n.avg_temp, 'max_t': n.max_temp,
                      'min_h': n.min_humi, 'avg_h': n.avg_humi, 'max_h': n.max_humi,
                      'x': n.created.day}  for n in entries]
        data.update({'chart_data': chart_data})
    data.update({'entries': entries.paginate(page, PAGE_SIZE, True)})

    return render_template('daily.html', **data)


@app.route('/detail/')
def detail():
    # список показаний за указаную дату(день)
    date = request.args.get('date', moscow_now().date())
    
    try:
        date = dt.strptime(str(date), '%Y-%m-%d').date()
    except(ValueError):
        return render_template('404.html'), 404

    table = request.args.get('table', False)
    device_id = request.args.get('device_id', 1)
    data = {'table': table, 'device_id': device_id, 'date': date}
    page = request.args.get('page', 1, type=int)
                             
    if not table:
        entries = (db.session.query(
            Entry.created,
            func.round(func.avg(Entry.temperature), 1).label('avg_temp'),
            func.round(func.avg(Entry.humidity), 1).label('avg_humi') ,
            extract('hour', Entry.created))
                .filter(func.date(Entry.created) == date,
                        Entry.device_id == device_id)
                .group_by(func.strftime('%H', Entry.created))
                .all())

        chart_data = [{'x': n.created.hour,
                       'avg_t': n.avg_temp,
                       'avg_h': n.avg_humi} for n in entries]
        data.update({'chart_data': chart_data})
    else:
        entries = (Entry.query.filter(
            func.date(Entry.created) == date,
            Entry.device_id == device_id)
                .paginate(page, DETAIL_PAGE_SIZE, True))
    data.update({'entries': entries})
    
    return render_template('detail.html', **data)


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


@app.errorhandler(404)
def not_found(e):
  return render_template("404.html"), 404


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
