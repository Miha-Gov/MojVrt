# Uvoz potrebnih modulov
from flask_login import UserMixin  # Za podporo prijav
from database import db  # SQLAlchemy objekt

# Model za uporabnika
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # Enolični identifikator
    email = db.Column(db.String(120), unique=True, nullable=False)  # E-pošta (enolična)
    password = db.Column(db.LargeBinary(60), nullable=False)  # Šifrirano geslo
    gardens = db.relationship('Garden', backref='user', lazy=True)  # Povezava z vrtovi uporabnika

# Model za vrt
class Garden(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Enolični identifikator
    name = db.Column(db.String(100), nullable=False)  # Ime vrta
    size = db.Column(db.Float, nullable=False)  # Velikost v m²
    sunlight = db.Column(db.String(50), nullable=False)  # Sončne razmere
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Povezava z uporabnikom