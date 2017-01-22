#From http://flask.pocoo.org/docs/0.12/quickstart/#quickstart
import os
import sys
import requests
import urllib.request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
import urllib.request
from flask import Flask, request, render_template, send_from_directory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test11.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

#Define User & Prediction for SQLite
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    pw = db.Column(db.String(80), unique=False)
    predictions = db.relationship('Prediction', backref='User',
                                lazy='dynamic')
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

#Add gisang-chung
@app.route("/add_kma")
def add_kma():
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
    


@app.route("/")
def template_test():
    return '''Register : <form method=POST name=login action="./connect"> 
  id : <input type=text name=id>
  passwd : <input type=passwd name = pw>
  <input type=submit value=register>'''

@app.route("/predict")
def predict():
    return '''<form method=POST name=login action="./predict_conn"> 
  User : <input type=text name = Username>
  Date : <input type=text name = date>
  Weather : <input type=text name = weather>
  Region : <input type=text name = region>
  <input type=submit value=Add>'''

@app.route("/predict_conn", methods=['POST'])
def predict_conn():
     #Weather prediction
    #Input : Date, User, "weather : snow, rain, nothing"
    
    """date = '2017-01-24'
    weather = 'snow'"""
    date = request.form['date']
    weather = request.form['weather']
    Username = request.form['Username']
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
@app.route("/login")
def login():
    return "Hello World!"


@app.route("/connect", methods=['POST'])
def connect():
    #For form
    global request
    query0 = request.form['id']
    query1 = request.form['pw']
    print(query0) 
    #User Already exists?
    if User.query.filter_by(username=query0).first() is not None:
        return "User with same username already exists!"
    else:
        user = User(query0, query1)
        db.session.add(user)
        db.session.commit()
        return "User %s register completed"%query0

@app.route("/user_list")
def user_list():
    all_users = User.query.all()
    user_list_str=''
    for i in range(len(all_users)):
        user_list_str+=all_users[i].username+'\n'
    return user_list_str

#Homepage finished

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5228)
