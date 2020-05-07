import os

from datetime import date
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import json

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

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    stocks = db.execute("SELECT sum(noshares), symbol FROM transactions1 WHERE id = :username GROUP BY symbol"
    , username=session.get("user_id"))
    cash = db.execute("SELECT cash FROM users WHERE id = :username", username=session.get("user_id"))
    s = len(stocks)
    curPrice = []
    for i in range(s):
        curPrice.append(lookup(stocks[i].get('symbol')))
    a = 0
    for i in range(s):
        a = a + (int(curPrice[i].get('price')) * int(stocks[i].get('sum(noshares)')))

    a = a + cash[0].get("cash")


    return render_template("portfolio.html", stocks=stocks,cash=cash,s=s,curPrice=curPrice, a=a)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("must provide symbol and no. of shares")

        quote = lookup(request.form.get("symbol"))
        cashav1 = db.execute("SELECT cash FROM users WHERE id = :username", username=session.get("user_id"))
        fash = int(quote.get("price"))
        hasd = int(request.form.get("shares"))
        cashafter = int(cashav1[0].get("cash") - (hasd * fash))

        #Check p's
        if not cashafter > 0 :
            return apology("Too broke fo' dat brah", 460)

        db.execute("UPDATE users SET cash = :cashafterr WHERE id = :id1"
        , cashafterr=cashafter, id1=session.get("user_id"))
        #INsert purchase into db
        db.execute("INSERT INTO transactions1 (id, symbol, noshares, price, date, trans) VALUES (:i, :s, :n, :p,:D,:se)",
        i=session.get("user_id"), s=quote.get("symbol"), n=hasd,p=quote.get("price"), D=date.today(), se="Buy")

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    return jsonify("TODO")


@app.route("/history")
@login_required
def history():
    trans = db.execute("SELECT symbol, noshares, price, date, trans FROM transactions1 WHERE (id=:username)"
    , username=session.get("user_id"))
    s=len(trans)


    return render_template("history.html", s=s,trans=trans)


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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide symbol")
        quote = lookup(request.form.get("symbol"))
        return render_template("quoted.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password") and request.form.get("confirmation"):
            return apology("must provide password and confirmation", 403)
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("The two Passwords don't match", 403)

        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        if len(rows) > 0:
            return apology("This user exists please select different Username.", 411)
        else:
            has = generate_password_hash(request.form.get("password"))
            db.execute("INSERT INTO users (username, hash) VALUES (:u, :p)",
            u=request.form.get("username"), p=has)
        return render_template("login.html")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    stocks = db.execute("SELECT sum(noshares), symbol FROM transactions1 WHERE id = :username GROUP BY symbol"
    , username=session.get("user_id"))
    s = len(stocks)
    if request.method == "POST":
        if not request.form.get("stock") or not request.form.get("share"):
            return apology("Idiot")
        i = 0
        d = 0
        for i in range(s):
            qw = stocks[i].get('symbol')
            if qw == request.form.get("stock"):
                d = i
                break

        if int(request.form.get("share")) > stocks[d].get('sum(noshares)'):
                return apology("MORON")
        quote = lookup(stocks[i].get('symbol'))


        cashav1 = db.execute("SELECT cash FROM users WHERE id = :username", username=session.get("user_id"))

        cashafter = int(cashav1[0].get("cash") + (int(request.form.get("share")) * quote.get("price")))

        db.execute("INSERT INTO transactions1 (id, symbol, noshares, price, date, trans) VALUES (:i, :s, :n, :p,:D,:Sell)"
        , i=session.get("user_id"), s=quote.get("symbol"), n=(0-int(request.form.get("share"))),p=quote.get("price"),
        D=date.today(), Sell="Sell")

        db.execute("UPDATE users SET cash = :cashafter WHERE id = :id1"
        , cashafter=cashafter, id1=session.get("user_id"))
        return redirect("/")
    else:
        return render_template("sell.html", stocks=stocks,s=s)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
