from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, RadioField, validators

class MasterclassRegistrationForm(FlaskForm):
    title = StringField('Name of session', [
        validators.DataRequired(),
        validators.Length(min=3, max=200)
    ])
    
    description = TextAreaField('Description', [
        validators.DataRequired(),
        validators.Length(min=20)
    ])
    
    duration = RadioField(
        'Duration',
        choices=[
            ('30', 'Up to 30 mins'),
            ('45', 'Up to 45 mins'),
            ('60', 'Up to 1 hour'),
            ('other', 'Other')
        ],
        validators=[validators.DataRequired()]
    )
    
    duration_other = StringField('Other duration')

class MasterclassSubmissionForm(FlaskForm):
    title = StringField('Name of session', validators=[validators.DataRequired()])
    description = TextAreaField('Description', validators=[validators.DataRequired()])
    duration = RadioField(
        'Duration',
        choices=[
            ('30', 'Up to 30 mins'),
            ('45', 'Up to 45 mins'),
            ('60', 'Up to 1 hour'),
            ('other', 'Other')
        ],
        validators=[validators.DataRequired()]
    )
    duration_other = StringField('Other duration') 