import flet as ft
from theme import *
from components.bottom_nav import build_bottom_nav
from services.screen_service import ScreenFloatingService

def ScreenPickerView(page: ft.Page) -> ft.View:
    """Tela de Captura de Tela (Menu Flutuante / Suspenso)."""
    service = ScreenFloatingService.get_instance()

    # 1. Topo: Botão Voltar + Breadcrumb
    header = ft.Row(
        spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda _: page.navigate("/"),
                content=ft.Container(
                    width=42,
                    height=42,
                    border_radius=14,
                    border=ft.Border.all(1.2, COLOR_BORDER_SUBTLE),
                    bgcolor=COLOR_CARD_BG,
                    alignment=ft.Alignment.CENTER,
                    ink=True,
                    content=ft.Icon(
                        ft.Icons.ARROW_BACK,
                        color=COLOR_TEXT_PRIMARY,
                        size=20,
                    ),
                ),
            ),
            ft.Text(
                "IRIS / Tela",
                size=14,
                weight=ft.FontWeight.W_600,
                color=COLOR_TEXT_MUTED,
            ),
        ],
    )

    # 2. Título & Subtítulo
    title_section = ft.Column(
        spacing=4,
        controls=[
            ft.Text(
                "Captura de Tela",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=COLOR_TEXT_PRIMARY,
            ),
            ft.Text(
                "Menu suspenso para identificar cores em qualquer lugar.",
                size=13.5,
                color=COLOR_TEXT_MUTED,
            ),
        ],
    )

    # Referências para atualização dinâmica de status
    status_indicator = ft.Container(
        width=10,
        height=10,
        border_radius=5,
        bgcolor="#10B981" if service.is_running else "#94A3B8",
    )
    status_label = ft.Text(
        "MENU FLUTUANTE ATIVO NA TELA" if service.is_running else "MENU FLUTUANTE DESATIVADO",
        size=10.5,
        weight=ft.FontWeight.W_700,
        color="#059669" if service.is_running else COLOR_TEXT_MUTED,
        style=ft.TextStyle(letter_spacing=0.5),
    )

    btn_toggle_text = ft.Text(
        "Desativar Menu Flutuante" if service.is_running else "Ativar Menu Flutuante",
        size=14.5,
        weight=ft.FontWeight.BOLD,
        color="#DC2626" if service.is_running else "#FFFFFF",
    )
    btn_toggle_icon = ft.Icon(
        ft.Icons.STOP_CIRCLE_OUTLINED if service.is_running else ft.Icons.LAYERS_ROUNDED,
        color="#DC2626" if service.is_running else "#FFFFFF",
        size=20,
    )
    btn_toggle_container = ft.Container(
        padding=ft.Padding.symmetric(vertical=14, horizontal=20),
        border_radius=14,
        bgcolor="#FEE2E2" if service.is_running else COLOR_PRIMARY,
        border=ft.Border.all(1.2, "#FCA5A5" if service.is_running else COLOR_PRIMARY),
        alignment=ft.Alignment.CENTER,
        shadow=None if service.is_running else ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color="#251D5CD4",
            offset=ft.Offset(0, 4),
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[btn_toggle_icon, btn_toggle_text],
        ),
    )

    def refresh_ui_state(is_active: bool):
        status_indicator.bgcolor = "#10B981" if is_active else "#94A3B8"
        status_label.value = "MENU FLUTUANTE ATIVO NA TELA" if is_active else "MENU FLUTUANTE DESATIVADO"
        status_label.color = "#059669" if is_active else COLOR_TEXT_MUTED

        btn_toggle_text.value = "Desativar Menu Flutuante" if is_active else "Ativar Menu Flutuante"
        btn_toggle_text.color = "#DC2626" if is_active else "#FFFFFF"
        btn_toggle_icon.name = ft.Icons.STOP_CIRCLE_OUTLINED if is_active else ft.Icons.LAYERS_ROUNDED
        btn_toggle_icon.color = "#DC2626" if is_active else "#FFFFFF"

        btn_toggle_container.bgcolor = "#FEE2E2" if is_active else COLOR_PRIMARY
        btn_toggle_container.border = ft.Border.all(1.2, "#FCA5A5" if is_active else COLOR_PRIMARY)
        btn_toggle_container.shadow = None if is_active else ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color="#251D5CD4",
            offset=ft.Offset(0, 4),
        )

        try:
            page.update()
        except Exception:
            pass

    def on_status_changed(active: bool):
        if page and hasattr(page, "loop") and page.loop:
            page.loop.call_soon_threadsafe(refresh_ui_state, active)
        else:
            refresh_ui_state(active)

    def toggle_floating_service(e=None):
        if service.is_running:
            service.stop()
            refresh_ui_state(False)
        else:
            service.start(on_status_change=on_status_changed)
            refresh_ui_state(True)

    # 3. Card Principal de Controle do Menu Suspenso
    main_control_card = ft.Container(
        bgcolor=COLOR_CARD_BG,
        border=ft.Border.all(1.2, COLOR_CARD_BORDER),
        border_radius=22,
        padding=ft.Padding.all(20),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color="#08000000",
            offset=ft.Offset(0, 2),
        ),
        content=ft.Column(
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Ilustração do ícone suspenso
                ft.Container(
                    width=72,
                    height=72,
                    border_radius=36,
                    bgcolor="#0D1B2A",
                    border=ft.Border.all(2.5, "#FFFFFF"),
                    alignment=ft.Alignment.CENTER,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=12,
                        color="#20000000",
                        offset=ft.Offset(0, 4),
                    ),
                    content=ft.Image(
                        src="assets/floating_eye.png",
                        width=60,
                        height=60,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                ),
                # Badge de Status Ativo / Desativado
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    border_radius=12,
                    bgcolor="#ECFDF5" if service.is_running else COLOR_BG,
                    content=ft.Row(
                        tight=True,
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[status_indicator, status_label],
                    ),
                ),
                # Texto explicativo
                ft.Text(
                    "O menu suspenso flutua sobre qualquer aplicativo no seu computador, permitindo identificar cores da tela em tempo real.",
                    size=12.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                # Botão de Ação
                ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_tap=toggle_floating_service,
                    content=btn_toggle_container,
                ),
            ],
        ),
    )

    # 4. Seção "Como Funciona" (Fiel ao protótipo de 3 etapas)
    def build_step_item(num: str, title: str, desc: str, icon: str):
        return ft.Container(
            padding=ft.Padding.all(14),
            border_radius=16,
            bgcolor=COLOR_CARD_BG,
            border=ft.Border.all(1.0, COLOR_CARD_BORDER),
            content=ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=38,
                        height=38,
                        border_radius=12,
                        bgcolor=COLOR_ICON_BG,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(icon, color=COLOR_PRIMARY, size=20),
                    ),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Text(num, size=11, weight=ft.FontWeight.W_800, color=COLOR_PRIMARY),
                                    ft.Text(title, size=13.5, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                                ],
                            ),
                            ft.Text(desc, size=11.5, color=COLOR_TEXT_MUTED),
                        ],
                    ),
                ],
            ),
        )

    guide_section = ft.Column(
        spacing=10,
        controls=[
            ft.Text(
                "COMO USAR O MENU SUSPENSO",
                size=11,
                weight=ft.FontWeight.W_700,
                color=COLOR_TEXT_MUTED,
                style=ft.TextStyle(letter_spacing=0.6),
            ),
            build_step_item(
                "1.",
                "Ícone na Lateral",
                "Fica recolhido na borda com baixa opacidade. Ao passar o mouse ou clicar, ele expande.",
                ft.Icons.RADIO_BUTTON_CHECKED,
            ),
            build_step_item(
                "2.",
                "Clique ou Seleção",
                "Abra o menu para alternar entre identificar o ponto exato da tela ou selecionar uma área retangular.",
                ft.Icons.TOUCH_APP_OUTLINED,
            ),
            build_step_item(
                "3.",
                "Barrinha de Cor em Tempo Real",
                "A barrinha flutuante indica a cor identificada instantaneamente sobre qualquer tela.",
                ft.Icons.PALETTE_OUTLINED,
            ),
        ],
    )

    # 5. Dica de Uso
    tip_pill = ft.Container(
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        border_radius=12,
        bgcolor="#F0F9FF",
        border=ft.Border.all(1.0, "#BAE6FD"),
        content=ft.Row(
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.LIGHTBULB_OUTLINED, size=18, color="#0284C7"),
                ft.Text(
                    "Para fechar o menu flutuante a qualquer momento, clique com o botão direito no ícone suspenso ou aperte Desativar acima.",
                    size=11.5,
                    color="#0369A1",
                    expand=True,
                ),
            ],
        ),
    )

    # 6. Barra de Navegação Inferior
    bottom_nav = build_bottom_nav(page, active_tab="screen")

    body_content = ft.Container(
        width=400,
        padding=ft.Padding.only(left=20, right=20, top=14, bottom=12),
        content=ft.Column(
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                header,
                title_section,
                main_control_card,
                guide_section,
                tip_pill,
            ],
        ),
    )

    return ft.View(
        route="/screen",
        bgcolor=COLOR_BG,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
        bottom_appbar=ft.BottomAppBar(
            padding=0,
            content=bottom_nav,
        ),
        controls=[body_content],
    )
