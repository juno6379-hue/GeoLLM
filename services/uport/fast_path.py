"""Deterministic U-Port map signal extraction before Registry retrieval."""

from services.uport.planning import MapSelection


class UportFastPathRouter:
    """Select a Registry capability from an explicit map event only.

    This fast path cannot execute or skip Ontology/ExecutionValidator gates.
    Natural-language-only requests still pass through Registry retrieval.
    """

    def capability_for_selection(self, selection: MapSelection | None) -> str | None:
        if selection is None:
            return None
        # The UI's typed selection has already been schema checked. Resolver
        # Registry validation follows before the plan can become ready.
        return "uport.s101.berth.search"
