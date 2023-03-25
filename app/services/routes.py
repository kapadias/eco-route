import googlemaps
import math
from opentelemetry import trace
from ..api.errors import raise_error

tracer = trace.get_tracer(__name__)

GOOGLE_MAPS_API_KEY = "GOOGLE_MAPS_API_KEY"
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


@tracer.start_as_current_span("haversine")
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on Earth using the Haversine formula.

    Args:
    lat1: Latitude of the first point in degrees.
    lon1: Longitude of the first point in degrees.
    lat2: Latitude of the second point in degrees.
    lon2: Longitude of the second point in degrees.

    Returns:
    Distance between two points in meters (float).

    Reference:
    https://en.wikipedia.org/wiki/Haversine_formula
    """
    # Radius of the Earth in meters
    R = 6371e3

    # Convert latitudes and longitudes from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Calculate the Haversine formula
    a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + math.cos(phi1) * math.cos(
        phi2
    ) * math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


@tracer.start_as_current_span("find_ev_stations")
def find_ev_stations(origin: str, destination: str, ev_range: int) -> list:
    """
    Find electric vehicle charging stations along a route using the Google Maps API.

    Args:
    origin: Starting address or latitude and longitude of the route.
    destination: Ending address or latitude and longitude of the route.
    ev_range: Maximum distance an electric vehicle can travel on a single charge in meters.

    Returns:
    List of dictionaries containing information about electric vehicle charging stations.

    Reference:
    https://developers.google.com/maps/documentation/places/web-service/search-nearby
    """

    # Get the route between the origin and destination
    route = gmaps.directions(origin, destination)

    # Extract the end location of each step along the route as waypoints
    waypoints = []
    for step in route[0]["legs"][0]["steps"]:
        waypoints.append(step["end_location"])

    # Search for electric vehicle charging stations near each waypoint
    ev_stations = []
    for waypoint in waypoints:
        nearby_ev_stations = gmaps.places_nearby(
            location=waypoint, radius=ev_range, type="charging_station"
        )
        ev_stations.extend(nearby_ev_stations["results"])

    return ev_stations


@tracer.start_as_current_span("find_nearby_restaurants")
def find_nearby_restaurants(ev_station: dict, food_preference: str) -> list:
    """
    Find nearby restaurants that serve a particular type of food using the Google Maps API.

    Args:
    ev_station: Dictionary containing information about the electric vehicle charging station.
    food_preference: Type of food to search for (e.g., "pizza", "sushi").

    Returns:
    List of dictionaries containing information about nearby restaurants that serve the specified type of food.

    Reference:
    https://developers.google.com/maps/documentation/places/web-service/search-nearby
    """

    # Search for nearby restaurants that serve the specified type of food
    nearby_restaurants = gmaps.places_nearby(
        location=ev_station["geometry"]["location"],
        radius=500,  # Radius in meters
        type="restaurant",
        keyword=food_preference,
    )

    return nearby_restaurants["results"]


@tracer.start_as_current_span("run")
async def run(
    origin: str, destination: str, food_preference: str, ev_range: int
) -> dict:
    """
    Find the top 10 electric vehicle charging stations along a route that are closest to restaurants
    serving a particular type of food using the Google Maps API.

    Args:
    origin: Starting address or latitude and longitude of the route.
    destination: Ending address or latitude and longitude of the route.
    food_preference: Type of food to search for (e.g., "pizza", "sushi").
    ev_range: Maximum distance an electric vehicle can travel on a single charge in meters.

    Returns:
    A dictionary containing information about the top 10 electric vehicle charging stations and nearby
    restaurants that serve the specified type of food, sorted by relevance score.

    Reference:
    https://developers.google.com/maps/documentation/places/web-service/search-nearby
    https://en.wikipedia.org/wiki/Haversine_formula
    """

    # Find electric vehicle charging stations along the route
    ev_stations = find_ev_stations(origin, destination, ev_range)

    # Remove duplicate EV stations
    unique_ev_stations = {
        station["place_id"]: station for station in ev_stations
    }.values()

    ranked_results = []

    # Find nearby restaurants for each unique EV station and calculate relevance score
    for ev_station in unique_ev_stations:
        restaurants = find_nearby_restaurants(ev_station, food_preference)

        if restaurants:
            nearby_restaurants = []
            for restaurant in restaurants:
                # Calculate the distance between the EV station and the restaurant
                distance = haversine(
                    ev_station["geometry"]["location"]["lat"],
                    ev_station["geometry"]["location"]["lng"],
                    restaurant["geometry"]["location"]["lat"],
                    restaurant["geometry"]["location"]["lng"],
                )
                # Add the restaurant to the list of nearby restaurants for this EV station
                nearby_restaurants.append(
                    {
                        "name": restaurant["name"],
                        "address": restaurant["vicinity"],
                        "location": restaurant["geometry"]["location"],
                        "distance": distance,
                    }
                )

            # Calculate the relevance score for this EV station
            relevance_score = sum(
                [
                    1 / (r["distance"] if r["distance"] != 0 else 0.0001)
                    for r in nearby_restaurants
                ]
            )

            # Add the ranked results for this EV station to the list of all ranked results
            ranked_results.append(
                {
                    "relevance_score": relevance_score,
                    "ev_station": ev_station,
                    "restaurants": nearby_restaurants,
                }
            )

    # Sort the ranked results by relevance score in descending order
    ranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Get the top 10 ranked results
    top_results = ranked_results[:10]

    # Add rank to each result
    for i, result in enumerate(top_results, start=1):
        result["rank"] = i

    # Format the output
    output = {
        "results": [
            {
                "rank": result["rank"],
                "relevance_score": result["relevance_score"],
                "ev_station": {
                    "name": result["ev_station"]["name"],
                    "address": result["ev_station"]["vicinity"],
                    "location": {
                        "latitude": result["ev_station"]["geometry"]["location"]["lat"],
                        "longitude": result["ev_station"]["geometry"]["location"][
                            "lng"
                        ],
                    },
                },
                "restaurants": [
                    {
                        "name": restaurant["name"],
                        "address": restaurant["address"],
                        "location": {
                            "latitude": restaurant["location"]["lat"],
                            "longitude": restaurant["location"]["lng"],
                        },
                        "distance": restaurant["distance"],
                    }
                    for restaurant in result["restaurants"]
                ],
            }
            for result in top_results
        ]
    }

    return output
