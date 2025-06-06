# Uvoz potrebnih modulov
from flask_login import UserMixin
from database import db

# Model za uporabnika
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.LargeBinary(60), nullable=False)
    gardens = db.relationship('Garden', backref='user', lazy=True)

# Model za vrt z novimi polji
class Garden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Float, nullable=False)
    sunlight = db.Column(db.String(50), nullable=False)
    soil_type = db.Column(db.String(50), nullable=False)  # Novo: tip tal
    wind_exposure = db.Column(db.String(50), nullable=False)  # Novo: izpostavljenost vetru
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)