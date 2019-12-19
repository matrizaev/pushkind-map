from app import db
from app.models import Placemark, Tag, Subtag, SubtagPlacemark
from flask import redirect, flash, render_template, request, jsonify, current_app, url_for, escape
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm, EditPlacemarkForm
import re


@bp.route('/')
@bp.route('/index/')
@login_required
def ShowIndex():
	add_form = AddPlacemarkForm()
	edit_form = EditPlacemarkForm()
	active_tag = request.args.getlist('active_tag', type=int)
	return render_template('index.html', add_form = add_form, edit_form = edit_form, active_tag = active_tag)

@bp.route('/remove')
@login_required
def RemovePlacemark():
	id = request.args.get('id')
	try:
		p = Placemark.query.filter(Placemark.user_id == current_user.id, Placemark.id == id).first()
		if p:
			db.session.delete(p)
			Subtag.query.filter(~Subtag.placemarks.any()).delete(synchronize_session=False)
			Tag.query.filter(~Tag.subtags.any()).delete(synchronize_session=False)
			db.session.commit()
			flash('Метка успешно удалена.')
		else:
			flash('Метка не найдена.')
	except:
		flash('Ошибка удаления.')
	active_tag = request.args.getlist('active_tag', type=int)
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))
	
@bp.route('/add', methods=['POST'])
@login_required
def AddPlacemark():
	form = AddPlacemarkForm(request.form)
	if form.validate_on_submit():
		try:
			if form.is_vendor.data:
				p = Placemark(name = escape(form.name.data), description = escape(form.description.data), latitude = form.latitude.data, longitude = form.longitude.data, is_vendor = True)
				pattern = re.compile('(\w+)(?:\s*-\w+:\d+(?:\.\d+)?)+')
				tags_list = [x for x in pattern.finditer(form.tags.data)]
				pattern = re.compile('-(\w+):(\d+(?:\.\d+)?)')
				for tag in tags_list:
					tag_name = tag.group(1).lower()
					t = Tag.query.filter(Tag.name == tag_name).first()
					if not t:
						t = Tag(name = tag_name)
						db.session.add(t)
					subtags_list = [x for x in pattern.finditer(tag.group(0))]
					for subtag in subtags_list:
						st_name = '{}-{}'.format(tag_name, subtag.group(1).lower())
						st = Subtag.query.filter(Subtag.name == st_name, Subtag.tag == t).first()
						if not st:
							st = Subtag(name = st_name)
							db.session.add(st)
						t.subtags.append(st)
						subtag_placemark = SubtagPlacemark(price = float(subtag.group(2)))
						subtag_placemark.placemark = p
						subtag_placemark.subtag = st
						db.session.add(subtag_placemark)
			else:
				p = Placemark(name = escape(form.name.data), description = escape(form.description.data), latitude = form.latitude.data, longitude = form.longitude.data, is_vendor = False)
			db.session.add(p)
			current_user.placemarks.append(p)
			db.session.commit()
		except:
			flash('Ошибка при добавлении метки.')
		flash('Метка успешно добавлена.')
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
		try:
			p = Placemark.query.filter(Placemark.user_id == current_user.id, Placemark.id == form.id.data).first()
			if p:
				p.description = escape(form.description.data)
				p.name = escape(form.name.data)
				if p.is_vendor:
					for subtag in form.prices.data:
						st = SubtagPlacemark.query.filter(SubtagPlacemark.subtag.has(Subtag.name == subtag['name']), SubtagPlacemark.placemark_id == p.id).first()
						if st:
							st.price = subtag['price']
				db.session.commit()
				flash('Метка успешно изменена.')
			else:
				flash('Метка не найдена.')
		except:
			flash('Ошибка изменения метки.')
	else:
		for error in form.id.errors + form.prices.errors + form.description.errors + form.name.errors:
			flash(error)
	active_tag = request.args.getlist('active_tag', type=int)
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))