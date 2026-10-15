import os
import colorsys
import ssl
import pandas as pd
from scipy.spatial import KDTree
from services.i18n_service import I18nService
from services.constants.dataset_constants import *

class ColorDatasetService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ColorDatasetService, cls).__new__(cls)
            cls._instance.tree = None
            cls._instance.names = None
            cls._instance.hexes = None
            cls._instance.is_loaded = False
        return cls._instance

    def load(self) -> bool:
        """Carrega a base de dados de cores (localmente ou via GitHub)."""
        if self.is_loaded:
            return True

        try:
            if os.path.exists(CSV_PATH):
                df = pd.read_csv(CSV_PATH)
            else:
                ssl._create_default_https_context = ssl._create_unverified_context
                df = pd.read_csv(GITHUB_URL, names=["Name", "Hex", "R", "G", "B"])

            self.names = df["Name"].values
            self.hexes = df["Hex"].values
            self.tree = KDTree(df[["R", "G", "B"]].values)
            self.is_loaded = True
            print("Dataset de cores carregado com sucesso!")
            return True
        except Exception as e:
            print(f"Erro ao carregar dataset de cores: {e}")
            return False

    def get_closest_color_name(self, r: int, g: int, b: int) -> str:
        """Retorna o nome específico da cor mais próxima pelo KDTree."""
        if not self.tree:
            return I18nService.get_instance().t("color_unknown", "Desconhecido")
        _, index = self.tree.query((r, g, b))
        return self.names[index]

    def query(self, pixels_rgb):
        """Consulta múltiplos pixels RGB simultaneamente."""
        if not self.tree:
            return None, None
        return self.tree.query(pixels_rgb)

    def classify_color(self, r: int, g: int, b: int) -> tuple[str, str, str]:
        """
        Classifica a cor em família em português, nome do dataset e hex.
        Exemplo de retorno: ('Azul', 'Royal Blue · #1D5CD4', '#1D5CD4')
        Fiel aos requisitos: Cor em cima, cor do dataset embaixo e do lado o código.
        """
        hex_code = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
        specific_name = self.get_closest_color_name(r, g, b)
        detail = f"{specific_name} · {hex_code}"

        rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
        h, l, s = colorsys.rgb_to_hls(rn, gn, bn)
        h_deg = h * 360.0

        # Neutros
        if l < 0.15:
            family = "Preto"
        elif l > 0.88 and s < 0.20:
            family = "Branco"
        elif s < 0.15:
            family = "Cinza"
        # Famílias cromáticas pelo Matiz (Hue)
        elif h_deg < 15 or h_deg >= 345:
            family = "Vermelho"
        elif h_deg < 45:
            family = "Marrom" if (l < 0.40 and s > 0.20) else "Laranja"
        elif h_deg < 65:
            family = "Bege" if (s < 0.35 and l > 0.60) else "Amarelo"
        elif h_deg < 165:
            family = "Verde"
        elif h_deg < 200:
            family = "Ciano"
        elif h_deg < 260:
            family = "Azul"
        elif h_deg < 300:
            family = "Roxo"
        else:
            family = "Rosa"

        family = I18nService.get_instance().translate_color(family)
        return family, detail, hex_code
