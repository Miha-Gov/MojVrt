from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user
from database import db
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mojvrt.db'
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import User

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password, user.password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Napačen email ali geslo.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        if User.query.filter_by(email=email).first():
            flash('Email že obstaja.')
        else:
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            new_user = User(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)