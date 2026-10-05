from ultralytics import YOLO

model = YOLO("yolo11n.pt")

print("\nYOLO MODEL CLASSES")
print("------------------")

for class_id, class_name in model.names.items():
    print(class_id, "->", class_name)

print("\nTotal classes:", len(model.names))