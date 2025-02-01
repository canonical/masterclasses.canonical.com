from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2TagsField
from wtforms import SelectField, SelectMultipleField, TextAreaField
from flask_admin.model.form import converts
from flask_admin.form.widgets import Select2Widget
from wtforms.widgets import Select as SelectWidget, TextArea
from flask import jsonify, redirect, url_for, session, abort, flash, request
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
from sqlalchemy import and_, or_
from flask_admin.contrib.sqla.filters import BaseSQLAFilter, FilterEqual
import os
import csv
import io
import json

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
    form_columns = ['name', 'category']

    @property
    def list_template(self):
        return 'admin/tag_list.html'

    @expose('/import-json', methods=['POST'])
    def import_json(self):
        if 'json_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('.index_view'))
            
        file = request.files['json_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('.index_view'))
            
        if not file.filename.endswith('.json'):
            flash('File must be a JSON', 'error')
            return redirect(url_for('.index_view'))
            
        try:
            # Read JSON file
            json_data = json.loads(file.read().decode('UTF8'))
            
            # Process each tag
            for tag_data in json_data:
                if not tag_data.get('name') or not tag_data.get('category'):
                    continue
                
                # Get category (must exist)
                category = db_session.query(TagCategory).filter_by(name=tag_data['category']).first()
                if not category:
                    continue
                
                # Create tag if it doesn't exist
                existing_tag = db_session.query(Tag).join(TagCategory).filter(
                    Tag.name == tag_data['name'],
                    TagCategory.id == category.id
                ).first()
                
                if not existing_tag:
                    tag = Tag(name=tag_data['name'], tag_type_id=category.id)
                    db_session.add(tag)
            
            db_session.commit()
            flash('Tags imported successfully', 'success')
            
        except Exception as e:
            db_session.rollback()
            log.error(f"Error importing JSON: {e}")
            flash('Error importing JSON file', 'error')
            
        return redirect(url_for('.index_view'))

    @expose('/export-json', methods=['GET'])
    def export_json(self):
        try:
            # Query all tags with their categories
            tags = db_session.query(Tag, TagCategory).join(TagCategory).order_by(TagCategory.name, Tag.name).all()
            
            # Create JSON data
            tag_list = []
            for tag, category in tags:
                tag_data = {
                    'name': tag.name,
                    'category': category.name
                }
                tag_list.append(tag_data)
            
            # Create the response
            response = flask.make_response(json.dumps(tag_list, indent=2))
            response.headers["Content-Disposition"] = "attachment; filename=tags.json"
            response.headers["Content-type"] = "application/json"
            
            return response
            
        except Exception as e:
            log.error(f"Error exporting JSON: {e}")
            flash('Error exporting JSON file', 'error')
            return redirect(url_for('.index_view'))

class TagCategoryModelView(RestrictedModelView):
    column_list = ['name', 'tags']
    form_columns = ['name']
    
    column_formatters = {
        'tags': lambda v, c, m, p: ', '.join([tag.name for tag in m.tags]) if m.tags else ''
    }

    @property
    def list_template(self):
        return 'admin/tag_category_list.html'

    @expose('/import-json', methods=['POST'])
    def import_json(self):
        if 'json_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('.index_view'))
            
        file = request.files['json_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('.index_view'))
            
        if not file.filename.endswith('.json'):
            flash('File must be a JSON', 'error')
            return redirect(url_for('.index_view'))
            
        try:
            # Read JSON file
            json_data = json.loads(file.read().decode('UTF8'))
            
            # Process each category
            for category_data in json_data:
                if not category_data.get('name'):
                    continue
                
                # Get or create category
                category = db_session.query(TagCategory).filter_by(name=category_data['name']).first()
                if not category:
                    category = TagCategory(name=category_data['name'])
                    db_session.add(category)
            
            db_session.commit()
            flash('Categories imported successfully', 'success')
            
        except Exception as e:
            db_session.rollback()
            log.error(f"Error importing JSON: {e}")
            flash('Error importing JSON file', 'error')
            
        return redirect(url_for('.index_view'))

    @expose('/export-json', methods=['GET'])
    def export_json(self):
        try:
            # Query all categories
            categories = db_session.query(TagCategory).order_by(TagCategory.name).all()
            
            # Create JSON data
            category_list = []
            for category in categories:
                category_data = {
                    'name': category.name
                }
                category_list.append(category_data)
            
            # Create the response
            response = flask.make_response(json.dumps(category_list, indent=2))
            response.headers["Content-Disposition"] = "attachment; filename=tag_categories.json"
            response.headers["Content-type"] = "application/json"
            
            return response
            
        except Exception as e:
            log.error(f"Error exporting JSON: {e}")
            flash('Error exporting JSON file', 'error')
            return redirect(url_for('.index_view'))

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

class ContainsFilter(BaseSQLAFilter):
    def __init__(self, column, name, options=None):
        super(ContainsFilter, self).__init__(column, name, options)

    def apply(self, query, value, alias=None):
        if value is None:
            return query
        return query.filter(self.column.ilike(f'%{value}%'))

    def operation(self):
        return 'contains'

    def validate(self, value):
        return True

class MultiSelectFilter(FilterEqual):
    def __init__(self, column, name, options=None):
        super(MultiSelectFilter, self).__init__(column, name, options)
        self.multiple = True  # Enable multiple selection

    def apply(self, query, value, alias=None):
        if value is None:
            return query
        return query.filter(self.column.in_(value))

class MultiSelectContainsFilter(MultiSelectFilter):
    def apply(self, query, values, alias=None):
        if not values:
            return query
        conditions = [self.column.ilike(f'%{value}%') for value in values]
        return query.filter(or_(*conditions))

class PresenterFilter(MultiSelectFilter):
    def apply(self, query, values, alias=None):
        if not values:
            return query
        # Convert single value to list if needed
        if isinstance(values, str):
            values = [values]
        return (query.join(Video.presenters)
               .filter(Presenter.name.in_(values)))

    def get_options(self, view):
        presenters = db_session.query(Presenter).order_by(Presenter.name).all()
        return [(p.name, p.name) for p in presenters]

class TagCategoryMultiFilter(MultiSelectContainsFilter):
    def __init__(self, column, name, category):
        super(TagCategoryMultiFilter, self).__init__(column, name)
        self.category = category

    def apply(self, query, values, alias=None):
        if not values:
            return query
        # Convert single value to list if needed
        if isinstance(values, str):
            values = [values]
        return (query.join(Video.tags)
                .join(Tag.category)
                .filter(and_(
                    TagCategory.name == self.category,
                    Tag.name.in_(values)  # Change to exact matches with in_
                )))

    def get_options(self, view):
        tags = (db_session.query(Tag)
                .join(TagCategory)
                .filter(TagCategory.name == self.category)
                .order_by(Tag.name)
                .all())
        return [(t.name, t.name) for t in tags]

class DateAfterFilter(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        if not value:
            return query
        try:
            # Add debug logging
            log.info(f"Filtering after date: {value}, type: {type(value)}")
            
            # Try multiple datetime formats
            try:
                timestamp = int(datetime.strptime(value, '%Y-%m-%d %H:%M').timestamp())
            except ValueError:
                try:
                    timestamp = int(datetime.strptime(value, '%Y-%m-%d %H:%M:%S').timestamp())
                except ValueError:
                    if isinstance(value, datetime):
                        timestamp = int(value.timestamp())
                    else:
                        return query

            log.info(f"Converted timestamp: {timestamp}")
            return query.filter(self.column >= timestamp)
        except Exception as e:
            log.error(f"Error in DateAfterFilter: {e}")
            return query

    def operation(self):
        return 'greater'

class DateBeforeFilter(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        if not value:
            return query
        try:
            try:
                timestamp = int(datetime.strptime(value, '%Y-%m-%d %H:%M').timestamp())
            except ValueError:
                try:
                    timestamp = int(datetime.strptime(value, '%Y-%m-%d %H:%M:%S').timestamp())
                except ValueError:
                    if isinstance(value, datetime):
                        timestamp = int(value.timestamp())
                    else:
                        return query

            return query.filter(self.column <= timestamp)
        except Exception as e:
            log.error(f"Error in DateBeforeFilter: {e}")
            return query

    def operation(self):
        return 'less'

class DateEqualsFilter(BaseSQLAFilter):
    def apply(self, query, value, alias=None):
        if not value:
            return query
        try:
            try:
                timestamp = int(datetime.strptime(value, '%Y-%m-%d %H:%M').timestamp())
            except ValueError:
                try:
                    timestamp = int(datetime.strptime(value, '%Y-%m-%d %H:%M:%S').timestamp())
                except ValueError:
                    if isinstance(value, datetime):
                        timestamp = int(value.timestamp())
                    else:
                        return query

            next_day = timestamp + 86400  # Add 24 hours
            return query.filter(and_(
                self.column >= timestamp,
                self.column < next_day
            ))
        except Exception as e:
            log.error(f"Error in DateEqualsFilter: {e}")
            return query

    def operation(self):
        return 'equals'

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

    # Remove the default column_filters since we're using custom ones
    column_filters = None

    # Remove search functionality
    column_searchable_list = None

    def get_filters(self):
        filters = []
        
        filters.extend([
            ContainsFilter(
                Video.title, 'Title'
            ),
            PresenterFilter(
                Video.presenters, 'Presenters'
            ),
            TagCategoryMultiFilter(
                Video.tags, 'Topic Tags', 'Topic'
            ),
            TagCategoryMultiFilter(
                Video.tags, 'Event Tags', 'Event'
            ),
            TagCategoryMultiFilter(
                Video.tags, 'Date Tags', 'Date'
            ),
            DateAfterFilter(
                Video.unixstart, 'Start Date After'
            ),
            DateBeforeFilter(
                Video.unixstart, 'Start Date Before'
            ),
            DateAfterFilter(
                Video.unixend, 'End Date After'
            ),
            DateBeforeFilter(
                Video.unixend, 'End Date Before'
            )
        ])
        
        return filters

    # Keep the query methods for proper joining
    def get_query(self):
        return (
            super(VideoModelView, self)
            .get_query()
            .outerjoin(Video.presenters)
            .outerjoin(Video.tags)
            .outerjoin(Tag.category)
            .distinct()
        )

    def get_count_query(self):
        return (
            super(VideoModelView, self)
            .get_count_query()
            .outerjoin(Video.presenters)
            .outerjoin(Video.tags)
            .outerjoin(Tag.category)
            .distinct()
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
        
        # Set template paths
        self.edit_template = 'admin/model/edit.html'
        self.create_template = 'admin/model/create.html'
        self.named_filter_urls = True
        
        # Add model templates directory
        self.model_template_path = 'admin/model'

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

    @property
    def list_template(self):
        """Override list template to add upload form"""
        return 'admin/video_list.html'

    @expose('/import-json', methods=['POST'])
    def import_json(self):
        if 'json_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('.index_view'))
            
        file = request.files['json_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('.index_view'))
            
        if not file.filename.endswith('.json'):
            flash('File must be a JSON', 'error')
            return redirect(url_for('.index_view'))
            
        try:
            # Read JSON file
            json_data = json.loads(file.read().decode('UTF8'))
            
            # Process each video
            for video_data in json_data:
                # Convert timestamps
                try:
                    unixstart = int(datetime.strptime(video_data['start_time'], '%Y-%m-%d %H:%M').timestamp())
                    unixend = int(datetime.strptime(video_data['end_time'], '%Y-%m-%d %H:%M').timestamp())
                except (ValueError, KeyError):
                    continue

                # Create or update video
                video = db_session.query(Video).filter_by(title=video_data['title']).first()
                if not video:
                    video = Video(
                        title=video_data['title'],
                        description=video_data.get('description', ''),
                        unixstart=unixstart,
                        unixend=unixend,
                        stream=video_data.get('stream'),
                        slides=video_data.get('slides'),
                        recording=video_data.get('recording'),
                        chat_log=video_data.get('chat_log'),
                        thumbnails=video_data.get('thumbnails'),
                        calendar_event=video_data.get('calendar_event')
                    )
                    db_session.add(video)
                else:
                    video.description = video_data.get('description', '')
                    video.unixstart = unixstart
                    video.unixend = unixend
                    video.stream = video_data.get('stream')
                    video.slides = video_data.get('slides')
                    video.recording = video_data.get('recording')
                    video.chat_log = video_data.get('chat_log')
                    video.thumbnails = video_data.get('thumbnails')
                    video.calendar_event = video_data.get('calendar_event')

                # Handle presenters
                presenter_names = video_data.get('presenters', [])
                video.presenters = []
                for name in presenter_names:
                    presenter = db_session.query(Presenter).filter_by(name=name).first()
                    if presenter:
                        video.presenters.append(presenter)

                # Handle tags
                tag_data = video_data.get('tags', [])
                video.tags = []
                for tag_info in tag_data:
                    tag = db_session.query(Tag).join(TagCategory).filter(
                        Tag.name == tag_info['name'],
                        TagCategory.name == tag_info['category']
                    ).first()
                    if tag:
                        video.tags.append(tag)
            
            db_session.commit()
            flash('Videos imported successfully', 'success')
            
        except Exception as e:
            db_session.rollback()
            log.error(f"Error importing JSON: {e}")
            flash('Error importing JSON file', 'error')
            
        return redirect(url_for('.index_view'))

    @expose('/export-json', methods=['GET'])
    def export_json(self):
        try:
            # Query all videos with their relationships
            videos = db_session.query(Video).order_by(Video.unixstart.desc()).all()
            
            # Create JSON data
            video_list = []
            for video in videos:
                # Format timestamps
                start_time = datetime.fromtimestamp(video.unixstart).strftime('%Y-%m-%d %H:%M')
                end_time = datetime.fromtimestamp(video.unixend).strftime('%Y-%m-%d %H:%M')
                
                video_data = {
                    'title': video.title,
                    'description': video.description or '',
                    'start_time': start_time,
                    'end_time': end_time,
                    'stream': video.stream or '',
                    'slides': video.slides or '',
                    'recording': video.recording or '',
                    'chat_log': video.chat_log or '',
                    'thumbnails': video.thumbnails or '',
                    'calendar_event': video.calendar_event or '',
                    'presenters': [p.name for p in video.presenters] if video.presenters else [],
                    'tags': [{'name': t.name, 'category': t.category.name} for t in video.tags] if video.tags else []
                }
                video_list.append(video_data)
            
            # Create the response
            response = flask.make_response(json.dumps(video_list, indent=2))
            response.headers["Content-Disposition"] = "attachment; filename=videos.json"
            response.headers["Content-type"] = "application/json"
            
            return response
            
        except Exception as e:
            log.error(f"Error exporting JSON: {e}")
            flash('Error exporting JSON file', 'error')
            return redirect(url_for('.index_view'))

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
    column_list = ['name', 'email', 'hrc_id', 'headshot']
    form_columns = ['name', 'email', 'hrc_id', 'headshot']

    @property
    def list_template(self):
        return 'admin/presenter_list.html'

    @expose('/import-json', methods=['POST'])
    def import_json(self):
        if 'json_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('.index_view'))
            
        file = request.files['json_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('.index_view'))
            
        if not file.filename.endswith('.json'):
            flash('File must be a JSON', 'error')
            return redirect(url_for('.index_view'))
            
        try:
            # Read JSON file
            json_data = json.loads(file.read().decode('UTF8'))
            
            # Process each presenter
            for presenter_data in json_data:
                if not presenter_data.get('name') or not presenter_data.get('hrc_id'):
                    continue
                
                # Check if presenter exists by hrc_id
                presenter = db_session.query(Presenter).filter_by(hrc_id=presenter_data['hrc_id']).first()
                if not presenter:
                    presenter = Presenter(
                        name=presenter_data['name'],
                        email=presenter_data.get('email'),
                        hrc_id=presenter_data['hrc_id'],
                        headshot=presenter_data.get('headshot')
                    )
                    db_session.add(presenter)
                else:
                    # Update existing presenter
                    presenter.name = presenter_data['name']
                    presenter.email = presenter_data.get('email')
                    if presenter_data.get('headshot'):
                        presenter.headshot = presenter_data['headshot']
            
            db_session.commit()
            flash('Presenters imported successfully', 'success')
            
        except Exception as e:
            db_session.rollback()
            log.error(f"Error importing JSON: {e}")
            flash('Error importing JSON file', 'error')
            
        return redirect(url_for('.index_view'))

    @expose('/export-json', methods=['GET'])
    def export_json(self):
        try:
            # Query all presenters
            presenters = db_session.query(Presenter).order_by(Presenter.name).all()
            
            # Create JSON data
            presenter_list = []
            for presenter in presenters:
                presenter_data = {
                    'name': presenter.name,
                    'email': presenter.email or '',
                    'hrc_id': presenter.hrc_id,
                    'headshot': presenter.headshot or ''
                }
                presenter_list.append(presenter_data)
            
            # Create the response
            response = flask.make_response(json.dumps(presenter_list, indent=2))
            response.headers["Content-Disposition"] = "attachment; filename=presenters.json"
            response.headers["Content-type"] = "application/json"
            
            return response
            
        except Exception as e:
            log.error(f"Error exporting JSON: {e}")
            flash('Error exporting JSON file', 'error')
            return redirect(url_for('.index_view'))