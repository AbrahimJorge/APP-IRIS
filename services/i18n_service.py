import os
import json

from services.constants.translate_constants import *

class I18nService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nService, cls).__new__(cls)
            cls._instance.language = "pt"
            cls._instance.listeners = []
            cls._instance._load_config()
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = I18nService()
        return cls._instance

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.language = data.get("language", "pt")
        except Exception as e:
            print(f"[I18nService] Aviso ao carregar config: {e}")
            self.language = "pt"

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump({"language": self.language}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[I18nService] Erro ao salvar config: {e}")

    def get_language(self) -> str:
        return self.language

    def set_language(self, lang: str):
        if lang not in ("pt", "en"):
            lang = "pt"
        if self.language != lang:
            self.language = lang
            self._save_config()
            self._notify_listeners()

    def add_listener(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _notify_listeners(self):
        for cb in list(self.listeners):
            try:
                cb(self.language)
            except Exception as e:
                print(f"[I18nService] Erro ao notificar listener: {e}")

    def t(self, key: str, default: str = None) -> str:
        """Retorna a string traduzida para o idioma atual."""
        lang_dict = TRANSLATIONS.get(self.language, TRANSLATIONS["pt"])
        if key in lang_dict:
            return lang_dict[key]
        pt_dict = TRANSLATIONS["pt"]
        if key in pt_dict:
            return pt_dict[key]
        return default if default is not None else key

    def translate_color(self, family_name: str) -> str:
        """Traduz a família de cor para o idioma ativo."""
        if not family_name:
            return family_name
        if self.language == "en":
            return PT_TO_EN_COLORS.get(family_name, family_name)
        else:
            return EN_TO_PT_COLORS.get(family_name, family_name)
