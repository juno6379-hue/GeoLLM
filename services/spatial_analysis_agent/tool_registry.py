import os
import yaml
from typing import Dict
from shared.observability.logger import get_logger

logger = get_logger("spatial_analysis_agent.tool_registry")

class QueryTemplateRegistry:
    def __init__(self):
        self.templates: Dict[str, dict] = {}
        self.load_registry()

    def load_registry(self):
        registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "query_template_registry.yaml")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "templates" in data:
                        self.templates = data["templates"]
                logger.info(f"Loaded Query Template Registry from {registry_path}")
            except Exception as e:
                logger.error("Failed to load Query Template Registry", error=str(e))
                
    def get_template_sql(self, tool_name: str) -> str:
        if tool_name not in self.templates:
            raise ValueError(f"Tool '{tool_name}' is not registered in Query Template Registry.")
        return self.templates[tool_name].get("sql_template", "")

_registry_instance = QueryTemplateRegistry()

def get_query_template(tool_name: str, table_name: str, nftc_codes: list = None, map_bounds: bool = False) -> str:
    """안전한 SQL 템플릿 반환 (yaml에서 로드된 SQL 반환)"""
    template = _registry_instance.get_template_sql(tool_name)
    
    # 레거시 템플릿용 포매팅 지원
    if "{" in template and "}" in template:
        actual_table = table_name
        if table_name == "gbenc_feature" or table_name == "enc_feature":
            actual_table = "feature f"
            
        select_id = "f.seq as id" if "feature f" in actual_table else "id"
        select_join = ", ci.name as feature_name, f.nftc" if "feature f" in actual_table else ""
        join_clause = "LEFT JOIN codeinformation ci ON ci.type = 0 AND ci.code = f.nftc" if "feature f" in actual_table else ""
        
        nftc_clause = ""
        if nftc_codes and "feature f" in actual_table:
            safe_codes = ",".join([str(int(c)) for c in nftc_codes])
            nftc_clause = f"AND f.nftc IN ({safe_codes})"
            
        geom_col = "f.geom" if "feature f" in actual_table else "geom"
        cte_clause = ""
        cross_join = ""
        bounds_clause = ""
        
        if tool_name == "dwithin":
            cte_parts = ["ST_SetSRID(ST_GeomFromText(:geom), 4326) AS search_geom"]
            if map_bounds:
                cte_parts.append("ST_SetSRID(ST_GeomFromText(:map_bounds_geom), 4326) AS map_bounds_geom")
                bounds_clause = f"AND {geom_col} && p.map_bounds_geom AND ST_Intersects({geom_col}, p.map_bounds_geom)"
            cte_clause = "WITH params AS (\n    SELECT " + ",\n           ".join(cte_parts) + "\n)"
            cross_join = "CROSS JOIN params AS p"
        else:
            if map_bounds:
                bounds_clause = f"AND ST_Intersects({geom_col}, ST_SetSRID(ST_GeomFromText(:map_bounds_geom), 4326))"
                
        return template.format(
            table=actual_table, 
            select_id=select_id,
            select_join=select_join,
            join_clause=join_clause,
            nftc_clause=nftc_clause,
            bounds_clause=bounds_clause,
            cte_clause=cte_clause,
            cross_join=cross_join,
            geom_col=geom_col
        )
        
    return template
