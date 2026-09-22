# Marine GeoLLM training framework

Canonical, registry-grounded training cases and derived views.

Run the verified dry workflow from the repository root:

```powershell
python -m scripts.training.build_seed_catalog
python -m training.pipeline schema
python -m scripts.training.run_training_framework
python -m pytest tests/unit/test_training_framework.py -q
```

The seed catalog contains 30 authoring cases. Only three reviewed navigation seeds are currently APPROVED; all other domain seeds remain REVIEW_REQUIRED and are excluded from expansion. Generated data remains CANDIDATE until an explicit reviewer uses `approve_training_cases.py`.
