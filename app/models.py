from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from sqlalchemy import or_
from flask import current_app
from flask import url_for
import json

@login.user_loader
def load_user(id):
	return User.query.get(int(id))
	
class User(UserMixin, db.Model):
	id  = db.Column(db.Integer, primary_key = True)
	email	= db.Column(db.String(120), index = True, unique = True, nullable=False)
	password = db.Column(db.String(128), nullable=False)
	placemarks = db.relationship('Placemark', backref = 'user', lazy='dynamic')
	
	def __repr__ (self):
		return '<User {}>'.format(self.email)
	
	def SetPassword(self, password):
		self.password = generate_password_hash(password)
		
	def CheckPassword(self, password):
		return check_password_hash(self.password, password)
		
	def EndpointPlacemarks(self):
		return self.placemarks.filter(Placemark.is_vendor == False).all()
		
	def VendorsPlacemarks(self, tags_list = None, search = None):
		search = f'%{search}%'
		if len(tags_list) > 0:
			return self.placemarks.filter(Placemark.subtags.any(SubtagPlacemark.subtag.has(Subtag.tag_id.in_(tags_list))), Placemark.is_vendor == True).all()
		elif search is not None:
			return self.placemarks.filter(Placemark.subtags.any(SubtagPlacemark.subtag.has(Subtag.name.ilike(search))), Placemark.is_vendor == True).all()
		else:
			return []
		
	def GetTags(self):
		subtags = Subtag.query.filter(Subtag.placemarks.any(SubtagPlacemark.placemark.has(Placemark.user_id == self.id))).all()
		result = {}
		for subtag in subtags:
			if not subtag.tag in result:
				result[subtag.tag] = list()
			result[subtag.tag].append(subtag)
		return result
		
	def GetActiveSubtags(self, tags_list):
		return Subtag.query.filter(Subtag.tag_id.in_(tags_list), Subtag.placemarks.any(SubtagPlacemark.placemark.has(Placemark.user_id == self.id))).all()
		
	def GetSearchedSubtags(self, search):
		search = f'%{search}%'
		return Subtag.query.filter(Subtag.name.ilike(search), Subtag.placemarks.any(SubtagPlacemark.placemark.has(Placemark.user_id == self.id))).all()
		
	def GetAvatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)


class Placemark(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	longitude = db.Column(db.Float, nullable=False)
	latitude = db.Column(db.Float, nullable=False)
	name = db.Column(db.String(128), nullable=False)
	description = db.Column(db.String(128), nullable=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	is_vendor = db.Column(db.Boolean, nullable=False, default=False, server_default='False')
	price_url = db.Column(db.String(), nullable=True)
	subtags = db.relationship('SubtagPlacemark', back_populates='placemark', cascade='save-update,merge,delete,delete-orphan')
	
	def Serialize(self):
		result = {
			'id':self.id,
			'coordinates':[self.longitude, self.latitude],
			'name':self.name,
			'description':self.description,
			'price_url':self.price_url
		}
		if self.is_vendor:
			result['prices'] = {st.subtag.name:[st.price, st.units if st.units else ''] for st in self.subtags}
			tags = self.GetTags()
			result['tags'] = {t.name:{st.name:[tags[t][st].price, tags[t][st].units if tags[t][st].units else ''] for st in tags[t]} for t in tags}
		return result
	
	def GetTags(self):
		subtags = Subtag.query.filter(Subtag.placemarks.any(SubtagPlacemark.placemark_id == self.id)).all()
		result = {}
		for subtag  in subtags:
			if not subtag.tag in result:
				result[subtag.tag] = {}
			result[subtag.tag][subtag] = SubtagPlacemark.query.filter(SubtagPlacemark.placemark_id == self.id, SubtagPlacemark.subtag_id == subtag.id).first()
		return result
	
	def __repr__ (self):
		return json.dumps(self.Serialize())

class SubtagPlacemark(db.Model):
	placemark_id = db.Column(db.Integer, db.ForeignKey('placemark.id'), primary_key = True)
	subtag_id = db.Column(db.Integer, db.ForeignKey('subtag.id'), primary_key = True)
	price = db.Column(db.Float, nullable=False, default=0.0, server_default='0.0')
	units = db.Column(db.String(30), nullable=True)
	placemark = db.relationship('Placemark', back_populates='subtags')
	subtag = db.relationship('Subtag', back_populates='placemarks')

	def __hash__(self):
		return hash((self.placemark_id, self.subtag_id))
	
	def __eg__(self, other):
		return (self.placemark_id, self.subtag_id) == (other.placemark_id, other.subtag_id)
		
	def __ne__(self, other):
		return not(self == other)

	def __repr__ (self):
		return '{}[{}:{}]'.format(self.subtag.tag.name, self.subtag.name.split(' / ')[1], self.price)

class Subtag(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(128), nullable=False, unique=True)
	tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))
	tag = db.relationship('Tag', back_populates='subtags')
	placemarks = db.relationship('SubtagPlacemark', back_populates='subtag')

	def __hash__(self):
		return hash(self.id)
	
	def __eg__(self, other):
		return self.id == other.id
		
	def __ne__(self, other):
		return not(self == other)
	
	def __repr__ (self):
		return '<Subtag {}>'.format(self.name)
		
class Tag(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(128), nullable=False, unique=True)
	subtags = db.relationship('Subtag', back_populates='tag')
	
	def __hash__(self):
		return hash(self.id)
	
	def __eg__(self, other):
		return self.id == other.id
		
	def __ne__(self, other):
		return not(self == other)
	
	def __repr__ (self):
		return '<Tag {}>'.format(self.name)