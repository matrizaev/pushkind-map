from app import db
from app.models import Placemark, Tag
from flask import redirect, flash, render_template, request, jsonify, current_app, url_for, escape
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm, EditPlacemarkForm


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
				p = Placemark(name = escape(form.name.data), description = escape(form.description.data), latitude = form.latitude.data, longitude = form.longitude.data, is_vendor = True, price = form.price.data)
				tagsList = set(form.tags.data.replace(',', ' ').lower().split())
				for tag in tagsList:
					if len(tag) > 128:
						tag = tag[:128]
					t = Tag.query.filter(Tag.name == tag).first()
					if not t:
						t = Tag(name = tag)
					p.tags.append(t)
					db.session.add(t)
			else:
				p = Placemark(name = escape(form.name.data), description = escape(form.description.data), latitude = form.latitude.data, longitude = form.longitude.data, is_vendor = False)
			db.session.add(p)
			current_user.placemarks.append(p)
			db.session.add(current_user)
			db.session.commit()
		except:
			flash('Ошибка при добавлении метки.')
		flash('Метка успешно добавлена.')
	else:
		for error in form.name.errors + form.longitude.errors + form.latitude.errors + form.tags.errors + form.price.errors + form.description.errors + form.is_vendor.errors:
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
				if p.is_vendor:
					p.price = form.price.data
				db.session.commit()
				flash('Метка успешно изменена.')
			else:
				flash('Метка не найдена.')
		except:
			flash('Ошибка изменения метки.')
	else:
		for error in form.id.errors + form.price.errors + form.description.errors:
			flash(error)
	active_tag = request.args.getlist('active_tag', type=int)
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))