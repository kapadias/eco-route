from fastapi import APIRouter, Query
from pydantic import BaseModel
from opentelemetry import trace
from app.services.routes import run

# Create instance of the router
router = APIRouter()
tracer = trace.get_tracer(__name__)


class RideRequest(BaseModel):
    origin: str
    destination: str
    food_preference: str
    ev_range: int


@tracer.start_as_current_span("root")
@router.post("/eco-route")
async def root(
    data: RideRequest,
):
    result = await run(
        data.origin, data.destination, data.food_preference, data.ev_range
    )
    return result
