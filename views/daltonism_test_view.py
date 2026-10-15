import flet as ft
from theme import *
from services.i18n_service import I18nService

def DaltonismTestView(page: ft.Page) -> ft.View:
    i18n = I18nService.get_instance()
    return ft.View(
        route="/daltonism_test",
        bgcolor=COLOR_BG,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=400,
                padding=ft.Padding.symmetric(horizontal=20, vertical=16),
                content=ft.Column(
                    spacing=20,
                    controls=[
                        # Barra superior com botão voltar
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                                    icon_color=COLOR_TEXT_PRIMARY,
                                    icon_size=20,
                                    on_click=lambda _: page.navigate("/"),
                                ),
                                ft.Text(
                                    i18n.t("daltonism_title"),
                                    size=17,
                                    weight=ft.FontWeight.W_600,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                            ]
                        ),
                        # Placeholder de conteúdo aguardando tela
                        ft.Container(
                            height=480,
                            bgcolor=COLOR_CARD_BG,
                            border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                            border_radius=20,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=12,
                                controls=[
                                    ft.Icon(ft.Icons.REMOVE_RED_EYE_OUTLINED, size=52, color=COLOR_PRIMARY),
                                    ft.Text(
                                        i18n.t("daltonism_heading"),
                                        size=16,
                                        weight=ft.FontWeight.W_600,
                                        color=COLOR_TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        i18n.t("daltonism_coming_soon"),
                                        size=13,
                                        color=COLOR_TEXT_MUTED,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ],
    )
