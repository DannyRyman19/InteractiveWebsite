from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
        return render_template('home.html')

@app.route('/starters')
def starters():
        return render_template('starters.html')


if __name__ == '__main__':
    app.run(debug = True)
