from flask import Blueprint, request, render_template, url_for, redirect, session, flash
from functools import wraps
from database import db
from models import User, PoolContribution, LoanRequest
from models import Pool
from models import BankAccount
import bcrypt

#
main = Blueprint('main', __name__)


# Creates a decorator which indicates that the page accessed requires a login
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for(".login"))

    return wrap


# Creates a decorator which indicates that the page accessed requires the user to be a bank manager
def bank_manager_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" in session:
            user = User.query.filter_by(id=session["user_id"]).first()
            if user.isBankManager:
                return f(*args, **kwargs)
            else:
                return redirect(url_for(".index"))
        else:
            return redirect(url_for(".index"))

    return wrap


# Retrieves and renders index.html whenever the server is accessed without a specific page defined
@main.route("/")
def index():
    if "logged_in" in session:
        return redirect(url_for(".dashboard"))
    else:
        return render_template("index.html")


# Retrieves and renders login.html whenever user accesses /login if GET method is performed
# Checks to see if the user's credentials are valid if POST method is performed
@main.route("/login", methods=["GET", "POST"])
def login():
    # If the user is already logged in, redirect them to dashboard.html
    if "logged_in" in session:
        return redirect(url_for(".dashboard"))

    # If an error occurs, this will be set to a string with an error message
    error = None

    # If the user submits the form
    if request.method == "POST":
        # Get the user's sign in information from the text boxes
        username = request.form["username"]
        password = request.form["password"]

        # If either of the text boxes were left empty, give the user an error message
        if username == "" or password == "":
            error = "Please fill out the required fields"
            return render_template("login.html", error=error)

        # Find the user in the database based on the username they entered
        user = User.query.filter_by(username=username).first()

        # If the user is found in the database set a session variable indicating they are logged in
        # then redirect them to the proper page
        if user:
            # Check if the password in the database matches the password that was entered
            if bcrypt.checkpw(password.encode("utf-8"), user.password):
                # Grant the user the required session variables
                session["logged_in"] = True
                session["user_id"] = user.id
                session["active_bank_account_id"] = user.bank_accounts[0].id

                return redirect(url_for(".index"))
            else:
                error = "Username/password is incorrect. Please try again"
        else:
            error = "Username/password is incorrect. Please try again."

    return render_template("login.html", error=error)


# Removes session variables from the user:
# - "logged_in" which would allow the user to access pages which require the user to be logged in
# - "user_id" which allowed the user's information to be accessed from the database from anywhere
@main.route("/logout")
@login_required
def logout():
    session.pop("logged_in", None)
    session.pop("user_id", None)
    session.pop("active_bank_account_id", None)
    return redirect(url_for(".index"))


# Retrieves and renders signup.html when the user navigates to /signup
# - Processes information from the form if filled out correctly. This information is used to create a user account
#   in the database. Once that is done, the user is given the "logged_in" and "user_id" session variables
# - If the form is not filled out correctly or the username is already taken, an error message is displayed for the user
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

        # Encrypt the password provided by the user before creating the database model
        password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Make a User model with the information provided by the user
        user = User(firstname, lastname, username, password)

        # Checks if the username entered is already in the database
        found_user = User.query.filter_by(username=username).first()

        # If the username already exists, notify the user via dynamic HTML
        # Otherwise the user will be added to the database and redirected
        if found_user:
            error = "This username has already been taken! Please try again."
        else:
            # Add the user to the database
            db.session.add(user)
            db.session.commit()

            # Retrieve the user from the database so that the user's ID can be accessed and assigned to a session var
            user = User.query.filter_by(username=username).first()
            session["logged_in"] = True
            session["user_id"] = user.id

            # Create a default bank account for the user
            defaultAccount = BankAccount("Checking", 0, user.id)
            db.session.add(defaultAccount)
            db.session.commit()

            # Retrieve the bank account from the user model so it can be assigned to a session var
            session["active_bank_account_id"] = user.bank_accounts[0].id

            # Redirect to the dashboard
            return redirect(url_for(".dashboard"))

    # If the user simply accesses the page or refreshes, serve the signup.html page
    return render_template("signup.html", error=error)


#
@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    # Get current user from database
    user = User.query.filter_by(id=session["user_id"]).first()

    return render_template("dashboard.html", isBankManager=user.isBankManager)


# Retrieves and renders poolBrowser.html when a GET method is performed
@main.route("/poolBrowser", methods=["GET", "POST"])
@login_required
def poolBrowser():
    # Get current user from database
    user = User.query.filter_by(id=session["user_id"]).first()

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
            return render_template("poolBrowser.html", chosenCategory=chosenCategory, categories=categories,
                                   pools=pools, isBankManager=user.isBankManager)

        # Loop through the list of pools and only keep pools which match the chosen category
        temp = []
        for pool in pools:
            if pool.category == chosenCategory:
                temp.append(pool)
        pools = temp

    return render_template("poolBrowser.html", chosenCategory=chosenCategory, categories=categories,
                           pools=pools, isBankManager=user.isBankManager)


@main.route("/contributeToPool", methods=["POST"])
@login_required
def contributeToPool():
    # Get the pool being used from the template
    poolId = request.form.get("poolId")
    pool = Pool.query.filter_by(id=poolId).first()

    # Get the user from session variable
    user = User.query.filter_by(id=session["user_id"]).first()

    # Get the active bank account using the session variable
    bankAccount = BankAccount.query.filter_by(id=session["active_bank_account_id"]).first()

    # Get the amount from the textbox
    amountContributed = float(request.form.get("contribute"))

    # If the amount contributed is greater than the amount the user has in their bank account, give error message
    if amountContributed > bankAccount.micro_dollars:
        flash("You do not have enough in your account to make that contribution!")
        return redirect(url_for(".poolBrowser"))

    # Add the amount to the pool amount
    # Subtract the amount from the user's bank account
    # Create a new pool contribution
    pool.amount = pool.amount + amountContributed
    bankAccount.micro_dollars = bankAccount.micro_dollars - amountContributed
    poolContribution = PoolContribution(amountContributed, user.id, pool.id)
    db.session.add(poolContribution)
    db.session.commit()

    return redirect(url_for(".poolBrowser"))


@main.route("/requestFromPool", methods=["POST"])
@login_required
def requestFromPool():
    # Get the pool being used from the template
    poolId = request.form.get("poolId")
    pool = Pool.query.filter_by(id=poolId).first()

    # Get the user from session variable
    user = User.query.filter_by(id=session["user_id"]).first()

    # Get the active bank account using the session variable
    bankAccount = BankAccount.query.filter_by(id=session["active_bank_account_id"]).first()

    # Get the amount from the textbox
    amountRequested = float(request.form.get("request"))

    # If the amount requested is greater than the amount in the pool, give error message
    if amountRequested > pool.amount:
        flash("The pool does not have enough in it for this request!")
        return redirect(url_for(".poolBrowser"))

    # Create a loan request in the database
    loanRequest = LoanRequest(amountRequested, user.id, bankAccount.id, pool.id)
    db.session.add(loanRequest)
    db.session.commit()

    return redirect(url_for(".poolBrowser"))


#
@main.route("/accountManagement", methods=["GET", "POST"])
@login_required
def accountManagement():
    # Get current user from database
    user = User.query.filter_by(id=session["user_id"]).first()
    bankAccount = BankAccount.query.filter_by(id=session["active_bank_account_id"]).first()

    return render_template("accountManagement.html", user=user, bankAccount=bankAccount,
                           isBankManager=user.isBankManager)


#
@main.route("/bankManagement", methods=["GET", "POST"])
@login_required
@bank_manager_required
def bankManagement():
    # Get current user from database
    user = User.query.filter_by(id=session["user_id"]).first()

    return render_template("bankManagement.html", isBankManager=user.isBankManager)