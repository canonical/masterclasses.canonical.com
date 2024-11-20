from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2TagsField
from wtforms import SelectField, SelectMultipleField
from flask_admin.model.form import converts
from flask_admin.form.widgets import Select2Widget
from wtforms.widgets import Select as SelectWidget
from flask import jsonify, redirect, url_for, session, abort
from wtforms.fields import DateTimeField
from datetime import datetime
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.associations import VideoPresenter, VideoTag
from webapp.database import db_session
from models.submission import VideoSubmission

class RestrictedModelView(ModelView):
    # Admin view is accessible to Web&Design team
    def is_accessible(self):
        return session["openid"]["is_admin"] is True

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
    
    def scaffold_form(self):
        form_class = super(TagModelView, self).scaffold_form()
        form_class.tag_type_id = SelectField(
            'Category',
            coerce=int,
            choices=[(c.id, c.name) for c in db_session.query(TagCategory).all()]
        )
        return form_class

    def on_model_change(self, form, model, is_created):
        if form.tag_type_id.data:
            category = db_session.query(TagCategory).get(form.tag_type_id.data)
            model.category = category

class TagCategoryModelView(RestrictedModelView):
    column_list = ['name', 'tags']
    form_columns = ['name']
    
    column_formatters = {
        'tags': lambda v, c, m, p: ', '.join([tag.name for tag in m.tags]) if m.tags else ''
    }

class DashboardView(AdminIndexView):
    def is_visible(self):
        return False

    @expose('/')
    def index(self):
        return redirect('/admin/video')

class SearchableSelect2Widget(Select2Widget):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', 'select2')
        kwargs.setdefault('data-ajax--url', '/admin/video/api/presenters')
        kwargs.setdefault('data-ajax--cache', 'true')
        kwargs.setdefault('data-ajax--delay', '250')
        kwargs.setdefault('data-ajax--data-type', 'json')
        kwargs.setdefault('data-minimum-input-length', '2')
        kwargs.setdefault('data-placeholder', 'Search presenters...')
        return super(SearchableSelect2Widget, self).__call__(field, **kwargs)
    
class SubmissionModelView(RestrictedModelView):
    column_list = ['title', 'email', 'duration', 'status', 'created_at']
    column_searchable_list = ['title', 'email']
    column_filters = ['status', 'created_at']
    form_excluded_columns = ['created_at', 'updated_at']
    
    # Add sorting
    column_default_sort = ('created_at', True)  # Sort by creation date, descending
    
    # Make the description viewable but not in the list
    column_details_list = ['title', 'email', 'description', 'duration', 'status', 'created_at']
    
    # Add nice labels
    column_labels = {
        'created_at': 'Submitted At'
    }
    
    def scaffold_form(self):
        form_class = super(SubmissionModelView, self).scaffold_form()
        form_class.status.choices = [
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('scheduled', 'Scheduled')
        ]
        return form_class

class VideoModelView(RestrictedModelView):
    # Display these columns in the list view using actual database column names
    column_list = ['title', 'presenters', 'topic_tags', 'event_tags', 'date_tags', 'unixstart', 'unixend', 'recording']
    
    # Format the relationships display in list view
    column_formatters = {
        'presenters': lambda view, context, model, name: 
            ', '.join([presenter.name for presenter in model.presenters]) if model.presenters else '',
        'topic_tags': lambda view, context, model, name:
            ', '.join([tag.name for tag in model.tags if tag.category.name == 'Topic']) if model.tags else '',
        'event_tags': lambda view, context, model, name:
            ', '.join([tag.name for tag in model.tags if tag.category.name == 'Event']) if model.tags else '',
        'date_tags': lambda view, context, model, name:
            ', '.join([tag.name for tag in model.tags if tag.category.name == 'Date']) if model.tags else '',
        'unixstart': lambda v, c, m, p: datetime.fromtimestamp(m.unixstart).strftime('%Y-%m-%d %H:%M') if m.unixstart else '',
        'unixend': lambda v, c, m, p: datetime.fromtimestamp(m.unixend).strftime('%Y-%m-%d %H:%M') if m.unixend else ''
    }
    
    # Add sorting configuration
    column_default_sort = ('unixstart', True)  # Sort by start time by default, descending
    
    # Configure sortable columns using actual database column names
    column_sortable_list = [
        'title',
        'unixstart',
        'unixend',
        'recording'
    ]

    # Add column labels to make the display nicer
    column_labels = {
        'unixstart': 'Start Time',
        'unixend': 'End Time'
    }
    
    # Configure which fields to show in the form
    form_columns = (
        'title', 'description', 'unixstart', 'unixend',
        'stream', 'slides', 'recording', 'chat_log', 
        'thumbnails', 'calendar_event', 'presenters', 'tags'
    )

    @expose('/api/presenters')
    def presenters_api(self):
        search = flask.request.args.get('q', '')
        query = db_session.query(Presenter)
        
        if search:
            query = query.filter(Presenter.name.ilike(f'%{search}%'))
        
        presenters = query.order_by(Presenter.name).all()
        return jsonify([{
            'id': str(p.id),
            'text': p.name
        } for p in presenters])

    def scaffold_form(self):
        form_class = super(VideoModelView, self).scaffold_form()
        
        # Remove the unix timestamp fields from the form
        delattr(form_class, 'unixstart')
        delattr(form_class, 'unixend')
        
        # Add datetime picker fields with the correct format
        form_class.start_time = DateTimeField(
            'Start Time',
            format='%Y-%m-%dT%H:%M',  # Changed format to match HTML5 datetime-local
            render_kw={
                "type": "datetime-local"
            }
        )
        
        form_class.end_time = DateTimeField(
            'End Time',
            format='%Y-%m-%dT%H:%M',  # Changed format to match HTML5 datetime-local
            render_kw={
                "type": "datetime-local"
            }
        )
        
        # Get all presenters
        presenters = db_session.query(Presenter).order_by(Presenter.name).all()
        
        # Configure presenters field with Select2
        form_class.presenters = SelectMultipleField(
            'Presenters',
            choices=[(str(p.id), p.name) for p in presenters],
            coerce=int,
            widget=Select2Widget(multiple=True)
        )
        
        # Get tags by category
        topic_tags = db_session.query(Tag).join(TagCategory).filter(TagCategory.name == 'Topic').order_by(Tag.name).all()
        event_tags = db_session.query(Tag).join(TagCategory).filter(TagCategory.name == 'Event').order_by(Tag.name).all()
        date_tags = db_session.query(Tag).join(TagCategory).filter(TagCategory.name == 'Date').order_by(Tag.name).all()
        
        # Replace the tags field with three separate fields
        delattr(form_class, 'tags')
        
        form_class.topic_tags = SelectMultipleField(
            'Topics',
            choices=[(str(t.id), t.name) for t in topic_tags],
            coerce=int,
            widget=Select2Widget(multiple=True)
        )
        
        form_class.event_tags = SelectMultipleField(
            'Event Type',
            choices=[(str(t.id), t.name) for t in event_tags],
            coerce=int,
            widget=Select2Widget()
        )
        
        form_class.date_tags = SelectMultipleField(
            'Date',
            choices=[(str(t.id), t.name) for t in date_tags],
            coerce=int,
            widget=Select2Widget()
        )
        
        return form_class

    def on_model_change(self, form, model, is_created):
        """
        Ensure relationships are properly set when the model changes
        """
        # Convert datetime to unix timestamp
        if hasattr(form, 'start_time') and form.start_time.data:
            try:
                model.unixstart = int(form.start_time.data.timestamp())
            except AttributeError:
                pass
                
        if hasattr(form, 'end_time') and form.end_time.data:
            try:
                model.unixend = int(form.end_time.data.timestamp())
            except AttributeError:
                pass
                
        if form.presenters.data:
            presenters = db_session.query(Presenter).filter(
                Presenter.id.in_(form.presenters.data)
            ).all()
            model.presenters = presenters
            
        # Combine all tag selections
        all_tag_ids = []
        if hasattr(form, 'topic_tags') and form.topic_tags.data:
            all_tag_ids.extend(form.topic_tags.data)
        if hasattr(form, 'event_tags') and form.event_tags.data:
            all_tag_ids.extend(form.event_tags.data)
        if hasattr(form, 'date_tags') and form.date_tags.data:
            all_tag_ids.extend(form.date_tags.data)
        
        if all_tag_ids:
            tags = db_session.query(Tag).filter(
                Tag.id.in_(all_tag_ids)
            ).all()
            model.tags = tags
            
        super(VideoModelView, self).on_model_change(form, model, is_created)

    def create_form(self, obj=None):
        form = super(VideoModelView, self).create_form(obj)
        self._populate_form_tags(form, obj)
        return form

    def edit_form(self, obj=None):
        form = super(VideoModelView, self).edit_form(obj)
        
        # Convert unix timestamps to datetime for the form
        if obj:
            if obj.unixstart:
                form.start_time.data = datetime.fromtimestamp(obj.unixstart)
            if obj.unixend:
                form.end_time.data = datetime.fromtimestamp(obj.unixend)
                
            # Populate tag fields
            form.topic_tags.data = [t.id for t in obj.tags if t.category.name == 'Topic']
            form.event_tags.data = [t.id for t in obj.tags if t.category.name == 'Event']
            form.date_tags.data = [t.id for t in obj.tags if t.category.name == 'Date']
                
        return form

    def _populate_form_tags(self, form, obj):
        """Helper method to populate tag fields"""
        if obj:
            form.topic_tags.data = [t.id for t in obj.tags if t.category.name == 'Topic']
            form.event_tags.data = [t.id for t in obj.tags if t.category.name == 'Event']
            form.date_tags.data = [t.id for t in obj.tags if t.category.name == 'Date']

    def __init__(self, *args, **kwargs):
        super(VideoModelView, self).__init__(*args, **kwargs)
        self.extra_js = [
            'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js'
        ]
        self.extra_css = [
            'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css'
        ]