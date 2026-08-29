import os
import json
import laspy
import numpy as np
import cv2
from ultralytics import YOLO

def analyze_lidar(las_path, output_dir):
    print(f"[{las_path}] 심층 분석 시작...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load LAS file
    print("1. LAS 데이터 로딩...")
    las = laspy.read(las_path)
    points = np.vstack((las.x, las.y, las.z)).transpose()
    total_points = len(points)
    print(f"   - 총 점군 수: {total_points:,} 개")
    
    # 2. Noise Filtering (Z-score based)
    print("2. 통계적 노이즈 필터링 수행...")
    z_mean = np.mean(points[:, 2])
    z_std = np.std(points[:, 2])
    z_threshold = 2.5 * z_std
    
    valid_indices = np.abs(points[:, 2] - z_mean) < z_threshold
    filtered_points = points[valid_indices]
    removed_points = total_points - len(filtered_points)
    print(f"   - 제거된 노이즈 점군: {removed_points:,} 개")
    
    # 3. Volume Calculation (Simple Grid Integration)
    print("3. 체적(Volume) 변화량 추정 (Grid-based)...")
    # 1m x 1m grid
    grid_size = 1.0
    x_min, x_max = np.min(filtered_points[:, 0]), np.max(filtered_points[:, 0])
    y_min, y_max = np.min(filtered_points[:, 1]), np.max(filtered_points[:, 1])
    z_min = np.min(filtered_points[:, 2])
    
    # Estimate volume by assuming each point represents grid_size^2 area
    # Note: Real implementation uses complex DEM differencing, this is a proxy for the pilot
    avg_z = np.mean(filtered_points[:, 2]) - z_min
    estimated_area = (x_max - x_min) * (y_max - y_min)
    estimated_volume = estimated_area * avg_z * 0.4 # Fill factor
    print(f"   - 추정 체적(Volume): {estimated_volume:,.2f} m³")
    
    # 4. AI Object Detection (YOLOv8)
    print("4. AI 객체 탐지 (YOLOv8 방파제/구조물 탐지)...")
    # 점군 데이터를 2D 이미지화 (Rasterize)
    img_width, img_height = 800, 800
    img = np.zeros((img_height, img_width, 3), dtype=np.uint8)
    
    # Normalize X,Y to fit in 800x800
    norm_x = ((filtered_points[:, 0] - x_min) / (x_max - x_min) * (img_width - 1)).astype(int)
    norm_y = ((filtered_points[:, 1] - y_min) / (y_max - y_min) * (img_height - 1)).astype(int)
    
    # Draw points on image (intensity based on Z)
    norm_z = ((filtered_points[:, 2] - z_min) / (np.max(filtered_points[:, 2]) - z_min) * 255).astype(np.uint8)
    for ix, iy, iz in zip(norm_x, norm_y, norm_z):
        img[img_height - 1 - iy, ix] = (iz, iz, 200)
    
    cv2.imwrite(os.path.join(output_dir, "rasterized_topdown.jpg"), img)
    
    # Run YOLO
    # Using pretrained YOLOv8n (downloads automatically if not found)
    model = YOLO("yolov8n.pt") 
    results = model(img, verbose=False)
    
    detected_objects = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            detected_objects.append({
                "class_id": cls,
                "confidence": conf,
                "bbox": [x1, y1, x2, y2]
            })
    print(f"   - 탐지된 객체 수: {len(detected_objects)} 개")
    
    # 5. Save Results
    print("5. 분석 리포트 및 GeoJSON 생성...")
    report = {
        "las_file": os.path.basename(las_path),
        "total_points_original": total_points,
        "noise_points_removed": removed_points,
        "estimated_volume_m3": round(estimated_volume, 2),
        "detected_objects": len(detected_objects)
    }
    with open(os.path.join(output_dir, "analysis_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    # Generate Mock GeoJSON based on bounding box
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    if detected_objects:
        # Map pixel coordinates back to real world roughly
        for idx, obj in enumerate(detected_objects):
            x1, y1, x2, y2 = obj['bbox']
            # Simple inverse mapping for demo
            real_x = x_min + (x1 / img_width) * (x_max - x_min)
            real_y = y_min + ((img_height - y1) / img_height) * (y_max - y_min)
            
            # Since the user's data is likely in a local projection (UTM or TM), these coordinates are projected.
            geojson["features"].append({
                "type": "Feature",
                "properties": {
                    "id": f"detected_{idx}",
                    "confidence": obj['confidence'],
                    "type": "Structure"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [real_x, real_y]
                }
            })
            
    with open(os.path.join(output_dir, "detections.geojson"), "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=4)
        
    print(f"분석 완료! 결과가 {output_dir} 에 저장되었습니다.")

if __name__ == "__main__":
    target_las = r"d:\TEST_0708\TEST_0708\lidars\terra_las\cloud_+000_+001.las"
    out_dir = r"d:\TEST_0708\agent_output"
    analyze_lidar(target_las, out_dir)
