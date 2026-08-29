import geopandas as gpd
from sqlalchemy import create_engine

def import_shapefile():
    print("Loading shapefile...")
    # The shapefile was copied to /app/data
    shp_path = "/app/data/TB_AREA_NAME_OCEAN.shp"
    
    # KHOA shapefiles are usually in EPSG:4326 or EPSG:5179
    gdf = gpd.read_file(shp_path, encoding='cp949') # CP949 or EUC-KR for Korean
    
    if gdf.crs is None or gdf.crs.to_string() != 'EPSG:4326':
        print(f"Converting CRS from {gdf.crs} to EPSG:4326...")
        gdf = gdf.to_crs(epsg=4326)
    
    engine = create_engine("postgresql://postgres:postgres@db:5432/marine_geo")
    
    print("Writing to PostGIS table 'maritime_gazetteer_khoa'...")
    gdf.to_postgis("maritime_gazetteer_khoa", engine, if_exists="replace", index=False)
    print("Import successful!")

if __name__ == "__main__":
    import_shapefile()
