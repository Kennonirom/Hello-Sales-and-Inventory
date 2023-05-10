import os
import datetime


from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():

        transactions_db=db.execute("SELECT * FROM transactions")

        return render_template("index.html", transactions=transactions_db)






"""
@app.route("/history")
@login_required
def history():
    return apology("TODO")
"""



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/add")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")









@app.route("/cart")
@login_required
def cart():

    cart_db = db.execute("SELECT * FROM Cart")

    inventory_db = db.execute("SELECT * FROM Inventory")


    search_query = request.args.get('q')
    if search_query:
        inventory_db = db.execute("SELECT * FROM inventory WHERE itemName LIKE ?", f"%{search_query}%")


    return render_template("cart.html", cart=cart_db, inventory=inventory_db, search_query=search_query)




@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    item_code = request.form.get('item_code')
    item_name = request.form.get('item_name')
    price = float(request.form.get('price'))
    quantity = int(request.form.get('quantity'))



    # Check if item is already in the cart
    result = db.execute("SELECT * FROM Cart WHERE item_name = ?", item_name)
    if result:
        # Item is already in the cart, update the quantity and total
        flash("Item already exist in the cart")
    else:
        # Item is not in the cart, insert a new row
        date = datetime.datetime.now()
        total = price * quantity
        db.execute("INSERT INTO Cart (date_time, item_code, item_name, quantity, price, total) VALUES (?, ?, ?, ?, ?, ?)", date, item_code, item_name, quantity, price, total)



    return redirect('/cart')






#ADD
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if (request.method == "POST"):
        itemName = request.form.get('itemName')
        description = request.form.get('description')
        category = request.form.get('category')
        price = request.form.get('price')
        stocks = request.form.get('stocks')

        try:
            db.execute("INSERT INTO inventory (itemName, description, category, price, stocks) VALUES (?, ?, ?, ?, ?)", itemName, description, category, price, stocks)

            return redirect('/add')
        except:
            return apology('item already exists')

    else:
        search_query = request.args.get('q')
        if search_query:
            inventory_db = db.execute("SELECT * FROM inventory WHERE itemName LIKE ?", f"%{search_query}%")
        else:
            inventory_db = db.execute("SELECT * FROM inventory")
        return render_template("add.html", inventory=inventory_db, search_query=search_query)




@app.route("/process", methods=["POST"])
def process():
#PROCESS ITEM
        if (request.method == "POST"):
            db.execute("INSERT INTO transactions (transaction_code, date_time, item_id, item_name, quantity, price, total)SELECT transaction_code, date_time, item_code, item_name, quantity, price, total FROM Cart")
            #db.execute("INSERT INTO transactions (transaction_code, date_time, item_id, item_name, quantity, price, total) VALUES (?, ?, ?, ?, ?, ?, ?)", transaction_code, date_time, item_id, item_name, quantity, price, total)
            db.execute("""UPDATE inventory
                SET stocks = stocks - (
                SELECT SUM(quantity)
                FROM Cart
                WHERE Cart.item_code = inventory.id
                )
                WHERE id IN (
                SELECT item_code
                FROM Cart
                )""")
            db.execute("DELETE  FROM Cart")


        return redirect("/cart")








@app.route("/delete_item", methods=["POST"])
def delete_item():
#REMOVE ITEM
        transaction_code = request.form.get("transaction_code")

        if transaction_code:
            db.execute("DELETE FROM Cart WHERE transaction_code = ?", transaction_code)

        return redirect("/cart")


@app.route("/remove", methods=["POST"])
def remove():
#REMOVE ID
        id = request.form.get("id")

        if id:
            db.execute("DELETE FROM inventory WHERE id = ?", id)

        return redirect("/add")



@app.route("/edit", methods=["POST"])
def edit():

        id = request.form.get("id")
        itemName = request.form.get('itemName')
        description = request.form.get('description')
        category = request.form.get('category')
        price = request.form.get('price')
        stocks = request.form.get('stocks')

        if id:   #updates the cash in the data sbe
            db.execute("UPDATE inventory SET itemName=?, description=?, category=?, price=?, stocks=? WHERE id=?", itemName, description, category, price, stocks, id)

        return redirect("/add")





@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if (request.method == "POST"):
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

         #chekcs if empty
        if not username:
            return apology("Must Give Username")

        if not password:
            return apology("Must Give password")

        if not confirmation:
            return apology("Must give Pass Confirmaiton")
        #pass must ==  to confirmation
        if password != confirmation:
            return apology("Password Do Not Match ")
        #turns pass into encrypted int
        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
            return redirect('/add')
        except:
            return apology('username has already been registered')
    else:
        return render_template("register.html")





if __name__ == '__main__':
    app.run(debug=True)



