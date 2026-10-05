from ultralytics import YOLO
import cv2
import requests
import time


# Load YOLO model
model = YOLO("yolo11n.pt")

print("YOLO model loaded successfully!")


# Open webcam
cap = cv2.VideoCapture(0)

print("Camera starting...")


# Send detections every 1 second
SEND_INTERVAL = 1.0

last_send_time = 0


while True:

    ret, frame = cap.read()

    if not ret:

        print("Could not read camera.")

        break


    # YOLO detection
    results = model(
        frame,
        verbose=False
    )


    # Draw detections
    annotated_frame = results[0].plot()


    # Current time
    current_time = time.time()


    # Send detections only after interval
    if current_time - last_send_time >= SEND_INTERVAL:

        last_send_time = current_time


        # Send detections to FastAPI
        for result in results:

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                object_name = model.names[
                    class_id
                ].upper()


                # Bounding box
                x1, y1, x2, y2 = box.xyxy[
                    0
                ].tolist()


                data = {

                    "camera_id": "CAM-01",

                    "location": "Factory Floor",

                    "event_type": object_name,

                    "confidence": confidence,

                    "bbox": [
                        x1,
                        y1,
                        x2,
                        y2
                    ]
                }


                try:

                    response = requests.post(

                        "http://127.0.0.1:8000/detect",

                        json=data,

                        timeout=2

                    )


                    print(

                        f"{object_name} → "

                        f"{confidence:.2f} "

                        f"→ API: "

                        f"{response.status_code}"

                    )


                except requests.RequestException:

                    print(
                        "FastAPI connection failed."
                    )


    # Show camera window
    cv2.imshow(
        "Factory Safety AI",
        annotated_frame
    )


    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


cap.release()

cv2.destroyAllWindows()