# Uvoz potrebnih knjižnic
from flask import Flask, render_template, request, redirect, url_for, flash  # Flask za spletno aplikacijo, render_template za predloge, request za obdelavo obrazcev, redirect in url_for za preusmeritve, flash za sporočila
from flask_login import LoginManager, login_user, login_required, logout_user, current_user  # Flask-Login za upravljanje uporabniških sej
from database import db  # SQLAlchemy za povezavo z bazo podatkov
import bcrypt  # Za šifriranje gesel

# Inicializacija Flask aplikacije
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Skrivni ključ za varnost sej
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mojvrt.db'  # Pot do SQLite baze podatkov
db.init_app(app)  # Povezava SQLAlchemy z aplikacijo
login_manager = LoginManager(app)  # Inicializacija upravljalnika prijav
login_manager.login_view = 'login'  # Določitev strani za prijavo

# Uvoz modelov (User, Garden) iz models.py
from models import User, Garden

# Ustvarjanje tabel v bazi podatkov
with app.app_context():
    db.create_all()

# Funkcija za nalaganje uporabnika iz seje
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Vrni uporabnika z danim ID-jem iz baze

# Seznam priporočil za sajenje z imenom rastline, združljivimi rastlinami, minimalno velikostjo in zahtevami za sonce
RECOMMENDATIONS = [
    {"ime": "Paradižnik", "združljiv_z": ["Bazilika", "Korenje", "Čebula"], "min_size": 2.0, "sunlight": "močno sonce"},
    {"ime": "Bazilika", "združljiv_z": ["Paradižnik", "Paprika"], "min_size": 0.5, "sunlight": "močno sonce"},
    {"ime": "Korenje", "združljiv_z": ["Paradižnik", "Čebula"], "min_size": 1.0, "sunlight": "močno sonce"},
    {"ime": "Paprika", "združljiv_z": ["Bazilika"], "min_size": 2.0, "sunlight": "močno sonce"},
    {"ime": "Bučke", "združljiv_z": ["Koruza"], "min_size": 4.0, "sunlight": "močno sonce"},
    {"ime": "Koruza", "združljiv_z": ["Bučke", "Fižol"], "min_size": 5.0, "sunlight": "močno sonce"},
    {"ime": "Fižol", "združljiv_z": ["Koruza"], "min_size": 2.0, "sunlight": "močno sonce"},
    {"ime": "Solata", "združljiv_z": ["Redkvice"], "min_size": 1.0, "sunlight": "delna senca"},
    {"ime": "Redkvice", "združljiv_z": ["Solata", "Korenje"], "min_size": 0.5, "sunlight": "delna senca"},
    {"ime": "Kumare", "združljiv_z": ["Fižol"], "min_size": 3.0, "sunlight": "močno sonce"}
]

# Pot za domačo stran
@app.route('/')
def home():
    return render_template('base.html')  # Prikaz osnovne predloge

# Pot za prijavo uporabnika
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Obdelava obrazca, če je poslan
        email = request.form['email']  # Pridobitev e-pošte iz obrazca
        password = request.form['password'].encode('utf-8')  # Pridobitev gesla in kodiranje v bajte
        user = User.query.filter_by(email=email).first()  # Iskanje uporabnika v bazi
        if user and bcrypt.checkpw(password, user.password):  # Preverjanje gesla
            login_user(user)  # Prijava uporabnika
            return redirect(url_for('garden'))  # Preusmeritev na stran z vrti
        flash('Napačen email ali geslo.')  # Sporočilo ob napaki
    return render_template('login.html')  # Prikaz strani za prijavo

# Pot za registracijo novega uporabnika
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Obdelava obrazca
        email = request.form['email']  # Pridobitev e-pošte
        password = request.form['password'].encode('utf-8')  # Pridobitev gesla
        if User.query.filter_by(email=email).first():  # Preverjanje, ali e-pošta že obstaja
            flash('Email že obstaja.')  # Sporočilo ob napaki
        else:
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())  # Šifriranje gesla
            new_user = User(email=email, password=hashed_password)  # Ustvarjanje novega uporabnika
            db.session.add(new_user)  # Dodajanje v bazo
            db.session.commit()  # Shranjevanje sprememb
            return redirect(url_for('login'))  # Preusmeritev na prijavo
    return render_template('register.html')  # Prikaz strani za registracijo

# Pot za upravljanje vrtov (dodajanje in prikaz)
@app.route('/garden', methods=['GET', 'POST'])
@login_required  # Zahteva prijavljenega uporabnika
def garden():
    if request.method == 'POST':  # Obdelava obrazca za dodajanje vrta
        name = request.form['name']  # Pridobitev imena vrta
        size = float(request.form['size'])  # Pridobitev velikosti (pretvorba v število)
        sunlight = request.form['sunlight']  # Pridobitev sončnih razmer
        if name and size > 0:  # Preverjanje veljavnosti podatkov
            new_garden = Garden(name=name, size=size, sunlight=sunlight, user_id=current_user.id)  # Ustvarjanje novega vrta
            db.session.add(new_garden)  # Dodajanje v bazo
            db.session.commit()  # Shranjevanje sprememb
            return redirect(url_for('garden'))  # Osvežitev strani
        flash('Neveljavni podatki.')  # Sporočilo ob napaki
    
    gardens = Garden.query.filter_by(user_id=current_user.id).all()  # Pridobitev vseh vrtov trenutnega uporabnika
    filtered_recommendations = []  # Seznam za filtrirana priporočila
    for garden in gardens:  # Za vsak vrt
        garden_recs = []  # Seznam priporočil za posamezen vrt
        for rec in RECOMMENDATIONS:  # Preverjanje vsakega priporočila
            if rec['min_size'] <= garden.size and rec['sunlight'] == garden.sunlight:  # Filtriranje po velikosti in soncu
                num_plants = int(garden.size / rec['min_size'])  # Izračun števila rastlin
                garden_recs.append({  # Dodajanje priporočila z dodatnimi podatki
                    "ime": rec["ime"],
                    "združljiv_z": rec["združljiv_z"],
                    "num_plants": num_plants
                })
        filtered_recommendations.append({"garden": garden, "recommendations": garden_recs})  # Dodajanje vrtov in priporočil
    
    return render_template('garden.html', gardens=gardens, filtered_recommendations=filtered_recommendations)  # Prikaz strani

# Pot za urejanje vrta
@app.route('/edit_garden/<int:garden_id>', methods=['GET', 'POST'])
@login_required
def edit_garden(garden_id):
    garden = Garden.query.get_or_404(garden_id)  # Pridobitev vrta ali napaka 404
    if garden.user_id != current_user.id:  # Preverjanje lastništva
        flash('Nimate dovoljenja za urejanje tega vrta.')
        return redirect(url_for('garden'))
    
    if request.method == 'POST':  # Obdelava obrazca za urejanje
        name = request.form['name']  # Novi podatki
        size = float(request.form['size'])
        sunlight = request.form['sunlight']
        if name and size > 0:  # Preverjanje veljavnosti
            garden.name = name  # Posodobitev podatkov
            garden.size = size
            garden.sunlight = sunlight
            db.session.commit()  # Shranjevanje sprememb
            flash('Vrt je bil uspešno posodobljen.')
            return redirect(url_for('garden'))
        flash('Neveljavni podatki.')
    
    return render_template('edit_garden.html', garden=garden)  # Prikaz obrazca za urejanje

# Pot za brisanje vrta
@app.route('/delete_garden/<int:garden_id>', methods=['POST'])
@login_required
def delete_garden(garden_id):
    garden = Garden.query.get_or_404(garden_id)  # Pridobitev vrta
    if garden.user_id != current_user.id:  # Preverjanje lastništva
        flash('Nimate dovoljenja za brisanje tega vrta.')
        return redirect(url_for('garden'))
    db.session.delete(garden)  # Brisanje vrta
    db.session.commit()  # Shranjevanje sprememb
    flash('Vrt je bil uspešno izbrisan.')
    return redirect(url_for('garden'))

# Pot za odjavo
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Odjava uporabnika
    return redirect(url_for('login'))  # Preusmeritev na prijavo

# Pot za API priporočil (trenutno neuporabljena)
@app.route('/api/recommendations')
@login_required
def api_recommendations():
    return jsonify(RECOMMENDATIONS)  # Vrnitev priporočil v JSON formatu

# Zagon aplikacije
if __name__ == '__main__':
    app.run(debug=True)  # Zagon v razvojnem načinu