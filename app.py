from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Starters
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
app = Flask(__name__)

Starters = Starters()
#config MYSQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'newpassword'
app.config['MYSQL_DB'] = 'restaurant'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL

mysql= MySQL(app)

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
        name = StringField('Name', [validators.Length(min=1)])
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
                name = form.name.data
                email = form.email.data
                username = form.username.data
                password = sha256_crypt.encrypt(str(form.password.data))

                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",(name, email, username, password))

                mysql.connection.commit()

                cur.close()
                
                flash("You are now registered! You can now log in!", "success")
                return redirect(url_for('login'))
        return render_template('register.html', form = form)


if __name__ == '__main__':
    app.secret_key ='secret123'
    app.run(debug = True)
