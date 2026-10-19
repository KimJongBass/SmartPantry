import cv2
from pathlib import Path

image_path = Path(
    "datasets/Groceries-detection/train/images/"
    "114_jpeg_jpg.rf.047bd3fe200e965be4ece4f2c8951d36.jpg"
)

label_path = Path(
    "datasets/Groceries-detection/train/labels/"
    "114_jpeg_jpg.rf.047bd3fe200e965be4ece4f2c8951d36.txt"
)

image = cv2.imread(str(image_path))

if image is None:
    print("No se pudo cargar la imagen")
    exit()

print("Ancho:", image.shape[1])
print("Alto:", image.shape[0])

with open(label_path, "r", encoding="utf-8") as file:
    labels = file.readlines()

print("Cantidad de etiquetas:", len(labels))

for line in labels[:1]:
    values = line.split()
    print("Valores:", values)

for line in labels:
    values = line.split()

    class_id = int(values[0])

    x_center = float(values[1]) * image.shape[1]
    y_center = float(values[2]) * image.shape[0]
    width = float(values[3]) * image.shape[1]
    height = float(values[4]) * image.shape[0]

    # Calcula las cuatro esquinas
    x1 = int(x_center - width / 2)
    y1 = int(y_center - height / 2)
    x2 = int(x_center + width / 2)
    y2 = int(y_center + height / 2)

    # Dibuja el rectángulo
    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    # Escribe el identificador de clase
    cv2.putText(
        image,
        str(class_id),
        (x1, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )

cv2.imshow("Etiquetas YOLO", image)
cv2.waitKey(0)
cv2.destroyAllWindows()