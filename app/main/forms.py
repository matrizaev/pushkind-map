from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, FloatField
from wtforms.validators import DataRequired, ValidationError
import re

class AddPlacemarkForm(FlaskForm):
	name = StringField('Название', validators = [DataRequired()])
	longitude = FloatField('Долгота', validators = [DataRequired()])
	latitude = FloatField('Широта', validators = [DataRequired()])
	tags = StringField('Тэги')
	is_vendor = BooleanField ('Поставщик')
	submit = SubmitField('Добавить')
	
	def validate_tags(self, tags):
		if self.is_vendor.data:
			if not re.fullmatch('\w+((\s*,\s*|\s+)\w+)*', tags.data):
				raise ValidationError('Теги - это слова, разделённые пробелами или запятыми.')