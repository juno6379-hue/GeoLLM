import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

def setup_telemetry():
    """
    OpenTelemetry Tracer Provider 설정.
    로컬 환경을 위해 Console Export를 사용하며, 향후 Jaeger/Zipkin 등으로 확장 가능합니다.
    """
    service_name = os.getenv("OTEL_SERVICE_NAME", "marine-geollm")
    
    resource = Resource.create(attributes={
        "service.name": service_name
    })
    
    provider = TracerProvider(resource=resource)
    
    # 개발/디버깅 시 콘솔 출력 (운영 시에는 OTLPSpanExporter 등으로 교체)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    
    return provider
