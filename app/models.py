from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from sqlalchemy import or_
from flask import current_app
from flask import url_for

@login.user_loader
def load_user(id):
	return User.query.get(int(id))
	
class User(UserMixin, db.Model):
	id  = db.Column(db.Integer, primary_key = True)
	email    = db.Column(db.String(120), index = True, unique = True, nullable=False)
	password = db.Column(db.String(128), nullable=False)
	placemarks = db.relationship('Placemark', backref = 'user', lazy='dynamic')
	
	def __repr__ (self):
		return '<User {}>'.format(self.email)
	
	def SetPassword(self, password):
		self.password = generate_password_hash(password)
		db.session.commit()
		
	def CheckPassword(self, password):
		return check_password_hash(self.password, password)
		
	def VendorPlacemarks(self):
		return self.placemarks.filter(Placemark.is_vendor == True).all()
		
	def GetAvatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)


tag_placemark = db.Table('tag_placemark', db.Model.metadata,
    db.Column('placemark_id', db.Integer, db.ForeignKey('placemark.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Placemark(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	coordinates = db.Column(db.String(128), nullable=False)
	name = db.Column(db.String(128), nullable=False)
	tags = db.relationship('Tag', secondary = 'tag_placemark')
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	is_vendor = db.Column(db.Boolean, nullable=False, default=False, server_default='False')
	def __repr__ (self):
		return '<Placemark {}>'.format(self.name)

class Tag(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(128), nullable=False)
	placemarks = db.relationship('Placemark', secondary = 'tag_placemark')
	def __repr__ (self):
		return '<Tag {}>'.format(self.name)