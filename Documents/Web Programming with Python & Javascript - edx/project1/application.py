import os
import requests
from flask import Flask, session, render_template, url_for, redirect, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = "Hello123"

# Check for environment variable
if not os.getenv("DATABASE_URL_BOOKS"):
    raise RuntimeError("DATABASE_URL is not set")

# pool_pre_ping helps handle DB connection drops
#app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL_BOOKS"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        login = True
        return render_template("index.html", login = login)
    else:
        return render_template("login.html")


@app.route("/login")
def login():
    return render_template('login.html')


@app.route("/signup")
def signup():
    return render_template('signup.html')

@app.route("/logging_out")
def log_me_out():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route("/logging_in" ,methods=['POST','GET'])
def logging_in():
    if request.method == 'POST':
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE user_id = :user_id", {"user_id": user_id}).fetchone()
        if ((user_id == user.user_id) and (password == user.password)):
            session['user_id'] = user_id
            return redirect(url_for('index'))
        else:
            return render_template("message.html", message = "UserID or Password was wrong.")
        #-----------------------------------------------------------------------------------


@app.route("/signing_up" ,methods=["POST","GET"])
def signing_up():
    user_id = request.form.get("user_id")
    name = request.form.get("name")
    password = request.form.get("password")
    if db.execute("SELECT * FROM users where user_id = :user_id", {"user_id":user_id}).rowcount != 0:
        return render_template("message.html", message = "Username already exists. Try different one.")
    db.execute("INSERT INTO users (user_id, name, password) VALUES (:user_id, :name, :password)",{"user_id":user_id, "name": name, "password": password})
    db.commit()
    session['user_id'] = user_id
    return redirect(url_for('index'))


@app.route("/search" ,methods=["POST"])
def search():
    title = request.form.get("title")
    books = db.execute("SELECT * FROM books WHERE (lower(title) LIKE '%' || :title || '%') OR (lower(isbn) LIKE '%' || :title || '%') OR (lower(author) LIKE '%' || :title || '%')", {"title": title.lower()}).fetchall()
    #isbns = db.execute("SELECT * FROM books WHERE ", {"title": title}).fetchall()
    #authors = db.execute("SELECT * FROM books WHERE author like '%:title%'", {"title": title}).fetchall()
    if 'user_id' in session:
        login = True
    else:
        login = False
    return render_template("result.html", books=books, login=login, search_title=title)


class rate_count():
    def __init__(self, rating):
        if float(rating) >= 4.5:
            self.check1='checked'
            self.check2='checked'
            self.check3='checked'
            self.check4='checked'
            self.check5='checked'
        elif float(rating) >= 3.5:
            self.check1='checked'
            self.check2='checked'
            self.check3='checked'
            self.check4='checked'
            self.check5='unchecked'
        elif float(rating) >= 2.5:
            self.check1='checked'
            self.check2='checked'
            self.check3='checked'
            self.check4='unchecked'
            self.check5='unchecked'
        elif float(rating) >= 1.5:
            self.check1='checked'
            self.check2='checked'
            self.check3='unchecked'
            self.check4='unchecked'
            self.check5='unchecked'
        elif float(rating) >= 0.5:
            self.check1='checked'
            self.check2='unchecked'
            self.check3='unchecked'
            self.check4='unchecked'
            self.check5='unchecked'
        else:
            self.check1='unchecked'
            self.check2='unchecked'
            self.check3='unchecked'
            self.check4='unchecked'
            self.check5='unchecked'



@app.route("/search/book/<string:isbn>")
def show_book(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "TwjuR4yaZ1usv5rxii40Q", "isbns": isbn})
    data = res.json()
    average_rating = data["books"][0]["average_rating"]
    ratings_count = data["books"][0]["ratings_count"]
    isbn13 = data["books"][0]["isbn13"]
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
    year = book.year
    author = book.author
    title = book.title
    check = rate_count(average_rating)
    if 'user_id' in session:
        login = True
    else:
        login = False
    return render_template("book.html", average_rating=average_rating, ratings_count=ratings_count, isbn=isbn, isbn13=isbn13, year=year, author=author, title=title, check=check, login=login)


@app.route("/book/<string:isbn>/review_added", methods=['POST','GET'])
def add_review(isbn):
    rating = request.form.get('user_rating')
    review = request.form.get('user_review')
    if 'user_id' in session:
        login = True
        user_id = session['user_id']
        db.execute("INSERT INTO reviews (user_id,rating,isbn,reviews) VALUES (:user_id,:rating,:isbn,:review)",{"user_id":user_id,"rating":rating,"isbn":isbn,"review":review})
        db.commit()
        return render_template("message.html", message="Review Added", login=login)
    else:
        return redirect(url_for('login'))



@app.route("/book/<string:isbn>/reviews")
def reviews(isbn):
    reviews = db.execute("SELECT * FROM reviews WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
    if 'user_id' in session:
        login = True
    else:
        login = False
    return render_template("reviews.html", login=login, reviews = reviews)
