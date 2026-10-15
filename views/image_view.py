import time
import threading
import flet as ft
from theme import (
    COLOR_BG,
    COLOR_PRIMARY,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_ICON_BG,
    COLOR_BORDER_SUBTLE,
)
from components.bottom_nav import build_bottom_nav
from services.image_service import ImageService


class ImageUIController:
    """
    Controlador da tela de Análise por Imagem integrado ao ImageService (OpenCV + KDTree).
    Realiza carregamento de imagem e identificação por ponto ou seleção de área.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.mode = "clique"  # 'clique' ou 'selecao'
        self.service = ImageService()

        # Estado da imagem e seleção
        self.has_image_loaded = False
        self.has_selected_color = False
        self.has_selected_area = False

        self.display_w = 360
        self.display_h = 380

        # Alvo e seleção
        self.target_x = 0.0
        self.target_y = 0.0
        self.drag_start = None
        self.drag_cur = None

        # Rastreamento de arrasto contínuo no modo clique
        self._last_drag_time = 0.0
        self._last_drag_pos = None
        self._is_drag_updating = False
        self._reticle_timer = None

        # Dados da cor selecionada (ponto)
        self.point_color_name = ""
        self.point_color_detail = ""
        self.point_color_hex = ""

        # Dados das cores identificadas (área)
        self.area_colors = []

        # Referências aos controles
        self.tab_clique = None
        self.tab_selecao = None
        self.upload_prompt = None
        self.image_control = None
        self.gesture_layer = None
        self.target_ring = None
        self.selection_box = None
        self.badge_container = None
        self.badge_text = None
        self.bottom_hint_pill = None
        self.instruction_text = None
        self.result_container = None
        self.btn_select_other = None

    def pick_image(self):
        """Abre o seletor nativo de arquivos de forma assíncrona/thread separada."""
        def _open():
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                path = filedialog.askopenfilename(
                    title="Selecione uma Imagem",
                    filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.webp *.heic")],
                )
                root.destroy()
                if path:
                    # Carrega e processa a imagem em segundo plano
                    res = self.service.load_image(path)
                    if res:
                        # Despacha a atualização visual de volta para o loop principal do Flet
                        if self.page and hasattr(self.page, "loop") and self.page.loop:
                            self.page.loop.call_soon_threadsafe(self.apply_loaded_image, res)
                        else:
                            self.apply_loaded_image(res)
            except Exception as e:
                print(f"Erro na seleção de arquivo: {e}")

        threading.Thread(target=_open, daemon=True).start()

    def load_selected_file(self, file_path: str):
        """Carrega a imagem selecionada e prepara a interface."""
        res = self.service.load_image(file_path)
        if not res:
            return
        if self.page and hasattr(self.page, "loop") and self.page.loop:
            self.page.loop.call_soon_threadsafe(self.apply_loaded_image, res)
        else:
            self.apply_loaded_image(res)

    def apply_loaded_image(self, res: dict):
        """Aplica os dados da imagem carregada na interface e atualiza a tela instantaneamente."""
        self.has_image_loaded = True
        self.has_selected_color = False
        self.has_selected_area = False
        self.area_colors = []

        self.display_w = res["display_width"]
        self.display_h = res["display_height"]

        # Configura imagem e camadas interativas
        if self.image_control:
            self.image_control.src = res["data_uri"]
            self.image_control.width = self.display_w
            self.image_control.height = self.display_h
            self.image_control.visible = True

        if self.gesture_layer:
            self.gesture_layer.content.width = self.display_w
            self.gesture_layer.content.height = self.display_h

        if self.upload_prompt:
            self.upload_prompt.visible = False

        if self.badge_container:
            self.badge_container.visible = True

        is_clique = self.mode == "clique"
        if self.badge_text:
            self.badge_text.value = "TOQUE EM UM PONTO" if is_clique else "SELECIONE UMA ÁREA"

        if self.instruction_text:
            self.instruction_text.value = (
                "Toque no ponto para identificar a cor"
                if is_clique
                else "Segure e arraste para selecionar uma área"
            )

        if self.bottom_hint_pill:
            self.bottom_hint_pill.visible = True

        if self.btn_select_other:
            self.btn_select_other.visible = True

        if self.target_ring:
            self.target_ring.visible = False

        if self.selection_box:
            self.selection_box.visible = False

        self._render_result_card()
        try:
            self.page.update()
        except Exception:
            pass

    def clear_image(self):
        """Limpa a imagem carregada e remove qualquer rastro da memória ao sair da tela."""
        self.service.clear()
        self.has_image_loaded = False
        self.has_selected_color = False
        self.has_selected_area = False
        self.area_colors = []

        if self.image_control:
            self.image_control.src = ""
            self.image_control.visible = False

        if self.upload_prompt:
            self.upload_prompt.visible = True

        if self.badge_container:
            self.badge_container.visible = False

        if self.bottom_hint_pill:
            self.bottom_hint_pill.visible = False

        if self.btn_select_other:
            self.btn_select_other.visible = False

        if self._reticle_timer:
            try:
                self._reticle_timer.cancel()
            except Exception:
                pass
            self._reticle_timer = None

        if self.target_ring:
            self.target_ring.visible = False

        if self.selection_box:
            self.selection_box.visible = False

        self._render_result_card()
        try:
            self.page.update()
        except Exception:
            pass

    def sample_point_at(self, local_x: float, local_y: float, is_final: bool = False):
        """Identifica a cor nas coordenadas especificadas com comportamento de mira idêntico ao da Tela e Câmera."""
        if not self.has_image_loaded:
            if is_final:
                self.pick_image()
            return

        self._last_drag_pos = (local_x, local_y)
        self.target_x = max(5.0, min(local_x, self.display_w - 5.0))
        self.target_y = max(5.0, min(local_y, self.display_h - 5.0))

        norm_x = max(0.0, min(self.target_x / float(self.display_w), 1.0))
        norm_y = max(0.0, min(self.target_y / float(self.display_h), 1.0))

        res = self.service.sample_point(norm_x, norm_y)
        if res:
            self.has_selected_color = True
            self.point_color_name = res["family"]
            self.point_color_detail = res["tone_detail"]
            self.point_color_hex = res["hex"]
            self._render_result_card()

        if is_final:
            self._show_reticle_at(self.target_x, self.target_y)
        else:
            self._hide_reticle()

        try:
            self.page.update()
        except Exception:
            pass

    def _show_reticle_at(self, x: float, y: float):
        """Posiciona a mira vazada no ponto final e agenda auto-fade após 2.5s."""
        if not self.target_ring:
            return

        self.target_ring.left = x - 16
        self.target_ring.top = y - 16
        self.target_ring.visible = True

        if self._reticle_timer:
            try:
                self._reticle_timer.cancel()
            except Exception:
                pass

        def auto_hide():
            try:
                if self.target_ring:
                    self.target_ring.visible = False
                    self.page.update()
            except Exception:
                pass

        self._reticle_timer = threading.Timer(2.5, auto_hide)
        self._reticle_timer.daemon = True
        self._reticle_timer.start()

    def _hide_reticle(self):
        """Oculta a mira imediatamente ao iniciar toque ou arrasto."""
        if self._reticle_timer:
            try:
                self._reticle_timer.cancel()
            except Exception:
                pass
            self._reticle_timer = None
        if self.target_ring and self.target_ring.visible:
            self.target_ring.visible = False

    def handle_tap_down(self, local_x: float, local_y: float):
        """Início do clique ou toque: faz a leitura contínua inicial e oculta a mira."""
        self._hide_reticle()
        self.sample_point_at(local_x, local_y, is_final=False)

    def handle_tap_up(self, local_x: float, local_y: float):
        """Finalização do toque único: leitura final e fixa a mira no ponto."""
        self.sample_point_at(local_x, local_y, is_final=True)

    def handle_drag_point(self, local_x: float, local_y: float):
        """Movimento contínuo de arrasto: atualiza a leitura em tempo real sem obstrução."""
        if not self.has_image_loaded:
            return
        now = time.time()
        if now - self._last_drag_time < 0.025 or self._is_drag_updating:
            return
        self._last_drag_time = now
        self._is_drag_updating = True
        try:
            self.sample_point_at(local_x, local_y, is_final=False)
        finally:
            self._is_drag_updating = False

    def handle_drag_end(self):
        """Finalização do arrasto: posiciona a mira exatamente onde soltou o mouse/dedo."""
        if not self.has_image_loaded:
            return
        if self._last_drag_pos:
            x, y = self._last_drag_pos
            self.sample_point_at(x, y, is_final=True)

    def handle_pan_start(self, x: float, y: float):
        """Início da seleção de área por arrasto."""
        if self.mode != "selecao" or not self.has_image_loaded:
            return
        self.drag_start = (x, y)
        self.drag_cur = (x, y)
        self._update_selection_box()

    def handle_pan_update(self, x: float, y: float):
        """Atualização do arrasto de seleção."""
        if self.mode != "selecao" or not self.has_image_loaded or not self.drag_start:
            return
        self.drag_cur = (x, y)
        self._update_selection_box()

    def handle_pan_end(self):
        """Fim da seleção: calcula cores na área e exibe em lista vertical."""
        if self.mode != "selecao" or not self.has_image_loaded or not self.drag_start or not self.drag_cur:
            return

        x0, y0 = self.drag_start
        x1, y1 = self.drag_cur

        norm_x0 = x0 / float(self.display_w)
        norm_x1 = x1 / float(self.display_w)
        norm_y0 = y0 / float(self.display_h)
        norm_y1 = y1 / float(self.display_h)

        colors = self.service.sample_area(norm_x0, norm_y0, norm_x1, norm_y1)
        if colors:
            self.has_selected_area = True
            self.area_colors = colors
            self._render_result_card()
            self.page.update()

    def _update_selection_box(self):
        """Atualiza a caixa visual de seleção."""
        if not self.selection_box or not self.drag_start or not self.drag_cur:
            return
        x0, y0 = self.drag_start
        x1, y1 = self.drag_cur

        left = min(x0, x1)
        top = min(y0, y1)
        width = max(10, abs(x1 - x0))
        height = max(10, abs(y1 - y0))

        self.selection_box.left = max(0, left)
        self.selection_box.top = max(0, top)
        self.selection_box.width = min(self.display_w - left, width)
        self.selection_box.height = min(self.display_h - top, height)
        self.selection_box.visible = True
        self.page.update()

    def switch_mode(self, new_mode: str):
        """Alterna entre os modos 'clique' e 'selecao'."""
        self.mode = new_mode
        is_clique = self.mode == "clique"

        if self.tab_clique and self.tab_selecao:
            self.tab_clique.bgcolor = COLOR_ICON_BG if is_clique else None
            self.tab_clique.content.color = COLOR_PRIMARY if is_clique else COLOR_TEXT_MUTED
            self.tab_clique.content.weight = ft.FontWeight.W_700 if is_clique else ft.FontWeight.W_500

            self.tab_selecao.bgcolor = None if is_clique else COLOR_ICON_BG
            self.tab_selecao.content.color = COLOR_TEXT_MUTED if is_clique else COLOR_PRIMARY
            self.tab_selecao.content.weight = ft.FontWeight.W_500 if is_clique else ft.FontWeight.W_700

        if self.badge_text:
            self.badge_text.value = "TOQUE EM UM PONTO" if is_clique else "SELECIONE UMA ÁREA"

        if self.target_ring:
            self.target_ring.visible = is_clique and self.has_selected_color
        if self.selection_box:
            self.selection_box.visible = (not is_clique) and self.has_selected_area

        if self.instruction_text:
            self.instruction_text.value = (
                "Toque no ponto para identificar a cor"
                if is_clique
                else "Segure e arraste para selecionar uma área"
            )

        self._render_result_card()
        self.page.update()

    def _render_result_card(self):
        """Renderiza o card inferior respeitando os estados de upload e seleção."""
        if not self.result_container:
            return

        if not self.has_image_loaded:
            # Estado sem imagem carregada
            self.result_container.content = ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=46,
                        height=46,
                        border_radius=12,
                        border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                        bgcolor=COLOR_BG,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(
                            ft.Icons.IMAGE_OUTLINED,
                            color=COLOR_TEXT_MUTED,
                            size=24,
                        ),
                    ),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(
                                "NENHUMA IMAGEM CARREGADA",
                                size=10,
                                weight=ft.FontWeight.W_700,
                                color=COLOR_TEXT_MUTED,
                                style=ft.TextStyle(letter_spacing=0.5),
                            ),
                            ft.Text(
                                "Carregue uma imagem",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Faça o upload de uma foto acima para identificar cores.",
                                size=12,
                                color=COLOR_TEXT_MUTED,
                            ),
                        ],
                    ),
                ],
            )
            return

        if self.mode == "clique":
            if not self.has_selected_color:
                # Imagem carregada, aguardando toque
                self.result_container.content = ft.Row(
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=12,
                            border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                            bgcolor=COLOR_BG,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                ft.Icons.TOUCH_APP_OUTLINED,
                                color=COLOR_TEXT_MUTED,
                                size=24,
                            ),
                        ),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(
                                    "NENHUMA COR SELECIONADA",
                                    size=10,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXT_MUTED,
                                    style=ft.TextStyle(letter_spacing=0.5),
                                ),
                                ft.Text(
                                    "Toque na foto",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Toque em qualquer ponto da foto para identificar a cor.",
                                    size=12,
                                    color=COLOR_TEXT_MUTED,
                                ),
                            ],
                        ),
                    ],
                )
            else:
                # Cor identificada no ponto
                self.result_container.content = ft.Row(
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=12,
                            bgcolor=self.point_color_hex,
                            border=ft.Border.all(1.0, "#00000018"),
                        ),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(
                                    "COR NO PONTO SELECIONADO",
                                    size=10,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXT_MUTED,
                                    style=ft.TextStyle(letter_spacing=0.5),
                                ),
                                ft.Text(
                                    self.point_color_name,
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    self.point_color_detail,
                                    size=12,
                                    color=COLOR_TEXT_MUTED,
                                ),
                            ],
                        ),
                    ],
                )
        else:
            # Modo Seleção: Cores uma embaixo da outra
            if not self.has_selected_area or not self.area_colors:
                self.result_container.content = ft.Row(
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=12,
                            border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                            bgcolor=COLOR_BG,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                ft.Icons.CROP_FREE,
                                color=COLOR_TEXT_MUTED,
                                size=24,
                            ),
                        ),
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(
                                    "NENHUMA ÁREA SELECIONADA",
                                    size=10,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXT_MUTED,
                                    style=ft.TextStyle(letter_spacing=0.5),
                                ),
                                ft.Text(
                                    "Selecione uma região",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Segure e arraste sobre a foto para listar as cores.",
                                    size=12,
                                    color=COLOR_TEXT_MUTED,
                                ),
                            ],
                        ),
                    ],
                )
            else:
                color_rows = []
                for item in self.area_colors:
                    color_rows.append(
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                            border_radius=12,
                            bgcolor=COLOR_BG,
                            border=ft.Border.all(1, COLOR_BORDER_SUBTLE),
                            content=ft.Row(
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        width=36,
                                        height=36,
                                        border_radius=9,
                                        bgcolor=item.get("hex", "#000000"),
                                        border=ft.Border.all(0.8, "#00000020"),
                                    ),
                                    ft.Column(
                                        spacing=1,
                                        expand=True,
                                        controls=[
                                            ft.Text(
                                                item.get("name", ""),
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                color=COLOR_TEXT_PRIMARY,
                                            ),
                                            ft.Text(
                                                f"{item.get('specific_name', item.get('name', ''))} · {item.get('hex', '').upper()}",
                                                size=11,
                                                color=COLOR_TEXT_MUTED,
                                            ),
                                        ],
                                    ),
                                    ft.Container(
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                        border_radius=8,
                                        bgcolor=COLOR_ICON_BG,
                                        content=ft.Text(
                                            f"{item.get('pct', 0):.0f}%",
                                            size=11.5,
                                            weight=ft.FontWeight.W_700,
                                            color=COLOR_PRIMARY,
                                        ),
                                    ),
                                ],
                            ),
                        )
                    )

                self.result_container.content = ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(
                            f"CORES NA ÁREA SELECIONADA ({len(self.area_colors)})",
                            size=10,
                            weight=ft.FontWeight.W_700,
                            color=COLOR_TEXT_MUTED,
                            style=ft.TextStyle(letter_spacing=0.5),
                        ),
                        ft.Column(
                            spacing=6,
                            controls=color_rows,
                        ),
                    ],
                )


def ImageView(page: ft.Page) -> ft.View:
    """Retorna a tela de Análise por Imagem."""
    ctrl = ImageUIController(page)

    def navigate_away(route: str):
        # Remove a imagem e limpa a memória ao sair da tela
        ctrl.clear_image()
        page.navigate(route)

    # 1. Topo: Botão Voltar + Breadcrumb
    header = ft.Row(
        spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda _: navigate_away("/"),
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
                "IRIS / Imagem",
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
                "Imagem",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=COLOR_TEXT_PRIMARY,
            ),
            ft.Text(
                "Toque em um ponto ou selecione uma área.",
                size=13.5,
                color=COLOR_TEXT_MUTED,
            ),
        ],
    )

    # 3. Seletor de Modo (Clique vs Seleção)
    ctrl.tab_clique = ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(vertical=9),
        border_radius=10,
        bgcolor=COLOR_ICON_BG,
        alignment=ft.Alignment.CENTER,
        content=ft.Text(
            "Clique",
            size=13,
            weight=ft.FontWeight.W_700,
            color=COLOR_PRIMARY,
        ),
        on_click=lambda _: ctrl.switch_mode("clique"),
    )

    ctrl.tab_selecao = ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(vertical=9),
        border_radius=10,
        alignment=ft.Alignment.CENTER,
        content=ft.Text(
            "Seleção",
            size=13,
            weight=ft.FontWeight.W_500,
            color=COLOR_TEXT_MUTED,
        ),
        on_click=lambda _: ctrl.switch_mode("selecao"),
    )

    mode_segmented_bar = ft.Container(
        bgcolor=COLOR_CARD_BG,
        border=ft.Border.all(1.0, COLOR_CARD_BORDER),
        border_radius=12,
        padding=ft.Padding.all(4),
        content=ft.Row(
            spacing=4,
            controls=[ctrl.tab_clique, ctrl.tab_selecao],
        ),
    )

    # 4. Viewport da Imagem
    ctrl.upload_prompt = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.CLICK,
        on_tap=lambda _: ctrl.pick_image(),
        content=ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.Container(
                        width=68,
                        height=68,
                        border_radius=34,
                        bgcolor="#FFFFFF",
                        alignment=ft.Alignment.CENTER,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=10,
                            color="#151D5CD4",
                            offset=ft.Offset(0, 4),
                        ),
                        content=ft.Icon(
                            ft.Icons.IMAGE_OUTLINED,
                            color=COLOR_PRIMARY,
                            size=34,
                        ),
                    ),
                    ft.Text(
                        "Faça o upload\nde uma imagem",
                        size=21,
                        weight=ft.FontWeight.W_800,
                        color=COLOR_PRIMARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        ),
    )

    ctrl.image_control = ft.Image(
        src="",
        fit=ft.BoxFit.CONTAIN,
        gapless_playback=True,
        visible=False,
    )

    # Badge Superior Esquerdo ((•)) TOQUE EM UM PONTO
    ctrl.badge_text = ft.Text(
        "TOQUE EM UM PONTO",
        size=10,
        weight=ft.FontWeight.W_700,
        color="#FFFFFF",
        style=ft.TextStyle(letter_spacing=0.6),
    )
    ctrl.badge_container = ft.Container(
        left=14,
        top=14,
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border_radius=14,
        bgcolor="#00000088",
        visible=False,
        content=ft.Row(
            spacing=6,
            tight=True,
            controls=[
                ft.Icon(ft.Icons.SENSORS_ROUNDED, color="#FFFFFF", size=13),
                ctrl.badge_text,
            ],
        ),
    )

    # Mira de seleção no ponto (vazada, sem ponto central obstrutivo, com sombra sutil)
    ctrl.target_ring = ft.Container(
        width=32,
        height=32,
        border_radius=16,
        border=ft.Border.all(2.0, "#FFFFFF"),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=4,
            color="#00000066",
            offset=ft.Offset(0, 1),
        ),
        visible=False,
    )

    # Caixa de seleção de área
    ctrl.selection_box = ft.Container(
        border_radius=8,
        border=ft.Border.all(2.0, "#FFFFFF"),
        bgcolor="#205BCC22",
        visible=False,
    )

    # Pílula de instrução inferior
    ctrl.instruction_text = ft.Text(
        "Toque no ponto para identificar a cor",
        size=11.5,
        color="#FFFFFF",
        weight=ft.FontWeight.W_400,
    )
    ctrl.bottom_hint_pill = ft.Container(
        bottom=12,
        alignment=ft.Alignment.CENTER,
        visible=False,
        content=ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            border_radius=14,
            bgcolor="#00000088",
            content=ctrl.instruction_text,
        ),
    )

    # Handlers de Gestos
    def on_tap_down(e: ft.TapEvent):
        if not ctrl.has_image_loaded:
            ctrl.pick_image()
            return
        if ctrl.mode == "clique" and e.local_position:
            ctrl.handle_tap_down(e.local_position.x, e.local_position.y)

    def on_tap_up(e: ft.TapEvent):
        if not ctrl.has_image_loaded:
            return
        if ctrl.mode == "clique" and e.local_position:
            ctrl.handle_tap_up(e.local_position.x, e.local_position.y)

    def on_pan_start(e: ft.DragStartEvent):
        if not ctrl.has_image_loaded:
            return
        if e.local_position:
            if ctrl.mode == "clique":
                ctrl.handle_tap_down(e.local_position.x, e.local_position.y)
            elif ctrl.mode == "selecao":
                ctrl.handle_pan_start(e.local_position.x, e.local_position.y)

    def on_pan_update(e: ft.DragUpdateEvent):
        if not ctrl.has_image_loaded:
            return
        if e.local_position:
            if ctrl.mode == "clique":
                ctrl.handle_drag_point(e.local_position.x, e.local_position.y)
            elif ctrl.mode == "selecao":
                ctrl.handle_pan_update(e.local_position.x, e.local_position.y)

    def on_pan_end(e: ft.DragEndEvent):
        if not ctrl.has_image_loaded:
            return
        if ctrl.mode == "clique":
            ctrl.handle_drag_end()
        elif ctrl.mode == "selecao":
            ctrl.handle_pan_end()

    ctrl.gesture_layer = ft.GestureDetector(
        on_tap_down=on_tap_down,
        on_tap_up=on_tap_up,
        on_pan_start=on_pan_start,
        on_pan_update=on_pan_update,
        on_pan_end=on_pan_end,
        content=ft.Container(
            width=360,
            height=380,
            bgcolor=None,
        ),
    )

    image_viewport = ft.Container(
        height=380,
        border_radius=28,
        bgcolor="#EEF4FE",
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        alignment=ft.Alignment.CENTER,
        content=ft.Stack(
            controls=[
                ctrl.upload_prompt,
                ctrl.image_control,
                ctrl.gesture_layer,
                ctrl.badge_container,
                ctrl.target_ring,
                ctrl.selection_box,
                ctrl.bottom_hint_pill,
            ]
        ),
    )

    # 5. Card de Resultado de Cor
    ctrl.result_container = ft.Container(
        bgcolor=COLOR_CARD_BG,
        border=ft.Border.all(1.2, COLOR_CARD_BORDER),
        border_radius=18,
        padding=ft.Padding.all(14),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=6,
            color="#06000000",
            offset=ft.Offset(0, 2),
        ),
    )
    ctrl._render_result_card()

    disclaimer = ft.Text(
        "Filtros e iluminação da foto podem alterar a cor.",
        size=11,
        color=COLOR_TEXT_MUTED,
    )

    # 6. Botão "Selecionar outra imagem"
    ctrl.btn_select_other = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.CLICK,
        on_tap=lambda _: ctrl.pick_image(),
        visible=False,
        content=ft.Container(
            border=ft.Border.all(1.2, COLOR_BORDER_SUBTLE),
            bgcolor=COLOR_CARD_BG,
            border_radius=14,
            padding=ft.Padding.symmetric(vertical=13, horizontal=16),
            alignment=ft.Alignment.CENTER,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(
                        ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
                        color=COLOR_PRIMARY,
                        size=20,
                    ),
                    ft.Text(
                        "Selecionar outra imagem",
                        size=14,
                        weight=ft.FontWeight.W_700,
                        color=COLOR_PRIMARY,
                    ),
                ],
            ),
        ),
    )

    # 7. Barra de Navegação Inferior
    bottom_nav = build_bottom_nav(page, active_tab="image")

    body_content = ft.Container(
        width=400,
        padding=ft.Padding.only(left=20, right=20, top=14, bottom=10),
        content=ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                header,
                title_section,
                mode_segmented_bar,
                image_viewport,
                ctrl.result_container,
                disclaimer,
                ctrl.btn_select_other,
            ],
        ),
    )

    return ft.View(
        route="/image",
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
