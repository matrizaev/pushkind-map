from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, FloatField
from wtforms.validators import DataRequired, ValidationError, Length
import re

class AddPlacemarkForm(FlaskForm):
	name = StringField('Название', validators = [DataRequired(message='Название  - обязательное поле.'), Length(max = 128, message='Название не должно быть длиннее 128 символов.')])
	longitude = FloatField('Долгота', validators = [DataRequired(message='Долгота  - обязательное поле.')])
	latitude = FloatField('Широта', validators = [DataRequired(message='Широта  - обязательное поле.')])
	description = StringField('Описание', validators = [Length(max = 128, message='Описание не должно быть длиннее 128 символов.')])
	tags = StringField('Тэги')
	is_vendor = BooleanField ('Поставщик')
	price = FloatField('Цена')
	submit = SubmitField('Добавить')
	
	def validate_tags(self, tags):
		if self.is_vendor.data:
			if not re.fullmatch('\s*\w+((\s*,\s*|\s+)\w+)*', tags.data):
				raise ValidationError('Теги - это слова, разделённые пробелами или запятыми.')