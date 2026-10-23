"""Prepares the DB that ships with the app. Idempotent: safe to run several times.

It keeps ONLY the products YOLO recognizes (see RECOGNIZABLE). Everything else in `productos`
is deleted, so run it on a copy if you still need the full catalog.

Usage:  python preparar_bd.py alacena_inteligente.db
"""
import sqlite3
import sys

# (display name in the DB, exact class name returned by YOLO).
# yolo11n.pt returns COCO class names in English, so the match is done with the English one;
# the Spanish name is only the label shown to the user.
RECOGNIZABLE = [("Manzana", "apple"), ("Naranja", "orange"), ("Plátano", "banana")]


def prepare_db(path: str) -> None:
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")

    # 1) productos.yolo_class: maps the display name to the class YOLO returns
    columns = {r[1] for r in con.execute("PRAGMA table_info(productos)")}
    if "yolo_class" not in columns:
        con.execute("ALTER TABLE productos ADD COLUMN yolo_class TEXT")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_productos_yolo "
                "ON productos(yolo_class) WHERE yolo_class IS NOT NULL")

    # 2) If a recognizable product already exists by name, it only gets its class
    for name, yolo_class in RECOGNIZABLE:
        con.execute("UPDATE productos SET yolo_class = ? WHERE nombre = ? AND yolo_class IS NULL",
                    (yolo_class, name))

    # 3) productos_usuario with a primary key and a foreign key (the old version had neither
    #    and its rows were empty). Column names id_productoFK and present are kept.
    current_sql = con.execute("SELECT sql FROM sqlite_master WHERE name = 'productos_usuario'").fetchone()
    if not current_sql or "PRIMARY KEY" not in current_sql[0]:
        con.execute("""CREATE TABLE productos_usuario_new (
            id_productoFK INTEGER PRIMARY KEY REFERENCES productos(id_producto) ON DELETE CASCADE,
            present       INTEGER NOT NULL DEFAULT 0 CHECK (present IN (0, 1)))""")
        if current_sql:
            con.execute("""INSERT OR IGNORE INTO productos_usuario_new (id_productoFK, present)
                           SELECT id_productoFK, COALESCE(present, 0) FROM productos_usuario
                           WHERE id_productoFK IS NOT NULL""")
            con.execute("DROP TABLE productos_usuario")
        con.execute("ALTER TABLE productos_usuario_new RENAME TO productos_usuario")

    # 4) Keep only what the model recognizes (rows in productos_usuario go away by cascade),
    #    then make the next id continue from the highest remaining one
    con.execute("DELETE FROM productos WHERE yolo_class IS NULL")
    con.execute("UPDATE sqlite_sequence SET seq = (SELECT COALESCE(MAX(id_producto), 0) FROM productos) "
                "WHERE name = 'productos'")

    # 5) Insert the recognizable products that are still missing
    for name, yolo_class in RECOGNIZABLE:
        if not con.execute("SELECT 1 FROM productos WHERE yolo_class = ?", (yolo_class,)).fetchone():
            con.execute("INSERT INTO productos (nombre, yolo_class) VALUES (?, ?)", (name, yolo_class))

    # 6) Initial user list: for now, everything the model recognizes
    con.execute("""INSERT OR IGNORE INTO productos_usuario (id_productoFK)
                   SELECT id_producto FROM productos WHERE yolo_class IS NOT NULL""")
    con.commit()
    con.close()


if __name__ == "__main__":
    prepare_db(sys.argv[1] if len(sys.argv) > 1 else "alacena_inteligente.db")
    print("DB ready.")