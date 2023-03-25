# Eco-Route
Eco-Route Planner is a web application that helps electric vehicle (EV) owners find the top 10 EV charging stations 
along a route that are closest to restaurants serving a particular type of food. 
The application uses the Google Maps API to find charging stations and restaurants and is deployed using FastAPI.

## Directory Structure
    .
    ├── app
    │   ├── api
    │   │   ├── errors.py
    │   │   └── router.py
    │   ├── config
    │   ├── db
    │   ├── services
    │   │   └── routes.py
    │   └── main.py
    ├── config
    │   ├── bandit.yml
    │   └── locust.yml
    ├── tests
    │   ├── test_unittests.py
    │   └── test_loadtests.py
    ├── Dockerfile
    └── README.md

## Setup
- Install [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) if you haven't already. 
- Clone the repository. 
- Run poetry install to set up the virtual environment and install dependencies. 
- Add your Google Maps API key in ./app/services/routes.py (replace GOOGLE_MAPS_API_KEY value).

## Running the Application
- Activate the virtual environment using `poetry shell`.
- Install dependencies using `poetry install`
- Set python environment `export PYTHONPATH=${PYTHONPATH}:${PWD}`
- Run the application `python app/main.py`

## API Usage
Endpoint: `/v1/eco-route`

#### Input JSON:
```json
{
    "origin": "longmeadow, ma",
    "destination": "brighton, ma",
    "food_preference": "pizza",
    "ev_range": 25000
}
```
The input JSON should include the origin, destination, food preference, and EV range in meters.

#### Output:

The output JSON will contain a list of the top 10 EV charging stations and nearby restaurants that serve the specified 
type of food, sorted by relevance score. Each result will include the rank, relevance score, EV station details, 
and restaurant details.
