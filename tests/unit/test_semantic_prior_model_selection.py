import io
import json

import pytest

from services.orchestrator import semantic_prior as prior


KEYS = ('GEOLLM_OLLAMA_MODEL', 'OLLAMA_MODEL', 'GEOLLM_WEB_SHADOW_MODEL')


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    for key in (*KEYS, 'GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC', 'GEOLLM_SEMANTIC_PRIOR_OLLAMA', 'OLLAMA_GENERATE_URL'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('OLLAMA_BASE_URL', 'http://test.invalid:11434')
    monkeypatch.setenv('LLM_MODEL', 'gemma2')


def test_model_precedence_keeps_explicit_research_condition(monkeypatch):
    monkeypatch.setenv(KEYS[2], 'qwen-shadow')
    assert prior.semantic_prior_model() == ('qwen-shadow', KEYS[2])
    monkeypatch.setenv(KEYS[1], 'qwen-ollama')
    assert prior.semantic_prior_model() == ('qwen-ollama', KEYS[1])
    monkeypatch.setenv(KEYS[0], 'qwen-research')
    assert prior.semantic_prior_model() == ('qwen-research', KEYS[0])


def test_blank_settings_fall_through_without_general_llm_coupling(monkeypatch):
    assert prior.semantic_prior_model() == ('llama3.1', 'legacy_default')
    monkeypatch.setenv(KEYS[0], ' ')
    monkeypatch.setenv(KEYS[1], '')
    monkeypatch.setenv(KEYS[2], 'qwen2.5:1.5b')
    assert prior.semantic_prior_model() == ('qwen2.5:1.5b', KEYS[2])


@pytest.mark.parametrize('configured_timeout,expected', [(None, 2.5), ('180', 180.0)])
def test_request_uses_selected_model_and_unchanged_timeout(monkeypatch, configured_timeout, expected):
    monkeypatch.setenv(KEYS[2], 'qwen2.5:1.5b')
    if configured_timeout:
        monkeypatch.setenv('GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC', configured_timeout)
    calls = []
    def fake_urlopen(request, timeout):
        calls.append((json.loads(request.data), timeout))
        return io.BytesIO(json.dumps({'response': '{"is_place_like":false}'}).encode())
    monkeypatch.setattr(prior.urllib.request, 'urlopen', fake_urlopen)
    result = prior._ollama_prior('ambiguous fixture', [])
    assert calls[0][0]['model'] == 'qwen2.5:1.5b'
    assert calls[0][1] == expected
    assert result['authority'] == 'candidate_only'
    assert result['model_selection_source'] == KEYS[2]


def test_trace_records_selection_even_when_ollama_disabled(monkeypatch):
    monkeypatch.setenv(KEYS[2], 'qwen2.5:1.5b')
    def forbidden(*args, **kwargs):
        raise AssertionError('disabled prior must not call model')
    monkeypatch.setattr(prior.urllib.request, 'urlopen', forbidden)
    trace = prior.build_semantic_prior('fixture', allow_ollama=False)['ollama']
    assert trace['model'] == 'qwen2.5:1.5b'
    assert trace['model_selection_source'] == KEYS[2]
    assert trace['used'] is False
    assert trace['timeout_seconds'] == '2.5'
