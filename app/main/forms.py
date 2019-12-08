from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, FloatField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Length
import re

class AddPlacemarkForm(FlaskForm):
	name = StringField('Название', validators = [DataRequired(message='Название  - обязательное поле.'), Length(max = 128, message='Название не должно быть длиннее 128 символов.')], id='addName')
	longitude = FloatField('Долгота', validators = [DataRequired(message='Долгота  - обязательное поле.')], id='addLongitude')
	latitude = FloatField('Широта', validators = [DataRequired(message='Широта  - обязательное поле.')], id='addLatitude')
	description = TextAreaField('Описание', validators = [Length(max = 128, message='Описание не должно быть длиннее 128 символов.')], id='addDescription')
	tags = StringField('Тэги', id='addTags')
	is_vendor = BooleanField ('Поставщик', id='addIsVendor')
	price = FloatField('Цена', id='addPrice')
	submit = SubmitField('Добавить', id='addSubmit')
	
	def validate_tags(self, tags):
		if self.is_vendor.data:
			if not re.fullmatch('\s*\w+((\s*,\s*|\s+)\w+)*', tags.data):
				raise ValidationError('Теги - это слова, разделённые пробелами или запятыми.')
				
class EditPlacemarkForm(FlaskForm):
	id = IntegerField('Идентификатор', validators = [DataRequired(message='Идентификатор  - обязательное поле.')], id = 'editId')
	description = TextAreaField('Описание', validators = [Length(max = 128, message='Описание не должно быть длиннее 128 символов.')], id = 'editDescription')
	price = FloatField('Цена', id = 'editPrice')
	submit = SubmitField('Сохранить', id = 'editSubmit')