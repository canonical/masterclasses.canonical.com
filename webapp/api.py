from flask import Blueprint, jsonify
from webapp.database import db_session
from models.presenter import Presenter
from webapp.auth import require_api_token

api = Blueprint("api", __name__)

# Get all presenters
@api.route("/v1/presenters", methods=['GET'])
@require_api_token
def get_presenters():
    presenters = db_session.query(Presenter).all()
    return jsonify([{'id': p.id, 'name': p.name, 'hrc_id': p.hrc_id, 'email': p.email} for p in presenters])

# Get a presenter by ID
@api.route("/v1/presenters/<id>", methods=['GET'])
@require_api_token
def get_presenter(id):
    presenter = db_session.query(Presenter).filter_by(id=id).first()
    return jsonify({'id': presenter.id, 'name': presenter.name, 'hrc_id': presenter.hrc_id, 'email': presenter.email})

# Get all talks for a presenter by HRC ID
@api.route("/v1/presenters/<hrc_id>/talks", methods=['GET'])
@require_api_token
def get_presenter_talks(hrc_id):
    presenter = db_session.query(Presenter).filter_by(hrc_id=hrc_id).first()
    
    if not presenter:
        return jsonify({'error': 'Presenter not found'}), 404
        
    return jsonify({
        'talks': [{
            'id': video.id,
            'title': video.title,
            'description': video.description,
            'start_time': video.unixstart,
            'end_time': video.unixend,
            'recording_url': video.recording,
            'slides_url': video.slides,
            'presenters': [{'name': p.name, 'hrc_id': p.hrc_id} for p in video.presenters],
            'tags': [{'name': t.name, 'category': t.category.name} for t in video.tags]
        } for video in presenter.videos]
    })

# Get all talks for a presenter by email
@api.route("/v1/presenters/email/<email>/talks", methods=['GET'])
@require_api_token
def get_presenter_talks_by_email(email):
    presenter = db_session.query(Presenter).filter_by(email=email).first()
    
    if not presenter:
        return jsonify({'error': 'Presenter not found'}), 404
        
    return jsonify({
        'talks': [{
            'id': video.id,
            'title': video.title,
            'description': video.description,
            'start_time': video.unixstart,
            'end_time': video.unixend,
            'recording_url': video.recording,
            'slides_url': video.slides,
            'presenters': [{'name': p.name, 'email': p.email} for p in video.presenters],
            'tags': [{'name': t.name, 'category': t.category.name} for t in video.tags]
        } for video in presenter.videos]
    })