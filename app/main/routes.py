from app import db
from app.models import Placemark, Tag, Subtag, SubtagPlacemark
from flask import redirect, flash, render_template, request, url_for, escape
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
			p = Placemark(name = escape(form.name.data.strip()), description = escape(form.description.data.strip()), latitude = form.latitude.data, longitude = form.longitude.data)
			db.session.add(p)
			if form.is_vendor.data:
				p.is_vendor = True
				for tag in form.tags.data:
					tag_name = tag['name'].lower().strip()
					t = Tag.query.filter(Tag.name == tag_name).first()
					if not t:
						t = Tag(name = tag_name)
						db.session.add(t)
					for subtag in tag['prices']:
						st_name = '{}-{}'.format(tag_name, subtag['name'].lower().strip())
						st = Subtag.query.filter(Subtag.name == st_name, Subtag.tag == t).first()
						if not st:
							st = Subtag(name = st_name)
							db.session.add(st)
						t.subtags.append(st)
						subtag_placemark = SubtagPlacemark(price = subtag['price'])
						subtag_placemark.placemark = p
						subtag_placemark.subtag = st
						db.session.add(subtag_placemark)
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
			p = Placemark.query.filter(Placemark.user_id == current_user.id, Placemark.id == form.id.data).first()
			if p:
				p.description = escape(form.description.data.strip())
				p.name = escape(form.name.data.strip())
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