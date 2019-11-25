from app import db
from flask import redirect, flash, render_template, request, jsonify, current_app, url_for
from flask_login import current_user, login_required
from app.main import bp
from app.main.forms import AddPlacemarkForm


@bp.route('/')
@bp.route('/index/')
@login_required
def ShowIndex():
	
	return render_template('index.html')