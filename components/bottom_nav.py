import flet as ft
from theme import (
    COLOR_PRIMARY,
    COLOR_ICON_BG,
    COLOR_TEXT_MUTED,
    COLOR_CARD_BG,
    COLOR_BORDER_SUBTLE,
)


def build_bottom_nav(page: ft.Page, active_tab: str = "camera") -> ft.Container:
    """
    Barra de navegação inferior alternando entre as telas Câmera e Imagem.
    A função Tela permanece com controle exclusivo na tela principal.
    """
    tabs = [
        ("camera", "Câmera", ft.Icons.PHOTO_CAMERA_OUTLINED, "/camera"),
        ("image", "Imagem", ft.Icons.IMAGE_OUTLINED, "/image"),
    ]

    item_controls = []

    for tab_id, label, icon, route in tabs:
        is_active = tab_id == active_tab

        if is_active:
            # Item Ativo: Pill suave com indicador azul inferior
            item = ft.Container(
                width=130,
                padding=ft.Padding.symmetric(vertical=8),
                border_radius=16,
                bgcolor=COLOR_ICON_BG,
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(icon, color=COLOR_PRIMARY, size=22),
                        ft.Text(
                            label,
                            size=12,
                            weight=ft.FontWeight.W_700,
                            color=COLOR_PRIMARY,
                        ),
                        # Barra indicadora ativa
                        ft.Container(
                            width=24,
                            height=2.5,
                            border_radius=2,
                            bgcolor=COLOR_PRIMARY,
                            margin=ft.Margin.only(top=1),
                        ),
                    ],
                ),
            )
        else:
            # Item Inativo: Clicável para navegar
            item = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda _, r=route: page.navigate(r),
                content=ft.Container(
                    width=130,
                    padding=ft.Padding.symmetric(vertical=8),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        spacing=3,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icon, color=COLOR_TEXT_MUTED, size=22),
                            ft.Text(
                                label,
                                size=12,
                                weight=ft.FontWeight.W_500,
                                color=COLOR_TEXT_MUTED,
                            ),
                            # Espaçador invisível para manter altura uniforme
                            ft.Container(height=2.5, margin=ft.Margin.only(top=1)),
                        ],
                    ),
                ),
            )

        item_controls.append(item)

    return ft.Container(
        bgcolor=COLOR_CARD_BG,
        border=ft.Border(top=ft.BorderSide(1.0, COLOR_BORDER_SUBTLE)),
        padding=ft.Padding.only(top=8, bottom=14, left=16, right=16),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=item_controls,
        ),
    )
