"""Actual isolated P1 adapter preflight, no model or operational API calls."""
import json
import os
from pathlib import Path
from .graph_source_scope import install


def main():
    snapshot=json.loads(Path('/research_snapshot/snapshot_manifest.json').read_text())
    installation=install(snapshot,'/research_snapshot')
    from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter
    from services.orchestrator.execution_validator import validate_execution_context,is_execution_authorized
    from shared.schemas.agent import QueryExecutionContext,ExecutionSlots
    import psycopg2
    records=[]
    for name,query,point,features,layers,expected in [
        ('q4','독도 반경 5km 해양지명을 찾아줘','POINT(131.86955555555556 37.24077777777778)',[],['marine_gazetteer'],True),
        ('control','기준점 반경 1000m Wreck','POINT(129.05 35.1)',['Wreck'],[],True),
        ('outside','독도 반경 1000m Wreck','POINT(131.87 37.24)',['Wreck'],[],False)]:
        qec=QueryExecutionContext(original_query=query,route_plan={'analysis_type':'feature_search_by_radius'},
            slots=ExecutionSlots(reference_geometry=point,crs='EPSG:4326',distance_m=5000 if name=='q4' else 1000,
                target_features=features,target_layers=layers))
        with psycopg2.connect(os.environ['S101_DB_URL']) as connection:
            connection.set_session(readonly=True,isolation_level='REPEATABLE READ')
            adapter=SchemaBindingAdapter(connection=connection)
            checked=validate_execution_context(qec,binding_adapter=adapter)
            records.append({'case':name,'expected':expected,'authorized':is_execution_authorized(checked),
                'blockers':checked.blockers,'scope':checked.provenance.get('coverage_validation'),
                'source_checks':getattr(adapter,'research_source_checks',[])})
    result={'installation':installation,'cases':records,'passed':all(x['authorized']==x['expected'] for x in records)}
    Path('/out/graph_source_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'passed':result['passed'],'cases':[{k:r[k] for k in ('case','authorized','blockers')} for r in records]}))
    raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
