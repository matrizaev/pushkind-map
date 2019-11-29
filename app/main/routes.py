from app import db
from app.models import Placemark, Tag
from flask import redirect, flash, render_template, request, jsonify, current_app, url_for
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index/', methods=['GET', 'POST'])
@login_required
def ShowIndex():
	form = AddPlacemarkForm()
	if form.validate_on_submit():
		try:
			p = Placemark(name = form.name.data, latitude = form.latitude.data, longitude = form.longitude.data, is_vendor = form.is_vendor.data)
			db.session.add(p)
			if form.is_vendor.data:
				for tag in form.tags.data.split():
					if tag == ',':
						continue
					t = Tag.query.filter(Tag.name == tag).first()
					if not t:
						t = Tag(name = tag.replace(',', ''))
					p.tags.append(t)
					db.session.add(t)
			current_user.placemarks.append(p)
			db.session.add(current_user)
			db.session.commit()
		except:
			flash('Ошибка при добавлении метки.')
		flash('Метка успешно добавлена.')
	active_tag = request.args.get('active_tag')
	return render_template('index.html', form = form, active_tag = active_tag)	