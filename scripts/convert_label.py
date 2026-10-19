
from pathlib import Path
import shutil

# Dataset original y destino
source_dir = Path("datasets/Groceries.v3i.yolov11")
output_dir = Path("datasets/Groceries-detection")

splits = ["train", "valid", "test"]

for split in splits:
    images_dir = source_dir / split / "images"
    labels_dir = source_dir / split / "labels"

    output_images = output_dir / split / "images"
    output_labels = output_dir / split / "labels"

    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    converted = 0
    invalid = 0

    for image_path in images_dir.iterdir():
        if not image_path.is_file():
            continue

        # Copiar imagen al nuevo dataset
        shutil.copy2(image_path, output_images / image_path.name)

        label_path = labels_dir / f"{image_path.stem}.txt"

        if not label_path.exists():
            print(f"Falta etiqueta: {image_path.name}")
            invalid += 1
            continue

        new_lines = []

        with open(label_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                parts = line.split()

                try:
                    values = [float(value) for value in parts]
                except ValueError:
                    print(f"Valores inválidos: {label_path}, línea {line_number}")
                    invalid += 1
                    continue

                if not values or not values[0].is_integer():
                    print(f"Clase inválida: {label_path}, línea {line_number}")
                    invalid += 1
                    continue

                class_id = int(values[0])
                coordinates = values[1:]

                # Formato YOLO de detección: clase + x_centro, y_centro, ancho, alto
                if len(coordinates) == 4:
                     x_center, y_center, width, height = coordinates

                # Formato polígono: clase + pares de coordenadas
                elif len(coordinates) >= 6 and len(coordinates) % 2 == 0:
                    if any(value < 0 or value > 1 for value in coordinates):
                        print(f"Coordenadas fuera de rango: {label_path.name}, línea {line_number}")
                        invalid += 1
                        continue

                    x_coords = coordinates[0::2]
                    y_coords = coordinates[1::2]

                    x_min = min(x_coords)
                    x_max = max(x_coords)
                    y_min = min(y_coords)
                    y_max = max(y_coords)

                    x_center = (x_min + x_max) / 2
                    y_center = (y_min + y_max) / 2
                    width = x_max - x_min
                    height = y_max - y_min

                else:
                    print(f"Etiqueta inválida: {label_path.name}, línea {line_number}")
                    invalid += 1
                    continue

                # Validar la caja resultante
                if (
                    any(value < 0 or value > 1 for value in (x_center, y_center, width, height))
                    or width <= 0
                    or height <= 0
                ):
                    print(f"Caja inválida: {label_path.name}, línea {line_number}")
                    invalid += 1
                    continue

                new_lines.append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                )

        output_label = output_labels / label_path.name

        with open(output_label, "w", encoding="utf-8") as file:
            file.write("\n".join(new_lines))
            if new_lines:
                file.write("\n")

        converted += 1

    print(f"\n--- {split} ---")
    print("Imágenes procesadas:", converted)
    print("Errores encontrados:", invalid)

print("\nConversión terminada.")
