from flask_wtf import FlaskForm
from wtforms import Form, SubmitField, StringField, BooleanField, FloatField, TextAreaField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, ValidationError, Length, Optional, URL
from wtforms.fields.html5 import URLField


class EditPricesForm(Form):
	name = StringField('Материал', validators = [DataRequired(message='Материал - обязательное поле.')])
	price = FloatField('Цена', validators = [DataRequired(message='Цена - обязательное поле.')])
	units = StringField('Единицы', validators = [Length(max = 30, message='Название не должно быть длиннее 30 символов.')])

class AddTagForm(Form):
	name = StringField('Тег', validators = [DataRequired(message='Тег - обязательное поле.')])
	prices = FieldList(FormField(EditPricesForm))

class AddPlacemarkForm(FlaskForm):
	name = StringField('Название', validators = [DataRequired(message='Название  - обязательное поле.'), Length(max = 128, message='Название не должно быть длиннее 128 символов.')], id='addName')
	longitude = FloatField('Долгота', validators = [DataRequired(message='Долгота  - обязательное поле.')], id='addLongitude')
	latitude = FloatField('Широта', validators = [DataRequired(message='Широта  - обязательное поле.')], id='addLatitude')
	description = TextAreaField('Описание', validators = [Length(max = 128, message='Описание не должно быть длиннее 128 символов.')], id='addDescription')
	tags = FieldList(FormField(AddTagForm))
	is_vendor = BooleanField ('Поставщик', id='addIsVendor')
	price_url = URLField('URL прайса', id='addPriceURL', validators=[Optional(), URL(message='Некорректный URL.')])
	submit = SubmitField('Добавить', id='addSubmit')

			
class EditPlacemarkForm(FlaskForm):
	id = IntegerField('Идентификатор', validators = [DataRequired(message='Идентификатор  - обязательное поле.')], id = 'editId')
	description = TextAreaField('Описание', validators = [Length(max = 128, message='Описание не должно быть длиннее 128 символов.')], id = 'editDescription')
	name = StringField('Название', validators = [DataRequired(message='Название  - обязательное поле.'), Length(max = 128, message='Название не должно быть длиннее 128 символов.')], id='editName')
	price_url = URLField('URL прайса', id='editPriceURL', validators=[Optional(), URL(message='Некорректный URL.')])
	tags = FieldList(FormField(AddTagForm))
	submit = SubmitField('Сохранить', id = 'editSubmit')