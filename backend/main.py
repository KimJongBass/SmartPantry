from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("yolo11n.pt")

@app.get("/")
def root():
    return {"message": "Smart Pantry API funcionando"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = Image.open(file.file)

    results = model(image, conf=0.5)
    detections = []
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        class_name = results[0].names[class_id]
        confidence = float(box.conf[0])

        detections.append({
        "name": class_name,
        "confidence": confidence
        })


    print(results[0].names)
    print(results[0].boxes)

    return {
    "filename": file.filename,
    "detections": detections
    }   