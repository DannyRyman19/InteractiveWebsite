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

def is_manager(f):
        @wraps(f)
        def wrap(*args, **kwargs):
                if 'manager' in session:
                        return f(*args, **kwargs)
                else:
                        flash("You must be a manager to access this page", 'danger')
                        return redirect(url_for('floor'))
        return wrap

mysql= MySQL(app)
@app.route('/restaurant_floor')
def floor():
        return render_template('restaurant_floor.html')


     
@app.route('/')
def index():
        return render_template('home.html')

#Product creation form
 


class productForm(Form):
        name = TextAreaField('Name', [validators.Length(min=1, max=200)])
        description = TextAreaField('Description', [validators.Length(min=0,max=200)])
        price = DecimalField('price')
        category_id = SelectField('Category', choices = [('1','Drinks'),('2','Starters'),('3','Mains'),('4','Sides'),('5', 'Desserts'),('6','Others')])
        stock = IntegerField('Stock Count')
        subcategory_id = SelectField('Sub Category', choices=[('1','Soft'),('2','Hot'),('3','White Wine'),('4','Red Wine'),('5','Sparkling/Fizzy'),('6','Beer'),('7','Cocktail'),('8','Drink Other'), ('9','Pizza'), ('10','Pasta'),('11','Grill'), ('12','Salad'),('13','Risotto'),('14','Starter Other'),('15','Main Other'),('16','Side Other'), ('17','Dessert Other')])  


#Product addition  to databse      
@app.route('/add_product', methods = ["GET", "POST"])
@is_logged_in
@is_manager                             
def add_product():
      
        form = productForm(request.form)
     
        if request.args.get('type'):
                form.category_id.process_data(request.args.get('type'))
        if request.method == "POST" and form.validate():
                     
                name = form.name.data
                description = form.description.data
                price = form.price.data
                category_id = form.category_id.data
                subcategory_id= form.subcategory_id.data
                stock = form.stock.data
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO product (name, description, subcategory_id) VALUES (%s, %s, %s)",(name,description,subcategory_id))
                mysql.connection.commit()
       
                cur.execute("INSERT INTO product_variation (product_id, price, stock) VALUES (LAST_INSERT_ID(),%s, %s)",(price,stock))
                mysql.connection.commit()
               
                cur.close()

                flash('Product Created!', 'success')

                return redirect(url_for('stock_management'))
        return render_template('add_product.html', form = form)


        
#Edit Product
@app.route('/edit_product/<int:product_id>', methods = ["GET", "POST"])
@is_logged_in
@is_manager
def edit_product(product_id):

        cur = mysql.connection.cursor()
        form = productForm(request.form)
           
        cur.execute("SELECT * FROM product, product_variation, sub_category, category WHERE product.product_id = product_variation.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = category.category_id and product.product_id = %s;", [product_id])
        product = cur.fetchone()
        form.name.data= product['name']
        form.description.data= product['description']
        form.price.data= product['price']
        form.subcategory_id.process_data(product['subcategory_id'])
        form.category_id.process_data(product['category_id'])
        form.stock.data = product['stock']
     

        if request.method == "POST" and form.validate():
                name = request.form['name']
                description = request.form['description']
                price = request.form['price']
                category_id = request.form['category_id']
                subcategory_id = request.form['subcategory_id']
                stock = request.form['stock']
                cur = mysql.connection.cursor()
                cur.execute("UPDATE product SET name=%s, description=%s, subcategory_id=%s WHERE product.product_id = %s", (name, description, subcategory_id, product_id))
                
                mysql.connection.commit()

                cur.execute("UPDATE product_variation SET price=%s, stock=%s WHERE product_id = %s", (price,  stock, product_id))
                mysql.connection.commit()

                cur.close()

                flash('Product updated!', 'success')

                return redirect(url_for('stock_management'))
        return render_template('_edit_product.html', form = form)


#Product delete
@app.route('/delete_product/<int:id>', methods = ["POST"])
@is_logged_in
@is_manager
def delete_product(id):
        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM product  WHERE product_id = %s", [id])

        mysql.connection.commit()

        cur.execute("DELETE FROM product_variation WHERE product_id = %s", [id])
        mysql.connection.commit()
        cur.close()
        
        flash('Product Deleted!', 'success')

        return redirect(url_for('stock_management'))
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

class EditForm(Form):
        name = StringField('Name', [validators.Length(min=1)])
        username = StringField('Username', [validators.Length(min=4,max=25)])
        email = StringField('Email', [validators.Length(min =6, max = 50)])
        authority = SelectField('Authority', choices=[('1','General Manager'),('2','Assistant Manager'),('3','Supervisor'),('4','Waiter')])





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

#stock management
@app.route('/stock_management')
@is_logged_in
@is_manager
def stock_management():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 1 and category.category_id = 1;")

        drinks = cur.fetchall()

        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 2 and category.category_id = 2;")

        starters= cur.fetchall()
        
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 3 and category.category_id = 3;")

        mains= cur.fetchall()

        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 4 and category.category_id = 4;")

        sides= cur.fetchall()

        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 5 and category.category_id = 5;")

        desserts = cur.fetchall()

        cur.close()
        return render_template('stock_management.html',drinks=drinks, starters=starters, mains = mains, sides=sides,desserts=desserts)

#user management
@app.route('/user_management')
@is_logged_in
@is_manager
def user_management():
       
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name, email, username, authority FROM users ")  
        users = cur.fetchall()
        cur.close()
        return render_template('user_management.html',users = users)

#User delete
@app.route('/delete_user/<int:id>', methods = ["POST"])
@is_logged_in
@is_manager
def delete_user(id):
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", [id])
        mysql.connection.commit()
        cur.close()
        flash('User Deleted!', 'success')

        return redirect(url_for('user_management'))

#Add user
@app.route('/add_user', methods = ["GET", "POST"])
@is_logged_in
@is_manager
def add_user():
        form = RegisterForm(request.form)
      
        if request.method == 'POST' and form.validate():
                name = form.name.data
                email = form.email.data
                username = form.username.data
                authority = form.authority.data
                password = sha256_crypt.encrypt(str(form.password.data)) #encrypts password
                cur = mysql.connection.cursor()
                result = cur.execute("SELECT * FROM users WHERE email = %s", [email] )
                result2 = cur.execute("SELECT * FROM users WHERE username = %s", [username])
                if result > 0:
                        flash("Email already in use. Please try another one!","danger")
                        cur.close()
                elif result2 > 0:
                        flash("Username already in use. Please try another one!","danger")
                        cur.close()
                else:
                        cur = mysql.connection.cursor()
                        cur.execute("INSERT INTO users(name, email, username, authority, password) VALUES(%s, %s, %s,%s, %s)",(name, email, username, authority, password)) #adds all registration information into database

                        mysql.connection.commit()

                        cur.close()
                
                        flash("User Added!", "success")
                        return redirect(url_for('user_management'))
        return render_template('add_user.html', form = form)

#Edit User
@app.route('/edit_user/<int:id>', methods = ["GET", "POST"])
@is_logged_in
@is_manager
def edit_user(id):

        cur = mysql.connection.cursor()
        
        result = cur.execute("SELECT * FROM users WHERE id = %s", [id])

        user = cur.fetchone()

        form = EditForm(request.form)

        form.name.data= user['name']
        form.username.data= user['username']
        form.email.data= user['email']
        form.authority.process_data(user['authority'])
        

        if request.method == "POST":
                name = request.form['name']
                username = request.form['username']
                email = request.form['email']
                authority = request.form['authority']
             
                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET name=%s, username=%s, email=%s, authority=%s WHERE  id = %s", (name, username, email,  authority, id))
                mysql.connection.commit()

                cur.close()

                flash('User updated!', 'success')    

                return redirect(url_for('user_management'))
        return render_template('_edit_user.html', form = form, user = user)


@app.route('/dashboard')
@is_logged_in
@is_manager
def dashboard():
        return render_template('dashboard.html')



if __name__ == '__main__':
    app.secret_key ='secret123'
    app.run(debug = True)