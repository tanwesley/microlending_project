from database import db


# The User model will be used to store any given user's information within the database
# Putting "db.Model" in the parentheses below tells SQLAlchemy to store all the information within this object
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # SQLAlchemy requires primary keys
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, firstname, lastname, username, password):
        self.firstname = firstname
        self.lastname = lastname
        self.username = username
        self.password = password

    # TODO: add encryption and decryption functions for the password


#
class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(100))
    amount = db.Column(db.Float)

    def __init__(self, name, category, amount):
        self.name = name
        self.category = category
        self.amount = amount
