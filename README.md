# 📁 Smart File Organizer (Dockerized)

Un servicio ligero y automatizado en Python empaquetado en Docker que monitorea la carpeta `downloads/` y clasifica/organiza automáticamente los archivos en subdirectorios según su tipo de contenido y extensión.

---

## ⚙️ ¿Cómo Funciona?

El demonio opera bajo un modelo de procesamiento continuo y en tiempo real a través de las siguientes fases lógicas:

1. **Escaneo Inicial de Arranque (Bootstrap Scan):** 
   Al encender o reiniciar el contenedor, el script escanea el directorio objetivo y procesa de inmediato cualquier archivo preexistente o sin clasificar que se encuentre allí.
2. **Monitoreo Continuo por Eventos (Polling / Watchdog):** 
   Utiliza la librería `watchdog` con una estrategia de `PollingObserver`. Esto garantiza una detección sumamente confiable de nuevos archivos, superando las limitaciones de propagación de eventos en volúmenes compartidos de Docker (independientemente de si ejecutas Docker en Windows, macOS o Linux).
3. **Control de Descargas e Incompletos (Debounce):** 
   Cuenta con un mecanismo de seguridad que ignora archivos temporales en pleno proceso de descarga (como `.crdownload`, `.tmp`, `.part`, `.download`). El sistema espera activamente a que el tamaño del archivo se estabilice antes de realizar cualquier movimiento para evitar corrupciones o bloqueos de E/S.
4. **Movimiento Atómico y Gestión de Colisiones:** 
   Clasifica el archivo según su extensión y lo traslada de forma segura a su respectiva subcarpeta. Si ya existe un archivo con exactamente el mismo nombre en el destino, genera un sufijo numérico automático (`archivo (1).ext`) para evitar sobrescribir información.
5. **Descompresión Estructurada de Paquetes (`.zip`):** 
   Si el archivo es un `.zip`, el sistema lo extrae de forma aislada, analiza de qué tipo son los archivos de su interior de forma inteligente y crea subcarpetas organizadas bajo el nombre del paquete comprimido (`downloads/Categoria/NombreDelPack/`). Al terminar, elimina el archivo comprimido original.
6. **Inspección Inteligente de Audio (`.wav`):** 
   Distingue mediante análisis de metadatos y peso si un archivo `.wav` es una pista de música convencional o una **Captura IR (Impulse Response)** para guitarristas, ubicándolas con precisión quirúrgica.

---

## 📂 Estructura de Organización y Extensiones Soportadas

Los archivos procesados se mueven automáticamente a las siguientes subcarpetas dentro de `downloads/`:

| Subcarpeta | Extensiones Soportadas | Descripción |
| :--- | :--- | :--- |
| 📄 `Documentos/` | `.pdf`, `.docx`, `.doc`, `.txt`, `.xlsx`, `.pptx`, `.csv`, `.epub`, `.ods`, `.odt` | Archivos de texto, hojas de cálculo, presentaciones y libros electrónicos. |
| 🖼️ `Imagenes/` | `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`, `.bmp`, `.ico`, `.tiff` | Fotografías, gráficos y vectores visuales. |
| 🎵 `Audio/` | `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma` | Pistas de música y archivos de audio generales. |
| 🎥 `Videos/` | `.mp4`, `.mkv`, `.mov`, `.avi`, `.wmv`, `.flv`, `.webm`, `.m4v` | Contenido multimedia en video. |
| 📦 `Comprimidos/` | `.zip`, `.tar`, `.gz`, `.rar`, `.7z`, `.bz2`, `.xz` | Archivos empaquetados y comprimidos. |
| 💻 `Codigo/` | `.py`, `.js`, `.html`, `.css`, `.json`, `.sh`, `.php`, `.cpp`, `.c`, `.java`, `.ts`, `.sql` | Scripts y archivos fuente de programación. |
| ⚙️ `Ejecutables/` | `.exe`, `.msi`, `.dmg`, `.deb`, `.rpm`, `.AppImage` | Instaladores y ejecutables de software. |
| 🎸 `Amplificadores_y_Presets/` | `.nam`, `.tone`, `.prst`, `.amp2`, `.cab2`, `.ir`, `.val`, `.prset`, `.prl`, `.patch` | Perfiles NAM, respuestas de impulso (IRs) y presets/parches para **Hotone Ampero II Stomp**, Valeton y otros multiefectos. |
| 📁 `Otros/` | *Cualquier otra extensión* | Archivos que no coinciden con las reglas anteriores. |

---

## 🚀 Uso Rápido

### Prerrequisitos
- [Docker](https://www.docker.com/) y Docker Compose instalados en tu equipo.

### Pasos de Despliegue
1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/jorgeguitars/file-organizer-docker.git](https://github.com/jorgeguitars/file-organizer-docker.git)
   cd file-organizer-docker