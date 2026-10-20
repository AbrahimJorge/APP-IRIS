import flet as ft
from theme import *
try:
    from services.screen_service import ScreenFloatingService
except Exception:
    class ScreenFloatingService:
        is_available = False
        is_running = False
        @classmethod
        def get_instance(cls):
            return cls()
        def start(self, *a, **kw): pass
        def stop(self): pass
        def shutdown(self): pass

from services.i18n_service import I18nService

def build_top_button(icon: str, label: str, on_click):
    """Cria o botão de cabeçalho (Teste / Configurações)."""
    return ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.CLICK,
        on_tap=on_click,
        content=ft.Column(
            spacing=5,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=14,
                    border=ft.Border.all(1.2, COLOR_BORDER_SUBTLE),
                    bgcolor=COLOR_CARD_BG,
                    alignment=ft.Alignment.CENTER,
                    ink=True,
                    content=ft.Icon(icon, color=COLOR_TEXT_PRIMARY, size=22),
                ),
                ft.Text(
                    label,
                    size=11,
                    weight=ft.FontWeight.W_700,
                    color=COLOR_TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )


def build_feature_card(icon: str, title: str, description: str, on_click):
    """Cria os cards de ação (Câmera, Imagem, Tela)."""
    return ft.Container(
        bgcolor=COLOR_CARD_BG,
        border=ft.Border.all(1.2, COLOR_CARD_BORDER),
        border_radius=18,
        padding=ft.Padding.symmetric(horizontal=16, vertical=16),
        ink=True,
        on_click=on_click,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=6,
            color="#08000000",
            offset=ft.Offset(0, 2),
        ),
        content=ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=13,
                    bgcolor=COLOR_ICON_BG,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(icon, color=COLOR_PRIMARY, size=24),
                ),
                
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(
                            title,
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(
                            description,
                            size=12.5,
                            color=COLOR_TEXT_MUTED,
                            weight=ft.FontWeight.W_400,
                        ),
                    ],
                ),
                
                ft.Icon(
                    ft.Icons.CHEVRON_RIGHT_ROUNDED,
                    color=COLOR_TEXT_CHEVRON,
                    size=20,
                ),
            ],
        ),
    )


def HomeView(page: ft.Page) -> ft.View:
    """Retorna a tela principal do IRIS."""
    i18n = I18nService.get_instance()

    
    header_bar = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            build_top_button(
                icon=ft.Icons.REMOVE_RED_EYE_OUTLINED,
                label=i18n.t("home_test_btn"),
                on_click=lambda _: page.navigate("/daltonism_test"),
            ),
            build_top_button(
                icon=ft.Icons.SETTINGS_OUTLINED,
                label=i18n.t("home_settings_btn"),
                on_click=lambda _: page.navigate("/settings"),
            ),
        ],
    )

    
    hero_section = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
        controls=[
            ft.Image(
                src="logo.png",
                width=64,
                height=64,
                fit=ft.BoxFit.CONTAIN,
            ),
            ft.Text(
                "IRIS",
                size=13,
                weight=ft.FontWeight.W_800,
                color=COLOR_PRIMARY,
                style=ft.TextStyle(letter_spacing=1.8),
            ),
            ft.Container(height=4),
            ft.Text(
                i18n.t("home_slogan"),
                size=19,
                weight=ft.FontWeight.W_600,
                color=COLOR_TEXT_HEADING,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
    )

    
    section_title = ft.Container(
        padding=ft.Padding.only(left=2, top=6),
        content=ft.Text(
            i18n.t("home_section_title"),
            size=11.5,
            weight=ft.FontWeight.W_700,
            color=COLOR_TEXT_MUTED,
            style=ft.TextStyle(letter_spacing=0.6),
        ),
    )

    
    service = ScreenFloatingService.get_instance()

    tela_icon = ft.Icon(
        ft.Icons.FIT_SCREEN_ROUNDED,
        color="#059669" if service.is_running else COLOR_PRIMARY,
        size=24,
    )
    tela_icon_box = ft.Container(
        width=48,
        height=48,
        border_radius=13,
        bgcolor="#ECFDF5" if service.is_running else COLOR_ICON_BG,
        alignment=ft.Alignment.CENTER,
        content=tela_icon,
    )

    tela_desc = ft.Text(
        i18n.t("home_screen_desc_active") if service.is_running else i18n.t("home_screen_desc_idle"),
        size=12.5,
        color="#059669" if service.is_running else COLOR_TEXT_MUTED,
        weight=ft.FontWeight.W_500 if service.is_running else ft.FontWeight.W_400,
    )

    tela_badge = ft.Container(
        content=(
            ft.Row(
                tight=True,
                spacing=4,
                controls=[
                    ft.Container(width=7, height=7, border_radius=3.5, bgcolor="#10B981"),
                    ft.Text(i18n.t("home_screen_badge_on"), size=10, weight=ft.FontWeight.W_800, color="#059669"),
                ],
            )
            if service.is_running
            else ft.Icon(
                ft.Icons.CHEVRON_RIGHT_ROUNDED,
                color=COLOR_TEXT_CHEVRON,
                size=20,
            )
        )
    )

    def refresh_tela_card():
        is_on = service.is_running
        tela_desc.value = (
            i18n.t("home_screen_desc_active")
            if is_on
            else i18n.t("home_screen_desc_idle")
        )
        tela_desc.color = "#059669" if is_on else COLOR_TEXT_MUTED
        tela_desc.weight = ft.FontWeight.W_500 if is_on else ft.FontWeight.W_400

        tela_icon_box.bgcolor = "#ECFDF5" if is_on else COLOR_ICON_BG
        tela_icon.color = "#059669" if is_on else COLOR_PRIMARY

        tela_badge.content = (
            ft.Row(
                tight=True,
                spacing=4,
                controls=[
                    ft.Container(width=7, height=7, border_radius=3.5, bgcolor="#10B981"),
                    ft.Text(i18n.t("home_screen_badge_on"), size=10, weight=ft.FontWeight.W_800, color="#059669"),
                ],
            )
            if is_on
            else ft.Icon(
                ft.Icons.CHEVRON_RIGHT_ROUNDED,
                color=COLOR_TEXT_CHEVRON,
                size=20,
            )
        )
        try:
            page.update()
        except Exception:
            pass

    def on_floating_status_change(active: bool):
        if page and hasattr(page, "loop") and page.loop:
            page.loop.call_soon_threadsafe(refresh_tela_card)
        else:
            refresh_tela_card()

    def toggle_tela(_):
        if service.is_running:
            service.stop()
            refresh_tela_card()
        else:
            service.start(on_status_change=on_floating_status_change, page=page)
            refresh_tela_card()

    tela_card = ft.Container(
        bgcolor=COLOR_CARD_BG,
        border=ft.Border.all(1.2, COLOR_CARD_BORDER),
        border_radius=18,
        padding=ft.Padding.symmetric(horizontal=16, vertical=16),
        ink=True,
        on_click=toggle_tela,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=6,
            color="#08000000",
            offset=ft.Offset(0, 2),
        ),
        content=ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                tela_icon_box,
                ft.Column(
                    spacing=3,
                    expand=True,
                    controls=[
                        ft.Text(
                            i18n.t("home_screen_title"),
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        tela_desc,
                    ],
                ),
                tela_badge,
            ],
        ),
    )

    
    cards_section = ft.Column(
        spacing=12,
        controls=[
            build_feature_card(
                icon=ft.Icons.PHOTO_CAMERA_OUTLINED,
                title=i18n.t("home_camera_title"),
                description=i18n.t("home_camera_desc"),
                on_click=lambda _: page.navigate("/camera"),
            ),
            build_feature_card(
                icon=ft.Icons.IMAGE_OUTLINED,
                title=i18n.t("home_image_title"),
                description=i18n.t("home_image_desc"),
                on_click=lambda _: page.navigate("/image"),
            ),
            tela_card,
        ],
    )

    
    footer = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=6,
        controls=[
            ft.Text(
                "T",
                size=12,
                weight=ft.FontWeight.W_600,
                color=COLOR_TEXT_MUTED,
            ),
            ft.Text(
                i18n.t("home_footer"),
                size=11.5,
                color=COLOR_TEXT_MUTED,
                weight=ft.FontWeight.W_400,
            ),
        ],
    )

    
    body_content = ft.Container(
        width=min(420, getattr(page, "width", 400) or 400),
        padding=ft.Padding.only(left=20, right=20, top=16, bottom=24),
        content=ft.Column(
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                header_bar,
                hero_section,
                section_title,
                cards_section,
                ft.Container(height=10),
                footer,
            ],
        ),
    )

    return ft.View(
        route="/",
        bgcolor=COLOR_BG,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
        controls=[body_content],
    )
