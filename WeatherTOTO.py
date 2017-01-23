#From http://flask.pocoo.org/docs/0.12/quickstart/#quickstart
import os
import hashlib
import sys
import requests
import urllib.request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
import urllib.request
from flask import redirect,Flask, request, render_template, send_from_directory,make_response
import traceback

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test12.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ashe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

session_moum={}

weather_check={}
weather_check['맑음']="wi-day-sunny"
weather_check['구름조금']="wi-day-cloudy-high"
weather_check['구름많음']="wi-day-cloudy"
weather_check['구름많고 비']="wi-day-rain"
weather_check['구름많고 눈']="wi-day-snow"
weather_check['구름많고 비 또는 눈']="wi-day-rain-mix"
weather_check['흐림']="wi-cloudy"
weather_check['흐리고 비']="wi-rain"
weather_check['흐리고 눈']="wi-snow"
weather_check['흐리고 비 또는 눈']="wi-rain-mix"
weather_check['흐리고 낙뢰']="wi-lightning"
weather_check['뇌우, 비']="wi-thunderstorm"
weather_check['뇌우, 눈']="wi-storm-showers"
weather_check['뇌우, 비 또는 눈']="wi-night-sleet-storm"

city_to_geo = {}
city_to_geo['서울'] = ('37.566535', '126.97796919999996')
city_to_geo['대전'] = ('36.3504119', '127.38454750000005')
city_to_geo['대구'] = ('35.8714354', '128.601445')
city_to_geo['부산'] = ('35.1795543', '129.07564160000004')

#Define User & Prediction for SQLite
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    pw = db.Column(db.String(80), unique=False)
    predictions = db.relationship('Prediction', backref='User',
                                lazy='dynamic')
    #money = db.Column(db.Integer, unique=False)
    #total = db.Column(db.Integer, unique=False)
    #win = db.Column(db.Integer, unique=False)

    def __init__(self, username, pw):
        self.username = username
        self.pw = pw
        return None
    def __repr__(self):
        return '<User %r>' %self.username

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    weather = db.Column(db.String(50))
    region = db.Column(db.String(50))
    user_name = db.Column(db.String(80), db.ForeignKey('user.username'))

    def __init__(self, date, weather, region):
        self.date = date
        self.weather = weather
        self.region = region
        return None
db.create_all()

#Homepage start

@app.route("/")
def red():
    return redirect('/home')


def api_call(city):
    if city=="Seoul":
        id=108
    if city=="Daejeon":
        id=133
    #url = "http://api.openweathermap.org/data/2.5/weather?q="+city+"&mode=json&appid=e12608ad352a39055355cacc3d6a2b8b"
    url="http://apis.skplanetx.com/weather/current/minutely?lon=&village=&county=&stnid="+str(id)+"&lat=&city=&version=1"
    
    request = urllib.request.Request(url)
    request.add_header('appKey','be02eb42-18ce-3488-830a-f8334ce8f2a2')
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        data = response.read()
        return data
    else:
        return "Error"


def api_call_dust(city):
    # url = "http://api.openweathermap.org/data/2.5/weather?q="+city+"&mode=json&appid=e12608ad352a39055355cacc3d6a2b8b"
    url = 'http://apis.skplanetx.com/weather/dust?version=1&lat='+city_to_geo[city][0]+'&lon='+city_to_geo[city][0]

    request = urllib.request.Request(url)
    request.add_header('appKey', 'be02eb42-18ce-3488-830a-f8334ce8f2a2')
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if (rescode == 200):
        data = response.read()
        return data
    else:
        return "Error"


def feels_like(temp, wind_speed):
    result = 13.12 + 0.6215*temp - 11.37*pow(wind_speed, 0.16) + 0.3965*temp*pow(wind_speed, 0.16)
    return round(result, 2)


@app.route("/home")
def home():
    if request.cookies.get('SESSIONID') is None:
        return redirect('/login')
    else:
        user = request.cookies.get('SESSIONID')
        try:
            Username = session_moum[user].decode("UTF-8")
            print(Username)
            data = api_call("Daejeon")
            dust_data = api_call_dust("대전")
            if data != "Error" and dust_data != "Error":
                j = json.loads(data.decode('utf-8'))
                dust_j = json.loads(dust_data.decode('utf-8'))
                print('returned json : ')
                print(dust_j)
                # json city name -> Seoul
                weather = j['weather']['minutely'][0]['sky']['name']
                weather = weather_check[weather]
                city_name = j['weather']['minutely'][0]['station']['name']
                temp = j['weather']['minutely'][0]['temperature']['tc']
                wind_speed = j['weather']['minutely'][0]['wind']['wspd']
                wind_direction = j['weather']['minutely'][0]['wind']['wdir']
                temp_feels_like = feels_like(float(temp), float(wind_speed))
                rain_fall = j['weather']['minutely'][0]['precipitation']['sinceOntime']
                humidity = j['weather']['minutely'][0]['humidity']
                pressure = j['weather']['minutely'][0]['pressure']['surface']
                dust = dust_j['weather']['dust'][0]['pm10']['grade']
                return render_template('home.html',username=Username,city=city_name,temp=temp,weather=weather, feels_like=str(temp_feels_like), rainfall=rain_fall, wind_speed=wind_speed, wind_orientation=wind_direction, humidity=humidity, pressure=pressure, dust=dust)
            else:
                return "Error while api calling"
        except:
            traceback.print_exc()
            return "Key Error"
    

#Add gisang-chung
@app.route("/add_kma")
def add_kma():
    global request
    cities = ["Seoul,%20KR","Daejeon,%20KR","Daegu,%20KR","Busan,%20KR"]
    user = User("KMA_Gisangchung","Amazing!")

    for city in cities:
        url = "http://api.openweathermap.org/data/2.5/forecast?q="+city+"&mode=json&appid=e12608ad352a39055355cacc3d6a2b8b"
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if(rescode==200):
            data = response.read()
        else:
            return "Error"

        j = json.loads(data.decode('utf-8'))
        #json city name -> Seoul
        city_name = (j['city']['name'])

        for i in range(len(j['list'])):
            #UNIX Timestamp with utc
            timestamp = (datetime.datetime.utcfromtimestamp(int(j['list'][i]['dt']))) #2017-01-20 15:00:00

            #list.weather.main Group of weather parameters (Rain, Snow, Extreme etc.)
            weather = (j['list'][i]['weather'][0]['main'])  # Clear
            user.predictions.append(Prediction(timestamp,weather,city_name))
    db.session.add(user)
    db.session.commit()
    return "Successfully added"


@app.route("/register", methods=['GET','POST'])
def register():
    global request
    if request.method =='GET':
        return render_template("register.html")
    else:
        #For form
        #global request
        query0 = request.form['username']
        query1 = request.form['password']
        #User Already exists?
        if User.query.filter_by(username=query0).first() is not None:
            return "User with same username already exists!"
        else:
            user = User(query0, query1)
            db.session.add(user)
            db.session.commit()
            return "User %s register completed"%query0

@app.route("/predict", methods=['GET','POST'])
def predict():
    if request.method == 'GET':
        return '''<form method=POST name=login action="./predict">
  Date : <input type=text name = date>
  Weather : <input type=text name = weather>
  Region : <input type=text name = region>
  <input type=submit value=Add>'''
    else:
    #Weather prediction
    #Input : Date, User, "weather : snow, rain, nothing"
        user = request.cookies.get('SESSIONID')
        try:
            Username = session_moum[user].decode("UTF-8")
        except:
            print("Key Error")
            print(session_moum)
            return "Key Error"

        date = request.form['date']
        weather = request.form['weather']
        #Username = request.form['Username']
        region = request.form['region']
        predict = Prediction(date,weather,region)

        #Username = asdf / Assume -> User already exists
        user = User.query.filter_by(username=Username).first()
        if user is not None:
            user.predictions.append(predict)
            db.session.add(user)
            db.session.commit()
            return "Date : %s, Weather : %s, region : %s, Username : %s add Succeed!"%(date,weather,region,Username)
        else:
            return "Username : %s doesn't exist!"%Username

@app.route("/predict_search")
def predict_search():
     return '''Predict_search. Input ex -> 2017-01-23
     <form method=POST name=login action="./predict_list">
  Date : <input type=text name = date>
  Region : <input type=text name = region>
  <input type=submit value=Search>'''

@app.route("/predict_list", methods=['POST','GET'])
def predict_list():
    date = request.form['date']
    region = request.form['region']
    rain='Rain: '
    snow='Snow: '
    nothing='Nothing: '
    clear='Clear: '
    final_str=''
    #First, Same date
    query = Prediction.query.filter_by(date=date,region=region).all()
    #Second, Same weather -> For time complexity(n^2 -> n)
    for i in range(len(query)):
        if query[i].weather=='rain':
            rain+=query[i].user_name+', '
        if query[i].weather=='snowy':
            snow+=query[i].user_name+', '
        if query[i].weather=='nothing':
            nothing+=query[i].user_name+', '
        if query[i].weather=='Clear':
            clear+=query[i].user_name+', '
    return rain+snow+nothing+clear+' On date %s, region %s'%(date,region)
@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        print(request.form['username'])
        query0 = request.form['username']
        query1 = request.form['password']
        if User.query.filter_by(username=query0,pw=query1).first() is None:
            return "Login Fail"
        else:
            #Now we give session-cookie -> Flask snipsets
            query0=query0.encode('utf-8')
            session_moum[hashlib.md5(query0).hexdigest()]=query0
            redirect_to_home = redirect('/home')
            response = make_response(redirect_to_home)
            response.set_cookie('SESSIONID',value=hashlib.md5(query0).hexdigest())
            return response


@app.route("/user_list")
def user_list():
    all_users = User.query.all()
    user_list_str=''
    for i in range(len(all_users)):
        user_list_str+=all_users[i].username+'\n'
    print(session_moum)
    return user_list_str

#Homepage finished

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5228)
