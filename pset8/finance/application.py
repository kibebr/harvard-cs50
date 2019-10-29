import os
import json

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, Response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from decimal import Decimal, ROUND_HALF_UP
import datetime
from helpers import apology, login_required, lookup, usd, usdFloat

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

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

class Stock:
    def __init__(self, symbol, shares):
        fetchData = lookup(symbol)
        self.name = fetchData["name"]
        self.price = fetchData["price"]
        self.symbol = symbol
        self.shares = shares
    def get_dict(self):
        return {"symbol": self.symbol, "name": self.name, "price": self.price, "shares": self.shares}


# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    return render_template("hub.html", stocks=session["user_stocks"])


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    requestedShares = request.args.get("shares")
    requestedSymbol = request.args.get("sym")

    if not requestedSymbol or not requestedShares:
        return apology("ERROR")

    # standard stock price * how many stocks user requested to purchase
    totalValue = usdFloat(float(data.lastQuote.get("price").replace("$",""))) * int(requestedShares)
    userFinalCash = session["user_cash"] - totalValue

    if not userFinalCash >= 0:
        return {"id": "NOT_ENOUGH_CASH"}
    else:
        userStocks = session["user_stocks"]
        session["user_cash"] = userFinalCash
        purchaseDateTime = datetime.datetime.utcnow()

        # UPDATE USER'S CASH IN THE DATABASE
        db.execute("UPDATE users SET cash = {} WHERE id = {}".format(userFinalCash, session["user_id"]))

        # INSERTS THE PURCHASE INTO THE 'PURCHASES' TABLE IN THE DATABASE
        db.execute("INSERT INTO purchases ('purchaser', 'price', 'date', 'symbol', 'shares') VALUES ('{}', '{}', '{}', '{}', '{}')".format(session["user_id"], totalValue, purchaseDateTime.strftime('%Y-%m-%d %H:%M:%S'), data.lastQuote.get("symbol"), int(requestedShares)))

        # CHECKS IF USER HAS ALREADY PURCHASED THAT STOCK, IF NOT: CREATE A COLUMN WITH THE STOCK'S SYMBOL AND SHARES.

        if len(db.execute("SELECT * from total_userShares WHERE userid = '{}' AND symbol = '{}'".format(session["user_id"], data.lastQuote.get("symbol")))) != 1:
            db.execute("INSERT INTO total_userShares ('userid', 'symbol', 'shares') VALUES ('{}', '{}', '{}')".format(session["user_id"], data.lastQuote.get("symbol"), int(requestedShares)))
            cacheNewStock = {"symbol": requestedSymbol, "name": data.lastQuote.get("name"), "price": data.lastQuote.get("price"), "shares": requestedShares}
            session["user_stocks"].append(cacheNewStock);
        else: # JUST UPDATE THE SHARES FOR THAT STOCK
            db.execute("UPDATE total_userShares SET shares = shares + '{}' WHERE userid = '{}' AND symbol = '{}'".format(int(requestedShares), session["user_id"], data.lastQuote.get("symbol")))
            for stock in userStocks: # updates cache
                if stock["symbol"] == requestedSymbol.upper():
                    stock["shares"] = stock["shares"] + int(requestedShares)

        flash("Success! Transaction (buying) completed.", category="success")
        return {"id":"BOUGHT"}

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
            flash("Please type your username.", category="danger");
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please type your password.", category="danger")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))


        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Username or password are invalid.", category="danger");
            return render_template("login.html")

        # Remember which user has logged in, and store their cash
        session["user_id"] = rows[0]["id"]
        session["user_cash"] = rows[0]["cash"]

        stocks = db.execute("SELECT symbol, shares FROM total_userShares WHERE userId = :userId", userId=session["user_id"])
        listOfStocks = []

        for stock in stocks:
            listOfStocks.append(Stock(stock["symbol"], stock["shares"]).get_dict())

        session["user_stocks"] = listOfStocks

        # Redirect user to home page
        flash("Logged in!", category="success")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id and user_cash and user_stocks
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/quote", methods=["GET"])
@login_required
def quote():
    requestedSymbol = request.args.get("sym")
    isAjax = request.args.get("fromAJAX")

    if not requestedSymbol:
        return "no symbol"

    quoteData = lookup(requestedSymbol)
    data.lastQuote = quoteData;
    if quoteData is None:
        return "NONE", 404
    else:
        if not isAjax:
            return render_template("hub.html", redirectDiv=1, quoteData=quoteData)
        return quoteData

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
        flash("Success! You can now log-in to your new account.", category="success")
        return redirect("/")
    else:
        flash("Username already taken.", category="danger")
        return render_template("login.html", redirectToRegister=True);


@app.route("/sell", methods=["POST"])
@login_required
def sell():
    requestedStockToSell = request.args.get("sym")
    requestedSharesToSell = int(request.form.get("shares"))
    userStocks = session["user_stocks"]

    for stock in userStocks:
        if requestedStockToSell == stock["symbol"]: # user has stock
            if requestedSharesToSell > int(stock["shares"]): # user doesn't have enough shares
                flash("You don't have enough shares.", category="danger")
                return render_template("hub.html")
            else: # user has enough shares
                totalValue = usdFloat(float(stock["price"].replace("$", ""))) * int(requestedSharesToSell)
                db.execute("UPDATE total_userShares SET shares = shares - :sharesToSell WHERE userId = :userId AND symbol = :stockSymbol", sharesToSell=requestedSharesToSell, userId=session["user_id"], stockSymbol=stock["symbol"])

                stock["shares"] = stock["shares"] - requestedSharesToSell
                session["user_cash"] = session["user_cash"] + totalValue
                db.execute("UPDATE users SET cash = :cash WHERE id = :userId", cash=session["user_cash"], userId=session["user_id"])

                flash("Success! Transaction (selling) completed.", category="success")
                return render_template("hub.html")

    return {"id":"NO_STOCK_FOUND"}



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
