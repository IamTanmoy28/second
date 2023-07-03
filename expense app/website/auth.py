from flask import Blueprint, render_template, request,flash,redirect,url_for
from .models import User
from . import db
from .views import views
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        bank_balance = float(request.form.get('bank_balance'))
        confirm_bank_balance=float(request.form.get('confirm_bank_balance'))
        user = User.query.filter_by(email=email).first()
        flash_messages = []

        if user:
            flash_messages.append('Email already exists.')

        if password != confirm_password:
            flash_messages.append('Passwords do not match!')

        if confirm_bank_balance != bank_balance:
            flash_messages.append('Bank balance does not match')

        if bank_balance <= 0:
            flash_messages.append('Invalid amount!')

        if not flash_messages:
            new_user = User(email=email, username=username, bank_balance=bank_balance, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            return redirect(url_for('views.transaction'))
        
        
        for message in flash_messages:
            flash(message, 'error')

    return render_template('sign_up.html')

@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password,password):
                login_user(user, remember=True)
                return redirect(url_for('views.dashboard'))
            else:
                flash('Incorrect Password.','error')
        else:
            flash('Email doesnt exist.','error')


    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
