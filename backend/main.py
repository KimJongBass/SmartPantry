from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File
from ultralytics import YOLO
from PIL import Image
import os
import sqlite3

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

DB_PATH = os.getenv("ALACENA_DB", os.path.join(os.path.dirname(__file__), "alacena_inteligente.db"))

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

    # Compare what YOLO detected against the user's list
    detected_names = {d["name"] for d in detections}
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""SELECT p.id_producto, p.nombre, p.yolo_class
                          FROM productos_usuario pu
                          JOIN productos p ON p.id_producto = pu.id_productoFK
                          ORDER BY p.nombre""").fetchall()
    con.close()
    pantry = [{"id": r[0], "name": r[1], "present": r[2] in detected_names} for r in rows]

    # Save the result in the DB (each scan overwrites the previous one)
    con = sqlite3.connect(DB_PATH)
    for item in pantry:
        con.execute("UPDATE productos_usuario SET present = ? WHERE id_productoFK = ?",
                    (int(item["present"]), item["id"]))
    con.commit()
    con.close()

    # Show the user's list in the terminal
    print("--- User list ---")
    for item in pantry:
        print(f'{item["name"]}: {"yes" if item["present"] else "no"}')

    return {
    "filename": file.filename,
    "detections": detections,
    "pantry": pantry
    }

@app.get("/pantry")
def get_pantry():
    # The user's list as stored in the DB: present is 1 (yes) or 0 (no)
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""SELECT p.id_producto, p.nombre, pu.present
                          FROM productos_usuario pu
                          JOIN productos p ON p.id_producto = pu.id_productoFK
                          ORDER BY p.nombre""").fetchall()
    con.close()
    return [{"id": r[0], "name": r[1], "present": r[2]} for r in rows]