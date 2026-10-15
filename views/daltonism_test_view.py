import flet as ft
from theme import COLOR_BG, COLOR_PRIMARY, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED


def DaltonismTestView(page: ft.Page) -> ft.View:
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
                                    "Teste de Daltonismo",
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
                                        "Teste de Visão e Daltonismo",
                                        size=16,
                                        weight=ft.FontWeight.W_600,
                                        color=COLOR_TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        "Em breve: Teste de identificação com placas de Ishihara e mapeamento de tipo de daltonismo.",
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
