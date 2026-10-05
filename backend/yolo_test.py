from ultralytics import YOLO
import requests


# Load YOLO model
model = YOLO("yolo11n.pt")

print("YOLO model loaded successfully!")


# Run YOLO on image
results = model("bus.jpg")


print("\nSending detections to FastAPI...")
print("--------------------------------")


for result in results:

    for box in result.boxes:

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        object_name = model.names[class_id].upper()

        # Bounding box
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # Send detection to FastAPI
        data = {
            "camera_id": "CAM-01",
            "location": "Factory Floor",
            "event_type": object_name,
            "confidence": confidence,
            "bbox": [x1, y1, x2, y2]
        }

        response = requests.post(
            "http://127.0.0.1:8000/detect",
            json=data
        )

        print(
            f"{object_name} → {confidence:.2f} "
            f"→ API Status: {response.status_code}"
        )


print("\nYOLO → FastAPI connection completed!")