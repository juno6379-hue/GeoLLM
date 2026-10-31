"""Explicit, bounded research-only variations of production graph settings."""
import math

BASE_METHOD = 'P_current_production_model_enabled_restricted'
DEFAULT_TIMEOUT = 2.5
TIMEOUT_ENV = 'GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC'
ROUTING_TIMEOUT_ENV = 'GEOLLM_ROUTING_FALLBACK_TIMEOUT_SEC'


def graph_condition(profile):
    value = profile.get('semantic_prior_timeout_seconds', DEFAULT_TIMEOUT)
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not DEFAULT_TIMEOUT <= value <= 180):
        raise ValueError('Research semantic prior timeout must be finite, 2.5..180 seconds')
    changed = value != DEFAULT_TIMEOUT
    condition = {
        'method': BASE_METHOD + (f'_semantic_prior_timeout_{value:g}s' if changed else ''),
        'semantic_prior_timeout_seconds': float(value),
        'production_default_timeout_seconds': DEFAULT_TIMEOUT,
        'research_timeout_override': changed,
        'generation_quality_verified': False,
        'interpretation': 'Explicit runtime deadlines; not evidence of successful generation, isolated timeout effects or equal-compute comparison',
    }
    if 'routing_fallback_timeout_seconds' in profile:
        routing = profile['routing_fallback_timeout_seconds']
        if isinstance(routing, bool) or not isinstance(routing, (int, float)) or not math.isfinite(routing) or not 0.1 <= routing <= 60:
            raise ValueError('Research routing fallback timeout must be finite, 0.1..60 seconds')
        condition['routing_fallback_timeout_seconds'] = float(routing)
        condition['method'] += f'_routing_fallback_{routing:g}s'
    return condition


def graph_condition_environment(profile):
    condition = graph_condition(profile)
    environment = {TIMEOUT_ENV: format(condition['semantic_prior_timeout_seconds'], 'g')}
    if 'routing_fallback_timeout_seconds' in condition:
        environment[ROUTING_TIMEOUT_ENV] = format(condition['routing_fallback_timeout_seconds'], 'g')
    return environment


def validate_condition_environment(profile, environment):
    expected = graph_condition_environment(profile)[TIMEOUT_ENV]
    if environment.get(TIMEOUT_ENV, str(DEFAULT_TIMEOUT)) != expected:
        raise RuntimeError('Research semantic prior timeout differs from fixed profile')
    if ROUTING_TIMEOUT_ENV in graph_condition_environment(profile):
        if environment.get(ROUTING_TIMEOUT_ENV) != graph_condition_environment(profile)[ROUTING_TIMEOUT_ENV]:
            raise RuntimeError('Research routing fallback timeout differs from fixed profile')
