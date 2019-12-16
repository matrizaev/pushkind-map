from app import create_app, db
from app.models import User, Placemark, Tag, Subtag, SubtagPlacemark

application = create_app()

@application.shell_context_processor
def make_shell_context():
	return {'db': db, 'User': User, 'Placemark' : Placemark, 'Tag':Tag, 'Subtag':Subtag, 'SubtagPlacemark':SubtagPlacemark}