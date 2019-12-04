from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, FloatField
from wtforms.validators import DataRequired, ValidationError, Length
import re

class AddPlacemarkForm(FlaskForm):
	name = StringField('Название', validators = [DataRequired(), Length(max = 128)])
	longitude = FloatField('Долгота', validators = [DataRequired()])
	latitude = FloatField('Широта', validators = [DataRequired()])
	description = StringField('Описание', validators = [Length(max = 128)])
	tags = StringField('Тэги')
	is_vendor = BooleanField ('Поставщик')
	price = FloatField('Цена')
	submit = SubmitField('Добавить')
	
	def validate_tags(self, tags):
		if self.is_vendor.data:
			if not re.fullmatch('\s*\w+((\s*,\s*|\s+)\w+)*', tags.data):
				raise ValidationError('Теги - это слова, разделённые пробелами или запятыми.')