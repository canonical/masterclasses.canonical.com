from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2TagsField
from wtforms import SelectField, SelectMultipleField, TextAreaField
from flask_admin.model.form import converts
from flask_admin.form.widgets import Select2Widget
from wtforms.widgets import Select as SelectWidget, TextArea
from flask import jsonify, redirect, url_for, session, abort, flash
from wtforms.fields import DateTimeField
from datetime import datetime
from models.video import Video
from models.presenter import Presenter
from models.tag import Tag, TagCategory
from models.associations import VideoPresenter, VideoTag
from webapp.database import db_session
from models.submission import VideoSubmission
import flask
from wtforms import validators
import logging as log

class RestrictedModelView(ModelView):
    # Admin view is accessible to Web&Design team
    def is_accessible(self):
        return session["openid"]["is_admin"] is True

    def get_url(self, endpoint, **kwargs):
        # Override delete URL to remove trailing slash
        if endpoint == '.delete_view':
            url = super(RestrictedModelView, self).get_url(endpoint, **kwargs)
            return url.rstrip('/')  # Remove trailing slash
        return super(RestrictedModelView, self).get_url(endpoint, **kwargs)

class TagModelView(RestrictedModelView):
    column_list = ['name', 'category']
    form_columns = ['name', 'tag_type_id']
    
    # Format the category display in list view
    column_formatters = {
        'category': lambda v, c, m, p: m.category.name if m.category else ''
    }
    
    def scaffold_form(self):
        form_class = super(TagModelView, self).scaffold_form()
        
        # Add name field explicitly
        form_class.name = TextAreaField(
            'Name',
            validators=[validators.DataRequired()],
            render_kw={'placeholder': 'Tag name'}
        )
        
        # Use query_factory for dynamic category loading
        form_class.tag_type_id = SelectField(
            'Category',
            validators=[validators.DataRequired()],
            coerce=int,
            choices=lambda: [(c.id, c.name) for c in db_session.query(TagCategory).order_by(TagCategory.name).all()]
        )
        
        return form_class

    def on_model_change(self, form, model, is_created):
        """Ensure the category relationship is properly set"""
        if form.tag_type_id.data:
            category = db_session.query(TagCategory).get(form.tag_type_id.data)
            model.category = category
            model.tag_type_id = category.id

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
        
        # Replace description field with custom markdown textarea
        form_class.description = TextAreaField(
            'Description',
            widget=MarkdownTextArea(),
        )
        
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
        'title': lambda v, c, m, p: flask.Markup(
            f'<a href="{flask.url_for("masterclasses.video_player", title=flask.current_app.jinja_env.filters["slugify"](m.title), id=m.id)}">{m.title}</a>'
        ) if m.recording else m.title,
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

    # Exclude relationship fields from form population
    form_excluded_columns = ('presenters', 'tags')

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

    def create_model(self, form):
        """Override create_model to handle relationships properly"""
        try:
            model = self.model()
            
            # Handle datetime fields
            if form.start_time.data:
                model.unixstart = int(form.start_time.data.timestamp())
            if form.end_time.data:
                model.unixend = int(form.end_time.data.timestamp())
            
            # Handle basic fields
            form_fields = form._fields.copy()
            
            # Remove fields we'll handle manually
            form_fields.pop('start_time', None)
            form_fields.pop('end_time', None)
            form_fields.pop('presenters', None)
            form_fields.pop('topic_tags', None)
            form_fields.pop('event_tags', None)
            form_fields.pop('date_tags', None)
            
            # Populate remaining fields
            for name, field in form_fields.items():
                field.populate_obj(model, name)
            
            # Handle presenters
            if form.presenters.data:
                presenters = db_session.query(Presenter).filter(
                    Presenter.id.in_(form.presenters.data)
                ).all()
                model.presenters = presenters
            
            # Handle tags
            all_tag_ids = []
            if form.topic_tags.data:
                all_tag_ids.extend(form.topic_tags.data)
            if form.event_tags.data:
                all_tag_ids.extend(form.event_tags.data)
            if form.date_tags.data:
                all_tag_ids.extend(form.date_tags.data)
            
            if all_tag_ids:
                tags = db_session.query(Tag).filter(
                    Tag.id.in_(all_tag_ids)
                ).all()
                model.tags = tags
            
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
            return model
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash('Failed to create record. %(error)s', 'error')
                log.exception('Failed to create record.')
            
            self.session.rollback()
            return False

    def __init__(self, *args, **kwargs):
        super(VideoModelView, self).__init__(*args, **kwargs)
        self.extra_js = [
            'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js'
        ]
        self.extra_css = [
            'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css'
        ]

    # Allow HTML in the title column
    column_formatters_args = {
        'title': dict(safe_attrs=['href']),
    }

    def scaffold_form(self):
        form_class = super(VideoModelView, self).scaffold_form()
        
        # Remove the unix timestamp fields from the form
        delattr(form_class, 'unixstart')
        delattr(form_class, 'unixend')
        
        # Add datetime picker fields with the correct format
        form_class.start_time = DateTimeField(
            'Start Time',
            format='%Y-%m-%dT%H:%M',  # HTML5 datetime-local format
            render_kw={
                "type": "datetime-local",
                "step": "60"  # 1 minute steps
            }
        )
        
        form_class.end_time = DateTimeField(
            'End Time',
            format='%Y-%m-%dT%H:%M',  # HTML5 datetime-local format
            render_kw={
                "type": "datetime-local",
                "step": "60"  # 1 minute steps
            }
        )
        
        # Configure presenters field with dynamic choices
        form_class.presenters = SelectMultipleField(
            'Presenters',
            coerce=int,
            widget=Select2Widget(multiple=True),
            choices=lambda: [(c.id, c.name) for c in db_session.query(Presenter).order_by(Presenter.name).all()]
        )
        
        # Replace the tags field with three separate dynamic fields
        delattr(form_class, 'tags')
        
        form_class.topic_tags = SelectMultipleField(
            'Topics',
            coerce=int,
            widget=Select2Widget(multiple=True),
            choices=lambda: [(t.id, t.name) for t in db_session.query(Tag).join(TagCategory)
                .filter(TagCategory.name == 'Topic')
                .order_by(Tag.name).all()]
        )
        
        form_class.event_tags = SelectMultipleField(
            'Event Type',
            coerce=int,
            widget=Select2Widget(),
            choices=lambda: [(t.id, t.name) for t in db_session.query(Tag).join(TagCategory)
                .filter(TagCategory.name == 'Event')
                .order_by(Tag.name).all()]
        )
        
        form_class.date_tags = SelectMultipleField(
            'Date',
            coerce=int,
            widget=Select2Widget(),
            choices=lambda: [(t.id, t.name) for t in db_session.query(Tag).join(TagCategory)
                .filter(TagCategory.name == 'Date')
                .order_by(Tag.name).all()]
        )
        
        # Replace description field with custom markdown textarea
        form_class.description = TextAreaField(
            'Description',
            widget=MarkdownTextArea(),
            description='Use markdown for formatting: **bold**, *italic*, [link text](url)'
        )
        
        return form_class

    def edit_form(self, obj=None):
        form = super(VideoModelView, self).edit_form(obj)
        
        # Only populate with existing data if this is not a form submission
        if not flask.request.form:
            log.info("Initial form load - populating with existing data")
            # Populate datetime fields
            if obj:
                if obj.unixstart:
                    form.start_time.data = datetime.fromtimestamp(obj.unixstart)
                if obj.unixend:
                    form.end_time.data = datetime.fromtimestamp(obj.unixend)
                
                # Populate presenter field
                if obj.presenters:
                    form.presenters.data = [p.id for p in obj.presenters]
                
                # Populate tag fields
                if obj.tags:
                    form.topic_tags.data = [t.id for t in obj.tags if t.category.name == 'Topic']
                    form.event_tags.data = [t.id for t in obj.tags if t.category.name == 'Event']
                    form.date_tags.data = [t.id for t in obj.tags if t.category.name == 'Date']
        else:
            log.info("Form submission - using submitted data")
            log.info(f"Submitted form data: {flask.request.form}")
        
        return form

    def update_model(self, form, model):
        """Override update_model to handle relationships properly"""
        try:
            # Log initial form data
            log.info(f"Updating video {model.id} with form data:")
            log.info(f"Start time: {form.start_time.data}")
            log.info(f"End time: {form.end_time.data}")
            log.info(f"Presenters: {form.presenters.data}")
            log.info(f"Topic tags: {form.topic_tags.data}")
            log.info(f"Event tags: {form.event_tags.data}")
            log.info(f"Date tags: {form.date_tags.data}")
            
            # Get the data before removing fields
            start_time = form.start_time.data
            end_time = form.end_time.data
            presenter_data = form.presenters.data
            topic_tags_data = form.topic_tags.data
            event_tags_data = form.event_tags.data
            date_tags_data = form.date_tags.data

            # Handle basic fields first
            form_fields = form._fields.copy()
            for field_name in ['start_time', 'end_time', 'presenters', 'topic_tags', 'event_tags', 'date_tags']:
                form_fields.pop(field_name, None)

            # Populate remaining basic fields
            for name, field in form_fields.items():
                field.populate_obj(model, name)

            # Handle datetime fields
            if start_time:
                try:
                    model.unixstart = int(start_time.timestamp())
                except AttributeError as e:
                    log.error(f"Failed to set start time: {e}")
                
            if end_time:
                try:
                    model.unixend = int(end_time.timestamp())
                except AttributeError as e:
                    log.error(f"Failed to set end time: {e}")

            # Clear existing relationships
            if hasattr(model, 'presenters'):
                model.presenters.clear()
            if hasattr(model, 'tags'):
                model.tags.clear()
            
            # Explicitly commit the relationship clearing
            self.session.flush()

            # Handle presenters
            if presenter_data:
                presenters = db_session.query(Presenter).filter(
                    Presenter.id.in_(presenter_data)
                ).all()
                model.presenters = presenters

            # Handle tags
            all_tag_ids = []
            if topic_tags_data:
                all_tag_ids.extend(topic_tags_data)
            if event_tags_data:
                all_tag_ids.extend(event_tags_data)
            if date_tags_data:
                all_tag_ids.extend(date_tags_data)

            if all_tag_ids:
                # Create a new query to ensure we get fresh data
                tags = db_session.query(Tag).filter(
                    Tag.id.in_(all_tag_ids)
                ).all()
                
                # Clear any existing tags and set new ones
                model.tags = []
                self.session.flush()
                model.tags = tags

            # Call model change hook and commit
            self._on_model_change(form, model, False)
            self.session.commit()
            
            # Verify the changes
            self.session.refresh(model)
            log.info(f"Final tags after update: {[t.name for t in model.tags]}")
            
            return True

        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(f'Failed to update record. Error: {str(ex)}', 'error')
                log.exception('Failed to update record.')
            
            self.session.rollback()
            return False

class MarkdownTextArea(TextArea):
    def __call__(self, field, **kwargs):
        # Add a help text below the textarea
        kwargs.setdefault('style', 'height: 300px; font-family: monospace;')
        html = super(MarkdownTextArea, self).__call__(field, **kwargs)
        help_text = """
        <small class="form-text text-muted">
            Markdown formatting supported:<br>
            <code>**bold**</code> for <strong>bold</strong><br>
            <code>*italic*</code> for <em>italic</em><br>
            <code>[link text](url)</code> for <a href="#">link text</a>
        </small>
        """
        return f"{html}{help_text}"

class PresenterModelView(RestrictedModelView):
    # List view configuration
    column_list = ['name', 'email', 'hrc_id', 'headshot']
    column_searchable_list = ['name', 'email', 'hrc_id']
    
    # Form configuration
    form_columns = ['name', 'email', 'hrc_id', 'headshot']
    
    # Add nice labels and descriptions
    column_labels = {
        'hrc_id': 'HRC ID',
    }

    def scaffold_form(self):
        form_class = super(PresenterModelView, self).scaffold_form()
        
        # Explicitly define form fields
        form_class.name = TextAreaField(
            'Name',
            validators=[validators.DataRequired()],
            render_kw={'placeholder': 'Full name of the presenter'}
        )
        
        form_class.email = TextAreaField(
            'Email',
            validators=[validators.Optional()],  # Removed Email() validator
            render_kw={'placeholder': 'Email address'}
        )
        
        form_class.hrc_id = TextAreaField(
            'HRC ID',
            validators=[validators.DataRequired()],
            render_kw={'placeholder': 'Unique HRC identifier'}
        )
        
        form_class.headshot = TextAreaField(
            'Headshot',
            validators=[validators.Optional()],  # Removed URL() validator
            render_kw={'placeholder': 'URL to presenter\'s headshot image'}
        )
        
        return form_class

    def on_model_change(self, form, model, is_created):
        """Ensure data is properly formatted before saving"""
        # Convert hrc_id to string if it isn't already
        if model.hrc_id is not None:
            model.hrc_id = str(model.hrc_id)