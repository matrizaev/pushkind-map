from app import db
from app.models import Placemark, Tag, Subtag, SubtagPlacemark
from flask import redirect, flash, render_template, request, url_for, escape, jsonify
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm, EditPlacemarkForm
from flask import current_app

import gspread
from gspread.exceptions import NoValidUrlKeyFound, APIError

import pandas as pd

def MakeTagsHierarchy(placemark, tags_data):
	for tag in tags_data:
		tag_name = tag['name'].strip().lower().replace('/', '_')
		t = Tag.query.filter(Tag.name == tag_name).first()
		if not t:
			t = Tag(name = tag_name)
			db.session.add(t)
		for subtag in tag['prices']:
			st_name = '{} / {}'.format(tag_name, subtag['name'].strip().lower().replace('/', '_'))
			st = Subtag.query.filter(Subtag.name == st_name, Subtag.tag == t).first()
			if not st:
				st = Subtag(name = st_name)
				db.session.add(st)
				t.subtags.append(st)
			subtag_placemark = SubtagPlacemark(price = subtag['price'], units = subtag['units'])
			subtag_placemark.placemark = placemark
			subtag_placemark.subtag = st
			db.session.add(subtag_placemark)

@bp.route('/')
@bp.route('/index/')
@login_required
def ShowIndex():
	add_form = AddPlacemarkForm()
	edit_form = EditPlacemarkForm()
	active_tag = request.args.getlist('active_tag', type=int)
	search = request.args.get('search')
	if search is not None and len(search) == 0:
		search = None
	return render_template('index.html', add_form = add_form, edit_form = edit_form, active_tag = active_tag, search=search)
	
def RemovePlacemarkSubtags(placemark):
	SubtagPlacemark.query.filter(SubtagPlacemark.placemark_id == placemark.id).delete(synchronize_session='fetch')
	Subtag.query.filter(~Subtag.placemarks.any()).delete(synchronize_session='fetch')
	Tag.query.filter(~Tag.subtags.any()).delete(synchronize_session='fetch')	

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
		gc = gspread.service_account(filename=current_app.config['GOOGLE_DRIVE_ACCOUNT'])
		spreadsheet = gc.open_by_url(placemark.price_url)
		worksheet = spreadsheet.get_worksheet(0)
		data = worksheet.get_all_records()
		df = pd.DataFrame(data)
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

	
@bp.route('/sync/')
@login_required
def SyncPlacemark():
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
	active_tag = request.args.getlist('active_tag', type=int)	
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))

@bp.route('/remove')
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
	active_tag = request.args.getlist('active_tag', type=int)
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))
	
@bp.route('/add', methods=['POST'])
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
				if form.price_url.data is not None and len(form.price_url.data) > 0:
					placemark.price_url = form.price_url.data
					if SyncPlacemarkWithPrice(placemark) is not True:
						raise APIError
				else:
					placemark.price_url = None
					if len(form.tags.data) == 0:
						raise TypeError
					MakeTagsHierarchy(placemark, form.tags.data)
			else:
				placemark.is_vendor = False
			current_user.placemarks.append(placemark)
			db.session.commit()
			flash('Метка успешно добавлена.')
		except:
			db.session.rollback()
			flash('Ошибка при добавлении метки.')
	else:
		for error in form.name.errors + form.longitude.errors + form.latitude.errors + form.tags.errors + form.description.errors + form.is_vendor.errors:
			flash(error)
	active_tag = request.args.getlist('active_tag', type=int)
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))
	
@bp.route('/edit', methods=['POST'])
@login_required
def EditPlacemark():
	form = EditPlacemarkForm(request.form)
	if form.validate_on_submit():
		placemark = Placemark.query.filter(Placemark.user_id == current_user.id, Placemark.id == form.id.data, Placemark.is_vendor == True).first()
		if placemark is not None:
			try:
				placemark.name = escape(form.name.data.strip())
				if (len(form.tags.data) == 0) and form.price_url.data is None:
					db.session.delete(placemark)
					flash('Метка успешно удалена.')
				else:
					placemark.description = form.description.data.strip()
					RemovePlacemarkSubtags(placemark)
					if form.price_url.data is not None and len(form.price_url.data) > 0:
						placemark.price_url = form.price_url.data
						if SyncPlacemarkWithPrice(placemark) is not True:
							raise APIError
					else:
						placemark.price_url = None
						if len(form.tags.data) == 0:
							raise TypeError
						MakeTagsHierarchy(placemark, form.tags.data)
				db.session.commit()
				flash('Метка успешно изменена.')
			except:
				db.session.rollback()
				flash('Ошибка изменения метки.')
		else:
			flash('Метка не найдена.')
	else:
		for error in form.id.errors + form.tags.errors + form.description.errors + form.name.errors:
			flash(error)
	active_tag = request.args.getlist('active_tag', type=int)
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))