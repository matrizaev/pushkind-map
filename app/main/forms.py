from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField
from wtforms.validators import DataRequired

class AddPlacemarkForm(FlaskForm):
	name = StringField('Название', validators = [DataRequired()])
	coordinates = StringField('Координаты', validators = [DataRequired()])
	tags = StringField('Тэги', validators = [DataRequired()])
	is_vendor = BooleanField ('Вендор', validators=[DataRequired()])
	submitField = SubmitField('Добавить')