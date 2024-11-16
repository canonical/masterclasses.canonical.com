import os
import flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from canonicalwebteam.flask_base.app import FlaskBase
from slugify import slugify as py_slugify
from datetime import datetime, timezone

from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.associations import VideoPresenter, VideoTag
from flask_admin.form import Select2Widget
from flask_admin.form import Select2Field
from wtforms import SelectField
from flask_admin.model.form import converts

db_engine = create_engine(os.getenv("DATABASE_URL"))
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
)

from webapp.masterclasses import masterclasses
from webapp.sso import init_sso

app = FlaskBase(
    __name__,
    "masterclasses.canonical.com",
    template_folder="../templates",
    static_folder="../static",
    template_404="404.html",
    template_500="500.html",
)

def slugify(text):
    return py_slugify(text)

app.add_template_filter(slugify)

init_sso(app)

app.register_blueprint(masterclasses, url_prefix="/")

class RestrictedModelView(ModelView):
    # Admin view is accessible to Web&Design team
    def is_accessible(self):
        return flask.session["openid"]["is_admin"] is True

class TagModelView(RestrictedModelView):
    column_list = ['name', 'category']
    
    # Format the category display in list view
    column_formatters = {
        'category': lambda v, c, m, p: m.category.name if m.category else ''
    }
    
    # Explicitly define form fields
    form_columns = ('name', 'tag_type_id')
    
    # Configure how fields are displayed/edited
    form_args = {
        'tag_type_id': {
            'label': 'Category',
            'query_factory': lambda: db_session.query(TagCategory).all(),
            'get_label': 'name'
        }
    }
    
    # Override the form creation to use the foreign key field
    def scaffold_form(self):
        form_class = super(TagModelView, self).scaffold_form()
        form_class.tag_type_id = SelectField(
            'Category',
            coerce=int,
            choices=[(c.id, c.name) for c in db_session.query(TagCategory).all()]
        )
        return form_class

    def on_model_change(self, form, model, is_created):
        # Ensure the category relationship is properly set
        if form.tag_type_id.data:
            category = db_session.query(TagCategory).get(form.tag_type_id.data)
            model.category = category

class TagCategoryModelView(RestrictedModelView):
    column_list = ['name', 'tags']
    form_columns = ['name']
    
    # Format the tags display in list view
    column_formatters = {
        'tags': lambda v, c, m, p: ', '.join([tag.name for tag in m.tags]) if m.tags else ''
    }

    def __init__(self, model, session, **kwargs):
        super(TagCategoryModelView, self).__init__(model, session, **kwargs)

class DashboardView(AdminIndexView):
    def is_visible(self):
        return False

    @expose('/')
    def index(self):
        return flask.redirect('/admin/video') 

# Initialize Flask-Admin
admin = Admin(app, name='Masterclasses Admin', template_mode='bootstrap3', index_view=DashboardView())

@expose('/admin/video/delete/')
def delete_video():
    video_id = flask.request.form.get('id')
    print(f"Deleting video with ID: {video_id}")
    return flask.redirect(flask.url_for('admin.index'))


# Register models with admin interface
admin.add_view(RestrictedModelView(Video, db_session))
admin.add_view(RestrictedModelView(Presenter, db_session))
admin.add_view(TagModelView(Tag, db_session))
admin.add_view(TagCategoryModelView(TagCategory, db_session))

@app.route("/")
def index():
    return flask.render_template("masterclasses.html")

def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

app.add_template_filter(timestamp_to_date)

@app.template_filter('time_until')
def time_until_filter(timestamp):
    now = datetime.now(timezone.utc)
    event_time = datetime.fromtimestamp(timestamp, timezone.utc)
    diff = event_time - now
    
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    
    return f"{hours}h {minutes}m"

@app.template_filter('format_date')
def format_date_filter(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime('%B %d, %Y')

@app.route("/videos/<video_id>")
def video_player(video_id):
    return flask.render_template("video_player.html", video_id=video_id)