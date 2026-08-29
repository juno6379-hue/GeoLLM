"""KG context contracts shared by specialist analysis agents."""
from pathlib import Path
from services.orchestrator.graph_rag_retriever import discover_graph_context

ROOT=Path(__file__).resolve().parents[2]

def build_specialist_kg_context(agent_name, request):
    supplied=getattr(request,'graph_context',None) or request.previous_agent_outputs.get('graph_context',{})
    graph=discover_graph_context(supplied, request.original_query)
    plan=request.task_plan
    slots=plan.slots if plan else {}
    if agent_name=='spatial':
        return {'target_features': supplied.get('target_features',[]) or slots.get('target_features',[]),
                'target_layers': supplied.get('target_layers',[]) or graph['rag_filters'].get('related_layers',['GBENC_S101_feature']),
                'query_template': slots.get('query_template','feature_search_by_radius'),
                'postgis_tool': slots.get('tool','postgis.dwithin'), 'source': 'S100_dev_postgis v2',
                'graph_paths': graph['graph_paths'], 'provenance': graph['provenance']}
    if agent_name=='traffic':
        layers=supplied.get('target_dynamic_layers',[]) or ['AIS','V-PASS']
        return {'target_dynamic_layers':layers,'traffic_metrics':['traffic_density','major_route','small_vessel_route','route_overlap','collision_risk'],
                'graph_paths':graph['graph_paths'],'provenance':graph['provenance']}
    if agent_name=='accident':
        return {'required_inputs':['accident_events','accident_types','accident_hotspot','accident_feature_relation','accident_traffic_correlation'],
                'graph_paths':graph['graph_paths'],'provenance':graph['provenance']}
    if agent_name=='validation':
        return {'required_inputs':['S-101 DCEG','S-158','source provenance','graph path consistency'],
                'graph_paths':graph['graph_paths'],'provenance':graph['provenance']}
    return {'required_inputs':['spatial results','traffic overlay','accident overlay','RAG evidence','graph explanation'],
            'graph_paths':graph['graph_paths'],'provenance':graph['provenance']}
