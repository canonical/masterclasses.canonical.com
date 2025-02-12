import json
from models.presenter import Presenter


def test_get_presenters(client, test_db):
    # Add test presenter
    presenter = Presenter(
        name="Test Presenter",
        email="test@canonical.com",
        hrc_id="123"
    )
    test_db.add(presenter)
    test_db.commit()
    
    # Test API endpoint
    response = client.get('/api/v1/presenters')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['name'] == "Test Presenter"


def test_get_presenter_not_found(client):
    response = client.get('/api/v1/presenters/999')
    assert response.status_code == 404