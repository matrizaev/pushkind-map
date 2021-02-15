from app import db
from app.models import Placemark, Tag, Subtag, SubtagPlacemark
from flask import redirect, flash, render_template, request, url_for, escape, jsonify
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm, SyncPlacemarksForm
from flask import current_app

import gspread
from gspread.exceptions import NoValidUrlKeyFound, APIError

import pandas as pd

from sqlalchemy.exc import StatementError

@bp.route('/')
@bp.route('/index/')
@login_required
def ShowIndex():
	add_form = AddPlacemarkForm()
	sync_form = SyncPlacemarksForm()
	if 'search' in request.args:
		search = request.args.get('search')
		active_subtags = current_user.GetSearchedSubtags(search)
		active_tags = [st.tag_id for st in active_subtags]
	else:
		active_tags = request.args.getlist('tag', type=int)
		search = None
		active_subtags = current_user.GetActiveSubtags(active_tags)
		
	tags = current_user.GetTags()
		
	return render_template('index.html', add_form = add_form, sync_form = sync_form,
							active_tags = active_tags, search=search,
							tags = tags, active_subtags = active_subtags)
	
def RemovePlacemarkSubtags(placemark):
	SubtagPlacemark.query.filter(SubtagPlacemark.placemark_id == placemark.id).delete(synchronize_session='fetch')
	Subtag.query.filter(~Subtag.placemarks.any()).delete(synchronize_session='fetch')
	Tag.query.filter(~Tag.subtags.any()).delete(synchronize_session='fetch')

def GoogleTable2DataFrame(url):
	gc = gspread.service_account(filename=current_app.config['GOOGLE_DRIVE_ACCOUNT'])
	spreadsheet = gc.open_by_url(url)
	worksheet = spreadsheet.get_worksheet(0)
	data = worksheet.get_all_records()
	df = pd.DataFrame(data)
	return df

def SyncPlacemarkWithPrice(placemark):
	def SyncSubtags(placemark, tag, template):
		st_name = '{} / {}'.format(tag.name, template['subtag'].strip().lower().replace('/', '_'))
		st = Subtag.query.filter(Subtag.name == st_name, Subtag.tag == tag).first()
		if not st:
			st = Subtag(name = st_name)
			db.session.add(st)
			tag.subtags.append(st)
		subtag_placemark = SubtagPlacemark(price = template['price'], units = template['units'])
		subtag_placemark.placemark = placemark
		subtag_placemark.subtag = st
		db.session.add(subtag_placemark)
	try:
		df = GoogleTable2DataFrame(placemark.price_url)
		if not all([key in df.columns for key in ['tag', 'subtag', 'price', 'units']]) or len(df.index) == 0:
			raise TypeError
		df = df.groupby(by = ['tag', 'subtag'], as_index = False, sort = False).agg({'price':'first', 'units':'first'})
		for _tag_name in df.tag.unique():
			tag_name = _tag_name.strip().lower().replace('/', '_')
			tag = Tag.query.filter(Tag.name == tag_name).first()
			if not tag:
				tag = Tag(name = tag_name)
				db.session.add(tag)
			tag_df = df[df['tag'] == _tag_name]
			tag_df.apply(lambda row: SyncSubtags(placemark, tag, row), axis=1)
		return True
	except (NoValidUrlKeyFound, APIError, TypeError):
		return False

	
@bp.route('/sync/price/')
@login_required
def SyncPrice():
	id = request.args.get('id', type=int)
	placemark = Placemark.query.filter(Placemark.user_id == current_user.id, Placemark.id == id, Placemark.is_vendor == True, Placemark.price_url != None).first()
	if placemark is not None:
		RemovePlacemarkSubtags(placemark)
		if SyncPlacemarkWithPrice(placemark) is True:
			flash('Метка успешно синхронизирована с прайс-листом.')
			db.session.commit()
		else:
			db.session.rollback()
			flash('Не удалось синхронизировать метку с прайс-листом.')
	else:
		flash('Метка не может быть синхронизирована.')
	active_tags = request.args.getlist('tag', type=int)	
	return redirect(url_for('main.ShowIndex', tag=active_tags))
	

@bp.route('/sync/placemarks/', methods=['POST'])
@login_required
def SyncPlacemarks():
	form = SyncPlacemarksForm()
	if form.validate_on_submit():
		try:
			df = GoogleTable2DataFrame(form.url.data)
			if not all([key in df.columns for key in ['type', 'name', 'organization name', 'address', 'coordinates', 'contact', 'phone', 'email', 'presentation', 'website', 'price']]) or len(df.index) == 0:
				raise TypeError
				
			df = df.astype(str)
				
			endpoints = df[df['type'] == 'объект']
			vendors = df[df['type'] == 'поставщик']
			
			Placemark.query.filter(Placemark.user_id == current_user.id).delete()
			SubtagPlacemark.query.filter(~SubtagPlacemark.placemark.has()).delete(synchronize_session = 'fetch')
			Subtag.query.filter(~Subtag.placemarks.any()).delete(synchronize_session='fetch')
			Tag.query.filter(~Tag.subtags.any()).delete(synchronize_session='fetch')
			
			for index, endpoint in endpoints.iterrows():
				coordinates = endpoint['coordinates'].split(',')
				if len(coordinates) != 2:
					raise ValueError
				p = Placemark(name = endpoint['name'], longitude = coordinates[0], latitude = coordinates[1], user_id = current_user.id, sequence = index + 1)
				db.session.add(p)
				
			for index, vendor in vendors.iterrows():
				coordinates = vendor['coordinates'].split(',')
				if len(coordinates) != 2:
					raise ValueError
				p = Placemark(name = vendor['name'], longitude = coordinates[0], latitude = coordinates[1],
							  user_id = current_user.id, is_vendor = True, price_url = vendor['price'],
							  phone = vendor.get('phone', ''),
							  email = vendor.get('email', ''),
							  address = vendor.get('address', ''),
							  contact = vendor.get('contact', ''),
							  website = vendor.get('website', ''),
							  presentation = vendor.get('presentation', ''),
							  full_name = vendor.get('organization name', ''),
							  sequence = index + 1)
				db.session.add(p)
				if SyncPlacemarkWithPrice(p) is False:
					raise APIError
				
			db.session.commit()
			flash('Метки успешно синхронизированы.')
		except (NoValidUrlKeyFound, APIError, TypeError, ValueError, StatementError):
			db.session.rollback()
			flash('Некорректный URL или формат таблицы меток.')
	else:
		for error in form.url.errors:
			flash(error)
	active_tags = request.args.getlist('tag', type=int)
	return redirect(url_for('main.ShowIndex', tag=active_tags))
	

@bp.route('/remove/')
@login_required
def RemovePlacemark():
	id = request.args.get('id', type=int)
	placemark = Placemark.query.filter(Placemark.user_id == current_user.id, Placemark.id == id).first()
	if placemark is not None:
		RemovePlacemarkSubtags(placemark)
		db.session.delete(placemark)
		db.session.commit()
		flash('Метка успешно удалена.')
	else:
		flash('Метка не найдена.')
	active_tags = request.args.getlist('tag', type=int)
	return redirect(url_for('main.ShowIndex', tag=active_tags))
	
@bp.route('/add/', methods=['POST'])
@login_required
def AddPlacemark():
	form = AddPlacemarkForm(request.form)
	if form.validate_on_submit():
		try:
			placemark = Placemark(name = escape(form.name.data.strip()), latitude = form.latitude.data, longitude = form.longitude.data)
			db.session.add(placemark)
			if form.is_vendor.data:
				placemark.is_vendor = True
				placemark.description = form.description.data.strip()
				placemark.price_url = form.price_url.data
				if SyncPlacemarkWithPrice(placemark) is not True:
					raise APIError
			else:
				placemark.is_vendor = False
			current_user.placemarks.append(placemark)
			db.session.commit()
			flash('Метка успешно добавлена.')
		except:
			db.session.rollback()
			flash('Ошибка при добавлении метки.')
	else:
		for error in form.name.errors + form.longitude.errors + form.latitude.errors + form.price_url.errors + form.description.errors + form.is_vendor.errors:
			flash(error)
	active_tags = request.args.getlist('tag', type=int)
	return redirect(url_for('main.ShowIndex', tag=active_tags))