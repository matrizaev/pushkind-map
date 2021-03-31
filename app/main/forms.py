from flask_wtf import FlaskForm
from wtforms import Form, SubmitField, StringField, BooleanField, FloatField, TextAreaField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, ValidationError, Length, Optional, URL
from wtforms.fields.html5 import URLField
from flask_wtf.file import FileField, FileRequired, FileAllowed

class AddPlacemarkForm(FlaskForm):
	name = StringField('Название', validators = [DataRequired(message='Название  - обязательное поле.'), Length(max = 128, message='Название не должно быть длиннее 128 символов.')], id='addName')
	longitude = FloatField('Долгота', validators = [DataRequired(message='Долгота  - обязательное поле.')], id='addLongitude')
	latitude = FloatField('Широта', validators = [DataRequired(message='Широта  - обязательное поле.')], id='addLatitude')
	description = TextAreaField('Описание', validators = [Length(max = 128, message='Описание не должно быть длиннее 128 символов.')], id='addDescription')
	is_vendor = BooleanField ('Поставщик', id='addIsVendor')
	price_url = URLField('URL прайса', id='addPriceURL')
	submit = SubmitField('Добавить', id='addSubmit')

	def validate_price_url(self, field):
		if self.is_vendor.data is True and len(field.data) == 0:
			raise ValidationError('URL прайса - обязательное поле.')

class SyncPlacemarksForm(FlaskForm):
	url = URLField('URL меток', id='syncPlacemarksURL', validators=[DataRequired(message='URL меток  - обязательное поле.'),URL(message='Некорректный URL.')])
	submit = SubmitField('Синхронизация', id='syncSubmit')
	
class ImportPlacemarksForm(FlaskForm):
	placemarks = FileField (label = 'Метки', id='importPlacemarks', validators=[FileRequired(), FileAllowed(['xlsx'], 'Разрешены только XLSX.')])
	submit = SubmitField('Загрузить')