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
from decimal import Decimal
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test12.db'
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

def api_call(num, city):
    if city=="Seoul":
        id=108
        lat=37.57
        lon=127
    if city=="Daejeon":
        id=133
        lat=36.32
        lon=127.42
    if city=="Busan":
        id=968
        lat=35
        lon=129
    if city=="Daegu":
        id=860
        lat=35.87
        lon=128.6
    #url = "http://api.openweathermap.org/data/2.5/weather?q="+city+"&mode=json&appid=e12608ad352a39055355cacc3d6a2b8b"
    if num==1:
        url="http://apis.skplanetx.com/weather/current/minutely?lon=&village=&county=&stnid="+str(id)+"&lat=&city=&version=1"
    if num==2:
        url="http://apis.skplanetx.com/weather/forecast/3days?version=1&lat="+str(lat)+"&lon="+str(lon)+"&city=&county=&village="
    if num==3:
        url="http://apis.skplanetx.com/weather/dust?version=1&lat="+str(lat)+"&lon="+str(lon)
    if num==4:
        url="http://api.openweathermap.org/data/2.5/weather?q="+city+"&mode=json&appid=e12608ad352a39055355cacc3d6a2b8b"
    request = urllib.request.Request(url)
    request.add_header('appKey','be02eb42-18ce-3488-830a-f8334ce8f2a2')
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        data = response.read()
        return data
    else:
        return "Error"

@app.route("/logout")
def logout():
    redirect_to_home = redirect('/login')
    response = make_response(redirect_to_home)
    response.set_cookie('SESSIONID','')
    return response


@app.route("/home", defaults={'region': 'Seoul'})
@app.route("/home/<region>")
def home(region):
    if request.cookies.get('SESSIONID') is None:
        return redirect('/login')
    else:
        user = request.cookies.get('SESSIONID')
        try:
            Username = session_moum[user].decode("UTF-8")
            if region==None:
                region="Seoul"
            data = api_call(1,region)
            data_rain = api_call(2,region)
            data_dust = api_call(3,region)
            data_now = api_call(4,region)
            if data != "Error":
                j = json.loads(data.decode('utf-8'))
                j_rain = json.loads(data_rain.decode('utf-8'))
                j_dust = json.loads(data_dust.decode('utf-8'))
                j_now = json.loads(data_now.decode('utf-8'))
                #json city name -> Seoul
                weather = j['weather']['minutely'][0]['sky']['name']
                weather = weather_check[weather]
                #city_name = j['weather']['minutely'][0]['station']['name']
                city_name = region
                temp = j['weather']['minutely'][0]['temperature']['tc']
                rain_list=[]
                precip=float(Decimal(j['weather']['minutely'][0]['precipitation']['sinceOntime']))
                print(precip)
                precip_type=j['weather']['minutely'][0]['precipitation']['sinceOntime']
                if precip_type == '3':
                    precip = precip * 10
                wind_speed=j_now['wind']['speed']
                wind_deg=j_now['wind']['deg']
                humidity=j_now['main']['humidity']
                pressure=j_now['main']['pressure']
                temp_float=float(Decimal(temp))
                speed_float=float(wind_speed)*3.6
                feel=13.12+0.6215*temp_float-11.37*pow(speed_float,0.15)+0.3965*pow(speed_float,0.15)*temp_float
                feel=round(feel)
                for i in [4,7,10,13,16,19,22,25,28]:
                    rain_list.append(int(Decimal(j_rain['weather']['forecast3days'][0]['fcst3hour']['precipitation']['prob'+str(i)+'hour'])))
                dust = j_dust['weather']['dust'][0]['pm10']['grade']
                return render_template('home.html',region=region,feel=feel,precipitation=precip,wind_deg=wind_deg,wind_speed=wind_speed,humidity=humidity,pressure=pressure,username=Username,city=city_name,temp=temp,weather=weather,rain_op=rain_list,dust=dust)
            else:
                return "Error while api calling"
        except:
            print(sys.exc_info()[0])
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
