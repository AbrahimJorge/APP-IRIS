import sys
import os
import cv2
import base64
import threading
import time
from collections import Counter
import numpy as np

from services.color_dataset import ColorDatasetService


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class CameraService:
    def __init__(self):
        self.dataset = ColorDatasetService()
        self.cap = None
        self.is_running = False
        self.thread = None
        self.current_frame = None
        self.camera_index = 0
        self.camera_facing = "back"  
        self.lock = threading.Lock()
        self.is_busy = False
        self.cap_available = False

    def load_frame_bytes(self, image_bytes: bytes) -> bool:
        """Carrega e orienta o frame a partir de bytes de imagem (JPEG/PNG) da câmera."""
        try:
            self.dataset.load()
            import io
            from PIL import Image, ImageOps

            # 1. Carrega via PIL para corrigir orientação EXIF
            img = Image.open(io.BytesIO(image_bytes))
            img = ImageOps.exif_transpose(img)

            # 2. Garante 3 canais de cor RGB
            if img.mode != "RGB":
                img = img.convert("RGB")

            # 3. Converte para array NumPy BGR
            rgb_arr = np.array(img)
            bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

            # 4. Se a imagem capturada estiver em paisagem no celular (largura > altura),
            # rotaciona 90 graus para alinhar perfeitamente com a orientação em pé (retrato)
            h, w = bgr_arr.shape[:2]
            if w > h:
                bgr_arr = cv2.rotate(bgr_arr, cv2.ROTATE_90_CLOCKWISE)

            with self.lock:
                self.current_frame = bgr_arr
            return True
        except Exception as e:
            print(f"Aviso no carregamento PIL do frame: {e}")
            try:
                nparr = np.frombuffer(image_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is not None:
                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    with self.lock:
                        self.current_frame = frame
                    return True
            except Exception as e2:
                print(f"Erro no fallback OpenCV: {e2}")
        return False

    def load_frame_array(self, frame: np.ndarray) -> bool:
        """Carrega um frame diretamente a partir de um array numpy BGR."""
        try:
            self.dataset.load()
            with self.lock:
                self.current_frame = frame
            return True
        except Exception:
            return False

    def start(self, on_frame_callback=None):
        """Inicia a captura da câmera em tempo real em uma thread de segundo plano."""
        if self.is_running:
            return

        self.dataset.load()
        self.is_running = True

        def stream_loop():
            try:
                self.cap = cv2.VideoCapture(self.camera_index)
                if (not self.cap or not self.cap.isOpened()) and hasattr(cv2, "CAP_DSHOW") and os.name == "nt":
                    self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                if self.cap and self.cap.isOpened():
                    self.cap_available = True
                    try:
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    except Exception:
                        pass
                    try:
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    except Exception:
                        pass
                else:
                    self.cap_available = False
            except Exception as e:
                print(f"Erro ao inicializar câmera OpenCV: {e}")
                self.cap = None
                self.cap_available = False

            while self.is_running:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if not self.is_running:
                        break

                    if ret and frame is not None:
                        
                        if self.camera_facing == "front":
                            frame = cv2.flip(frame, 1)

                        with self.lock:
                            self.current_frame = frame

                        
                        if on_frame_callback and not self.is_busy:
                            self.is_busy = True
                            try:
                                
                                h, w = frame.shape[:2]
                                target_w = 340
                                scale = target_w / float(w)
                                target_h = int(h * scale)
                                display_frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

                                
                                success, buffer = cv2.imencode(".jpg", display_frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
                                if success:
                                    b64_str = base64.b64encode(buffer).decode("utf-8")
                                    data_uri = f"data:image/jpeg;base64,{b64_str}"
                                    on_frame_callback(data_uri)
                            except Exception:
                                pass
                            finally:
                                self.is_busy = False

                time.sleep(0.015)  

            
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None

        self.thread = threading.Thread(target=stream_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Para a thread de captura e aguarda a finalização limpa da câmera."""
        self.is_running = False
        if self.thread and threading.current_thread() != self.thread:
            try:
                self.thread.join(timeout=0.3)
            except Exception:
                pass
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def toggle_facing(self):
        """Alterna entre câmera frontal e traseira."""
        self.camera_facing = "front" if self.camera_facing == "back" else "back"
        self.camera_index = 1 if self.camera_facing == "front" else 0
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        return self.camera_facing

    def sample_point(self, norm_x: float, norm_y: float) -> dict | None:
        """
        Identifica a cor no ponto normalizado (0.0 a 1.0).
        Retorna dicionário com família, tom, hex e nome específico.
        """
        with self.lock:
            if self.current_frame is None:
                return None
            frame = self.current_frame.copy()

        h, w = frame.shape[:2]
        px = max(0, min(int(norm_x * w), w - 1))
        py = max(0, min(int(norm_y * h), h - 1))

        
        if frame.ndim == 2:
            val = int(frame[py, px])
            r, g, b = val, val, val
        elif frame.ndim == 3:
            pixel = frame[py, px]
            if hasattr(pixel, "__len__") and len(pixel) >= 3:
                b, g, r = int(pixel[0]), int(pixel[1]), int(pixel[2])
            else:
                val = int(pixel[0]) if hasattr(pixel, "__getitem__") else int(pixel)
                r, g, b = val, val, val
        else:
            return None

        family, tone_detail, hex_code = self.dataset.classify_color(r, g, b)
        specific_name = self.dataset.get_closest_color_name(r, g, b)

        return {
            "family": family,
            "tone_detail": tone_detail,
            "hex": hex_code,
            "specific_name": specific_name,
            "r": r,
            "g": g,
            "b": b,
        }

    def sample_area(self, norm_x0: float, norm_y0: float, norm_x1: float, norm_y1: float) -> list[dict]:
        """
        Analisa uma região retangular e retorna as cores predominantes
        baseado na lógica de analyze_region do projeto IRIS.
        """
        with self.lock:
            if self.current_frame is None:
                return []
            frame = self.current_frame.copy()

        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        h, w = frame.shape[:2]
        x0 = max(0, min(int(min(norm_x0, norm_x1) * w), w - 1))
        x1 = max(0, min(int(max(norm_x0, norm_x1) * w), w - 1))
        y0 = max(0, min(int(min(norm_y0, norm_y1) * h), h - 1))
        y1 = max(0, min(int(max(norm_y0, norm_y1) * h), h - 1))

        if (x1 - x0) < 5 or (y1 - y0) < 5:
            return []

        region = frame[y0:y1, x0:x1]
        pixels_bgr = region.reshape(-1, 3).astype(np.int32)
        pixels_rgb = pixels_bgr[:, ::-1]

        if len(pixels_rgb) > 1500:
            idx = np.random.choice(len(pixels_rgb), 1500, replace=False)
            pixels_rgb = pixels_rgb[idx]
            pixels_bgr = pixels_bgr[idx]

        distances, indices = self.dataset.query(pixels_rgb)
        if indices is None:
            return []

        labels = self.dataset.names[indices]
        counter = Counter(labels)
        total = len(labels)

        results = []
        for label, count in counter.most_common(5):
            sel = labels == label
            mean_bgr = pixels_bgr[sel].mean(axis=0).astype(int)
            mr, mg, mb = int(mean_bgr[2]), int(mean_bgr[1]), int(mean_bgr[0])

            family, _, hex_code = self.dataset.classify_color(mr, mg, mb)
            pct = (count / total) * 100.0

            results.append({
                "name": family,
                "detail": f"{pct:.0f}% · {hex_code}",
                "hex": hex_code,
                "specific_name": label,
                "pct": pct,
            })

        return results


if __name__ == "__main__":
    print("Testando CameraService diretamente...")
    service = CameraService()
    service.dataset.load()
    print("CameraService inicializado com sucesso!")
