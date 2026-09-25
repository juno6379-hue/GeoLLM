"""Report evaluation availability without inventing calibrated accuracy."""


def unmeasured_quality(*, method="not_evaluated", **observations):
    return {
        "intent_similarity": None,
        "kg_similarity": None,
        "evidence_similarity": None,
        "evidence_average_similarity": None,
        "analysis_completeness": None,
        "estimated_accuracy": None,
        "confidence_band": "not_evaluated",
        "method": method,
        "evaluation_status": "NOT_EVALUATED",
        "observations": observations,
        "notes": ["No calibrated or gold-label accuracy measurement is available for this response."],
    }
