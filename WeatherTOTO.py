#From http://flask.pocoo.org/docs/0.12/quickstart/#quickstart
import os
import hashlib
import sys
import requests
import urllib.request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import pytz
import json
import urllib.request
from flask import redirect,Flask, request, render_template, send_from_directory,make_response
from decimal import Decimal
import traceback
from bs4 import BeautifulSoup
import atexit
from apscheduler.scheduler import Scheduler
import pytz
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_secret_key import secret


app = Flask(__name__)
cron = Scheduler(daemon=True)
cron.start()
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test14.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ashe.db'
csrf = CSRFProtect(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test12.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ashe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = secret
db = SQLAlchemy(app)

session_moum={}

weather_check={}
weather_check['맑음']="wi-day-sunny"
weather_check['구름조금']="wi-day-cloudy-high"
weather_check['구름많음']="wi-day-cloudy"
weather_check['차차 흐려짐']="wi-day-cloudy"
weather_check['구름많고 비']="wi-day-rain"
weather_check['비 후 갬']="wi-day-rain"
weather_check['구름많고 눈']="wi-day-snow"
weather_check['눈 후 갬']="wi-day-snow"
weather_check['구름많고 비 또는 눈']="wi-day-rain-mix"
weather_check['구름많고 비/눈']="wi-day-rain-mix"
weather_check['눈비 후 갬']="wi-day-rain-mix"
weather_check['흐림']="wi-cloudy"
weather_check['흐리고 비']="wi-rain"
weather_check['흐려져 비']="wi-rain"
weather_check['흐리고 눈']="wi-snow"
weather_check['흐려져 눈']="wi-rain"
weather_check['흐리고 비 또는 눈']="wi-rain-mix"
weather_check['흐리고 비/눈']="wi-rain-mix"
weather_check['흐려져 눈비']="wi-rain-mix"
weather_check['눈비']="wi-rain-mix"
weather_check['흐리고 낙뢰']="wi-lightning"
weather_check['뇌우, 비']="wi-thunderstorm"
weather_check['뇌우, 눈']="wi-storm-showers"
weather_check['뇌우, 비 또는 눈']="wi-night-sleet-storm"
weather_check['뇌우, 비/눈']="wi-night-sleet-storm"

city_to_geo = {}
city_to_geo['서울'] = ('37.566535', '126.97796919999996')
city_to_geo['Seoul'] = ('37.566535', '126.97796919999996')
city_to_geo['대전'] = ('36.3504119', '127.38454750000005')
city_to_geo['Daejeon'] = ('36.3504119', '127.38454750000005')
city_to_geo['대구'] = ('35.8714354', '128.601445')
city_to_geo['Daegu'] = ('35.8714354', '128.601445')
city_to_geo['부산'] = ('35.1795543', '129.07564160000004')
city_to_geo['Busan'] = ('35.1795543', '129.07564160000004')

dow_kor_eng = {}
dow_kor_eng['월'] = 'Monday'
dow_kor_eng['화'] = 'Tuesday'
dow_kor_eng['수'] = 'Wednesday'
dow_kor_eng['목'] = 'Thursday'
dow_kor_eng['금'] = 'Friday'
dow_kor_eng['토'] = 'Saturday'
dow_kor_eng['일'] = 'Sunday'

dow_list_glob = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

#Define User & Prediction for SQLite
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    pw = db.Column(db.String(80), unique=False)
    total_money = db.Column(db.Integer)
    predictions = db.relationship('Prediction', backref='User',
                                lazy='dynamic')
    #money = db.Column(db.Integer, unique=False)
    #total = db.Column(db.Integer, unique=False)
    #win = db.Column(db.Integer, unique=False)

    def __init__(self, username, pw, total_money):
        self.username = username
        self.pw = pw
        self.total_money = total_money
        return None
    def __repr__(self):
        return '<User %r>' %self.username

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    weather = db.Column(db.String(50))
    region = db.Column(db.String(50))
    bet_money = db.Column(db.Integer)
    user_name = db.Column(db.String(80), db.ForeignKey('user.username'))

    def __init__(self, date, weather, region, bet_money):
        self.date = date
        self.weather = weather
        self.region = region
        self.bet_money = bet_money
        return None
db.create_all()


def datetime_to_str(dt):
    result = {}
    string=""
    result['year'] = str(dt.year)[2:]
    result['month'] = str(dt.month)
    result['day'] = str(dt.day)
    result['hour'] = str(dt.hour)
    result['minute'] = str(dt.minute)
    result['second'] = str(dt.second)
    if len(result['month']) == 1:
        result['month'] = '0' + result['month']
    if len(result['day']) == 1:
        result['day'] = '0' + result['day']
    if len(result['hour']) == 1:
        result['hour'] = '0' + result['hour']
    if len(result['minute']) == 1:
        result['minute'] = '0' + result['minute']
    string = result['year'] + '.' + result['month'] + '.' + result['day'] + '.' + result['hour'] + ':' + result['minute']
    return string


@cron.interval_schedule(hours=6)
def job_function():
    #print(datetime.datetime.utcnow())
    time_str=datetime.datetime.now(pytz.timezone('Asia/Seoul'))
    time_str=datetime_to_str(time_str)
    print(time_str)
    #3시간마다 토토를 돌린다.
    #Example Time : 17.02.22.18:00
    #Server Time - Example Time < 0: 즉 시간이 지나면.
    #모든 prediction 중에서 시간이 Example Time 인 prediction 다 긁어옴
    #결과가 : Rain일 때,
    #js는 1000, js3는 2000원 걸어서 이김
    #user js의 total money를 1000원 증가
    #user js3의 total money를 2000원 증가
    #if Time :
    weather = ""
    cities = ["Seoul","Daejeon","Busan","Daegu"]
    money_all = 0
    money_win = 0
    bedang = 0  # 배당률 money_all / money_win
    for city in cities:
        weather = ""
        money_all = 0
        money_win = 0
        bedang = 0  # 배당률 money_all / money_win

        data = api_call(1,city)
        j = json.loads(data.decode('utf-8'))
        precip_type=j['weather']['minutely'][0]['precipitation']['sinceOntime'] #Weather
        print(precip_type)
        if precip_type=='0.00':
            weather_win = "dry"
        else:
            weather_win = "rain"
        predicts = Prediction.query.filter_by(date=time_str,region=city)
        for predict in predicts:
            money_all+=predict.bet_money #걸린 돈 모조리 가져옴 Total_money = 1000+2000+2000+2000
            if predict.weather == weather_win:
                money_win+=predict.bet_money #이긴 돈 money_win = 1000+2000
        try:
            bedang = money_all / money_win
        except:
            bedang = 1
        for predict in predicts:
            if predict.weather == weather_win:
                User.query.filter_by(username=predict.user_name).first().total_money+=predict.bet_money * bedang    #할당된 돈만큼 user에게 더해줌
                db.session.commit()

            #print(predict.bet_money)
    print("Finish Cron")

#cron.add_cron_job(job_function, minute='0-59')
atexit.register(lambda: cron.shutdown(wait=False))


def get_week_forecast():
    url = "https://www.weatheri.co.kr/forecast/forecast04.php"

    request_weather_i = urllib.request.Request(url)
    response = urllib.request.urlopen(request_weather_i)
    rescode = response.getcode()
    if rescode == 200:
        html = response.read()
        return html.decode('utf-8')
    else:
        return "Error"


def parse_week_forecast(city, html):
    soup = BeautifulSoup(html, 'html.parser')
    result_json_list = []
    dow_list = soup.find_all("td", {'align': 'center', 'bgcolor': '#f6f6f6', 'width': '88'})
    dow_list = [child.string for child in dow_list]
    dow_list = [dow_kor_eng[elem.split()[1][1:-1]] for elem in dow_list]
    weather_temp_list = soup.find_all("tr", {'bgcolor': '#FFFFFF'})

    if city == 'Seoul':
        while '\n' in weather_temp_list[0].contents:
            weather_temp_list[0].contents.remove("\n")
        while '\n' in weather_temp_list[1].contents:
            weather_temp_list[1].contents.remove("\n")
        weather_list = [content.img['alt'] for content in weather_temp_list[0].contents[1:]]
        temp_list = [content.string for content in weather_temp_list[1].contents[1:]]
        temp_list = [(elem.split(' / ')[0], elem.split(' / ')[1]) for elem in temp_list]
    elif city == 'Daejeon':
        while '\n' in weather_temp_list[12].contents:
            weather_temp_list[12].contents.remove("\n")
        while '\n' in weather_temp_list[13].contents:
            weather_temp_list[13].contents.remove("\n")
        weather_list = [content.img['alt'] for content in weather_temp_list[12].contents[1:]]
        temp_list = [content.string for content in weather_temp_list[13].contents[1:]]
        temp_list = [(elem.split(' / ')[0], elem.split(' / ')[1]) for elem in temp_list]
    elif city == 'Daegu':
        while '\n' in weather_temp_list[23].contents:
            weather_temp_list[23].contents.remove("\n")
        while '\n' in weather_temp_list[24].contents:
            weather_temp_list[24].contents.remove("\n")
        weather_list = [content.img['alt'] for content in weather_temp_list[23].contents[1:]]
        temp_list = [content.string for content in weather_temp_list[24].contents[1:]]
        temp_list = [(elem.split(' / ')[0], elem.split(' / ')[1]) for elem in temp_list]
    elif city == 'Busan':
        while '\n' in weather_temp_list[27].contents:
            weather_temp_list[27].contents.remove("\n")
        while '\n' in weather_temp_list[28].contents:
            weather_temp_list[28].contents.remove("\n")
        weather_list = [content.img['alt'] for content in weather_temp_list[27].contents[1:]]
        temp_list = [content.string for content in weather_temp_list[28].contents[1:]]
        temp_list = [(elem.split(' / ')[0], elem.split(' / ')[1]) for elem in temp_list]
    for i in range(len(weather_list)):
        result_json_list.append({'dow': dow_list[i][:3], 'weather': weather_check[weather_list[i]], 'max_temp': temp_list[i][1], 'min_temp': temp_list[i][0]})

    # 내일 날씨 추가####################################################
    request_tomorrow = urllib.request.Request('http://apis.skplanetx.com/weather/forecast/3days?version=1&lat='+city_to_geo[city][0]+'&lon='+city_to_geo[city][0])
    request_tomorrow.add_header('appKey', '3592fc77-8776-3276-a914-06b06cddcd3f')
    tomorrow_json = json.loads(urllib.request.urlopen(request_tomorrow).read().decode('utf-8'))
    result_json_list.insert(0, {'dow': dow_list_glob[dow_list_glob.index(dow_list[0])-1][:3], 'weather': weather_check[tomorrow_json['weather']['forecast3days'][0]['fcst3hour']['sky']['name22hour']], 'max_temp': tomorrow_json['weather']['forecast3days'][0]['fcstdaily']['temperature']['tmax2day'][:-3], 'min_temp': tomorrow_json['weather']['forecast3days'][0]['fcstdaily']['temperature']['tmin2day'][:-3]})
    return result_json_list

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
    request.add_header('appKey','3592fc77-8776-3276-a914-06b06cddcd3f')
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if rescode==200:
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
            user_obj = User.query.filter_by(username=Username).first()
            week_forcast_list = parse_week_forecast(region, get_week_forecast())
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
                return render_template('home.html', region=region, feel=feel, precipitation=precip,wind_deg=wind_deg,wind_speed=wind_speed,humidity=humidity,pressure=pressure,username=Username,city=city_name,temp=temp,weather=weather,rain_op=rain_list,dust=dust, week_forcast_list=week_forcast_list[:6], user_money=user_obj.total_money)
            else:
                return "Error while api calling"
        except:
            traceback.print_exc()
            return "Key Error"


@app.route('/my')
def my():
    user = request.cookies.get('SESSIONID')
    Username = session_moum[user].decode("UTF-8")
    user_obj = User.query.filter_by(username=Username).first()
    prediction_list = Prediction.query.filter_by(user_name=Username).order_by(Prediction.date)
    print('prediction list')
    print([p.user_name for p in prediction_list])
    return render_template('my.html', prediction_list=prediction_list, user_money = user_obj.total_money)
    

@app.route("/hourly", defaults={'region': 'Seoul'})
@app.route("/hourly/<region>")
def hourly(region):
    if request.cookies.get('SESSIONID') is None:
        return redirect('/login')
    else:
        user = request.cookies.get('SESSIONID')
        try:
            Username = session_moum[user].decode("UTF-8")
            user_obj = User.query.filter_by(username=Username).first()
        except:
            traceback.print_exc()
            return "Key Error. Call Admin"
    t_list=[]
    h_list=[]
    s_list=[]
    r_list=[]
    data_forecast = api_call(2,region)
    if data_forecast != "Error":
        j = json.loads(data_forecast.decode('utf-8'))
        for i in [4,7,10,13,16,19,22,25,28]:
            s_list.append(float(j['weather']['forecast3days'][0]['fcst3hour']['wind']['wspd'+str(i)+'hour']))
            t_list.append(float(j['weather']['forecast3days'][0]['fcst3hour']['temperature']['temp'+str(i)+'hour']))
            h_list.append(float(j['weather']['forecast3days'][0]['fcst3hour']['humidity']['rh'+str(i)+'hour']))
            r_list.append(float(j['weather']['forecast3days'][0]['fcst3hour']['precipitation']['prob'+str(i)+'hour']))

    return render_template("hourly.html",region=region,username=Username,speed_list=s_list,temp_list=t_list,humidity_list=h_list,rain_list=r_list, user_money = user_obj.total_money)



#Add gisang-chung


@app.route("/toto", defaults={'region': 'Seoul'})
@app.route("/toto/<region>")
def toto(region):
    user = request.cookies.get('SESSIONID')
    Username = session_moum[user].decode("UTF-8")
    user_obj = User.query.filter_by(username=Username).first()
    current_time = datetime.datetime.now(pytz.timezone('Asia/Seoul'))
    start_time = round_time(current_time, round_to=3*60*60) + datetime.timedelta(hours=6)

    target_time_list = []
    due_time_list = []
    bet_on_rain_list = []
    bet_on_dry_list = []
    for i in range(8):
        dt = start_time + datetime.timedelta(hours=3*i)
        dt_json = datetime_to_json(dt)
        target_time_list.append(dt_json)
        due_time_list.append(datetime_to_json(dt - datetime.timedelta(hours=3)))
        print('rain money')
        print([p.bet_money for p in Prediction.query.filter_by(date=dt_json['complete'], weather='rain').all()])
        bet_on_rain = [int(p.bet_money) for p in Prediction.query.filter_by(date=dt_json['complete'], weather='rain').all()]
        bet_on_rain_list.append(sum(bet_on_rain))
        bet_on_dry = [int(p.bet_money) for p in Prediction.query.filter_by(date=dt_json['complete'], weather='dry').all()]
        bet_on_dry_list.append(sum(bet_on_dry))

    already = [prediction.date for prediction in Prediction.query.filter_by(user_name=Username).all()]


    return render_template('predict.html', region=region, target_time_list=target_time_list, due_time_list=due_time_list, username=Username, already=already, bet_on_rain_list=bet_on_rain_list, bet_on_dry_list=bet_on_dry_list, user_money = user_obj.total_money)


@app.route("/toto_fast", defaults={'region': 'Seoul'})
@app.route("/toto_fast/<region>")
def toto_fast(region):
    user = request.cookies.get('SESSIONID')
    Username = session_moum[user].decode("UTF-8")
    user_obj = User.query.filter_by(username=Username).first()
    current_time = datetime.datetime.now(pytz.timezone('Asia/Seoul'))
    start_time = round_time(current_time, round_to=60) + datetime.timedelta(minutes=2)

    target_time_list = []
    due_time_list = []
    bet_on_rain_list = []
    bet_on_dry_list = []
    for i in range(8):
        dt = start_time + datetime.timedelta(minutes=i)
        dt_json = datetime_to_json(dt)
        target_time_list.append(dt_json)
        due_time_list.append(datetime_to_json(dt - datetime.timedelta(minutes=1)))
        print('rain money')
        print([p.bet_money for p in Prediction.query.filter_by(date=dt_json['complete'], weather='rain').all()])
        bet_on_rain = [int(p.bet_money) for p in
                       Prediction.query.filter_by(date=dt_json['complete'], weather='rain').all()]
        bet_on_rain_list.append(sum(bet_on_rain))
        bet_on_dry = [int(p.bet_money) for p in
                      Prediction.query.filter_by(date=dt_json['complete'], weather='dry').all()]
        bet_on_dry_list.append(sum(bet_on_dry))

    already = [prediction.date for prediction in Prediction.query.filter_by(user_name=Username).all()]

    return render_template('predict.html', region=region, target_time_list=target_time_list, due_time_list=due_time_list, username=Username, already=already, bet_on_rain_list=bet_on_rain_list, bet_on_dry_list=bet_on_dry_list, user_money=user_obj.total_money)


def round_time(dt=None, round_to=60):
    """Round a datetime object to any time laps in seconds
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    """
    if dt is None:
        dt = datetime.datetime.now(pytz.timezone('Asia/Seoul'))
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds+round_to/2) // round_to * round_to
    return dt + datetime.timedelta(0, rounding-seconds, -dt.microsecond)


def datetime_to_json(dt):
    result = {}
    result['year'] = str(dt.year)[2:]
    result['month'] = str(dt.month)
    result['day'] = str(dt.day)
    result['hour'] = str(dt.hour)
    result['minute'] = str(dt.minute)
    result['second'] = str(dt.second)
    if len(result['month']) == 1:
        result['month'] = '0' + result['month']
    if len(result['day']) == 1:
        result['day'] = '0' + result['day']
    if len(result['hour']) == 1:
        result['hour'] = '0' + result['hour']
    if len(result['minute']) == 1:
        result['minute'] = '0' + result['minute']
    result['complete'] = result['year'] + '.' + result['month'] + '.' + result['day'] + '.' + result['hour'] + ':' + result['minute']
    return result


@app.route("/ajax/toto/add", methods=["GET", "POST"])
def add_toto():
    if request.method == 'POST':
        Username = request.json['user_name']
        date_json = request.json['date']
        date = date_json['year']+'.'
        date += date_json['month']+'.'
        date += date_json['day']+'.'
        date += date_json['hour']+':'+date_json['minute']
        user = User.query.filter_by(username=Username).first()
        if user is not None:
            predict = Prediction(date=date, weather=request.json['weather'], region=request.json['region'], bet_money=request.json['money'])
            user.total_money -= int(request.json['money'])
            user.predictions.append(predict)
            db.session.add(user)
            db.session.commit()
            return "Date : %s, Weather : %s, region : %s, Username : %s add Succeed!"%(date, request.json['weather'], request.json['region'], Username)
        else:
            return "Username : %s doesn't exist!" % Username


# Add gisang-chung
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
            user = User(query0, query1, 1000000000)
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
  Money : <input type=text name = money>
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
        money = request.form['money']
        predict = Prediction(date,weather,region,int(Decimal(money)))
        #Username = asdf / Assume -> User already exists
        user = User.query.filter_by(username=Username).first()
        user.total_money-=int(Decimal(money))
        if user is not None:
            user.predictions.append(predict)
            db.session.add(user)
            db.session.commit()
            return "Date : %s, Weather : %s, region : %s, money : %s Username : %s add Succeed!"%(date,weather,region,money,Username)
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
    dry='Dry: '
    final_str=''
    #First, Same date
    query = Prediction.query.filter_by(date=date,region=region).all()
    #Second, Same weather -> For time complexity(n^2 -> n)
    for i in range(len(query)):
        if query[i].weather=='rain':
            rain+=query[i].user_name+', '+str(query[i].bet_money)+'\n'
        if query[i].weather=='dry':
            dry+=query[i].user_name+', '+str(query[i].bet_money)+'\n'
    return rain+'\n'+dry+'\n On date %s, region %s'%(date,region)


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
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
        user_list_str+=all_users[i].username+', '+str(all_users[i].total_money)+'\n'
    print(session_moum)
    return user_list_str

#Homepage finished

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5228)
