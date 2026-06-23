from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from core.config import settings

def setup_tracing():
    resource = Resource(attributes={
        "service.name": settings.app_name,
        "deployment.environment": settings.environment
    })

    provider = TracerProvider(resource=resource)

    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

def get_tracer(name: str):
    return trace.get_tracer(name)
