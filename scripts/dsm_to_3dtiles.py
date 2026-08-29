import rasterio
import rasterio.warp
import numpy as np
import trimesh
import json
import os

def convert_dsm(tif_path):
    print(f"Reading {tif_path} ...")
    with rasterio.open(tif_path) as src:
        # Downsample to max 500x500 for WebGL performance
        max_size = 500
        scale = min(max_size / src.width, max_size / src.height)
        new_width = int(src.width * scale)
        new_height = int(src.height * scale)
        
        print(f"Resampling from {src.width}x{src.height} to {new_width}x{new_height}...")
        data = src.read(1, out_shape=(new_height, new_width), resampling=rasterio.enums.Resampling.bilinear)
        
        west, south, east, north = rasterio.warp.transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
        print(f"WGS84 Bounds: {west}, {south}, {east}, {north}")
        
        width_m = src.bounds.right - src.bounds.left
        height_m = src.bounds.top - src.bounds.bottom
        
        # X goes left to right, Y goes top to bottom
        x = np.linspace(-width_m/2, width_m/2, new_width)
        y = np.linspace(height_m/2, -height_m/2, new_height)
        xv, yv = np.meshgrid(x, y)
        
        nodata = src.nodata
        valid_mask = np.isfinite(data)
        if nodata is not None:
            valid_mask = valid_mask & (data != nodata)
            
        min_z = float(np.min(data[valid_mask]))
        max_z = float(np.max(data[valid_mask]))
        print(f"Elevation: {min_z} to {max_z} meters")
        
        vertices = np.stack([xv.flatten(), yv.flatten(), data.flatten()], axis=-1)
        
        i, j = np.meshgrid(np.arange(new_height-1), np.arange(new_width-1), indexing='ij')
        v0 = i * new_width + j
        v1 = v0 + 1
        v2 = (i + 1) * new_width + j
        v3 = v2 + 1
        
        f1 = np.stack([v0, v2, v1], axis=-1).reshape(-1, 3)
        f2 = np.stack([v1, v2, v3], axis=-1).reshape(-1, 3)
        faces = np.vstack([f1, f2])
        
        valid_v0 = valid_mask.flatten()[faces[:, 0]]
        valid_v1 = valid_mask.flatten()[faces[:, 1]]
        valid_v2 = valid_mask.flatten()[faces[:, 2]]
        valid_faces_mask = valid_v0 & valid_v1 & valid_v2
        faces = faces[valid_faces_mask]
        
        print(f"Triangulating mesh: {len(vertices)} vertices, {len(faces)} faces...")
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Color the mesh based on elevation (just a simple gradient)
        # Cesium renders it better if it has vertex colors
        z_vals = vertices[:, 2]
        z_norm = (z_vals - min_z) / (max_z - min_z + 1e-6)
        # Apply a colormap (e.g., terrain colors)
        colors = np.zeros((len(vertices), 4), dtype=np.uint8)
        colors[:, 0] = (z_norm * 255).astype(np.uint8) # Red
        colors[:, 1] = ((1 - z_norm) * 200).astype(np.uint8) # Green
        colors[:, 2] = 50 # Blue
        colors[:, 3] = 255
        mesh.visual.vertex_colors = colors
        
        out_folder = os.path.dirname(tif_path)
        glb_path = os.path.join(out_folder, "terrain.glb")
        
        # Ensure we rotate the mesh so +Z is Up in Cesium
        # The GLB format uses Y-up, but Trimesh handles this if configured, or Cesium handles it via tileset.
        mesh.export(glb_path)
        print(f"Exported {glb_path}")
        
        center_lon = (west + east) / 2
        center_lat = (south + north) / 2
        
        tileset = {
            "asset": { "version": "1.0" },
            "geometricError": 1000,
            "root": {
                "transform": enu_matrix(center_lon, center_lat, 0),
                "boundingVolume": {
                    "region": [
                        np.radians(west), np.radians(south), 
                        np.radians(east), np.radians(north), 
                        min_z, max_z
                    ]
                },
                "geometricError": 0.0,
                "refine": "ADD",
                "content": { "uri": "terrain.glb" }
            }
        }
        
        tileset_path = os.path.join(out_folder, "tileset.json")
        with open(tileset_path, "w") as f:
            json.dump(tileset, f, indent=2)
        print(f"Exported {tileset_path}")
        print("Conversion Complete! You can now load this folder in the UI.")

def WGS84_to_ECEF(lon, lat, alt):
    a = 6378137.0
    e2 = 0.00669437999014
    rad_lat = np.radians(lat)
    rad_lon = np.radians(lon)
    clat = np.cos(rad_lat)
    slat = np.sin(rad_lat)
    clon = np.cos(rad_lon)
    slon = np.sin(rad_lon)
    N = a / np.sqrt(1 - e2 * slat**2)
    X = (N + alt) * clat * clon
    Y = (N + alt) * clat * slon
    Z = (N * (1 - e2) + alt) * slat
    return X, Y, Z

def enu_matrix(lon, lat, alt):
    x, y, z = WGS84_to_ECEF(lon, lat, alt)
    rad_lat = np.radians(lat)
    rad_lon = np.radians(lon)
    clat = np.cos(rad_lat)
    slat = np.sin(rad_lat)
    clon = np.cos(rad_lon)
    slon = np.sin(rad_lon)
    
    east = [-slon, clon, 0]
    north = [-slat*clon, -slat*slon, clat]
    up = [clat*clon, clat*slon, slat]
    
    matrix = [
        float(east[0]), float(east[1]), float(east[2]), 0.0,
        float(north[0]), float(north[1]), float(north[2]), 0.0,
        float(up[0]), float(up[1]), float(up[2]), 0.0,
        float(x), float(y), float(z), 1.0
    ]
    return matrix

if __name__ == "__main__":
    convert_dsm(r"D:\TEST_0708\TEST_0708\lidars\terra_dsm\dsm.tif")
