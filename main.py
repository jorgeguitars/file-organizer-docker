import time
import os
import shutil
import logging
from pathlib import Path
# Importación correcta del PollingObserver en watchdog moderno
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

EXTENSION_MAP = {
    "Documentos": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx"],
    "Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"],
    "Audio": [".mp3", ".wav", ".flac"],
    "Videos": [".mp4", ".mkv", ".mov"],
    "Comprimidos": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "Codigo": [".py", ".js", ".html", ".css", ".json", ".sh"]
}

TEMP_EXTENSIONS = {".tmp", ".crdownload", ".part", ".download", ".tmp_download"}

TARGET_DIR = Path("/app/target")
DRY_RUN = os.getenv("DRY_RUN", "false").strip().lower() == "true"

def process_file(item: Path):
    if item.is_dir() or "organizer.log" in item.name:
        return

    ext = item.suffix.lower()

    if ext in TEMP_EXTENSIONS or item.name.startswith("."):
        return

    time.sleep(1)
    if not item.exists():
        return

    category_found = "Otros"
    for category, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            category_found = category
            break

    dest_dir = TARGET_DIR / category_found

    if DRY_RUN:
        logging.info(f"🔍 [Simulación] Se movería: {item.name} ➡️  {category_found}/")
    else:
        dest_dir.mkdir(exist_ok=True)
        dest_path = dest_dir / item.name
        if not dest_path.exists():
            shutil.move(str(item), str(dest_path))
            logging.info(f"📦 Movid@: {item.name} ➡️  {category_found}/")

def scan_existing_files():
    logging.info("🧹 Escaneando y clasificando archivos preexistentes...")
    for item in TARGET_DIR.iterdir():
        if item.is_file():
            process_file(item)

class OrganizerHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            process_file(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            process_file(Path(event.dest_path))

if __name__ == "__main__":
    if not TARGET_DIR.exists():
        logging.error(f"La carpeta objetivo '{TARGET_DIR}' no existe.")
        exit(1)

    if DRY_RUN:
        logging.info("⚠️ MODO SIMULACIÓN ACTIVADO (Watchdog Polling en marcha)")
    else:
        logging.info("🚀 Watchdog Polling iniciado: Escuchando cambios...")

    scan_existing_files()

    event_handler = OrganizerHandler()
    observer = PollingObserver(timeout=2)
    observer.schedule(event_handler, path=str(TARGET_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()