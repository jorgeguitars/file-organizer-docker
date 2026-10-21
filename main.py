import os
import time
import shutil
import logging
import zipfile
import tempfile
import struct
from pathlib import Path
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

# Configuración de variables
TARGET_DIR = Path("/app/target")
DRY_RUN = False
TEMP_EXTENSIONS = ('.crdownload', '.tmp', '.part', '.download')

TARGET_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(TARGET_DIR / "organizer.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

AMPLIFIER_EXTENSIONS = {
    ".nam": "Amplificadores_y_Presets/NAM",
    ".tone": "Amplificadores_y_Presets/Hotone_Ampero",
    ".prst": "Amplificadores_y_Presets/Hotone_Ampero",
    ".amp2": "Amplificadores_y_Presets/Hotone_Ampero",
    ".cab2": "Amplificadores_y_Presets/Hotone_Ampero",
    ".prl": "Amplificadores_y_Presets/Hotone_Ampero",
    ".patch": "Amplificadores_y_Presets/Hotone_Ampero",
    ".amp": "Amplificadores_y_Presets/Hotone_Ampero",
    ".cab": "Amplificadores_y_Presets/Hotone_Ampero",
    ".val": "Amplificadores_y_Presets/Valeton",
    ".prset": "Amplificadores_y_Presets/Valeton",
    ".ir": "Amplificadores_y_Presets/Impulse_Responses_IRs"
}

EXTENSION_MAP = {
    "Documentos": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv", ".epub", ".ods", ".odt"],
    "Imagenes": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico", ".tiff"],
    "Audio": [".mp3", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".mpeg"],  # .wav se maneja dinámicamente
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm", ".m4v"],
    "Comprimidos": [".tar", ".gz", ".rar", ".7z", ".bz2", ".xz"],
    "Codigo": [".py", ".js", ".html", ".css", ".json", ".sh", ".php", ".cpp", ".c", ".java", ".ts", ".sql"],
    "Ejecutables": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".appimage"]
}

def classify_wav(file_path: Path) -> str:
    """
    Inspecciona el .wav para determinar si es una IR o Audio musical.
    Combina análisis de tamaño en disco y lectura del formato WAV.
    """
    try:
        file_size = file_path.stat().st_size  # Tamaño en bytes
        
        # Regla 1 (Filtro por peso): Un archivo de audio musical .wav casi siempre supera los 3-5 MB.
        # Las IRs de guitarra (2048/1024 samples) pesan usualmente entre 5 KB y 500 KB (rara vez superan 2 MB).
        if file_size < 2 * 1024 * 1024:  # Menor a 2 MB
            return "Amplificadores_y_Presets/Impulse_Responses_IRs"

        # Regla 2 (Análisis de cabecera PCM/Float nativa con fallback):
        with open(file_path, 'rb') as f:
            header = f.read(44)
            if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                # Intentar leer Sample Rate (bytes 24-27) y Byte Rate (bytes 28-31)
                sample_rate = struct.unpack('<I', header[24:28])[0]
                byte_rate = struct.unpack('<I', header[28:32])[0]
                
                if byte_rate > 0:
                    duration = file_size / float(byte_rate)
                    if duration < 3.0:  # Menor a 3 segundos
                        return "Amplificadores_y_Presets/Impulse_Responses_IRs"
    except Exception as e:
        logging.warning(f"⚠️ No se pudo analizar en detalle el .wav {file_path.name}: {e}")

    # Si supera los 2MB y dura más de 3 segundos, es un audio/song normal
    return "Audio"

def get_target_category(item_path: Path) -> str:
    ext = item_path.suffix.lower()
    
    if ext in AMPLIFIER_EXTENSIONS:
        return AMPLIFIER_EXTENSIONS[ext]
    
    # Inspección inteligente si es un archivo .wav
    if ext == ".wav":
        return classify_wav(item_path)
    
    for category, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return category
            
    return "Otros"

def get_unique_destination(dest_dir: Path, filename: str) -> Path:
    dest_path = dest_dir / filename
    if not dest_path.exists():
        return dest_path
    
    stem = dest_path.stem
    suffix = dest_path.suffix
    counter = 1
    while True:
        new_name = f"{stem} ({counter}){suffix}"
        new_path = dest_dir / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def process_compressed_file(zip_path: Path):
    pack_name = zip_path.stem
    logging.info(f"📦 Descomprimiendo y procesando paquete: {zip_path.name}")

    if DRY_RUN:
        logging.info(f"🔍 [Simulación] Se descomprimiría '{zip_path.name}' clasificando sus .wav inteligentemente.")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
        except Exception as e:
            logging.error(f"❌ Error al descomprimir {zip_path.name}: {e}")
            return

        categorized_files = {}

        for file_item in temp_path.rglob('*'):
            if file_item.is_file() and not file_item.name.startswith('.'):
                target_cat = get_target_category(file_item)

                if target_cat not in categorized_files:
                    categorized_files[target_cat] = []
                categorized_files[target_cat].append(file_item)

        for cat, files in categorized_files.items():
            dest_folder = TARGET_DIR / cat / pack_name
            dest_folder.mkdir(parents=True, exist_ok=True)

            for f in files:
                dest_file = get_unique_destination(dest_folder, f.name)
                shutil.copy2(f, dest_file)

            logging.info(f"📁 Paquete '{pack_name}' organizado en ➡️ {cat}/{pack_name}/ ({len(files)} archivos)")

    try:
        zip_path.unlink()
        logging.info(f"🗑️ Archivo comprimido procesado y eliminado: {zip_path.name}")
    except Exception as e:
        logging.error(f"❌ No se pudo eliminar el archivo comprimido {zip_path.name}: {e}")

def process_file(item: Path):
    if item.is_dir() or "organizer.log" in item.name:
        return

    ext = item.suffix.lower()

    if ext in TEMP_EXTENSIONS or item.name.startswith("."):
        return

    time.sleep(0.5)
    if not item.exists():
        return

    if ext == ".zip":
        process_compressed_file(item)
        return

    target_category = get_target_category(item)
    dest_dir = TARGET_DIR / target_category

    if DRY_RUN:
        logging.info(f"🔍 [Simulación] Se movería: {item.name} ➡️  {target_category}/")
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = get_unique_destination(dest_dir, item.name)
        shutil.move(str(item), str(dest_path))
        logging.info(f"📦 Movid@: {item.name} ➡️  {target_category}/{dest_path.name}")

class FileOrganizerHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or "organizer.log" in event.src_path:
            return
        process_file(Path(event.src_path))

    def on_moved(self, event):
        if event.is_directory or "organizer.log" in event.dest_path:
            return
        process_file(Path(event.dest_path))

def initial_bootstrap_scan():
    logging.info("🚀 Iniciando escaneo de arranque...")
    if not TARGET_DIR.exists():
        TARGET_DIR.mkdir(parents=True, exist_ok=True)
        return

    for item in list(TARGET_DIR.iterdir()):
        if item.is_file() and not item.name.startswith('.'):
            process_file(item)
    logging.info("✨ Escaneo de arranque finalizado.")

if __name__ == "__main__":
    logging.info("📁 Smart File Organizer Daemon iniciado con análisis inteligente de .wav.")
    logging.info(f"👀 Monitoreando directorio: {TARGET_DIR}")

    initial_bootstrap_scan()

    event_handler = FileOrganizerHandler()
    observer = PollingObserver(timeout=0.5)
    observer.schedule(event_handler, path=str(TARGET_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("🛑 Deteniendo el organizador de archivos...")
    observer.join()