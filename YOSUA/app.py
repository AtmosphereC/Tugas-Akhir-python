from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kamus-pintar-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kamus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = 'development'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    words = db.relationship('Word', backref='author', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), unique=True, nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('signup'))
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dictionary'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dictionary', methods=['GET', 'POST'])
@login_required
def dictionary():
    if request.method == 'POST':
        search_word = request.form.get('search')
        word = Word.query.filter_by(word=search_word.lower()).first()
        return render_template('dictionary.html', word=word, search=search_word)
    return render_template('dictionary.html')

@app.route('/add_word', methods=['GET', 'POST'])
@login_required
def add_word():
    if request.method == 'POST':
        word = request.form.get('word')
        meaning = request.form.get('meaning')
        example = request.form.get('example')
        
        if Word.query.filter_by(word=word.lower()).first():
            flash('Word already exists!')
            return redirect(url_for('add_word'))
        
        new_word = Word(word=word.lower(), meaning=meaning, example=example, user_id=current_user.id)
        db.session.add(new_word)
        db.session.commit()
        flash('Word added successfully!')
        return redirect(url_for('dictionary'))
        
    return render_template('add_word.html')

@app.route('/word_list')
@login_required
def word_list():
    words = Word.query.all()
    return render_template('word_list.html', words=words)

@app.route('/delete_word/<int:word_id>')
@login_required
def delete_word(word_id):
    word = Word.query.get_or_404(word_id)
    if word.user_id == current_user.id:
        db.session.delete(word)
        db.session.commit()
        flash('Kata berhasil dihapus!')
    else:
        flash('Anda tidak memiliki izin untuk menghapus kata ini!')
    return redirect(url_for('word_list'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)