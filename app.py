# Uvoz potrebnih knjižnic
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import db
import bcrypt

# Inicializacija aplikacije
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mojvrt.db'
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from models import User, Garden

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Razširjen seznam priporočil z novimi lastnostmi: čas sajenja in tip tal
RECOMMENDATIONS = [
    {"ime": "Paradižnik", "združljiv_z": ["Bazilika", "Korenje", "Čebula"], "min_size": 2.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["srednje težka", "lahka"]},
    {"ime": "Bazilika", "združljiv_z": ["Paradižnik", "Paprika"], "min_size": 0.5, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["lahka"]},
    {"ime": "Korenje", "združljiv_z": ["Paradižnik", "Čebula"], "min_size": 1.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["lahka", "peščena"]},
    {"ime": "Paprika", "združljiv_z": ["Bazilika"], "min_size": 2.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["srednje težka"]},
    {"ime": "Bučke", "združljiv_z": ["Koruza"], "min_size": 4.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["težka", "srednje težka"]},
    {"ime": "Koruza", "združljiv_z": ["Bučke", "Fižol"], "min_size": 5.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["srednje težka"]},
    {"ime": "Fižol", "združljiv_z": ["Koruza"], "min_size": 2.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["lahka", "srednje težka"]},
    {"ime": "Solata", "združljiv_z": ["Redkvice"], "min_size": 1.0, "sunlight": "delna senca", "planting_time": "pomlad-jesen", "soil_type": ["lahka", "srednje težka"]},
    {"ime": "Redkvice", "združljiv_z": ["Solata", "Korenje"], "min_size": 0.5, "sunlight": "delna senca", "planting_time": "pomlad-jesen", "soil_type": ["lahka", "peščena"]},
    {"ime": "Kumare", "združljiv_z": ["Fižol"], "min_size": 3.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["srednje težka"]},
    {"ime": "Špinača", "združljiv_z": ["Solata", "Redkvice"], "min_size": 1.0, "sunlight": "delna senca", "planting_time": "pomlad-jesen", "soil_type": ["lahka"]},
    {"ime": "Čebula", "združljiv_z": ["Korenje", "Paradižnik"], "min_size": 1.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["lahka", "peščena"]},
    {"ime": "Drobnjak", "združljiv_z": ["Paradižnik"], "min_size": 0.5, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["lahka"]},
    {"ime": "Zelje", "združljiv_z": ["Fižol"], "min_size": 3.0, "sunlight": "močno sonce", "planting_time": "pomlad", "soil_type": ["težka", "srednje težka"]},
    {"ime": "Rukola", "združljiv_z": ["Solata"], "min_size": 0.5, "sunlight": "delna senca", "planting_time": "pomlad-jesen", "soil_type": ["lahka"]}
]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password, user.password):
            login_user(user)
            return redirect(url_for('garden'))
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

@app.route('/garden', methods=['GET', 'POST'])
@login_required
def garden():
    if request.method == 'POST':
        # Pridobitev novih polj iz obrazca
        name = request.form['name']
        size = float(request.form['size'])
        sunlight = request.form['sunlight']
        soil_type = request.form['soil_type']
        wind_exposure = request.form['wind_exposure']
        if name and size > 0:
            new_garden = Garden(
                name=name,
                size=size,
                sunlight=sunlight,
                soil_type=soil_type,
                wind_exposure=wind_exposure,
                user_id=current_user.id
            )
            db.session.add(new_garden)
            db.session.commit()
            return redirect(url_for('garden'))
        flash('Neveljavni podatki.')
    
    gardens = Garden.query.filter_by(user_id=current_user.id).all()
    filtered_recommendations = []
    for garden in gardens:
        garden_recs = []
        for rec in RECOMMENDATIONS:
            # Filtriranje priporočil glede na več kriterijev
            if (rec['min_size'] <= garden.size and
                rec['sunlight'] == garden.sunlight and
                garden.soil_type in rec['soil_type'] and
                (garden.wind_exposure != "visoka" or rec['ime'] not in ["Bazilika", "Drobnjak"])):  # Nekatere rastline ne prenesejo vetra
                num_plants = int(garden.size / rec['min_size'])
                garden_recs.append({
                    "ime": rec["ime"],
                    "združljiv_z": rec["združljiv_z"],
                    "num_plants": num_plants,
                    "planting_time": rec["planting_time"]
                })
        filtered_recommendations.append({"garden": garden, "recommendations": garden_recs})
    
    return render_template('garden.html', gardens=gardens, filtered_recommendations=filtered_recommendations)

@app.route('/edit_garden/<int:garden_id>', methods=['GET', 'POST'])
@login_required
def edit_garden(garden_id):
    garden = Garden.query.get_or_404(garden_id)
    if garden.user_id != current_user.id:
        flash('Nimate dovoljenja za urejanje tega vrta.')
        return redirect(url_for('garden'))
    
    if request.method == 'POST':
        name = request.form['name']
        size = float(request.form['size'])
        sunlight = request.form['sunlight']
        soil_type = request.form['soil_type']
        wind_exposure = request.form['wind_exposure']
        if name and size > 0:
            garden.name = name
            garden.size = size
            garden.sunlight = sunlight
            garden.soil_type = soil_type
            garden.wind_exposure = wind_exposure
            db.session.commit()
            flash('Vrt je bil uspešno posodobljen.')
            return redirect(url_for('garden'))
        flash('Neveljavni podatki.')
    
    return render_template('edit_garden.html', garden=garden)

@app.route('/delete_garden/<int:garden_id>', methods=['POST'])
@login_required
def delete_garden(garden_id):
    garden = Garden.query.get_or_404(garden_id)
    if garden.user_id != current_user.id:
        flash('Nimate dovoljenja za brisanje tega vrta.')
        return redirect(url_for('garden'))
    db.session.delete(garden)
    db.session.commit()
    flash('Vrt je bil uspešno izbrisan.')
    return redirect(url_for('garden'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/recommendations')
@login_required
def api_recommendations():
    return jsonify(RECOMMENDATIONS)

if __name__ == '__main__':
    app.run(debug=True)