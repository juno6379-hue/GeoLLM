import os
import argparse
import numpy as np
import tifffile
import trimesh
import math
import pyproj

def generate_terrain(dsm_path, output_path, downsample_factor=100, max_triangles=500000):
    print(f"Loading DSM from {dsm_path}...")
    
    # Read the DSM file
    with tifffile.TiffFile(dsm_path) as tif:
        image = tif.asarray()
        
        print(f"Original DSM Shape: {image.shape}")
        
        h, w = image.shape
        ds_h = h // downsample_factor
        ds_w = w // downsample_factor
        
        print(f"Downsampling factor: {downsample_factor}. New Shape: ({ds_h}, {ds_w})")
        # Ensure we only take exactly ds_h and ds_w elements
        sampled_z = image[:ds_h*downsample_factor:downsample_factor, :ds_w*downsample_factor:downsample_factor]
        
        # Grid bounds based on pixel size 0.0226 (approx 2.26cm per px)
        x = np.linspace(-ds_w/2, ds_w/2, ds_w) * downsample_factor * 0.0226
        y = np.linspace(ds_h/2, -ds_h/2, ds_h) * downsample_factor * 0.0226 # Y is usually flipped
        
        xv, yv = np.meshgrid(x, y)
        
        # Flatten
        xv = xv.flatten()
        yv = yv.flatten()
        zv = sampled_z.flatten()
        
        # Filter out NODATA (e.g., < -1000)
        valid_mask = zv > -1000
        
        print("Generating mesh vertices...")
        
        vertices = np.column_stack((xv, yv, zv))
        
        # Create faces for the grid
        faces = []
        for r in range(ds_h - 1):
            for c in range(ds_w - 1):
                idx_tl = r * ds_w + c
                idx_tr = idx_tl + 1
                idx_bl = (r + 1) * ds_w + c
                idx_br = idx_bl + 1
                
                # Only create face if all 4 vertices are valid
                if valid_mask[idx_tl] and valid_mask[idx_tr] and valid_mask[idx_bl] and valid_mask[idx_br]:
                    faces.append([idx_tl, idx_bl, idx_tr])
                    faces.append([idx_tr, idx_bl, idx_br])
                    
        faces = np.array(faces)
        print(f"Created {len(faces)} faces.")
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
        
        # Save output
        print(f"Exporting to {output_path}...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        mesh.export(output_path)
        print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default=r'd:\TEST_0708\TEST_0708\lidars\terra_dsm\dsm.tif')
    parser.add_argument('--output', type=str, default=r'd:\An_GeoLLM\ui\terrain.glb')
    parser.add_argument('--downsample', type=int, default=100)
    args = parser.parse_args()
    
    generate_terrain(args.input, args.output, args.downsample)
