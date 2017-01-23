from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/hourly')
def hourly():
    return render_template('hourly.html')


@app.route('/predict/')
def predict():
    return render_template('predict.html')


if __name__ == '__main__':
    app.run()
