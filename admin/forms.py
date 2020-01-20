from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class SaleForm(FlaskForm):
    """Contact form."""
    sale = IntegerField('Sale', validators=[DataRequired()])
    submit = SubmitField('Применить ко всем пользователям')

