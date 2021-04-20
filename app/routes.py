from flask import Blueprint, request, render_template, url_for, redirect, session, flash
from functools import wraps
from database import db
from models import User
from models import Pool
from models import BankAccount

#
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
    # If the user is already logged in, redirect them to dashboard.html
    if "logged_in" in session:
        return redirect(url_for(".index"))

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
                # Grant the user the required session variables
                session["logged_in"] = True
                session["first_name"] = user_query.firstname
                session["last_name"] = user_query.lastname
                session["username"] = user_query.username

                # TODO: add if statement to determine whether or not the user is a bank manager
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
    # Pop all session variables that are given to logged in users
    session.pop("logged_in", None)
    session.pop("first_name", None)
    session.pop("last_name", None)
    session.pop("username", None)
    return redirect(url_for(".index"))


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
            session["first_name"] = user.firstname
            session["last_name"] = user.lastname
            session["username"] = user.username
            db.session.add(user)
            db.session.commit()
            return redirect(url_for(".index"))

    # If the user simply accesses the page or refreshes, serve the signup.html page
    return render_template("signup.html", error=error)


#
@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    return render_template("dashboard.html")


# Retrieves and renders poolBrowser.html when a GET method is performed
@main.route("/poolBrowser", methods=["GET", "POST"])
@login_required
def poolBrowser():
    # Set to "All" by default so that pools of all categories show up unless specifically requested by user
    chosenCategory = "All"

    # Query the pool table for a list of all categories found in the category field
    categoryQuery = [item[0] for item in Pool.query.with_entities(Pool.category)]
    # Remove duplicates from the list
    categories = []
    for c in categoryQuery:
        if c not in categories:
            categories.append(c)

    # Query the pool table for a list of all pools
    pools = Pool.query.all()

    # POST occurs when the user clicks the "go" button to switch categories
    if request.method == "POST":
        # Set the chosenCategory variable to whatever the user chose from the drop down list
        chosenCategory = request.form.get("categoryList")

        # If the user selected "All", simply launch the webpage without filtering pools
        if chosenCategory == "All":
            return render_template("poolBrowser.html", chosenCategory=chosenCategory, categories=categories, pools=pools)

        # Loop through the list of pools and only keep pools which match the chosen category
        temp = []
        for pool in pools:
            if pool.category == chosenCategory:
                temp.append(pool)
        pools = temp

    return render_template("poolBrowser.html", chosenCategory=chosenCategory, categories=categories, pools=pools)


#
@main.route("/accountManagement", methods=["GET", "POST"])
@login_required
def accountManagement():
    return render_template("accountManagement.html")


#
@main.route("/bankManagement", methods=["GET", "POST"])
@login_required
def bankManagement():
    return render_template("bankManagement.html")