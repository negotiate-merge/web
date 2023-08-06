import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from gen import *
import mysql.connector
from datetime import datetime
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

from helpers import apology, login_required, db_connect, get_status, check_password

# Configure application
app = Flask(__name__)

# Tell flask it is behind a proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = b'>p\xf2\xae\x8c\x0cZ9'
Session(app)

""" BEGIN HOME PAGE """
@app.route("/", methods=["GET"])
def home():
    return render_template("/home.html")



""" END HOME PAGE   BEGIN SO-RANDOM """
# URL for web scraping results
URL = 'https://australia.national-lottery.com/powerball/results-archive-2023'

@app.route("/so-random", methods=["GET", "POST"])
def index_sr():
    """ Show recent draw stats and provide interface for user input to generate numbers """
    if request.method == "GET":
        # Get 2 buffered cursor
        cnx = db_connect('s')
        curA = cnx.cursor(buffered=True)

        # Ensure database has the latest draw results
        dbUpdate(URL)

        # Aggregate ball counts for last week - must be run before the counter of next week because 
        # the function will clear its global arrays if 53 is passed in as 2nd arg
        lastAggregated = aggregate(curA, 53)
        
        # Aggregate ball counts for this week
        aggregated = aggregate(curA, 52)
        

        # Print heat for this week and last week
        #print("\nThis weeks heat check\n")
        #print(aggregated)
        #print("\nLast weeks heat check\n")
        #print(lastAggregated)
        

        # Get results from last draw
        lastDraw = getLastDraw(curA)
       
        # Retrieve additional info for display on home page
        curA.execute("SELECT MAX(drawDate) AS drawDate FROM results") #[0]['drawDate']
        lastRecord = curA.fetchone()
        lastRecord = str(lastRecord[0])
        #print(lastRecord)

        # Reformat date 
        latestDate = f"{lastRecord[8:]}-{lastRecord[5:7]}-{lastRecord[0:4]}"

        curA.close()
        cnx.close()

        return render_template('so-random/index.html', latest=latestDate, previousColdNums=lastAggregated['coldNumbers'], 
        previousHotNums=lastAggregated['hotNumbers'], previousColdPows=lastAggregated['coldPowers'],
        previousHotPows=lastAggregated['hotPowers'], coldNumbers=aggregated['coldNumbers'], 
        hotNumbers=aggregated['hotNumbers'], coldPowers=aggregated['coldPowers'], 
        hotPowers=aggregated['hotPowers'], ldn=lastDraw['lastNums'], ldp=lastDraw['lastPower'])

@app.route("/so-random/generate", methods=["GET", "POST"])
def generate():
    if request.method == "POST":
        # Store Drawn numbers
        thisDraw = []

        # Generate random numbers
        randomNos = int(request.form.get('random'))
        while randomNos > 0:
            balls = 0
            drawn = []
            while balls < 7:
                b = drawBall('r')
                if b not in drawn:
                    drawn.append(b)
                    balls += 1
            drawn.append(drawPower('r'))
            thisDraw.append(drawn)
            randomNos -= 1

        # Converts stringified numbers to integers
        changeState()

        '''
        Dynamic generation of hot cold selections
        '''
        # Integer for concatenation to html name attributes
        rowCount = 1

        while ('hot' + str(rowCount)) in request.form:
            names = ['hot', 'power', 'count']

            # Dynamic key name assignment for form
            hotRow = names[0] + str(rowCount)
            powerRow = names[1] + str(rowCount)
            countRow = names[2] + str(rowCount)

            # Get values from web form
            hot = int(request.form.get(f'{hotRow}'))
            count = int(request.form.get(f'{countRow}'))
            power = request.form.get(f'{powerRow}')
            
            # Variable heat number generator
            # For each line
            while count > 0:
                balls = 0
                drawn = []
                # Generate hot balls
                while balls < hot:
                    b = drawBall('h')
                    if b not in drawn:
                        drawn.append(b)
                        balls += 1
                # Generate cold balls
                while balls < 7:
                    b = drawBall('c')
                    if b not in drawn:
                        drawn.append(b)
                        balls += 1
                # Generate power ball
                if power == 'hot':
                    drawn.append(drawPower('h'))
                else:
                    drawn.append(drawPower('c'))
                thisDraw.append(drawn)
                count -= 1
            
            # Increment concatenation counter at top of main loop
            rowCount += 1

        return render_template("/so-random/numbers.html", message="Your lotto numbers", link="Return to Parameter Selection", lines=thisDraw)
    else:
        return render_template("/so-random/error.html", message="Woops, you seem to have lost your way", link="Return home to Enter Parameters.")

@app.route("/so-random/usage", methods=["GET"])
def usage():
    if request.method == 'GET':
        return render_template("/so-random/usage.html")

""" END SO-RANDOM   BEGIN ROTADYNE PAGES """

def get_orders(client_id):
    """ Retrieve order history for a given companys client_id """
    # Get buffered cursor
    cnx = db_connect('r')
    curA = cnx.cursor(buffered=True)

    """     FIRST VERSION HAS NO TRADING NAME
    # Replaced Doc_ID with CDH_ID as DOC_ID had no rows in detail query
    sales_query = ("SELECT CDH_ID, Doc_Date, Doc_Amount, Order_Status "
            "FROM client_docs_header WHERE (Tran_Type = 'SORD') "
            "AND (Client_ID = %s) ORDER BY Doc_ID DESC")
    """

    sales_query = ("SELECT CDH_ID, Doc_Date, Doc_Amount, Order_Status, client_master.Trading_Name "
                    "FROM client_docs_header INNER JOIN client_master ON client_docs_header.Client_ID = client_master.Client_ID "
                    "WHERE (Tran_Type = 'SORD') AND (client_docs_header.Client_ID = %s) ORDER BY Doc_ID DESC")

    curA.execute(sales_query, (client_id,))

    sales_records = []

    for row in curA:
        # Reformat date from YYYYMMDD to DDMMYYYYY
        row_date = str(row[1])
        rev_date = f"{row_date[8:]}/{row_date[5:7]}/{row_date[0:4]}"

        record = {
            "doc_id": row[0],
            "doc_date": rev_date,
            "doc_amount": "${:,.2f}".format(row[2]),
            "order_status": get_status(row[3]),
            "trading_name": row[4]
        }
        sales_records.append(record)

    curA.close()
    cnx.close()

    return sales_records


@app.route("/rotadyne", methods=["GET"]) # changed from / to /rotadyne
@login_required
def index():
    """Show history of sales"""
    if request.method == 'GET':
        if not session['query_id']:
            records = get_orders(session["client_id"])
        else:
            records = get_orders(session['query_id'])
            # print(f"query_id is {session['query_id']}")
        
        return render_template("rotadyne/index.html", records=records)
    else:
        return redirect("/rotadyne")


@app.route("/rotadyne/order_details/<int:order_id>", methods=["GET"])
@login_required
def get_details(order_id):
    if request.method == "GET":
        # Get buffered cursor
        cnx = db_connect('r')
        curA = cnx.cursor(buffered=True)

        details = ("SELECT client_docs_items.OrdInv_Item, stock_item_master.StockID, "
        "stock_item_master.Item_Desc, client_docs_items.Item_Qty, client_docs_items.Item_Price, "
        "client_docs_items.Items_Shipped,  client_docs_items.Item_Status "
        "FROM client_docs_items INNER JOIN stock_item_master ON "
        "client_docs_items.Int_Stock_ID = stock_item_master.Int_Stock_ID WHERE "
        "(client_docs_items.CDH_ID = %s) ORDER BY client_docs_items.OrdInv_Item")

        # Execute query with url argument order_id
        curA.execute(details, (order_id,))

        lines = []

        for row in curA:
            # print(row)
            line = {
                    "item": row[0],
                    "stock_id": row[1],
                    "description": row[2],
                    "qnt": "{:,.0f}".format(row[3]),
                    "item_price": "${:,.2f}".format(row[4]),
                    "items_shpd": "{:,.0f}".format(row[5]),
                    "item_status": get_status(row[6])
                }
            #print(row[6], "is of type ", type(row[6]))
            #print(row[6], "is of type ", type(row[6]))
            lines.append(line)

        return render_template("rotadyne/details.html", order_id=order_id, lines=lines)

    else:
        return apology("Method not permitted", 403)


@app.route("/rotadyne/admin", methods=["GET", "POST"])
@login_required
def admin():
    if request.method == "POST":
        client_id = request.form.get('organization')
        # print("client_id is ", client_id)
        session['query_id'] = client_id
        client_orders = get_orders(client_id)

        if not client_orders:
            flash("Organization has no order history at this time")
            return redirect("/rotadyne/admin")

        return redirect("/rotadyne")
        #return render_template("rotadyne/index.html", records=client_orders) # redirect here to use get request

    else:
        # Ensure user is admin
        if session["client_id"] != -1:
            return apology("Unauthorized", 403)
        
        # Get list of companys for drop down
        bulk_query = ("SELECT Client_ID, Trading_Name FROM client_master")

        # Get all company names
        cnx = db_connect('r')
        curA = cnx.cursor(buffered=True)
        curA.execute(bulk_query,)
        all_companys = curA.fetchall()

        organizations = []

        for c in all_companys:
            company = {
                "clientId" : c[0],
                "name" : c[1]
            }

            organizations.append(company)

        curA.close()
        cnx.close()
        return render_template("rotadyne/admin.html", orgs=organizations)


@app.route("/rotadyne/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":
        # Retreive fields from form
        username = request.form.get("username")
        password = request.form.get("password")
        
        
        # Ensure username & password submitted
        if not username:
            return apology("must provide username", 401)
        elif not password:
            return apology("must provide password", 401)
        
        # Get buffered cursor
        cnx = db_connect('r')
        curA = cnx.cursor(buffered=True)
        
        # Login without company assigned
        query_unassigned = ("SELECT UID, Client_ID, UserName, Password FROM users WHERE UserName = %(user_name)s")
        
        # Login in with company assigned
        query_registered = ("SELECT UID, users.Client_ID, UserName, Password, client_master.Trading_Name "
                "FROM users INNER JOIN client_master ON users.Client_ID = client_master.Client_ID "
                "WHERE UserName = %(user_name)s")
        
        # Get first row matching username
        curA.execute(query_registered, {'user_name': username})
        row = curA.fetchone()
        #print(row)

        # If no assisnged user, check for unassigned users
        if row == None:
            curA.execute(query_unassigned, {'user_name': username})
            row = curA.fetchone()

            # Handle no user
            if row == None:
                return apology("Invalid username", 403)

            # Handle invalid password
            if not check_password_hash(row[3], password):
                return apology("Invalid Password", 403)

            if row[1] < 0:
                # Log in Administrators
                session["user_id"] = row[0]
                session["client_id"] = row[1]
                session["user_name"] = row[2]
                session["trading_name"] = "Rotadyne"

                return redirect("/rotadyne/admin")

            # Log in unnassigned users
            session["user_id"] = row[0]
            session["client_id"] = row[1]
            session["user_name"] = row[2]
            session["trading_name"] = "No Organiztion Assigned"

            return redirect("/rotadyne")

        # Handle invalid Password
        if not check_password_hash(row[3], password):
            return apology("Invalid Password", 403)

        # Log in assigned users
        session["user_id"] = row[0]
        session["client_id"] = row[1]
        session["user_name"] = row[2]
        session["trading_name"] = row[4]

        # print(f"session-user-id = {session['user_id']}")
        # print(f"session-client-id = {session['client_id']}")
        # print(f"session-user-name = {session['user_name']}")
        # print(f"session-trading-name = {session['trading_name']}")

        curA.close()
        cnx.close()

        # Experimental flashing of login success message
        #flash("Login Successful")

        # Redirect user to home page
        return redirect("/rotadyne")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("rotadyne/login.html")


@app.route("/rotadyne/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/rotadyne/register", methods=["GET", "POST"])
def register():
    #Register user
    if request.method == "GET":
        return render_template("rotadyne/register.html")
    else:
        cnx = db_connect('r')
        # Get two buffered cursors
        curA = cnx.cursor(buffered=True)
        curB = cnx.cursor(buffered=True)

        query_user = ("SELECT UID, UserName, Email FROM users")

        add_user = ("INSERT INTO users (UID, UserName, Email, Password) "
                    "VALUES (%(uid)s, %(user_name)s, %(email)s, %(password)s)")

        new_user = {
            'uid': 0,
            'user_name': request.form.get("username"),
            'email': request.form.get("email"),
            'password': ''
        }

        # Will check this and password validity using js 
        if not new_user['user_name'] or not new_user['email']:
            return apology("Blank username or email")

        curA.execute(query_user)

        for uid, name, email in curA:
            # print(uid, ' ' + name + ' ' + email)
            if name == new_user['user_name']:
                # print("Username already in use")
                return apology("Username already in use")
            elif email == new_user['email']:
                # print("Email already in use")
                return apology("Email already in use")
            if uid > new_user['uid']:
                new_user['uid'] = uid

        # Increment new uid by 1
        new_user['uid'] += 1
        
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if password != confirmation:
            return apology("Passwords do not match")

        new_user['password'] = generate_password_hash(password, "sha256", salt_length=8)

        curB.execute(add_user, new_user)

        # Close cursor and connection
        cnx.commit()
        curA.close()
        curB.close()
        cnx.close()
        return redirect("/rotadyne")


# Not currently in use
""" 
@app.route("/page2", methods=["GET", "POST"])
@login_required
def page2():
    if request.method == "GET":
        return render_template("page2.html")
    else:
        return redirect("/")


@app.route("/page3", methods=["GET", "POST"])
@login_required
def page3():
    if request.method == "GET":
        return render_template("page3.html")
    else:
        return redirect("/")
"""


@app.route("/rotadyne/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        '''Retrieve last three passwords from database and check to see if they match the
        new password'''
        # TODO add password validity checks and eliminate common phrases
        new_password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure valid password
        if new_password != confirmation:
            return apology("Passwords do not match")
        
        # Get buffered cursor
        cnx = db_connect('r')
        curA = cnx.cursor(buffered=True)

        get_passwords = ("SELECT Password, Password2, Password3 FROM users WHERE UID = %s")

        update_password = ("UPDATE users SET Password = %s, Password2 = %s, Password3 = %s "
                    "WHERE UID = %s")

        curA.execute(get_passwords, (session['user_id'],))
        row = curA.fetchone()

        # Check for duplicate passwords
        for item in row:
            # Account for null in db, check_password_hash will throw error
            if item == None:
                pass
            elif check_password_hash(item, new_password):
                return apology("Cannot re-use passwords that exist in recent history", 409)

        newpass = {
            'word1': generate_password_hash(new_password, "sha256", salt_length=8),
            'word2': row[0],
            'word3': row[1]
        }

        curA.execute(update_password, (newpass['word1'], newpass['word2'], newpass['word3'], session['user_id']))

        cnx.commit()
        curA.close()
        cnx.close()
        # TODO Pass msg through to Javascript alert for display
        return render_template("rotadyne/profile.html")#, msg='Password sucessfully updated')
    else:
        return render_template("rotadyne/profile.html")


def errorhandler(e):
    """Handle error"""
    # print(e)b
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
