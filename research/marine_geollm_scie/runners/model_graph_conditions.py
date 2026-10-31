"""Explicit, bounded research-only variations of production graph settings."""
import math

BASE_METHOD = 'P_current_production_model_enabled_restricted'
DEFAULT_TIMEOUT = 2.5
TIMEOUT_ENV = 'GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC'


def graph_condition(profile):
    value = profile.get('semantic_prior_timeout_seconds', DEFAULT_TIMEOUT)
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not DEFAULT_TIMEOUT <= value <= 180):
        raise ValueError('Research semantic prior timeout must be finite, 2.5..180 seconds')
    changed = value != DEFAULT_TIMEOUT
    return {
        'method': BASE_METHOD + (f'_semantic_prior_timeout_{value:g}s' if changed else ''),
        'semantic_prior_timeout_seconds': float(value),
        'production_default_timeout_seconds': DEFAULT_TIMEOUT,
        'research_timeout_override': changed,
        'generation_quality_verified': False,
        'interpretation': 'Timeout condition only; not evidence of successful model generation or equal-compute comparison',
    }


def graph_condition_environment(profile):
    condition = graph_condition(profile)
    return {TIMEOUT_ENV: format(condition['semantic_prior_timeout_seconds'], 'g')}


def validate_condition_environment(profile, environment):
    expected = graph_condition_environment(profile)[TIMEOUT_ENV]
    if environment.get(TIMEOUT_ENV, str(DEFAULT_TIMEOUT)) != expected:
        raise RuntimeError('Research semantic prior timeout differs from fixed profile')
