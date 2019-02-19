from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Starters
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

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

# starters
@app.route('/starters')
def starters():
        return render_template('starters.html', starters = Starters)

#individual food pages
@app.route('/starter/<string:id>/')
def starter(id):
        return render_template('starter.html', id = id)

#sign up form validation
class RegisterForm(Form):
        name = StringField('Name', [validators.Length(min=1)])
        username = StringField('Username', [validators.Length(min=4,max=25)])
        email = StringField('Email', [validators.Length(min =6, max = 50)])
        password = PasswordField('Password', [
                validators.DataRequired(),
                validators.EqualTo('confirm', message = "Passwords do not match")

        ])
        confirm = PasswordField('Confirm Password')

#Register
@app.route('/register',methods=['GET','POST'])
def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
                name = form.name.data
                email = form.email.data
                username = form.username.data
                password = sha256_crypt.encrypt(str(form.password.data)) #encrypts password

                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",(name, email, username, password)) #adds all registration information into database

                mysql.connection.commit()

                cur.close()
                
                flash("You are now registered! You can now log in!", "success")
                return redirect(url_for('login'))
        return render_template('register.html', form = form)

#login
@app.route('/login', methods = ['GET','POST'])
def login():
        if request.method == 'POST':
                username = request.form['username']
                password_candidate = request.form['password']

                cur = mysql.connection.cursor()
                result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

                if result > 0: #checks if username exists
                        data = cur.fetchone()
                        password = data['password']
                        if sha256_crypt.verify(password_candidate, password): #checks if passwords match
                                session['logged_in'] = True
                                session['username'] = username

                                flash('You are now logged in', 'success')
                                return redirect(url_for('dashboard')) #logs user in to dashboard
                        else: #passswords don't match
                                error = "Login Failed"
                                return render_template('login.html', error = error)
                        cur.close() #closes connection to database
                else: #user doesn't exist
                        error = "Username not found"
                        return render_template('login.html', error = error)
        
        return render_template('login.html')

#login check - prevents non logged in users from accesing dashboard page
def is_logged_in(f):
        @wraps(f)
        def wrap(*args, **kwargs):
                if 'logged_in' in session:
                        return f(*args, **kwargs)
                else:
                        flash("You must be logged in to access this page", 'danger')
                        return redirect(url_for('login'))
        return wrap
#Logout
@app.route('/logout')
def logout():
        session.clear() 
        flash("You have been logged out!", 'success')
        return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
        return render_template('dashboard.html')

if __name__ == '__main__':
    app.secret_key ='secret123'
    app.run(debug = True)
    
