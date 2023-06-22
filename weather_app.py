from sqlalchemy import Column, Integer, String, create_engine, MetaData, Table, text, select, delete
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__,static_url_path='',static_folder='web/static',template_folder='web/templates')
API_KEY = os.environ["API_KEY"]
SECRET_KEY = os.environ['SECRET_KEY']
SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
app.config["SECRET_KEY"] = SECRET_KEY

engine = create_engine(SQLALCHEMY_DATABASE_URI)
metadata = MetaData()
city = Table('city', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('name', String))
metadata.create_all(engine)


def get_weather_data(city):
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid="+API_KEY
    r = requests.get(BASE_URL.format(city)).json()
    return r

@app.route('/')
def index_get():
    try:
        conn = engine.connect()
        result = conn.execute(text("select name from city order by id desc"))
        cities = result.fetchall()

        weather_data = []
        for city_row in cities:
            data = get_weather_data(city_row.name)
            weather ={
                'city_name' : data['name'].title(),
                'country' : data['sys']['country'],
                'description' : data['weather'][0]['description'].title(),
                'icon' : data['weather'][0]['icon'],
                'temperature' : data['main']['temp'],
            }
            weather_data.append(weather)
        conn.close()
        return render_template('index.html',weather_data=weather_data)
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('index.html'))
        


@app.route('/', methods=['POST'])
def index_post():
    try:
        conn = engine.connect()
        err_msg = ''

        new_city = request.form.get('add_city')
        new_city = new_city.lower()
        if new_city:  #added for null
            select_query = select(city.c.name).where(city.c.name == new_city)
            result = conn.execute(select_query)
            existing_city = [row[0] for row in result]
            if not existing_city:
                new_city_data = get_weather_data(new_city)
                if new_city_data['cod'] == 200:
                    add_new_city = city.insert().values(name=new_city)
                    conn.execute(add_new_city)
                    conn.commit()
                else:
                    err_msg = "city does not exist in the world!"
            else:
                err_msg = "City already exists in the list!"

            if err_msg:
                flash(err_msg, 'error')
            else:
                flash('City added successfully!')
            
        conn.close()
        
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('index_get')) 


@app.route('/delete/<name>')
def delete_city(name):
    try:
        conn = engine.connect()
        name = name.lower()
        delete_query = city.delete().where(city.c.name == name)
        conn.execute(delete_query)
        conn.commit()
        print('deleted')
        conn.close()

        flash(f'Successfully deleted { name }', 'success')
        
    except Exception as e:
        flash(str(e), 'error')
    return redirect(url_for('index_get'))
