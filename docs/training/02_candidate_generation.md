# Candidate Generation

`prompts/training/SEED_EXPANSION_PROMPT.md` is the generation contract. The deterministic dry-run adapter exercises paraphrase, slot variation, hard-negative, ambiguity, and conversational follow-up categories. All generated records remain `CANDIDATE`; registry and ontology mutation is outside this pipeline.

Full-scale generation should replace the deterministic adapter with an approved model runner while retaining the same Pydantic output contract, snapshot input, validation gates, and lineage.
