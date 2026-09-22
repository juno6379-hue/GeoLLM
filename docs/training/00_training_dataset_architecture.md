# Marine GeoLLM Training Dataset Architecture

The canonical case is `training.models.TrainingCase`; JSON Schema is generated from that model. Registry-grounded golden seeds produce synthetic candidates, validation quarantines failures, explicit human approval alone can merge cases into the master dataset, and task views are projections rather than independently labelled copies.

Flow: `seed authoring YAML → canonical seed JSONL → CANDIDATE expansion → schema/registry/dependency/leakage validation → human approval → approved master → task views`.

Gold teacher-forcing views and raw-query end-to-end views remain separate to prevent target leakage. Dynamic answers require a frozen fixture; behavioral cases may specify requirements but never fabricated result values.
