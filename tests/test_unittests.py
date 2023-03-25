import pytest
from unittest.mock import patch
from app.api.errors import raise_error
from app.services.routes import (
    haversine,
    find_ev_stations,
    find_nearby_restaurants,
    run,
)


@pytest.fixture
def gmaps_client():
    with patch("app.services.routes.gmaps") as mock_gmaps:
        yield mock_gmaps


def test_haversine():
    # Test distance between two same points
    assert haversine(40.7128, -74.0060, 40.7128, -74.0060) == 0.0

    # Test distance between two different points
    assert haversine(40.7128, -74.0060, 51.5074, -0.1278) == pytest.approx(5574745.5, 1)


def test_find_nearby_restaurants(gmaps_client):
    ev_station = {"geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}}
    food_preference = "pizza"

    # Test places_nearby call
    mock_places_nearby = gmaps_client.places_nearby.return_value
    find_nearby_restaurants(ev_station, food_preference)
    gmaps_client.places_nearby.assert_called_once_with(
        location=ev_station["geometry"]["location"],
        radius=500,
        type="restaurant",
        keyword=food_preference,
    )

    # Test return value
    mock_places_nearby = gmaps_client.places_nearby.return_value
    mock_places_nearby.__getitem__.return_value = [
        {"name": "Restaurant 1"},
        {"name": "Restaurant 2"},
    ]
    assert (
        find_nearby_restaurants(ev_station, food_preference)
        == mock_places_nearby.__getitem__.return_value
    )
