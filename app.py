from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, DecimalField, BooleanField, SelectField, IntegerField, ValidationError
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#config MYSQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'newpassword'
app.config['MYSQL_DB'] = 'restaurant'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL

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


     
@app.route('/')
def index():
        return render_template('home.html')

#Product creation form
 



#drinks
@app.route('/drinks')
def drinks():
       
        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM category, sub_category WHERE category.category_id = sub_category.category_id AND category.category_id = 1")
        
       
        sub_categories = cur.fetchall()
        cur1 = mysql.connection.cursor()
        sub=[]
        for subcat in sub_categories:
                cur1.execute(("SELECT * FROM product, product_variation WHERE product.subcategory_id = {0} AND product.product_id = product_variation.product_id").format((str((subcat["subcategory_id"])))))
                sub.append([subcat["subcategory_name"],cur1.fetchall()])
                #print(subcat["subcategory_id"])

      

        cur.close()
     
        
        return render_template('drinks.html',  sub_categories = sub)


# starters
@app.route('/starters')
def starters():
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 2 and category.category_id = 2;")

        starters= cur.fetchall()
        cur.close()
       
        return render_template('starters.html', starters=starters)
       
   



# sides
@app.route('/sides')
def sides():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 4 and category.category_id = 4;")

        sides= cur.fetchall()
        cur.close()
       
        return render_template('sides.html', sides=sides)


# mains
@app.route('/mains')
def mains():
        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM category, sub_category WHERE category.category_id = sub_category.category_id AND category.category_id = 3")
        
       
        sub_categories = cur.fetchall()
        cur1 = mysql.connection.cursor()
        sub=[]
        for subcat in sub_categories:
                cur1.execute(("SELECT * FROM product, product_variation WHERE product.subcategory_id = {0} AND product.product_id = product_variation.product_id").format((str((subcat["subcategory_id"])))))
                sub.append([subcat["subcategory_name"],cur1.fetchall()])
                #print(subcat["subcategory_id"])

      

        cur.close()
     
        
        return render_template('mains.html',  sub_categories = sub)

# desserts
@app.route('/desserts')
def desserts():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 5 and category.category_id = 5;")

        desserts = cur.fetchall()
        cur.close()
       
        return render_template('desserts.html', desserts=desserts)



#sign up form validation
class RegisterForm(Form):
        name = StringField('Name', [validators.Length(min=1)])
        username = StringField('Username', [validators.Length(min=4,max=25)])
        email = StringField('Email', [validators.Length(min =6, max = 50)])
        authority = SelectField('Authority', choices=[('1','General Manager'),('2','Assistant Manager'),('3','Supervisor'),('4','Waiter')])
        password = PasswordField('Password', [
                validators.DataRequired(),
                validators.EqualTo('confirm', message = "Passwords do not match")

        ])
        confirm = PasswordField('Confirm Password')
      

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
                        cur.execute("SELECT authority FROM users WHERE username = %s", [username]) 
                        auth = cur.fetchone() 
                        cur.execute("SELECT id FROM users WHERE username = %s", [username]) 
                        userID = cur.fetchone() 
                        cur.execute("SELECT name FROM users WHERE username = %s", [username]) 
                        name = cur.fetchone() 
                        name = str(name)
                        name = name[10:-2]                              
                        password = data['password']
                        auth = str(auth)
                        userID = str(userID)
                        userID = userID[6:-1]
                        userID = int(userID)
                        if auth == "{'authority': 1}":
                                auth = "General Manager"
                                session['manager'] = True
                        elif auth == "{'authority': 2}":
                                auth = "Assistant Manager"
                                session['manager'] = True
                        elif auth == "{'authority': 3":
                                auth = "Supervisor"
                        else:
                                auth = "Waiter"
                        if sha256_crypt.verify(password_candidate, password): #checks if passwords match
                                session['auth'] = auth
                                session['logged_in'] = True
                                session['username'] = username
                                session['password'] = password
                                session['name'] = name
                                session['id'] = userID
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




#Logout
@app.route('/logout')
@is_logged_in
def logout():
        session.clear() 
        flash("You have been logged out!", 'success')
        return redirect(url_for('login'))



@app.route('/dashboard')
@is_logged_in
@is_manager
def dashboard():
        return render_template('dashboard.html')



if __name__ == '__main__':
    app.secret_key ='secret123'
    app.run(debug = True)