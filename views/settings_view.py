import flet as ft
from theme import *
from services.i18n_service import I18nService


def SettingsView(page: ft.Page) -> ft.View:
    i18n = I18nService.get_instance()

    # Container principal que conterá o layout dinamicamente atualizado
    main_column = ft.Column(spacing=20)

    def select_language(lang: str):
        if i18n.get_language() != lang:
            i18n.set_language(lang)
            build_layout()
            try:
                page.update()
            except Exception:
                pass

    def build_language_card(lang_code: str, title: str, sub_unselected: str, sub_selected: str):
        is_selected = i18n.get_language() == lang_code

        radio_icon = (
            ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED_ROUNDED, color=COLOR_PRIMARY, size=22)
            if is_selected
            else ft.Icon(ft.Icons.RADIO_BUTTON_OFF_ROUNDED, color="#94A3B8", size=22)
        )

        trailing_icon = (
            ft.Icon(ft.Icons.CHECK_ROUNDED, color=COLOR_PRIMARY, size=20)
            if is_selected
            else ft.Container(width=20)
        )

        return ft.Container(
            bgcolor=COLOR_CARD_BG,
            border=ft.Border.all(1.8 if is_selected else 1.2, COLOR_PRIMARY if is_selected else COLOR_CARD_BORDER),
            border_radius=16,
            padding=ft.Padding.symmetric(horizontal=16, vertical=16),
            ink=True,
            on_click=lambda _: select_language(lang_code),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=6,
                color="#06000000",
                offset=ft.Offset(0, 2),
            ),
            content=ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    radio_icon,
                    ft.Column(
                        spacing=3,
                        expand=True,
                        controls=[
                            ft.Text(
                                title,
                                size=15,
                                weight=ft.FontWeight.W_700 if is_selected else ft.FontWeight.W_600,
                                color=COLOR_TEXT_PRIMARY,
                            ),
                            ft.Text(
                                sub_selected if is_selected else sub_unselected,
                                size=12.5,
                                color=COLOR_PRIMARY if is_selected else COLOR_TEXT_MUTED,
                                weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400,
                            ),
                        ],
                    ),
                    trailing_icon,
                ],
            ),
        )

    def build_layout():
        cur_lang = i18n.get_language()

        # 1. Top Bar com Botão Voltar e Breadcrumb
        top_bar = ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=42,
                    height=42,
                    border_radius=13,
                    border=ft.Border.all(1.2, COLOR_BORDER_SUBTLE),
                    bgcolor=COLOR_CARD_BG,
                    alignment=ft.Alignment.CENTER,
                    ink=True,
                    on_click=lambda _: page.navigate("/"),
                    content=ft.Icon(
                        ft.Icons.ARROW_BACK_ROUNDED,
                        color=COLOR_TEXT_PRIMARY,
                        size=20,
                    ),
                ),
                ft.Text(
                    i18n.t("settings_breadcrumb"),
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color="#475569",
                ),
            ],
        )

        # 2. Título da Página e Subtítulo
        title_section = ft.Column(
            spacing=4,
            controls=[
                ft.Text(
                    i18n.t("settings_title"),
                    size=26,
                    weight=ft.FontWeight.W_700,
                    color=COLOR_TEXT_PRIMARY,
                ),
                ft.Text(
                    i18n.t("settings_subtitle"),
                    size=13.5,
                    color=COLOR_TEXT_MUTED,
                ),
            ],
        )

        # 3. Cabeçalho da Seção de Idioma
        section_header = ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.TRANSLATE_ROUNDED, size=20, color=COLOR_PRIMARY),
                        ft.Text(
                            i18n.t("settings_section_title"),
                            size=16,
                            weight=ft.FontWeight.W_700,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                    ],
                ),
                ft.Text(
                    i18n.t("settings_section_desc"),
                    size=12.5,
                    color=COLOR_TEXT_MUTED,
                    height=1.35,
                ),
            ],
        )

        # 4. Cards de Opções de Idioma (Português / English)
        card_pt = build_language_card(
            lang_code="pt",
            title=i18n.t("settings_lang_pt"),
            sub_unselected=i18n.t("settings_lang_pt_sub"),
            sub_selected=i18n.t("settings_lang_pt_selected"),
        )

        card_en = build_language_card(
            lang_code="en",
            title=i18n.t("settings_lang_en"),
            sub_unselected=i18n.t("settings_lang_en_sub"),
            sub_selected=i18n.t("settings_lang_en_selected"),
        )

        # 5. Status inferior com confirmação do idioma atual
        status_note = ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINED, size=16, color=COLOR_PRIMARY),
                ft.Text(
                    i18n.t("settings_status_pt") if cur_lang == "pt" else i18n.t("settings_status_en"),
                    size=12.5,
                    color=COLOR_TEXT_MUTED,
                ),
            ],
        )

        # 6. Card "Sobre o IRIS"
        about_card = ft.Container(
            bgcolor=COLOR_CARD_BG,
            border=ft.Border.all(1.2, COLOR_CARD_BORDER),
            border_radius=20,
            padding=ft.Padding.all(18),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=6,
                color="#06000000",
                offset=ft.Offset(0, 2),
            ),
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Image(
                                src="logo.png",
                                width=44,
                                height=44,
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        i18n.t("settings_about_title"),
                                        size=15,
                                        weight=ft.FontWeight.W_700,
                                        color=COLOR_TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        i18n.t("settings_about_version"),
                                        size=12,
                                        color=COLOR_TEXT_MUTED,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(
                        i18n.t("settings_about_p1"),
                        size=12.5,
                        color=COLOR_TEXT_MUTED,
                        height=1.4,
                    ),
                    ft.Text(
                        i18n.t("settings_about_p2"),
                        size=12.5,
                        color=COLOR_TEXT_MUTED,
                        height=1.4,
                    ),
                ],
            ),
        )

        main_column.controls = [
            top_bar,
            title_section,
            section_header,
            card_pt,
            card_en,
            status_note,
            ft.Container(height=4),
            about_card,
        ]

    # Constrói o layout inicial
    build_layout()

    return ft.View(
        route="/settings",
        bgcolor=COLOR_BG,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=400,
                padding=ft.Padding.only(left=20, right=20, top=16, bottom=24),
                content=main_column,
            )
        ],
    )
