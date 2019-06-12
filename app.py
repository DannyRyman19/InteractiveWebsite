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
                        flash("You must be logged in to access this ßpage", 'danger')
                        return redirect(url_for('login'))
        return wrap
#manager check - checks if the logged in user is a manager, managers can access stock management and user management.
def is_manager(f):
        @wraps(f)
        def wrap(*args, **kwargs):
                if 'manager' in session:
                        return f(*args, **kwargs)
                else:
                        flash("You must be a manager to access this page", 'danger')
                        return redirect(url_for('floor'))
        return wrap
#chef check - checks if the logged in user is a chef, chefs cn access stock management and floor
def is_chef(f):
        @wraps(f)
        def wrap(*args, **kwargs):
                if 'chef' in session:
                        return f(*args, **kwargs)
                elif 'manager' in session:
                        return f(*args, **kwargs)
                else:
                        flash("You must be a manager/chef to access this page", 'danger')
                        return redirect(url_for('floor'))
        return wrap

mysql= MySQL(app)
@app.route('/restaurant_floor')
def floor():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tables")
        tables = cur.fetchall()
        print (tables)
        return render_template('restaurant_floor.html', tables = tables)

#kitchen page - will show orders for the kitchen to see
@app.route('/kitchen')
def kitchen():
        cur = mysql.connection.cursor()
        cur.execute("SELECT order_id, table_id FROM tables WHERE active = 1")
        activeTables = cur.fetchall()
        print(activeTables)
        tables = []
        for table in activeTables:
                cur.execute(("SELECT sum(product_variation.price) AS price, product.name, tables.table_id, order_item.message, product.product_id, SUM(order_item.quantity) AS quantity, sum(order_item.subtotal) AS subtotal FROM order_item INNER JOIN tables ON tables.table_id = order_item.table_id INNER JOIN product ON product.product_id = order_item.product_id INNER JOIN sub_category ON sub_category.subcategory_id = product.subcategory_id INNER JOIN product_variation ON product_variation.product_id = product.product_id INNER JOIN category ON category.category_id = sub_category.category_id WHERE tables.order_id = order_item.order_id and tables.order_id = '{0}' AND tables.table_id = {1} GROUP BY product.name, order_item.message, product.product_id;").format(table['order_id'], table['table_id']))
                tables.append(cur.fetchall())
        print(tables)
        return render_template('kitchen.html', tables = tables)
#SELECT * FROM restaurant.order_item WHERE  LIKE '%2019-05-03%' and table_id = 1;

#Bill History
@app.route('/bill_history')
@is_logged_in
@is_manager
def bill_history():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM bill_history ORDER BY date_closed DESC")
        History = cur.fetchall()
        cur.close()
        return render_template('bill_history.html', History = History)

#Individual bill history
@app.route('/bill_history/<string:order_id>')
@is_logged_in
def individual_bill_history(order_id):
        cur = mysql.connection.cursor()

        cur.execute(("SELECT table_id FROM order_item WHERE order_item.order_id = '{0}';").format(order_id))
        id = cur.fetchone()
        id = id['table_id']
        cur.execute(("SELECT * FROM bill_history WHERE order_id = '{0}' ORDER BY date_closed DESC").format(order_id))
        history = cur.fetchone()
        print(history)
        for i in range(1,6):
                cur.execute(("SELECT sum(product_variation.price) AS price, product.name, SUM(order_item.quantity) AS quantity, sum(order_item.subtotal) AS subtotal FROM order_item INNER JOIN tables ON tables.table_id = order_item.table_id INNER JOIN product ON product.product_id = order_item.product_id INNER JOIN sub_category ON sub_category.subcategory_id = product.subcategory_id INNER JOIN product_variation ON product_variation.product_id = product.product_id INNER JOIN category ON category.category_id = sub_category.category_id WHERE  order_item.order_id = '{0}' AND order_item.table_id = {1} and sub_category.category_id = {2} GROUP BY product.name;").format(order_id, id,i))
                if i == 1:
                        drinks = cur.fetchall()
                elif i == 2:
                        starters = cur.fetchall()
                elif i == 3:
                        mains = cur.fetchall()
                elif i == 4:
                        sides = cur.fetchall()
                else:
                        desserts = cur.fetchall()
        cur.execute(("SELECT SUM(subtotal) AS total FROM order_item WHERE order_id = '{0}' AND table_id = {1}").format(order_id, id))
        total = cur.fetchone()
        total = total['total']
        cur.close()
        return render_template('individual_bill_history.html', id = id, history = history, tables = tables, drinks=drinks, starters = starters, mains = mains, sides = sides, desserts = desserts, total = total, order_id = order_id)

#Daily Summary
@app.route('/daily_summary/<string:date>')
@is_logged_in
@is_manager
def daily_summary(date):
        from datetime import datetime
        displayDate = datetime.today().strftime('%d-%m-%y')
        cur = mysql.connection.cursor()
        cur.execute(("SELECT COUNT(*) FROM restaurant.bill_history WHERE date_closed LIKE '%{0}%';").format(date))
        DailyTables = cur.fetchone()
        DailyTables = DailyTables['COUNT(*)']
        cur.execute(("SELECT sum(total) as DailyTotal FROM restaurant.bill_history WHERE date_closed LIKE '%{0}%';").format(date))
        DailyTotal = cur.fetchone()
        DailyTotal = DailyTotal['DailyTotal']
        cur.execute(("SELECT sum(covers) as DailyCovers FROM restaurant.bill_history WHERE date_closed LIKE '%{0}%';").format(date))
        DailyCovers = cur.fetchone()
        DailyCovers = DailyCovers['DailyCovers']
        cur.execute(("SELECT order_item.product_id, sum(order_item.quantity) as quantityTotal, sum(order_item.subtotal) as total, product.name FROM restaurant.order_item, restaurant.product WHERE last_order_time LIKE '%{0}%' AND order_item.product_id = product.product_id GROUP BY product.name, order_item.product_id").format(date))
        DailyItems = cur.fetchall()
        cur.close()
        return render_template('daily_summary.html', date =date, DailyTotal=DailyTotal, DailyCovers = DailyCovers, DailyTables = DailyTables, displayDate = displayDate, DailyItems= DailyItems)

#tables
@app.route('/tables/<string:id>')
@is_logged_in
def tables(id):
        form = TableForm(request.form)
        discountForm = DiscountForm(request.form)
        cur = mysql.connection.cursor()
        cur.execute(("SELECT * FROM tables where table_id = {0};").format(id))
        tables = cur.fetchone()
        order_id=tables['order_id']
        form = TableForm(request.form)
        cur = mysql.connection.cursor()        
        cur.execute(("SELECT covers FROM tables WHERE table_id = {0};").format(id))
        covers = cur.fetchone()
        form.covers.process_data(covers['covers'])
        for i in range(1,6):
                cur.execute(("SELECT sum(product_variation.price) AS price, product.name, order_item.message, product.product_id, SUM(order_item.quantity) AS quantity, sum(order_item.subtotal) AS subtotal FROM order_item INNER JOIN tables ON tables.table_id = order_item.table_id INNER JOIN product ON product.product_id = order_item.product_id INNER JOIN sub_category ON sub_category.subcategory_id = product.subcategory_id INNER JOIN product_variation ON product_variation.product_id = product.product_id INNER JOIN category ON category.category_id = sub_category.category_id WHERE tables.order_id = order_item.order_id and tables.order_id = '{0}' AND tables.table_id = {1} and sub_category.category_id = {2} GROUP BY product.name, order_item.message, product.product_id;").format(order_id, id,i))
                if i == 1:
                        drinks = cur.fetchall()
                elif i == 2:
                        starters = cur.fetchall()
                elif i == 3:
                        mains = cur.fetchall()
                elif i == 4:
                        sides = cur.fetchall()
                else:
                        desserts = cur.fetchall()
        
        cur.execute(("SELECT SUM(subtotal) AS total FROM order_item WHERE order_id = '{0}' AND table_id = {1}").format(order_id, id))
        total = cur.fetchone()
        total = total['total']
        if str(total) == 'None':
                total = 0.00
                service = 0.00
                totalservice = 0.00
        else:
                total -= tables['discountAmount']
                service = float(total / 10)
                totalservice = str(round(((float(total) + service)),2))
                cur.execute(("UPDATE tables SET total = {0}, service = {1}, totalservice = {2} WHERE order_id = '{3}' AND table_id = {4}").format(total,service,totalservice,order_id, id))
        mysql.connection.commit()
        cur.close()
        
        return render_template('tables.html', id = id, form = form, discountForm = discountForm, tables = tables, drinks=drinks, starters = starters, mains = mains, sides = sides, desserts = desserts, order_id = order_id)

#open table
@app.route('/tables/opentable/<string:id>/', methods = ["GET", "POST"])
@is_logged_in
def opentable(id):
        form = TableForm(request.form)
        if request.method == "POST":
                     
                covers = form.covers.data
                cur = mysql.connection.cursor()
                if int(covers) >= 7:
                        cur.execute("UPDATE tables SET order_id = UUID(),active = %s, covers = %s, total = 0.00, date = NOW(), serviceApplied = 1 WHERE table_id = %s;",("1", covers, id))
                else:
                        cur.execute("UPDATE tables SET order_id = UUID(),active = %s, covers = %s, total = 0.00, date = NOW(), serviceApplied = 0 WHERE table_id = %s;",("1", covers, id))
                mysql.connection.commit()
                cur.close()
                mess = ('Table ' + (id)  +' Opened!')
                flash(mess,'success')

                return redirect(url_for('tables', id = id))
        return render_template('open_table.html', form = form)

#add drinks
@app.route('/tables/<string:table_id>/orderdrinks')
@is_logged_in
def orderdrinks(table_id):
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM category, sub_category WHERE category.category_id = sub_category.category_id AND category.category_id = 1")
        sub_categories = cur.fetchall()
        cur.execute(("SELECT order_id FROM tables where table_id = {0};").format(table_id))
        order_id = cur.fetchone()
        order_id = order_id['order_id']
        sub=[]
        for subcat in sub_categories:
                cur.execute("SELECT * FROM product, product_variation WHERE product.subcategory_id = %s AND product.product_id = product_variation.product_id ", (str((subcat["subcategory_id"]))))
                sub.append([subcat["subcategory_name"],cur.fetchall(),subcat["subcategory_id"]])
        cur.close()
        return render_template('orderdrinks.html', sub_categories = sub, order_id = order_id, table_id = table_id)


#add mains
@app.route('/tables/<string:table_id>/ordermains')
@is_logged_in
def ordermains(table_id):
        
       
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM category, sub_category WHERE category.category_id = sub_category.category_id AND category.category_id = 3")
        sub_categories = cur.fetchall()
        cur.execute(("SELECT order_id FROM tables where table_id = {0};").format(table_id))        
        order_id = cur.fetchone()
        order_id = order_id['order_id']
        sub=[]
        for subcat in sub_categories:
                cur.execute(("SELECT * FROM product, product_variation WHERE product.subcategory_id = {0} AND product.product_id = product_variation.product_id ").format((subcat["subcategory_id"])))
                sub.append([subcat["subcategory_name"],cur.fetchall(),subcat["subcategory_id"]])
        cur.close()

        return render_template('ordermains.html', sub_categories = sub, order_id = order_id, table_id = table_id)

#add starters
@app.route('/tables/<string:table_id>/orderstarters')
@is_logged_in
def orderstarters(table_id):
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 2 and category.category_id = 2;")
        starters= cur.fetchall()
        print(starters)
        cur.execute(("SELECT order_id FROM tables where table_id = {0};").format(table_id))        
        order_id = cur.fetchone()
        order_id = order_id['order_id']
        cur.close()

        return render_template('orderstarters.html', starters = starters, order_id = order_id, table_id = table_id)

#add sides
@app.route('/tables/<string:table_id>/ordersides')
@is_logged_in
def ordersides(table_id):
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 4 and category.category_id = 4;")
        sides= cur.fetchall()
        print(sides)
        cur.execute(("SELECT order_id FROM tables where table_id = {0};").format(table_id))        
        order_id = cur.fetchone()
        order_id = order_id['order_id']
        cur.close()

        return render_template('ordersides.html', sides = sides, order_id = order_id, table_id = table_id)

#add desserts
@app.route('/tables/<string:table_id>/orderdesserts')
@is_logged_in
def orderdesserts(table_id):
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 5 and category.category_id = 5;")
        desserts= cur.fetchall()
        print(desserts)
        cur.execute(("SELECT order_id FROM tables where table_id = {0};").format(table_id))        
        order_id = cur.fetchone()
        order_id = order_id['order_id']
        cur.close()

        return render_template('orderdesserts.html', desserts = desserts, order_id = order_id, table_id = table_id)

#add to order
@app.route('/tables/<string:id>/add_to_order/<string:order_id>/<string:product_id>/<string:price>/', methods = ["GET", "POST"])
@is_logged_in
def add_to_order(id, order_id, product_id, price):
        cur = mysql.connection.cursor()
        quantity = request.form.get("quantity" + str(product_id))
        message = request.form.get("message" + str(product_id))
        cur.execute(("SELECT stock FROM product_variation where product_id = {0}").format(product_id))
        stock= cur.fetchone()
        stock = stock['stock']
        if int(quantity) > 0 :
                if int(stock) - int(quantity) > 0:
                        price = float(price)
                        cur.execute(("SELECT COUNT(*) AS exist FROM order_item where order_id = '{0}' and product_id = {1} and message = Null").format(order_id, product_id))
                        result= cur.fetchone()  
                        result = result['exist']
                        if message == "":
                                if int(result) > 0 :
                                        cur.execute(("UPDATE order_item SET quantity = (quantity + {0}), subtotal=( subtotal +  ({1} * {2})), last_order_time = NOW()  WHERE table_id = {3} and product_id = {4} and order_id = '{5}' ").format(quantity, price, quantity,id, product_id, order_id))
                                else:
                                        cur.execute(("INSERT INTO  order_item(order_id, table_id, quantity, subtotal, product_id, last_order_time)  VALUES('{0}',{1},{2},{3},{4},NOW())").format(order_id, id, quantity, int(quantity) * price, product_id))
                        else:
                                cur.execute(("INSERT INTO order_item(order_id, table_id, quantity, subtotal, product_id, message, last_order_time)  VALUES('{0}',{1},{2},{3},{4},'{5}',NOW())").format(order_id, id, quantity, int(quantity) * price, product_id, message))
                        
                        cur.execute(("UPDATE product_variation SET stock = (stock - {0}) WHERE product_id = {1}").format(quantity,product_id))
                        mysql.connection.commit()
                else:
                        tables(id)        
                        flash("Please add a valid quantity.", 'danger')
                
        else:
                flash("Please add a valid quantity.", 'danger')
        tables(id)
        return redirect(url_for('tables', id = id))

#Update order
@app.route('/tables/<string:id>/update_order/<string:order_id>/<string:product_id>/<string:price>/', methods = ["GET", "POST"])
@is_logged_in
def update_order(id, order_id, product_id, price):
        try:
                quantity = int(request.form.get("quantity" + str(product_id)))
                message = request.form.get("message" + str(product_id))
                cur = mysql.connection.cursor()
                cur.execute(("SELECT quantity from order_item WHERE table_id = {0} and order_id = '{1}' and product_id = {2}").format(id, order_id,product_id))
                currentquantity = cur.fetchone()
                currentquantity = currentquantity['quantity']
                #print(("Current Quantity:{0}").format(currentquantity))

                if quantity > 0 :
                        price = float(price)
                        cur.execute(("SELECT COUNT(*) AS exist FROM order_item where order_id = '{0}' and product_id = {1}").format(order_id, product_id))
                        result= cur.fetchone()  
                        result = result['exist']
                        cur.execute(("SELECT stock FROM product_variation where product_id = {0}").format(product_id))
                        stock= cur.fetchone()
                        stock = stock['stock']
                        if int(stock) - quantity > 0:
                                if int(result) > 0 :
                                        cur.execute(("UPDATE order_item SET quantity = {0}, subtotal=({1} * {2}), last_order_time = NOW(), message = '{3}'  WHERE table_id = {4} and product_id = {5} and order_id = '{6}' ").format(quantity, price, quantity,message,id, product_id,order_id)) #already ordered before
                                else:
                                        cur.execute(("INSERT INTO  order_item(order_id, table_id, quantity, subtotal, product_id, last_order_time)  VALUES('{0}',{1},{2},{3},{4},NOW())").format(order_id, id, quantity, int(quantity) * price, product_id)) # new order
                        
                                cur.execute(("UPDATE product_variation SET stock = (stock + {0}) WHERE product_id = {1}").format(currentquantity-quantity,product_id)) #change stock quantity
                                mysql.connection.commit()
                                cur.close()
                        else: # no stock
                                tables(id)
                                flash(('Not enough stock! Current stock {0}').format(stock),'danger')
                elif quantity == 0:     #Delete order from table

                        remove_order(product_id,order_id,id)
                return redirect(url_for('tables', id = id))
                        
        except:
                flash("Please add a valid quantity.", 'danger')
                return redirect(url_for('tables', id = id))



#remove from order
@app.route('/remove_order/<int:id>/<string:order_id>/<string:table_id>', methods = ["GET","POST"])
@is_logged_in
def remove_order(id,order_id,table_id):
        cur = mysql.connection.cursor()
        cur.execute(("DELETE FROM order_item  WHERE product_id = {0} AND order_id = '{1}' AND table_id = {2};").format(id,order_id,table_id))
        mysql.connection.commit()
        cur.close()
        tables(table_id)
        flash('Item Removed!', 'success')
        return redirect(url_for('tables', id = table_id))
        
#Editing Covers
@app.route('/tables/covers/<string:id>/', methods = ["GET", "POST"])
@is_logged_in
def covers(id):       
        cur = mysql.connection.cursor()
        covers = request.form['covers']
        if int(covers) >=7:
                cur.execute(("UPDATE tables SET covers = {0}, serviceApplied = 1 WHERE table_id = {1};").format(covers, id))    
        else:
                cur.execute(("UPDATE tables SET covers = {0}, serviceApplied = 0 WHERE table_id = {1};").format(covers, id))   
        mysql.connection.commit()             
        cur.close()
        tables(id)
        flash('Covers Updated','success')
        return redirect(url_for('tables', id = id))

#Removing a discount
@app.route('/tables/removediscount/<string:id>/', methods = ["GET", "POST"])
@is_logged_in
def removediscount(id):
        
        cur = mysql.connection.cursor() 
        cur.execute(("SELECT discountCode from tables where table_id = {0} ").format(id))
        discount_code = cur.fetchone()
        discount_code = discount_code['discountCode']
        cur.execute(("UPDATE tables set discountCode = NULL, discountType = 0, discountMessage = NULL, discountAmount = 0.00 WHERE (table_id = {0});").format(id))
        cur.execute(("UPDATE discounts set used = 0 WHERE discount_code = '{0}'").format(discount_code))
        mysql.connection.commit()
        cur.close()
        tables(id)
        flash('Discount Removed!','success')
        return redirect(url_for('tables', id = id))

#Adding a discount
@app.route('/tables/discount/<string:id>/', methods = ["GET", "POST"])
@is_logged_in
def discount(id):
        cur = mysql.connection.cursor() 
        form = DiscountForm(request.form)
        discountCode = form.discountCode.data
        cur.execute(("SELECT * FROM discounts WHERE discount_code = '{0}' and used = 0").format(discountCode))
        result = cur.fetchone()
        print(result)
        if str(result) =='None': #Potentially have a database with a bunch of valid discount codes in that this can check against in the future.
                flash('Discount not applied. Code has been used or it is not valid.','danger')
        else:
                discount = result['discount_type']
                cur.execute(("UPDATE tables set discountCode = '{0}', discountType = {1} WHERE (table_id = {2});").format(discountCode,discount,id))
                cur.execute(("SELECT * FROM tables WHERE table_id = {0}").format(id))
                tablesDict = cur.fetchone()
                cur.execute(("SELECT SUM(subtotal) AS total FROM order_item, product, sub_category WHERE order_id = '{0}' AND table_id = {1} and order_item.product_id = product.product_id and product.subcategory_id = sub_category.subcategory_id and sub_category.subcategory_id > 7").format(tablesDict['order_id'],id))
                price = cur.fetchone()
                if result['manager_code'] == 0:
                        cur.execute(("UPDATE discounts set used = 1 WHERE discount_code = '{0}'").format(discountCode))
                try:
                        if int(discount) == 8:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, serviceApplied = 0, discountMessage = '{1}' WHERE table_id = {2}").format(tablesDict['total'],"100% off Bill",id))
                        elif int(discount) == 7:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, discountMessage = '{1}' WHERE table_id = {2}").format(float(tablesDict['total'])*0.2,"20% off Bill",id))
                        elif int(discount) == 6:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, discountMessage = '{1}' WHERE table_id = {2}").format(float(tablesDict['total'])*0.1,"10% off Bill",id))
                        elif int(discount) == 5:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, discountMessage = '{1}' WHERE table_id = {2}").format(float(price['total'])*0.5,"50% off Food",id))     
                        elif int(discount) == 4:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, discountMessage = '{1}' WHERE table_id = {2}").format(float(tablesDict['total'])*0.25,"25% off Bill",id))
                        elif int(discount) == 3:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, discountMessage = '{1}' WHERE table_id = {2}").format(float(price['total'])*0.3,"30% off Food",id))
                        elif int(discount) == 2:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, discountMessage = '{1}' WHERE table_id = {2}").format(float(price['total'])*0.2,"20% off Food",id))
                        elif int(discount) == 1:
                                cur.execute(("UPDATE TABLES SET discountAmount = {0}, discountMessage = '{1}' WHERE table_id = {2}").format(float(price['total'])*0.1,"10% off Food",id))
                        mysql.connection.commit()
                        cur.close()
                        tables(id)
                        flash('Discount Applied!','success')

                except:
                        flash('Discount could not be applied. No items could be discounted!','danger')

        return redirect(url_for('tables', id = id))

#Adding and removing service charge
@app.route('/tables/service/<string:id>/<int:service>', methods = ["GET", "POST"])
@is_logged_in
def service(id,service):
        cur = mysql.connection.cursor()
        cur.execute(("UPDATE tables SET serviceApplied = {0} WHERE table_id = {1}").format(service,id))
        mysql.connection.commit()
        cur.close()
        tables(id)
        flash('Service Charge Updated','success')
        return redirect(url_for('tables', id = id))

#Close table
@app.route('/tables/closetable/<string:id>/', methods = ["GET", "POST"])
@is_logged_in
def close_table(id):
        cur = mysql.connection.cursor()
        cur.execute(("SELECT order_item.order_id, tables.date, tables.covers, sum(order_item.subtotal) AS subtotal, tables.table_id, tables.serviceApplied, tables.discountAmount, tables.discountType, tables.discountCode, tables.discountMessage, tables.service, tables.totalservice FROM order_item INNER JOIN tables ON tables.table_id = order_item.table_id INNER JOIN product ON product.product_id = order_item.product_id INNER JOIN sub_category ON sub_category.subcategory_id = product.subcategory_id INNER JOIN product_variation ON product_variation.product_id = product.product_id INNER JOIN category ON category.category_id = sub_category.category_id  WHERE tables.order_id = order_item.order_id and tables.table_id = {0} GROUP BY order_item.order_id;").format(id))
        results = cur.fetchone()
        if str(results) != "None":
                covers =int(results['covers'])
                table_id =int(results['table_id'])
                date = results['date']
                order_id = results['order_id']
                subtotal = float(results['subtotal'])
                serviceApplied = results['serviceApplied']
                discountAmount = float(results['discountAmount'])
                discountCode = results['discountCode']
                discountType = results['discountType']
                discountMessage = results['discountMessage']
                totalservice = results['totalservice']
                service = results['service']
                if str(discountCode) == 'None':
                        if str(discountType) == 'None':
                                discountCode = ''
                                discountMessage = ''
                                discountType = 0
                cur.execute(("INSERT INTO bill_history(covers, table_id,  total, order_id, date_opened, date_closed, serviceApplied, discountAmount, discountCode, discountType, discountMessage,service, totalservice) VALUES ({0},{1},{2},'{3}','{4}', NOW(),{5},{6},'{7}','{8}','{9}',{10},{11})").format(covers,table_id,subtotal,order_id,date,serviceApplied,discountAmount, discountCode, discountType, discountMessage,service,totalservice))
        cur.execute(("UPDATE tables SET active = 0, covers = 0, order_id = NULL, total = 0.00, service = 0.00, serviceApplied = 0, totalservice = 0.00, serviceApplied = 0, discountCode = NULL, discountType = 0, discountAmount = 0.00, discountMessage = NULL WHERE table_id = {0};").format(id))
        mysql.connection.commit()
        cur.close()
        
        flash('Table Closed!', 'danger')

        return redirect(url_for('floor'))

class TableForm(Form):
        covers = SelectField('Covers', choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10'),('11','11'),('12','12'),('13','13'),('14','14'),('15','15')])

class DiscountForm(Form):
        discount = SelectField('Apply Discount', choices=[('1','10% off Food'),('2','20% off Food'),('3','30% off Food'),('4','25% off Bill'),('5','50% off Food'),('6','10% off Bill'),('7','20% off Bill'),('8','100% Discount')])     
        discountCode = TextAreaField('Discount Code:')

@app.route('/')
def index():
        return render_template('home.html')

#Product creation form
class productForm(Form):
        name = TextAreaField('Name', [validators.Length(min=1, max=200)])
        description = TextAreaField('Description', [validators.Length(min=0,max=200)])
        price = DecimalField('Price')
        category_id = SelectField('Category', choices = [('1','Drinks'),('2','Starters'),('3','Mains'),('4','Sides'),('5', 'Desserts'),('6','Others')])
        stock = IntegerField('Stock Count')
        subcategory_id = SelectField('Sub Category', choices=[('0','Please select a sub category'),('1','Soft'),('2','Hot'),('3','White Wine'),('4','Red Wine'),('5','Rosè/Sparkling/Fizzy'),('6','Beer'),('7','Cocktail'),('8','Drink Other'), ('9','Pizza'), ('10','Pasta'),('11','Grill'), ('12','Salad'),('13','Risotto'),('14','Starter Other'),('15','Main Other'),('16','Side Other'), ('17','Dessert Other')])  


#Product addition  to databse      
@app.route('/add_product', methods = ["GET", "POST"])
@is_logged_in
@is_manager      
@is_chef                       
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
@is_chef
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
@is_chef
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
        sub=[]
        for subcat in sub_categories:
                cur.execute(("SELECT * FROM product, product_variation WHERE product.subcategory_id = {0} AND product.product_id = product_variation.product_id").format((str((subcat["subcategory_id"])))))
                sub.append([subcat["subcategory_name"],cur.fetchall()])
        cur.close()
        return render_template('drinks.html',  sub_categories = sub)


# starters
@app.route('/starters')
def starters():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 2 and category.category_id = 2;")
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
        sub=[]
        for subcat in sub_categories:
                cur.execute(("SELECT * FROM product, product_variation WHERE product.subcategory_id = {0} AND product.product_id = product_variation.product_id").format((str((subcat["subcategory_id"])))))
                sub.append([subcat["subcategory_name"],cur.fetchall()])
        cur.close()
        return render_template('mains.html',  sub_categories = sub)

# desserts
@app.route('/desserts')
def desserts():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = 5  and category.category_id = 5;")

        desserts = cur.fetchall()
        cur.close()
       
        return render_template('desserts.html', desserts=desserts)

class EditForm(Form):
        name = StringField('Name', [validators.Length(min=1)])
        username = StringField('Username', [validators.Length(min=4,max=25)])
        email = StringField('Email', [validators.Length(min =6, max = 50)])
        authority = SelectField('Authority', choices=[('1','General Manager'),('2','Assistant Manager'),('3','Supervisor'),('4','Chef'),('5','Waiter')])

#sign up form validation
class RegisterForm(Form):
        name = StringField('Name', [validators.Length(min=1)])
        username = StringField('Username', [validators.Length(min=4,max=25)])
        email = StringField('Email', [validators.Length(min =6, max = 50)])
        authority = SelectField('Authority', choices=[('1','General Manager'),('2','Assistant Manager'),('3','Supervisor'),('4','Chef'),('5','Waiter')])
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
                        name = name['name']                              
                        password = data['password']
                        auth = auth['authority']
                        userID = userID['id']
                        if auth == 1:
                                auth = "General Manager"
                                session['manager'] = True
                        elif auth == 2:
                                auth = "Assistant Manager"
                                session['manager'] = True
                        elif auth == 3:
                                auth = "Supervisor"
                        elif auth == 4:
                                auth = "Chef"
                                session['chef'] = True
                                print(session['chef'])
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
                                if "manager" in session:
                                        return redirect(url_for('dashboard'))
                                elif "chef" in session:
                                        return redirect(url_for('kitchen'))
                                else:
                                        return redirect(url_for('floor')) #logs user in to dashboard
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
@is_chef
def stock_management():
        cur = mysql.connection.cursor()
        for i in range(1,6):
                cur.execute(("SELECT * FROM product_variation, product, sub_category, category WHERE product_variation.product_id = product.product_id AND product.subcategory_id = sub_category.subcategory_id AND sub_category.category_id = {0} and category.category_id = {0};").format(i))
                if i == 1:
                        drinks = cur.fetchall()
                elif i == 2:
                        starters = cur.fetchall()
                elif i == 3:
                        mains = cur.fetchall()
                elif i == 4:
                        sides = cur.fetchall()
                else:
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
        
        cur.execute("SELECT * FROM users WHERE id = %s", [id])

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
