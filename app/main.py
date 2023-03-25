import uvicorn
from fastapi import FastAPI
from app.api.router import router
from app.api.errors import raise_error
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

app = FastAPI()

# Configure opentelemetry
FastAPIInstrumentor.instrument_app(app)

tracer_provider = TracerProvider()
# cloud_trace_exporter = CloudTraceSpanExporter()
# tracer_provider.add_span_processor(
#     # BatchSpanProcessor buffers spans and sends them in batches in a
#     # background thread. The default parameters are sensible, but can be
#     # tweaked to optimize your performance
#     BatchSpanProcessor(cloud_trace_exporter)
# )
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)


app.add_exception_handler(Exception, raise_error)

# Include the router in the main FastAPI application
app.include_router(router, prefix="/v1")


# Run the app
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        use_colors=True,
    )
