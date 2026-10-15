import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "config.json")

TRANSLATIONS = {
    "pt": {
        # App / Geral
        "app_title": "IRIS - Identificador de Cores",
        "breadcrumb_iris": "IRIS",
        "active": "Ativo",
        "active_badge": "  (Ativo)",

        # Cores (Famílias)
        "color_black": "Preto",
        "color_white": "Branco",
        "color_gray": "Cinza",
        "color_red": "Vermelho",
        "color_brown": "Marrom",
        "color_orange": "Laranja",
        "color_beige": "Bege",
        "color_yellow": "Amarelo",
        "color_green": "Verde",
        "color_cyan": "Ciano",
        "color_blue": "Azul",
        "color_purple": "Roxo",
        "color_pink": "Rosa",
        "color_unknown": "Desconhecido",

        # Navegação inferior
        "nav_camera": "Câmera",
        "nav_image": "Imagem",

        # Tela Inicial (HomeView)
        "home_test_btn": "Teste · Em breve",
        "home_settings_btn": "Configurações",
        "home_slogan": "No ambiente ou no digital, encontre\na cor de que você precisa.",
        "home_section_title": "COMO VOCÊ QUER IDENTIFICAR?",
        "home_camera_title": "Câmera",
        "home_camera_desc": "Identifique cores ao seu redor.",
        "home_image_title": "Imagem",
        "home_image_desc": "Escolha uma foto e toque em uma\nregião.",
        "home_screen_title": "Tela",
        "home_screen_desc_idle": "Menu flutuante para identificar cores\nem qualquer tela.",
        "home_screen_desc_active": "Menu flutuante ativo na tela. Toque para desligar.",
        "home_screen_badge_on": "LIGADO",
        "home_footer": "Sempre uma cor. Sempre um nome.",

        # Configurações (SettingsView)
        "settings_breadcrumb": "IRIS / Configurações",
        "settings_title": "Configurações",
        "settings_subtitle": "Deixe o IRIS no seu idioma.",
        "settings_section_title": "Idioma do aplicativo",
        "settings_section_desc": "Escolha o idioma dos textos e orientações. A mudança é aplicada ao selecionar.",
        "settings_lang_pt": "Português",
        "settings_lang_pt_sub": "Brasil",
        "settings_lang_pt_selected": "Brasil · Selecionado",
        "settings_lang_en": "English",
        "settings_lang_en_sub": "Inglês",
        "settings_lang_en_selected": "Inglês · Selecionado",
        "settings_status_pt": "Seu idioma atual é Português.",
        "settings_status_en": "Seu idioma atual é Inglês.",
        "settings_about_title": "Sobre o IRIS",
        "settings_about_version": "Protótipo · Versão 0.1",
        "settings_about_p1": "Um apoio para reconhecer e nomear cores no ambiente físico e digital, com mais autonomia.",
        "settings_about_p2": "As leituras são aproximadas. Iluminação, câmera e qualidade da imagem podem influenciar o resultado.",

        # Modos / Tabs
        "tab_clique": "Clique",
        "tab_selecao": "Seleção",

        # Menu Flutuante / Tela (ScreenFloatingService)
        "opt_clique_desc": "Usa o ponto exato da tela.",
        "opt_selecao_desc": "Marca uma área da tela.",
        "waiting_click": "Aguardando clique",
        "waiting_click_desc": "Toque em um ponto da tela",
        "waiting_select": "Aguardando seleção",
        "waiting_select_desc": "Arraste na tela para listar as cores",
        "select_area_hint": "Selecione uma área",
        "drag_hint": "Arraste na tela para listar",
        "area_colors_title": "Cores da Área",

        # Câmera e Imagem
        "camera_tap_hint": "Toque na câmera para identificar",
        "camera_drag_hint": "Arraste na câmera para marcar uma área",
        "camera_waiting_tap": "Aguardando toque na câmera",
        "image_tap_hint": "Toque na imagem para identificar a cor",
        "image_drag_hint": "Arraste para selecionar uma área",
        "image_upload_prompt": "Toque aqui para escolher uma imagem do seu dispositivo",
        "image_select_other": "Escolher outra imagem",
        "image_none_loaded": "Nenhuma imagem selecionada",
        "image_waiting_tap": "Aguardando toque",
        "image_waiting_tap_sub": "Toque em um ponto da imagem",

        # Teste de Daltonismo
        "daltonism_title": "Teste de Daltonismo",
        "daltonism_heading": "Teste de Visão e Daltonismo",
        "daltonism_coming_soon": "Em breve: Teste de identificação com placas de Ishihara e mapeamento de tipo de daltonismo.",
    },
    "en": {
        # App / General
        "app_title": "IRIS - Color Identifier",
        "breadcrumb_iris": "IRIS",
        "active": "Active",
        "active_badge": "  (Active)",

        # Colors (Families)
        "color_black": "Black",
        "color_white": "White",
        "color_gray": "Gray",
        "color_red": "Red",
        "color_brown": "Brown",
        "color_orange": "Orange",
        "color_beige": "Beige",
        "color_yellow": "Yellow",
        "color_green": "Green",
        "color_cyan": "Cyan",
        "color_blue": "Blue",
        "color_purple": "Purple",
        "color_pink": "Pink",
        "color_unknown": "Unknown",

        # Bottom nav
        "nav_camera": "Camera",
        "nav_image": "Image",

        # HomeView
        "home_test_btn": "Test · Coming soon",
        "home_settings_btn": "Settings",
        "home_slogan": "In physical or digital spaces, find\nthe color you need.",
        "home_section_title": "HOW DO YOU WANT TO IDENTIFY?",
        "home_camera_title": "Camera",
        "home_camera_desc": "Identify colors around you.",
        "home_image_title": "Image",
        "home_image_desc": "Choose a photo and tap a\nregion.",
        "home_screen_title": "Screen",
        "home_screen_desc_idle": "Floating menu to identify colors\non any screen.",
        "home_screen_desc_active": "Floating menu active on screen. Tap to turn off.",
        "home_screen_badge_on": "ON",
        "home_footer": "Always a color. Always a name.",

        # SettingsView
        "settings_breadcrumb": "IRIS / Settings",
        "settings_title": "Settings",
        "settings_subtitle": "Set IRIS to your language.",
        "settings_section_title": "App language",
        "settings_section_desc": "Choose the language for texts and guides. Changes take effect on selection.",
        "settings_lang_pt": "Português",
        "settings_lang_pt_sub": "Portuguese",
        "settings_lang_pt_selected": "Portuguese · Selected",
        "settings_lang_en": "English",
        "settings_lang_en_sub": "English",
        "settings_lang_en_selected": "English · Selected",
        "settings_status_pt": "Your current language is Portuguese.",
        "settings_status_en": "Your current language is English.",
        "settings_about_title": "About IRIS",
        "settings_about_version": "Prototype · Version 0.1",
        "settings_about_p1": "A support to recognize and name colors in physical and digital environments, with more autonomy.",
        "settings_about_p2": "Readings are approximate. Lighting, camera, and image quality may influence the result.",

        # Modes / Tabs
        "tab_clique": "Click",
        "tab_selecao": "Selection",

        # Floating Menu / Screen
        "opt_clique_desc": "Uses the exact screen point.",
        "opt_selecao_desc": "Marks an area of the screen.",
        "waiting_click": "Waiting for click",
        "waiting_click_desc": "Tap a point on the screen",
        "waiting_select": "Waiting for selection",
        "waiting_select_desc": "Drag on screen to list colors",
        "select_area_hint": "Select an area",
        "drag_hint": "Drag on screen to list",
        "area_colors_title": "Area Colors",

        # Camera & Image
        "camera_tap_hint": "Tap on camera to identify",
        "camera_drag_hint": "Drag on camera to mark an area",
        "camera_waiting_tap": "Waiting for tap on camera",
        "image_tap_hint": "Tap image to identify color",
        "image_drag_hint": "Drag to select an area",
        "image_upload_prompt": "Tap here to choose an image from your device",
        "image_select_other": "Choose another image",
        "image_none_loaded": "No image selected",
        "image_waiting_tap": "Waiting for tap",
        "image_waiting_tap_sub": "Tap a point on the image",

        # Color Blindness Test
        "daltonism_title": "Color Blindness Test",
        "daltonism_heading": "Vision and Color Blindness Test",
        "daltonism_coming_soon": "Coming soon: Identification test with Ishihara plates and color blindness type mapping.",
    }
}

PT_TO_EN_COLORS = {
    "Preto": "Black",
    "Branco": "White",
    "Cinza": "Gray",
    "Vermelho": "Red",
    "Marrom": "Brown",
    "Laranja": "Orange",
    "Bege": "Beige",
    "Amarelo": "Yellow",
    "Verde": "Green",
    "Ciano": "Cyan",
    "Azul": "Blue",
    "Roxo": "Purple",
    "Rosa": "Pink",
    "Desconhecido": "Unknown",
}

EN_TO_PT_COLORS = {v: k for k, v in PT_TO_EN_COLORS.items()}