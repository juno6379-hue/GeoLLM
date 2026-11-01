"""Typed public tool interface for plan generation, never slot completion.

The same candidate is frozen before B3/B4/P0/H branch. This schema describes
syntax, not an execution approval or a semantic correctness oracle.
"""
import copy
from .plan_comparison import PLAN_SCHEMA

VERSION = 'typed_tool_plan_v1'


def tool(tool_id, arguments):
    return {'type': 'object', 'required': ['tool_id', 'arguments'],
            'additionalProperties': False,
            'properties': {'tool_id': {'const': tool_id}, 'arguments': arguments}}


def arguments(properties, required):
    return {'type': 'object', 'properties': properties, 'required': required,
            'additionalProperties': False}


TEXT = {'type': 'string', 'minLength': 1}
SPATIAL_ARGUMENTS = arguments({
    'source': {'enum': ['s101', 'marine_places', 'navigation_aids']},
    'feature_types': {'type': 'array', 'items': TEXT},
    'crs': {'type': ['string', 'null']},
    'reference_geometry': {'type': ['string', 'null'], 'description': 'WKT copied from input, not a registry key'},
    'geometry_ref': {'type': ['string', 'null'], 'description': 'Exact key from supplied reference registry'},
    'relation': {'enum': ['dwithin', 'within', 'covers', 'intersects', 'nearest']},
    'radius_m': {'type': ['number', 'null']},
    'analysis_type': {'enum': ['feature_search_by_radius', 'feature_within_area',
                              'feature_search_by_area', 'nearest_feature']},
}, ['source', 'feature_types', 'crs', 'relation', 'radius_m', 'analysis_type'])
TOOL_SCHEMAS = [
    tool('catalogue.search', arguments({'term': TEXT,
        'source': {'const': 's101_feature_catalogue_v2'},
        'analysis_type': {'const': 'public_catalogue_document_lookup'}},
        ['term', 'source', 'analysis_type'])),
    tool('documents.search', arguments({'term': TEXT}, ['term'])),
    tool('places.resolve', arguments({'name': TEXT}, ['name'])),
    tool('spatial.query', SPATIAL_ARGUMENTS),
]
TOOL_PLAN_SCHEMA = copy.deepcopy(PLAN_SCHEMA)
TOOL_PLAN_SCHEMA['properties']['spatial_relation']['enum'].append('covers')
TOOL_PLAN_SCHEMA['properties']['tool_calls']['items'] = {'oneOf': TOOL_SCHEMAS}

TOOL_INSTRUCTIONS = '''These are optional tool interfaces, not example argument values or a required call sequence.
Choose only the tool needed by the request. source is ONE enum string, never a list.
All spatial arguments belong in the individual call; top-level slots are not inherited.
reference_geometry contains supplied WKT; geometry_ref contains a supplied registry key. Never exchange them.
No geometry or CRS may be invented. If a required input is absent, clarify and list missing_inputs; no calls.
Use exact feature codes available in public evidence; do not copy schema descriptions as values.
Operator to analysis_type: dwithin=feature_search_by_radius; within/covers=feature_within_area;
intersects=feature_search_by_area; nearest=nearest_feature. nearest radius_m is null.
within excludes boundary; covers includes boundary. No automatic result chaining is supported.
Catalogue terms are actual requested feature codes, document terms actual requested substrings,
and place names actual requested names. Do not execute every listed tool.
Coverage is a common executor safety floor; out-of-scope is not empty. Preserve independent document subtasks.
action clarify/unsupported executes no calls. Answers precede execution and cannot claim returned objects.
'''
