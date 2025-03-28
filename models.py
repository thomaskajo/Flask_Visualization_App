from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    data = db.Column(db.Text, nullable=False)

class Chart(db.Model):
    name = db.Column(db.String(150), primary_key=True, nullable=False)
    x_axis = db.Column(db.Text, nullable=False)
    y_axis = db.Column(db.Text)
    type = db.Column(db.String(150))
    content = db.Column(db.Text)

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class CollectionFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
