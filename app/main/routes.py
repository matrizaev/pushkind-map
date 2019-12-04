from app import db
from app.models import Placemark, Tag
from flask import redirect, flash, render_template, request, jsonify, current_app, url_for, escape
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index/', methods=['GET', 'POST'])
@login_required
def ShowIndex():
	form = AddPlacemarkForm()
	if form.validate_on_submit():
		#try:
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
		#except:
		#	flash('Ошибка при добавлении метки.')
		flash('Метка успешно добавлена.')
	active_tag = request.args.get('active_tag')
	return render_template('index.html', form = form, active_tag = active_tag)

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
	return redirect(url_for('main.ShowIndex'))