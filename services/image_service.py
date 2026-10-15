import sys
import os
import cv2
import base64
from collections import Counter
import numpy as np
from services.color_dataset import ColorDatasetService

# Permite execução direta do script ou importação via módulo raiz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class ImageService:
    def __init__(self):
        self.dataset = ColorDatasetService()
        self.current_image = None
        self.image_path = None
        self.dataset.load()

    def load_image(self, file_path: str) -> dict | None:
        """Carrega e prepara a imagem para exibição e processamento."""
        if not file_path or not os.path.exists(file_path):
            return None

        img = cv2.imread(file_path)
        if img is None:
            return None

        self.current_image = img
        self.image_path = file_path

        h, w = img.shape[:2]

        # Calcula dimensões proporcionais para o container do app (máx 360x380)
        scale = min(360.0 / w, 380.0 / h, 1.0)
        display_w = max(50, int(w * scale))
        display_h = max(50, int(h * scale))

        display_img = cv2.resize(img, (display_w, display_h))
        success, buffer = cv2.imencode(".jpg", display_img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not success:
            return None

        b64_str = base64.b64encode(buffer).decode("utf-8")
        data_uri = f"data:image/jpeg;base64,{b64_str}"

        return {
            "data_uri": data_uri,
            "display_width": display_w,
            "display_height": display_h,
            "original_width": w,
            "original_height": h,
        }

    def clear(self):
        """Limpa a imagem carregada da memória."""
        self.current_image = None
        self.image_path = None

    def sample_point(self, norm_x: float, norm_y: float) -> dict | None:
        """Identifica a cor no ponto normalizado (0.0 a 1.0)."""
        if self.current_image is None:
            return None

        h, w = self.current_image.shape[:2]
        px = max(0, min(int(norm_x * w), w - 1))
        py = max(0, min(int(norm_y * h), h - 1))

        b, g, r = self.current_image[py, px]
        r, g, b = int(r), int(g), int(b)

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
        Analisa uma área retangular na imagem e retorna as cores predominantes
        baseado na lógica de analyze_region do projeto IRIS.
        """
        if self.current_image is None:
            return []

        h, w = self.current_image.shape[:2]
        x0 = max(0, min(int(min(norm_x0, norm_x1) * w), w - 1))
        x1 = max(0, min(int(max(norm_x0, norm_x1) * w), w - 1))
        y0 = max(0, min(int(min(norm_y0, norm_y1) * h), h - 1))
        y1 = max(0, min(int(max(norm_y0, norm_y1) * h), h - 1))

        if (x1 - x0) < 3 or (y1 - y0) < 3:
            return []

        region = self.current_image[y0:y1, x0:x1]
        pixels_bgr = region.reshape(-1, 3).astype(np.int32)
        pixels_rgb = pixels_bgr[:, ::-1]

        if len(pixels_rgb) > 2000:
            idx = np.random.choice(len(pixels_rgb), 2000, replace=False)
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
