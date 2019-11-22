from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, FloatField
from wtforms.validators import ValidationError, DataRequired, Email
from wtforms.fields.html5 import EmailField
from flask_wtf.file import FileField, FileRequired, FileAllowed

