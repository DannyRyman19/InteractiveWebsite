from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Starters
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
app = Flask(__name__)

Starters = Starters()

@app.route('/')
def index():
        return render_template('home.html')

@app.route('/starters')
def starters():
        return render_template('starters.html', starters = Starters)

@app.route('/starter/<string:id>/')
def starter(id):
        return render_template('starter.html', id = id)

class RegisterForm(Form):
        name = StringField('Name', [validators.Length(min=1, max = 50)])
        username = StringField('Username', [validators.Length(min=4,max=25)])
        email = StringField('Email', [validators.Length(min =6, max = 50)])
        password = PasswordField('Password', [
                validators.DataRequired(),
                validators.EqualTo('confirm', message = "Passwords do not match")

        ])
        confirm = PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
                return render_template('register.html')
        return render_template('register.html', form = form)


if __name__ == '__main__':
    app.run(debug = True)
