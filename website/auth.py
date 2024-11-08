from flask import Blueprint, render_template
from .forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash


auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        password_hash = generate_password_hash(form.password.data, method='scrypt')

    return render_template('auth/register.html', title='Inregistrare', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        return
    
    return render_template('auth/login.html', title='Autentificare', form=form)