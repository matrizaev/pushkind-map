from app import db
from app.models import Placemark, Tag, Subtag, SubtagPlacemark
from flask import redirect, flash, render_template, request, url_for, escape
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm, EditPlacemarkForm


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
			p = Placemark(name = escape(form.name.data.strip()), latitude = form.latitude.data, longitude = form.longitude.data)
			db.session.add(p)
			if form.is_vendor.data:
				p.is_vendor = True
				p.description = form.description.data.strip()
				p.price_url = form.price_url.data
				MakeTagsHierarchy(p, form.tags.data)
			else:
				p.is_vendor = False
			current_user.placemarks.append(p)
			db.session.commit()
			flash('Метка успешно добавлена.')
		except:
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
		try:
			p = Placemark.query.filter(Placemark.user_id == current_user.id, Placemark.id == form.id.data, Placemark.is_vendor == True).first()
			if p:
				p.name = escape(form.name.data.strip())
				if (len(form.tags.data) == 0):
					db.session.delete(p)
					flash('Метка успешно удалена.')
				else:
					p.description = form.description.data.strip()
					p.price_url = form.price_url.data
					SubtagPlacemark.query.filter(SubtagPlacemark.placemark_id == p.id).delete(synchronize_session=False)
					MakeTagsHierarchy(p, form.tags.data)
				Subtag.query.filter(~Subtag.placemarks.any()).delete(synchronize_session=False)
				Tag.query.filter(~Tag.subtags.any()).delete(synchronize_session=False)
				db.session.commit()
				flash('Метка успешно изменена.')
			else:
				flash('Метка не найдена.')
		except:
			flash('Ошибка изменения метки.')
	else:
		for error in form.id.errors + form.tags.errors + form.description.errors + form.name.errors:
			flash(error)
	active_tag = request.args.getlist('active_tag', type=int)
	return redirect(url_for('main.ShowIndex', active_tag=active_tag))