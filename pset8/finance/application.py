import os
import json

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, Response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from decimal import Decimal
import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["lookup"] = lookup

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Last quote user looked up
class DataStore():
    lastQuote = None
data = DataStore()

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    stocks = {}
    thisStock = db.execute("SELECT shares, symbol FROM purchases WHERE purchaser = '{}'".format(session["user_id"]))

    for i in range(len(thisStock)):
        stockSymbol = thisStock[i]["symbol"]
        if stockSymbol not in stocks.keys():
            stocks[stockSymbol] = thisStock[i]["shares"]
        else:
            stocks[stockSymbol] += thisStock[i]["shares"]

    print("RELOADED!!")

    session["user_stocks"] = stocks

    return render_template("hub.html", stocks=stocks)


@app.route("/buy", methods=["POST"])
@login_required
def buy():
    requestedShares = request.form.get("sharesInput")
    if not requestedShares:
        return render_template("hub.html", redirectDiv=0, quoteData=data.lastQuote, error_message="Quantity of shares not specified.")

    # standard stock price * how many stocks user requested to purchase
    totalValue = Decimal(data.lastQuote.get("price").replace("$","")) * int(requestedShares)
    userFinalCash = session["user_cash"] - totalValue

    if not userFinalCash >= 0:
        return render_template("hub.html", redirectDiv=0, quoteData=data.lastQuote, error_message="Could not purchase stocks: not enough cash.")
    else:
        purchaseDateTime = datetime.datetime.utcnow()
        session["user_cash"] = userFinalCash

        # UPDATE USER'S CASH IN THE DATABASE
        db.execute("UPDATE users SET cash = {} WHERE id = {}".format(userFinalCash, session["user_id"]))

        # INSERTS THE PURCHASE INTO THE 'PURCHASES' TABLE IN THE DATABASE
        db.execute("INSERT INTO purchases ('purchaser', 'price', 'date', 'symbol', 'shares') VALUES ('{}', '{}', '{}', '{}', '{}')".format(session["user_id"], totalValue, purchaseDateTime.strftime('%Y-%m-%d %H:%M:%S'), data.lastQuote.get("symbol"), int(requestedShares)))

        # CHECKS IF USER HAS ALREADY PURCHASED THAT STOCK, IF NOT: CREATE A COLUMN WITH THE STOCK'S SYMBOL AND SHARES. ELSE: JUST UPDATE THE SHARES FOR THAT STOCK
        if len(db.execute("SELECT * from total_userShares WHERE userid = '{}' AND symbol = '{}'".format(session["user_id"], data.lastQuote.get("symbol")))) != 1:
            db.execute("INSERT INTO total_userShares ('userid', 'symbol', 'shares') VALUES ('{}', '{}', '{}')".format(session["user_id"], data.lastQuote.get("symbol"), int(requestedShares)))
        else:
            db.execute("UPDATE total_userShares SET shares = shares + '{}' WHERE userid = '{}' AND symbol = '{}'".format(int(requestedShares), session["user_id"], data.lastQuote.get("symbol")))

        return redirect("/")


    return apology("TODO")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    return jsonify("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id and user_cash
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error_message="Must provide username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error_message="Must provide password.")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))


        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error_message="Invalid username/password.")

        # Remember which user has logged in, and store their cash
        session["user_id"] = rows[0]["id"]
        session["user_cash"] = Decimal(rows[0]["cash"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id and user_cash
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["POST"])
@login_required
def quote(): # FIND A WAY TO NOT RELOAD THE PAGE WHEN QUOTING!! and reset the tables plz
    userInput = request.form.get("symbol")
    if not userInput:
        return render_template("hub.html", redirectDiv=0, error_message="Please insert a symbol.")

    data.lastQuote = lookup(userInput)
    print(session["user_stocks"])
    return render_template("hub.html", redirectDiv=1, quoteData=data.lastQuote)

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    passwordConfirmation = request.form.get("passwordCheck")
    canRegister = True

    # DOUBLE CHECKS IF USER DIDN'T LEAVE THE FORM BLANK
    if not username or not password or not passwordConfirmation:
        flash("One or more fields were left blank.")
        canRegister = False

    # CHECKS IF USERNAME IS ALREADY TAKEN
    for usernames in db.execute("SELECT username FROM 'users'"):
        if usernames.get("username", None).lower() == username.lower():
            canRegister = False

    # CREATES A HASH FOR USER'S PASSWORD AND INSERTS DATA IN THE DATABASE
    if canRegister:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=2)
        db.execute("INSERT INTO 'users' ('username', 'hash') VALUES ('{}', '{}')".format(username, hashed_password))
        return redirect("/")
    else:
        return render_template("login.html", error_message="Username already taken.", redirectToRegister=True);


@app.route("/sell", methods=["POST"])
@login_required
def sell():
    requestedStockToSell = request.args.get("sym")
    requestedSharesToSell = int(request.form.get("shares"))

    if requestedStockToSell not in session["user_stocks"]:
        return render_template("hub.html", error_message="You don't have that stock.")
    elif requestedSharesToSell > int(session["user_stocks"][requestedStockToSell]):
        return render_template("hub.html", error_message="You don't have enough shares for that stock.")
    else:
        totalValue = Decimal(lookup(requestedStockToSell).get("price").replace("$", "")) * int(requestedSharesToSell)



    return "AH "


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
