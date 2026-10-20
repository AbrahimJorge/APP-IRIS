import os
import time
import threading
import flet as ft
from theme import *
from components.bottom_nav import build_bottom_nav
from services.image_service import ImageService
from services.i18n_service import I18nService

try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except (ImportError, Exception):
    tk = None
    filedialog = None
    HAS_TKINTER = False

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


class ScreenPickerUIController:
    """
    Controlador da tela de Captura de Tela (Print do Celular / Screenshot),
    permitindo carregar prints de qualquer app do celular e inspecionar cores com a mira de precisão.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.mode = "clique"
        self.service = ImageService()

        self.has_image_loaded = False
        self.has_selected_color = False
        self.has_selected_area = False

        self.display_w = 360
        self.display_h = 380

        self.target_x = 0.0
        self.target_y = 0.0
        self.drag_start = None
        self.drag_cur = None

        self._last_drag_time = 0.0
        self._last_drag_pos = None
        self._is_drag_updating = False
        self._reticle_timer = None

        self.point_color_name = ""
        self.point_color_detail = ""
        self.point_color_hex = ""
        self.area_colors = []

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

        # Inicializa o FilePicker para ambiente mobile (Android/iOS)
        self.file_picker = ft.FilePicker()
        if hasattr(page, "services") and self.file_picker not in page.services:
            page.services.append(self.file_picker)

    def pick_screenshot(self):
        """Abre o seletor nativo para escolher a captura de tela (print)."""
        if HAS_TKINTER:
            def _open_desktop():
                try:
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes("-topmost", True)
                    path = filedialog.askopenfilename(
                        title="Selecione a Captura de Tela",
                        filetypes=[("Imagens e Prints", "*.png *.jpg *.jpeg *.bmp *.webp *.heic")],
                    )
                    root.destroy()
                    if path:
                        res = self.service.load_image(file_path=path)
                        if res:
                            if self.page and hasattr(self.page, "loop") and self.page.loop:
                                self.page.loop.call_soon_threadsafe(self.apply_loaded_image, res)
                            else:
                                self.apply_loaded_image(res)
                except Exception as e:
                    print(f"Erro ao selecionar print desktop: {e}")

            threading.Thread(target=_open_desktop, daemon=True).start()
            return

        async def _open_mobile():
            try:
                files = await self.file_picker.pick_files(
                    dialog_title="Selecione o Print da Tela",
                    file_type=ft.FilePickerFileType.IMAGE,
                    allow_multiple=False,
                    with_data=True,
                )
                if files and len(files) > 0:
                    selected_file = files[0]
                    file_path = getattr(selected_file, "path", None)
                    file_bytes = getattr(selected_file, "bytes", None)
                    res = self.service.load_image(file_path=file_path, image_bytes=file_bytes)
                    if res:
                        self.apply_loaded_image(res)
            except Exception as e:
                print(f"Erro ao selecionar print via FilePicker no celular: {e}")

        if hasattr(self.page, "run_task"):
            self.page.run_task(_open_mobile)
        elif self.page and hasattr(self.page, "loop") and self.page.loop:
            import asyncio
            asyncio.run_coroutine_threadsafe(_open_mobile(), self.page.loop)

    def apply_loaded_image(self, res: dict):
        """Exibe a captura de tela na interface e prepara a mira."""
        self.has_image_loaded = True
        self.has_selected_color = False
        self.has_selected_area = False
        self.area_colors = []

        self.display_w = res["display_width"]
        self.display_h = res["display_height"]

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
                "Toque no ponto do print para identificar a cor"
                if is_clique
                else "Segure e arraste para selecionar uma área"
            )

        if self.bottom_hint_pill:
            self.bottom_hint_pill.visible = True

        if self.btn_select_other:
            self.btn_select_other.visible = True

        self._render_result_card()
        try:
            self.page.update()
        except Exception:
            pass

    def switch_mode(self, new_mode: str):
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
                "Toque no ponto do print para identificar a cor"
                if is_clique
                else "Segure e arraste para selecionar uma área"
            )

        self._render_result_card()
        try:
            self.page.update()
        except Exception:
            pass

    def sample_point_at(self, local_x: float, local_y: float, is_final: bool = False):
        if not self.has_image_loaded:
            return

        self._last_drag_pos = (local_x, local_y)
        self.target_x = max(0.0, min(local_x, float(self.display_w)))
        self.target_y = max(0.0, min(local_y, float(self.display_h)))

        norm_x = self.target_x / float(self.display_w)
        norm_y = self.target_y / float(self.display_h)
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

        self._reticle_timer = threading.Timer(3.0, auto_hide)
        self._reticle_timer.daemon = True
        self._reticle_timer.start()

    def _hide_reticle(self):
        if self._reticle_timer:
            try:
                self._reticle_timer.cancel()
            except Exception:
                pass
            self._reticle_timer = None
        if self.target_ring and self.target_ring.visible:
            self.target_ring.visible = False

    def handle_tap_down(self, local_x: float, local_y: float):
        self._hide_reticle()
        self.sample_point_at(local_x, local_y, is_final=False)

    def handle_tap_up(self, local_x: float, local_y: float):
        self.sample_point_at(local_x, local_y, is_final=True)

    def handle_drag_point(self, local_x: float, local_y: float):
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
        if self._last_drag_pos:
            x, y = self._last_drag_pos
            self.sample_point_at(x, y, is_final=True)

    def handle_pan_start(self, x: float, y: float):
        if self.mode != "selecao" or not self.has_image_loaded:
            return
        self.drag_start = (x, y)
        self.drag_cur = (x, y)
        self._update_selection_box()

    def handle_pan_update(self, x: float, y: float):
        if self.mode != "selecao" or not self.drag_start:
            return
        self.drag_cur = (x, y)
        self._update_selection_box()

    def handle_pan_end(self):
        if self.mode != "selecao" or not self.drag_start or not self.drag_cur:
            return

        x0, y0 = self.drag_start
        x1, y1 = self.drag_cur

        norm_x0, norm_x1 = x0 / float(self.display_w), x1 / float(self.display_w)
        norm_y0, norm_y1 = y0 / float(self.display_h), y1 / float(self.display_h)

        colors = self.service.sample_area(norm_x0, norm_y0, norm_x1, norm_y1)
        if colors:
            self.has_selected_area = True
            self.area_colors = colors
            self._render_result_card()
            try:
                self.page.update()
            except Exception:
                pass

    def _update_selection_box(self):
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
        try:
            self.page.update()
        except Exception:
            pass

    def _render_result_card(self):
        if not self.result_container:
            return

        if not self.has_image_loaded:
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
                            ft.Icons.MOBILE_SCREEN_SHARE_ROUNDED,
                            color=COLOR_TEXT_MUTED,
                            size=24,
                        ),
                    ),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(
                                "CAPTURA DA TELA",
                                size=10,
                                weight=ft.FontWeight.W_700,
                                color=COLOR_TEXT_MUTED,
                                style=ft.TextStyle(letter_spacing=0.5),
                            ),
                            ft.Text(
                                "Nenhum print carregado",
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Carregue um print da tela para ver as cores.",
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
                                    "AGUARDANDO TOQUE",
                                    size=10,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXT_MUTED,
                                    style=ft.TextStyle(letter_spacing=0.5),
                                ),
                                ft.Text(
                                    "Toque em qualquer ponto",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Toque em um ponto do print para ver a cor exata.",
                                    size=12,
                                    color=COLOR_TEXT_MUTED,
                                ),
                            ],
                        ),
                    ],
                )
            else:
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
                                    "COR IDENTIFICADA NA TELA",
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
                                    "AGUARDANDO SELEÇÃO",
                                    size=10,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXT_MUTED,
                                    style=ft.TextStyle(letter_spacing=0.5),
                                ),
                                ft.Text(
                                    "Arraste para selecionar uma área",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Selecione uma região do print para ver as cores.",
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


def ScreenPickerView(page: ft.Page) -> ft.View:
    """Tela de Captura de Tela (Print do Celular e Desktop)."""
    ctrl = ScreenPickerUIController(page)
    floating_service = ScreenFloatingService.get_instance()
    has_desktop_floating = getattr(floating_service, "is_available", False)

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
                "IRIS / Captura de Tela",
                size=14,
                weight=ft.FontWeight.W_600,
                color=COLOR_TEXT_MUTED,
            ),
        ],
    )

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
                "Identifique cores em prints e telas do seu celular com a mira.",
                size=13.5,
                color=COLOR_TEXT_MUTED,
            ),
        ],
    )

    ctrl.tab_clique = ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(vertical=9),
        border_radius=10,
        bgcolor=COLOR_ICON_BG,
        alignment=ft.Alignment.CENTER,
        content=ft.Text(
            "Toque no Ponto",
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
            "Selecionar Área",
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

    ctrl.image_control = ft.Image(
        src="",
        width=360,
        height=380,
        fit=ft.BoxFit.CONTAIN,
        visible=False,
    )

    ctrl.upload_prompt = ft.Container(
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Container(
                    width=68,
                    height=68,
                    border_radius=34,
                    bgcolor=COLOR_ICON_BG,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.MOBILE_SCREEN_SHARE_ROUNDED,
                        color=COLOR_PRIMARY,
                        size=34,
                    ),
                ),
                ft.Text(
                    "Selecione uma Captura da Tela",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=COLOR_TEXT_PRIMARY,
                ),
                ft.Text(
                    "Tire um print de qualquer app do seu celular e abra aqui.",
                    size=12,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_tap=lambda _: ctrl.pick_screenshot(),
                    content=ft.Container(
                        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                        border_radius=12,
                        bgcolor=COLOR_PRIMARY,
                        content=ft.Row(
                            tight=True,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, color="#FFFFFF", size=20),
                                ft.Text("Carregar Print da Tela", color="#FFFFFF", size=14, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                    ),
                ),
            ],
        ),
    )

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
                ft.Icon(ft.Icons.FILTER_CENTER_FOCUS_ROUNDED, color="#FFFFFF", size=13),
                ctrl.badge_text,
            ],
        ),
    )

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

    ctrl.selection_box = ft.Container(
        border_radius=8,
        border=ft.Border.all(2.0, "#FFFFFF"),
        bgcolor="#205BCC22",
        visible=False,
    )

    ctrl.instruction_text = ft.Text(
        "Toque no ponto do print para identificar a cor",
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

    def _get_coords(e):
        pos = getattr(e, "local_position", None)
        if pos is not None and hasattr(pos, "x") and hasattr(pos, "y"):
            return float(pos.x), float(pos.y)
        if hasattr(e, "local_x") and e.local_x is not None:
            return float(e.local_x), float(e.local_y)
        return None

    def on_tap_down(e: ft.TapEvent):
        coords = _get_coords(e)
        if ctrl.mode == "clique" and coords:
            ctrl.handle_tap_down(coords[0], coords[1])

    def on_tap_up(e: ft.TapEvent):
        coords = _get_coords(e)
        if ctrl.mode == "clique" and coords:
            ctrl.handle_tap_up(coords[0], coords[1])

    def on_pan_start(e: ft.DragStartEvent):
        coords = _get_coords(e)
        if coords:
            if ctrl.mode == "clique":
                ctrl.handle_tap_down(coords[0], coords[1])
            elif ctrl.mode == "selecao":
                ctrl.handle_pan_start(coords[0], coords[1])

    def on_pan_update(e: ft.DragUpdateEvent):
        coords = _get_coords(e)
        if coords:
            if ctrl.mode == "clique":
                ctrl.handle_drag_point(coords[0], coords[1])
            elif ctrl.mode == "selecao":
                ctrl.handle_pan_update(coords[0], coords[1])

    def on_pan_end(e: ft.DragEndEvent):
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

    screen_viewport = ft.Container(
        height=380,
        border_radius=24,
        bgcolor="#0F172A",
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
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

    ctrl.btn_select_other = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.CLICK,
        on_tap=lambda _: ctrl.pick_screenshot(),
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
                    ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED, color=COLOR_PRIMARY, size=20),
                    ft.Text("Selecionar Outro Print", size=14, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                ],
            ),
        ),
    )

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
                "COMO IDENTIFICAR CORES DE QUALQUER APP",
                size=11,
                weight=ft.FontWeight.W_700,
                color=COLOR_TEXT_MUTED,
                style=ft.TextStyle(letter_spacing=0.6),
            ),
            build_step_item(
                "1.",
                "Tire o Print da Tela",
                "Pressione os botões Liga/Desliga + Diminuir Volume no seu celular enquanto estiver no app ou jogo desejado.",
                ft.Icons.SCREENSHOT_OUTLINED,
            ),
            build_step_item(
                "2.",
                "Abra o Print no IRIS",
                "Toque no botão 'Carregar Print da Tela' acima e escolha a captura da sua galeria.",
                ft.Icons.IMAGE_SEARCH_OUTLINED,
            ),
            build_step_item(
                "3.",
                "Inspecione com a Mira",
                "Toque ou arraste o dedo em qualquer detalhe para obter a família, tom e código hexadecimal da cor.",
                ft.Icons.FILTER_CENTER_FOCUS_ROUNDED,
            ),
        ],
    )

    # Se estiver no Windows/Desktop e com suporte a Tkinter, adiciona o card de Menu Flutuante como opcional
    desktop_floating_section = None
    if has_desktop_floating:
        status_indicator = ft.Container(
            width=10,
            height=10,
            border_radius=5,
            bgcolor="#10B981" if floating_service.is_running else "#94A3B8",
        )
        status_label = ft.Text(
            "MENU FLUTUANTE ATIVO NA ÁREA DE TRABALHO" if floating_service.is_running else "MENU FLUTUANTE DESATIVADO",
            size=10.5,
            weight=ft.FontWeight.W_700,
            color="#059669" if floating_service.is_running else COLOR_TEXT_MUTED,
            style=ft.TextStyle(letter_spacing=0.5),
        )
        btn_desktop_label = ft.Text(
            "Desativar Menu Flutuante" if floating_service.is_running else "Ativar Menu Flutuante (Desktop)",
            size=13,
            weight=ft.FontWeight.BOLD,
            color="#DC2626" if floating_service.is_running else COLOR_PRIMARY,
        )
        btn_desktop_icon = ft.Icon(
            ft.Icons.STOP_CIRCLE_OUTLINED if floating_service.is_running else ft.Icons.LAYERS_ROUNDED,
            color="#DC2626" if floating_service.is_running else COLOR_PRIMARY,
            size=18,
        )
        btn_desktop_container = ft.Container(
            padding=ft.Padding.symmetric(vertical=10, horizontal=16),
            border_radius=12,
            bgcolor="#FEE2E2" if floating_service.is_running else COLOR_ICON_BG,
            border=ft.Border.all(1.0, "#FCA5A5" if floating_service.is_running else COLOR_CARD_BORDER),
            content=ft.Row(
                tight=True,
                spacing=8,
                controls=[btn_desktop_icon, btn_desktop_label],
            ),
        )

        def refresh_desktop_ui(active: bool):
            status_indicator.bgcolor = "#10B981" if active else "#94A3B8"
            status_label.value = "MENU FLUTUANTE ATIVO NA ÁREA DE TRABALHO" if active else "MENU FLUTUANTE DESATIVADO"
            status_label.color = "#059669" if active else COLOR_TEXT_MUTED
            btn_desktop_label.value = "Desativar Menu Flutuante" if active else "Ativar Menu Flutuante (Desktop)"
            btn_desktop_label.color = "#DC2626" if active else COLOR_PRIMARY
            btn_desktop_icon.name = ft.Icons.STOP_CIRCLE_OUTLINED if active else ft.Icons.LAYERS_ROUNDED
            btn_desktop_icon.color = "#DC2626" if active else COLOR_PRIMARY
            btn_desktop_container.bgcolor = "#FEE2E2" if active else COLOR_ICON_BG
            btn_desktop_container.border = ft.Border.all(1.0, "#FCA5A5" if active else COLOR_CARD_BORDER)
            try:
                page.update()
            except Exception:
                pass

        def on_floating_changed(active: bool):
            if page and hasattr(page, "loop") and page.loop:
                page.loop.call_soon_threadsafe(refresh_desktop_ui, active)
            else:
                refresh_desktop_ui(active)

        def toggle_desktop(_):
            if floating_service.is_running:
                floating_service.stop()
                refresh_desktop_ui(False)
            else:
                floating_service.start(on_status_change=on_floating_changed)
                refresh_desktop_ui(True)

        btn_desktop_toggle = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=toggle_desktop,
            content=btn_desktop_container,
        )

        desktop_floating_section = ft.Container(
            padding=ft.Padding.all(16),
            border_radius=18,
            bgcolor=COLOR_CARD_BG,
            border=ft.Border.all(1.0, COLOR_CARD_BORDER),
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text(
                        "RECURSO PARA COMPUTADOR (DESKTOP)",
                        size=11,
                        weight=ft.FontWeight.W_700,
                        color=COLOR_TEXT_MUTED,
                        style=ft.TextStyle(letter_spacing=0.6),
                    ),
                    ft.Row(
                        tight=True,
                        spacing=8,
                        controls=[status_indicator, status_label],
                    ),
                    ft.Text(
                        "O menu suspenso flutua sobre as janelas do Windows para identificar cores diretamente do cursor.",
                        size=12,
                        color=COLOR_TEXT_MUTED,
                    ),
                    btn_desktop_toggle,
                ],
            ),
        )

    bottom_nav = build_bottom_nav(page, active_tab="screen")

    body_controls = [
        header,
        title_section,
        mode_segmented_bar,
        screen_viewport,
        ctrl.btn_select_other,
        ctrl.result_container,
        guide_section,
    ]
    if desktop_floating_section:
        body_controls.append(desktop_floating_section)

    body_content = ft.Container(
        width=min(420, getattr(page, "width", 400) or 400),
        padding=ft.Padding.only(left=20, right=20, top=14, bottom=12),
        content=ft.Column(
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=body_controls,
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
