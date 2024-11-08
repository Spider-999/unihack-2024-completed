from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email


class RegisterForm(FlaskForm):
    username = StringField('Nume Utilizator', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    user_role = SelectField('Rol', )
    submit = SubmitField('Creeaza contul', choices=['Elev', 'Profesor'], validators=[DataRequired()], default='Elev')