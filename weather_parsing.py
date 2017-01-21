##OpenWeatherMap data parsing
import datetime
import json
import urllib.request

cities = ["Seoul,%20KR","Daejeon,%20KR","Daegu,%20KR","Busan,%20KR"]

for city in cities:
    url = "http://api.openweathermap.org/data/2.5/forecast?q="+city+"&mode=json&appid=e12608ad352a39055355cacc3d6a2b8b"

    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()
    if(rescode==200):
        data = response.read()
        #print(data)
    else:
        print("Error")

    j = json.loads(data.decode('utf-8'))

    #json city name -> Seoul
    print(j['city']['name'])

    for i in range(len(j['list'])):
        #UNIX Timestamp with utc
        timestamp = (datetime.datetime.utcfromtimestamp(int(j['list'][i]['dt']))) #2017-01-20 15:00:00

        #list.weather.main Group of weather parameters (Rain, Snow, Extreme etc.)
        weather_main = (j['list'][i]['weather'][0]['main'])  # Clear

        print("%s %s"%(timestamp,weather_main))


