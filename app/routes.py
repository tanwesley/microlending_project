from flask import Blueprint, request, render_template, url_for, redirect, session, flash
from functools import wraps
from database import db
from models import User

main = Blueprint('main', __name__)


# Creates a decorator which indicates that the page accessed requires a login
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first.")
            return redirect(url_for(".login"))

    return wrap


# Retrieves and renders index.html whenever the server is accessed without a specific page defined
@main.route("/")
def index():
    return render_template("index.html")


# Retrieves and renders login.html whenever user accesses /login if GET method is performed
# Checks to see if the user's credentials are valid if POST method is performed
@main.route("/login", methods=["GET", "POST"])
def login():
    # If an error occurs, this will be set to a string with an error message
    error = None

    # If the user submits the form
    if request.method == "POST":
        # Get the user's sign in information from the text boxes
        username = request.form["username"]
        password = request.form["password"]

        # Find the user in the database based on the username they entered
        user_query = User.query.filter_by(username=username).first()

        # If the user is found in the database set a session variable indicating they are logged in
        # then redirect them to the proper page
        if user_query:
            # Check if the password in the database matches the password that was entered
            if password == user_query.password:
                session["logged_in"] = True
                flash("Login Successful: \n" + user_query.firstname + "\n" + user_query.lastname + "\n" + user_query.username)
                return redirect(url_for(".index"))
            else:
                error = "Username/password is incorrect. Please try again."
        else:
            error = "Username/password is incorrect. Please try again."

    return render_template("login.html", error=error)


# Removes the "logged_in" session variable from the user, making it so they cannot
# access pages which require it (ie use the @login_required decorator)
@main.route("/logout")
@login_required
def logout():
    session.pop("logged_in", None)
    return redirect(url_for(".main"))


# Retrieves and renders signup.html when a GET method is performed
# Checks for required information in the text boxes, gathers the info, and creates a database
# entry for the user's new account
@main.route("/signup", methods=["GET", "POST"])
def signup():
    # If the username entered by the user is already in use, this variable will change to an error
    # message which will be displayed on the template
    error = None

    # If the user submits the form
    if request.method == "POST":
        # Gather all data needed and put it into the User model
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        username = request.form["username"]
        password = request.form["password"]

        # Make sure each of the text boxes are filled with the required information
        # If not, give the user an error message
        if firstname == "" or lastname == "" or username == "" or password == "":
            error = "Please fill out each text box to continue."
            return render_template("signup.html", error=error)

        # Make a User model with the information provided by the user
        user = User(firstname, lastname, username, password)

        # Checks if the username entered is already in the database
        found_user = User.query.filter_by(username=username).first()

        # If the username already exists, notify the user via dynamic HTML
        # Otherwise the user will be added to the database and redirected to the main page
        if found_user:
            error = "This username has already been taken! Please try again."
        else:
            session["logged_in"] = True
            db.session.add(user)
            db.session.commit()
            return redirect(url_for(".index"))

    # If the user simply accesses the page or refreshes, serve the signup.html page
    return render_template("signup.html", error=error)