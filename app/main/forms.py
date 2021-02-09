from flask_wtf import FlaskForm
from wtforms import Form, SubmitField, StringField, BooleanField, FloatField, TextAreaField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, ValidationError, Length, Optional, URL
from wtforms.fields.html5 import URLField


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
			
class EditPlacemarkForm(FlaskForm):
	id = IntegerField('Идентификатор', validators = [DataRequired(message='Идентификатор  - обязательное поле.')], id = 'editId')
	description = TextAreaField('Описание', validators = [Length(max = 128, message='Описание не должно быть длиннее 128 символов.')], id = 'editDescription')
	name = StringField('Название', validators = [DataRequired(message='Название  - обязательное поле.'), Length(max = 128, message='Название не должно быть длиннее 128 символов.')], id='editName')
	price_url = URLField('URL прайса', id='editPriceURL', validators=[DataRequired(message='URL прайса  - обязательное поле.'),URL(message='Некорректный URL.')])
	submit = SubmitField('Сохранить', id = 'editSubmit')