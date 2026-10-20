import asyncio
import ctypes
import io
import threading
import time
import numpy as np
import flet as ft

try:
    from PIL import Image
except (ImportError, Exception):
    Image = None

try:
    import tkinter as tk
    from PIL import ImageTk, ImageGrab
    from pynput import mouse
    import mss
    DESKTOP_SCREEN_AVAILABLE = True
except (ImportError, Exception):
    tk = None
    ImageTk = None
    ImageGrab = None
    mouse = None
    mss = None
    DESKTOP_SCREEN_AVAILABLE = False

from services.color_dataset import ColorDatasetService
from services.i18n_service import I18nService
from services.constants.screen_constants import *


if hasattr(ctypes, "windll"):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _make_window_click_through(win):
    """Torna a janela 100% transparente a eventos de mouse (Windows Desktop)."""
    if not hasattr(ctypes, "windll") or not win:
        return
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        if not hwnd:
            hwnd = win.winfo_id()
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_LAYERED)
    except Exception:
        pass


class MobileFloatingOverlay:
    """
    Menu Flutuante sobreposto em Flet (page.overlay).
    Permite arrastar o olho do IRIS na tela do celular, expandir opções
    e identificar cores de pontos e áreas com retorno em tempo real,
    reproduzindo exatamente o protótipo visual do projeto IRIS.
    """
    def __init__(self, page: ft.Page, service):
        self.page = page
        self.service = service
        self.dataset = service.dataset
        self.i18n = service.i18n

        pw = float(getattr(page, "width", 380) or 380)
        self.btn_size = 52
        self.dock_side = "right"
        self.btn_y = 220.0
        self.btn_x = pw - self.btn_size - 6.0
        self.is_menu_open = False
        self.mode = None
        self.cached_image = None
        self.sel_start = None
        self.sel_cur = None
        self.is_mounted = False

        self._build_controls()

    def _build_controls(self):
        # 1. Mira de precisão (Círculo com ponto central, exatamente como no protótipo)
        self.reticle_ring = ft.Container(
            width=28,
            height=28,
            border_radius=14,
            border=ft.Border.all(2.0, "#FFFFFF"),
            shadow=ft.BoxShadow(
                blur_radius=5,
                spread_radius=1,
                color="#00000066",
            ),
            alignment=ft.Alignment.CENTER,
            content=ft.Container(
                width=4,
                height=4,
                border_radius=2,
                bgcolor="#FFFFFF",
            ),
            visible=False,
        )

        # 2. Retângulo de seleção de área
        self.selection_box = ft.Container(
            border_radius=8,
            border=ft.Border.all(2, "#38BDF8"),
            bgcolor="#38BDF822",
            visible=False,
        )

        # 3. Camada de inspeção em tela cheia (quase transparente para capturar toques)
        self.inspection_layer = ft.Container(
            left=0,
            top=0,
            right=0,
            bottom=0,
            visible=False,
            content=ft.Stack(
                controls=[
                    ft.GestureDetector(
                        left=0,
                        top=0,
                        right=0,
                        bottom=0,
                        on_tap_up=self._on_inspection_tap,
                        on_pan_start=self._on_inspection_pan_start,
                        on_pan_update=self._on_inspection_pan_update,
                        on_pan_end=self._on_inspection_pan_end,
                        content=ft.Container(
                            bgcolor="#00000005",
                        ),
                    ),
                    self.selection_box,
                    self.reticle_ring,
                ]
            ),
        )

        # 4. Botão Flutuante (Olho do IRIS com docking na borda da tela)
        self.floating_btn = ft.Container(
            left=self.btn_x,
            top=self.btn_y,
            width=self.btn_size,
            height=self.btn_size,
            border_radius=self.btn_size // 2,
            bgcolor="#0B132B",
            border=ft.Border.all(1.5, "#38BDF8"),
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=1,
                color="#55000000",
                offset=ft.Offset(0, 3),
            ),
            alignment=ft.Alignment.CENTER,
            content=ft.GestureDetector(
                on_pan_update=self._on_btn_pan_update,
                on_pan_end=self._on_btn_pan_end,
                on_tap=lambda _: self.toggle_options(),
                content=ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Image(
                        src="floating_eye.png",
                        width=36,
                        height=36,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                ),
            ),
        )

        # 5. Menu Popup de Opções (Fiel ao protótipo)
        self.opt_clique = ft.Container(
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            ink=True,
            on_click=lambda _: self.set_mode("clique"),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=34,
                        height=34,
                        border_radius=10,
                        bgcolor="#F1F5F9",
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(
                            ft.Icons.FILTER_CENTER_FOCUS_ROUNDED,
                            color="#1D5CD4",
                            size=18,
                        ),
                    ),
                    ft.Column(
                        spacing=2,
                        tight=True,
                        controls=[
                            ft.Text("Clique", size=13.5, weight=ft.FontWeight.W_700, color="#1E293B"),
                            ft.Text("Usa o ponto exato da tela.", size=10.5, color="#64748B"),
                        ],
                    ),
                ],
            ),
        )

        self.opt_selecao = ft.Container(
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            ink=True,
            on_click=lambda _: self.set_mode("selecao"),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=34,
                        height=34,
                        border_radius=10,
                        bgcolor="#F1F5F9",
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(
                            ft.Icons.CROP_FREE_ROUNDED,
                            color="#1D5CD4",
                            size=18,
                        ),
                    ),
                    ft.Column(
                        spacing=2,
                        tight=True,
                        controls=[
                            ft.Text("Seleção", size=13.5, weight=ft.FontWeight.W_700, color="#1E293B"),
                            ft.Text("Marca uma área da tela.", size=10.5, color="#64748B"),
                        ],
                    ),
                ],
            ),
        )

        self.options_card = ft.Container(
            visible=False,
            width=215,
            bgcolor="#FFFFFF",
            border=ft.Border.all(1.0, "#E2E8F0"),
            border_radius=16,
            padding=ft.Padding.all(6),
            shadow=ft.BoxShadow(
                blur_radius=16,
                spread_radius=1,
                color="#20000000",
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=4,
                tight=True,
                controls=[
                    self.opt_clique,
                    ft.Divider(height=1, color="#F1F5F9"),
                    self.opt_selecao,
                ],
            ),
        )

        # 6. Card Flutuante de Resultado (Pill idêntico ao protótipo)
        self.pill_swatch = ft.Container(
            width=32,
            height=32,
            border_radius=8,
            bgcolor="#CBD5E1",
            border=ft.Border.all(1.0, "#CBD5E1"),
        )
        self.pill_title = ft.Text("Toque na tela", size=13.5, weight=ft.FontWeight.W_700, color="#1E293B")
        self.pill_detail = ft.Text("Identificar cor do ponto", size=10.5, color="#64748B")
        self.pill_area_content = ft.Column(spacing=4, visible=False)

        self.pill_card = ft.Container(
            visible=False,
            bgcolor="#FFFFFF",
            border=ft.Border.all(1.0, "#E2E8F0"),
            border_radius=14,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            shadow=ft.BoxShadow(
                blur_radius=12,
                spread_radius=0,
                color="#1E000000",
                offset=ft.Offset(0, 3),
            ),
            content=ft.Column(
                tight=True,
                spacing=6,
                controls=[
                    ft.Row(
                        spacing=10,
                        tight=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.pill_swatch,
                            ft.Column(
                                spacing=1,
                                tight=True,
                                controls=[
                                    self.pill_title,
                                    self.pill_detail,
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_size=16,
                                padding=ft.Padding.all(2),
                                on_click=lambda _: self.deactivate_mode(),
                            ),
                        ],
                    ),
                    self.pill_area_content,
                ],
            ),
        )

    def _on_btn_pan_update(self, e: ft.DragUpdateEvent):
        self.btn_x += getattr(e, "delta_x", 0) or 0
        self.btn_y += getattr(e, "delta_y", 0) or 0
        pw = float(getattr(self.page, "width", 380) or 380)
        ph = float(getattr(self.page, "height", 800) or 800)
        self.btn_x = max(6.0, min(pw - self.btn_size - 6.0, self.btn_x))
        self.btn_y = max(30.0, min(ph - self.btn_size - 40.0, self.btn_y))
        self.floating_btn.left = self.btn_x
        self.floating_btn.top = self.btn_y
        self._reposition_options()
        self._reposition_pill()
        try:
            self.page.update()
        except Exception:
            pass

    def _on_btn_pan_end(self, e: ft.DragEndEvent):
        pw = float(getattr(self.page, "width", 380) or 380)
        if self.btn_x > pw / 2:
            self.btn_x = pw - self.btn_size - 6.0
            self.dock_side = "right"
        else:
            self.btn_x = 6.0
            self.dock_side = "left"
        self.floating_btn.left = self.btn_x
        self._reposition_options()
        self._reposition_pill()
        try:
            self.page.update()
        except Exception:
            pass

    def _reposition_options(self):
        pw = float(getattr(self.page, "width", 380) or 380)
        ph = float(getattr(self.page, "height", 800) or 800)
        if self.dock_side == "right":
            self.options_card.left = max(10.0, self.btn_x - 225.0)
        else:
            self.options_card.left = min(pw - 225.0, self.btn_x + self.btn_size + 10.0)
        self.options_card.top = max(40.0, min(ph - 160.0, self.btn_y - 10.0))

    def _reposition_pill(self):
        pw = float(getattr(self.page, "width", 380) or 380)
        ph = float(getattr(self.page, "height", 800) or 800)
        if self.dock_side == "right":
            self.pill_card.left = max(10.0, self.btn_x - 220.0)
        else:
            self.pill_card.left = min(pw - 220.0, self.btn_x + self.btn_size + 10.0)
        self.pill_card.top = max(40.0, min(ph - 120.0, self.btn_y - 4.0))

    def toggle_options(self, force: bool | None = None):
        if force is not None:
            self.is_menu_open = force
        else:
            self.is_menu_open = not self.is_menu_open

        self._reposition_options()
        self.options_card.visible = self.is_menu_open
        try:
            self.page.update()
        except Exception:
            pass

    def set_mode(self, new_mode: str):
        if self.mode == new_mode:
            self.deactivate_mode()
            return

        self.mode = new_mode
        self.is_menu_open = False
        self.options_card.visible = False
        self.reticle_ring.visible = False
        self.selection_box.visible = False
        self._reposition_pill()
        self.pill_card.visible = True

        if new_mode == "clique":
            self.pill_swatch.visible = True
            self.pill_area_content.visible = False
            self.pill_title.value = "Toque na tela"
            self.pill_detail.value = "Identificar cor do ponto"
            self.opt_clique.bgcolor = "#EEF4FE"
            self.opt_selecao.bgcolor = None
        else:
            self.pill_swatch.visible = False
            self.pill_area_content.visible = False
            self.pill_title.value = "Arraste na tela"
            self.pill_detail.value = "Selecionar área"
            self.opt_clique.bgcolor = None
            self.opt_selecao.bgcolor = "#EEF4FE"

        self.inspection_layer.visible = True
        try:
            self.page.update()
        except Exception:
            pass

        async def _snapshot():
            try:
                self.inspection_layer.visible = False
                self.pill_card.visible = False
                self.options_card.visible = False
                try:
                    self.page.update()
                except Exception:
                    pass
                await asyncio.sleep(0.04)
                png_bytes = await self.page.take_screenshot()
                if png_bytes and Image:
                    self.cached_image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            except Exception as e:
                print(f"Aviso screenshot Flet overlay: {e}")
            finally:
                self.inspection_layer.visible = True
                self.pill_card.visible = True
                try:
                    self.page.update()
                except Exception:
                    pass

        if hasattr(self.page, "run_task"):
            self.page.run_task(_snapshot)
        elif self.page and hasattr(self.page, "loop") and self.page.loop:
            asyncio.run_coroutine_threadsafe(_snapshot(), self.page.loop)

    def deactivate_mode(self):
        self.mode = None
        self.inspection_layer.visible = False
        self.pill_card.visible = False
        self.reticle_ring.visible = False
        self.selection_box.visible = False
        self.opt_clique.bgcolor = None
        self.opt_selecao.bgcolor = None
        try:
            self.page.update()
        except Exception:
            pass

    def _on_inspection_tap(self, e: ft.TapEvent):
        if self.mode != "clique":
            return
        pos = getattr(e, "local_position", None)
        if pos is not None and hasattr(pos, "x") and hasattr(pos, "y"):
            x, y = float(pos.x), float(pos.y)
        elif hasattr(e, "local_x") and e.local_x is not None:
            x, y = float(e.local_x), float(e.local_y)
        else:
            return

        sampled = self._sample_pixel_at(x, y)
        if sampled is None:
            return
        r, g, b = sampled

        self.reticle_ring.left = max(0.0, x - 14.0)
        self.reticle_ring.top = max(0.0, y - 14.0)
        self.reticle_ring.visible = True

        family, tone_detail, hex_code = self.dataset.classify_color(r, g, b)

        self.pill_swatch.visible = True
        self.pill_swatch.bgcolor = hex_code
        self.pill_title.value = family
        self.pill_detail.value = tone_detail
        self._reposition_pill()
        try:
            self.page.update()
        except Exception:
            pass

    def _on_inspection_pan_start(self, e: ft.DragStartEvent):
        if self.mode != "selecao":
            return
        pos = getattr(e, "local_position", None)
        if pos is not None and hasattr(pos, "x") and hasattr(pos, "y"):
            x, y = float(pos.x), float(pos.y)
        elif hasattr(e, "local_x") and e.local_x is not None:
            x, y = float(e.local_x), float(e.local_y)
        else:
            return
        self.sel_start = (x, y)
        self.sel_cur = (x, y)
        self._update_sel_box()

    def _on_inspection_pan_update(self, e: ft.DragUpdateEvent):
        if self.mode != "selecao" or not self.sel_start:
            return
        pos = getattr(e, "local_position", None)
        if pos is not None and hasattr(pos, "x") and hasattr(pos, "y"):
            x, y = float(pos.x), float(pos.y)
        elif hasattr(e, "local_x") and e.local_x is not None:
            x, y = float(e.local_x), float(e.local_y)
        else:
            return
        self.sel_cur = (x, y)
        self._update_sel_box()

    def _update_sel_box(self):
        if not self.sel_start or not self.sel_cur:
            return
        x0, y0 = self.sel_start
        x1, y1 = self.sel_cur
        left = min(x0, x1)
        top = min(y0, y1)
        w = max(10.0, abs(x1 - x0))
        h = max(10.0, abs(y1 - y0))
        self.selection_box.left = left
        self.selection_box.top = top
        self.selection_box.width = w
        self.selection_box.height = h
        self.selection_box.visible = True
        try:
            self.page.update()
        except Exception:
            pass

    def _on_inspection_pan_end(self, e: ft.DragEndEvent):
        if self.mode != "selecao" or not self.sel_start or not self.sel_cur:
            return
        x0, y0 = self.sel_start
        x1, y1 = self.sel_cur
        self._sample_area_colors(x0, y0, x1, y1)

    def _sample_pixel_at(self, x: float, y: float) -> tuple[int, int, int] | None:
        if self.cached_image:
            try:
                pw = float(getattr(self.page, "width", 380) or 380)
                ph = float(getattr(self.page, "height", 800) or 800)
                iw, ih = self.cached_image.size
                px = max(0, min(int(x * iw / pw), iw - 1))
                py = max(0, min(int(y * ih / ph), ih - 1))
                pix = self.cached_image.getpixel((px, py))
                if isinstance(pix, (tuple, list)) and len(pix) >= 3:
                    return int(pix[0]), int(pix[1]), int(pix[2])
                elif isinstance(pix, (int, float)):
                    val = int(pix)
                    return val, val, val
            except Exception:
                pass

        if hasattr(self.service, "_grab_screen_pixel"):
            try:
                val = self.service._grab_screen_pixel(int(x), int(y))
                if val is not None:
                    return val
            except Exception:
                pass

        return None

    def _sample_area_colors(self, x0: float, y0: float, x1: float, y1: float):
        if not self.cached_image:
            return
        try:
            pw = float(getattr(self.page, "width", 380) or 380)
            ph = float(getattr(self.page, "height", 800) or 800)
            iw, ih = self.cached_image.size

            rx0 = max(0, min(int(min(x0, x1) * iw / pw), iw - 1))
            rx1 = max(0, min(int(max(x0, x1) * iw / pw), iw - 1))
            ry0 = max(0, min(int(min(y0, y1) * ih / ph), ih - 1))
            ry1 = max(0, min(int(max(y0, y1) * ih / ph), ih - 1))

            if (rx1 - rx0) < 5 or (ry1 - ry0) < 5:
                return

            cropped = self.cached_image.crop((rx0, ry0, rx1, ry1))
            arr = np.array(cropped)
            if arr.ndim == 3 and arr.shape[2] >= 3:
                pixels_rgb = arr[:, :, :3].reshape(-1, 3).astype(np.int32)
                if len(pixels_rgb) > 1500:
                    idx = np.random.choice(len(pixels_rgb), 1500, replace=False)
                    pixels_rgb = pixels_rgb[idx]

                distances, indices = self.dataset.query(pixels_rgb)
                matched_names = self.dataset.get_names_by_indices(indices)

                import pandas as pd
                counts = pd.Series(matched_names).value_counts()
                total = len(matched_names)

                top_colors = []
                for label, count in counts.head(4).items():
                    pct = (count / total) * 100
                    if pct < 3.0 and len(top_colors) >= 1:
                        continue
                    sel = (matched_names == label)
                    mean_rgb = pixels_rgb[sel].mean(axis=0).astype(int)
                    mr, mg, mb = int(mean_rgb[0]), int(mean_rgb[1]), int(mean_rgb[2])
                    family, _, hex_code = self.dataset.classify_color(mr, mg, mb)
                    top_colors.append({
                        "name": family,
                        "specific_name": label,
                        "hex": hex_code,
                        "pct": pct,
                    })

                if top_colors:
                    self.pill_title.value = f"Área: {len(top_colors)} cores"
                    self.pill_detail.value = "Cores na seleção"
                    self.pill_swatch.visible = False
                    self.pill_area_content.controls = [
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Container(
                                            width=16,
                                            height=16,
                                            border_radius=4,
                                            bgcolor=c["hex"],
                                            border=ft.Border.all(1, "#CBD5E1"),
                                        ),
                                        ft.Text(f"{c['name']} ({c['hex']})", size=11, weight=ft.FontWeight.W_600),
                                    ],
                                ),
                                ft.Container(
                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=6,
                                    bgcolor="#EEF4FE",
                                    content=ft.Text(f"{c['pct']:.0f}%", size=10, weight=ft.FontWeight.W_700, color="#1D5CD4"),
                                ),
                            ],
                        )
                        for c in top_colors
                    ]
                    self.pill_area_content.visible = True
                    self._reposition_pill()
                    try:
                        self.page.update()
                    except Exception:
                        pass
        except Exception as e:
            print(f"Erro analisando área overlay: {e}")

    def show(self):
        if not self.is_mounted:
            if self.inspection_layer not in self.page.overlay:
                self.page.overlay.append(self.inspection_layer)
            if self.options_card not in self.page.overlay:
                self.page.overlay.append(self.options_card)
            if self.pill_card not in self.page.overlay:
                self.page.overlay.append(self.pill_card)
            if self.floating_btn not in self.page.overlay:
                self.page.overlay.append(self.floating_btn)
            self.is_mounted = True

        self.floating_btn.visible = True
        self.options_card.visible = False
        self.pill_card.visible = False
        self.inspection_layer.visible = False
        self._reposition_options()
        self._reposition_pill()
        try:
            self.page.update()
        except Exception:
            pass

    def hide(self):
        self.deactivate_mode()
        self.floating_btn.visible = False
        self.options_card.visible = False
        self.pill_card.visible = False
        try:
            self.page.update()
        except Exception:
            pass

    def destroy(self):
        self.hide()
        for ctrl in [self.inspection_layer, self.options_card, self.pill_card, self.floating_btn]:
            if ctrl in self.page.overlay:
                self.page.overlay.remove(ctrl)
        self.is_mounted = False
        try:
            self.page.update()
        except Exception:
            pass

    def close(self):
        self.service.stop()

    def on_language_changed(self):
        pass


class ScreenFloatingService:
    """
    Serviço do Menu Flutuante Suspenso (Tela) para identificação de cores do desktop e celular.
    Suporta modo Desktop (janelas nativas Tkinter) e modo Mobile (overlay nativo Flet).
    """

    _instance = None
    is_available = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ScreenFloatingService()
        return cls._instance

    def __init__(self):
        self.is_available = True
        self.is_running = False
        self.mode = None
        self.is_menu_open = False
        self.dock_side = "right"
        self.on_status_change = None
        self.page = None
        self.mobile_overlay = None

        self.dataset = ColorDatasetService()
        self.dataset.load()

        self.i18n = I18nService.get_instance()
        self.i18n.add_listener(self._on_language_changed)

        self.current_hex = "#94A3B8"
        self.current_name = self.i18n.t("waiting_click")
        self.current_detail = self.i18n.t("waiting_click_desc")
        self.area_colors = []

        # Desktop Tkinter state
        self.tk_thread = None
        self._thread_initialized = threading.Event()
        self.root = None
        self.btn_win = None
        self.options_win = None
        self.pill_win = None
        self.reticle_win = None
        self.overlay_win = None
        self.overlay_canvas = None
        self._eye_photo = None
        self._reticle_hide_timer = None

        self.btn_size = 56
        self.opt_w = 280
        self.opt_h = 178
        self.pill_w = 248
        self.pill_h = 60
        self.ret_size = 32

        self.btn_x = 0
        self.btn_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging_btn = False
        self.mouse_listener = None
        self.sel_start_x = None
        self.sel_start_y = None
        self.sel_cur_x = 0
        self.sel_cur_y = 0
        self.is_drawing_area = False
        self.area_rect_id = None

    def start(self, on_status_change=None, page=None):
        """Ativa o menu flutuante suspenso."""
        self.on_status_change = on_status_change
        if page:
            self.page = page

        if self.current_name in ("Aguardando clique", "Waiting for click", ""):
            self.current_name = self.i18n.t("waiting_click")
            self.current_detail = self.i18n.t("waiting_click_desc")

        # 1. Modo Desktop Nativo (Janelas flutuantes Tkinter fora do app, sobre qualquer janela/programa)
        if DESKTOP_SCREEN_AVAILABLE:
            if self.root is None:
                self.is_running = True
                self.tk_thread = threading.Thread(target=self._run_tk_thread, daemon=True)
                self.tk_thread.start()
                self._thread_initialized.wait(timeout=2.0)
            else:
                self.is_running = True
                self.root.after(0, self._show_floating_button)

            if self.on_status_change:
                try:
                    self.on_status_change(True)
                except Exception:
                    pass
            return

        # 2. Modo Mobile (Android via Flet overlay)
        if not self.mobile_overlay and self.page:
            self.mobile_overlay = MobileFloatingOverlay(self.page, self)
        if self.mobile_overlay:
            self.is_running = True
            self.mobile_overlay.show()
            if self.on_status_change:
                try:
                    self.on_status_change(True)
                except Exception:
                    pass

            # Solicita permissão de sobrepor a outros apps no Android (SYSTEM_ALERT_WINDOW)
            try:
                import flet_permission_handler as fph
                if self.page and hasattr(self.page, "run_task"):
                    async def _req_overlay():
                        try:
                            perm = fph.PermissionHandler()
                            status = await perm.check(fph.Permission.SYSTEM_ALERT_WINDOW)
                            if status != fph.PermissionStatus.GRANTED:
                                await perm.request(fph.Permission.SYSTEM_ALERT_WINDOW)
                        except Exception as pe:
                            print(f"Aviso permissao overlay: {pe}")
                    self.page.run_task(_req_overlay)
            except Exception:
                pass
            return

    def stop(self):
        """Desativa o menu flutuante e oculta as janelas."""
        self.is_running = False
        self.mode = None
        self.is_menu_open = False
        self.area_colors = []

        if self.mobile_overlay:
            try:
                self.mobile_overlay.hide()
            except Exception:
                pass

        if self.mouse_listener and self.mouse_listener.is_alive():
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
            self.mouse_listener = None

        if self.root:
            try:
                self.root.after(0, self._hide_all_windows)
            except Exception:
                pass

        if self.on_status_change:
            try:
                self.on_status_change(False)
            except Exception:
                pass

    def shutdown(self):
        """Encerramento completo ao fechar o app Flet."""
        self.stop()
        if self.mobile_overlay:
            try:
                self.mobile_overlay.destroy()
            except Exception:
                pass
            self.mobile_overlay = None
        if self.root:
            try:
                self.root.after(0, self.root.quit)
            except Exception:
                pass

    def _show_floating_button(self):
        """Exibe o botão flutuante e restaura seu estado na thread do Tkinter."""
        self.mode = None
        self.is_menu_open = False
        self.area_colors = []

        if self.dock_side == "right":
            self.btn_x = self.sw - self.btn_size - 14
        else:
            self.btn_x = 14

        self._update_btn_geometry()
        if self.btn_win:
            self.btn_win.attributes("-alpha", 0.75)
            self.btn_win.deiconify()
            self.btn_win.lift()

    def _on_language_changed(self, lang):
        """Atualiza os textos das janelas do menu flutuante ao mudar de idioma."""
        if self.current_name in ("Aguardando clique", "Waiting for click", ""):
            self.current_name = self.i18n.t("waiting_click")
            self.current_detail = self.i18n.t("waiting_click_desc")
        elif self.mode == "selecao" and not self.area_colors:
            self.current_name = self.i18n.t("waiting_select")
            self.current_detail = self.i18n.t("waiting_select_desc")
        else:
            self.current_name = self.i18n.translate_color(self.current_name)

        if self.mobile_overlay:
            try:
                self.mobile_overlay.on_language_changed()
            except Exception:
                pass

        if self.root:
            def _update_ui():
                try:
                    if self.options_win and self.options_win.winfo_exists():
                        self._render_options_card()
                    if self.pill_win and self.pill_win.winfo_exists():
                        self._render_pill_card()
                except Exception as ex:
                    print(f"Erro ao atualizar UI do menu flutuante: {ex}")

            try:
                self.root.after(0, _update_ui)
            except Exception:
                pass

    def _hide_all_windows(self):
        """Oculta todas as janelas na thread do Tkinter."""
        if self.btn_win:
            self.btn_win.withdraw()
        if self.options_win:
            self.options_win.withdraw()
        if self.pill_win:
            self.pill_win.withdraw()
        if self.reticle_win:
            self.reticle_win.withdraw()
        if self.overlay_win:
            if self.overlay_canvas:
                self.overlay_canvas.delete("all")
            self.overlay_win.withdraw()

    def _run_tk_thread(self):
        """Loop principal do Tkinter persistente."""
        self.root = tk.Tk()
        self.root.withdraw()

        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()

        self.btn_x = self.sw - self.btn_size - 14
        self.btn_y = int(self.sh * 0.38)
        self.dock_side = "right"

        self._build_button_window()
        self._build_options_window()
        self._build_pill_window()
        self._build_reticle_window()
        self._build_overlay_window()

        self._thread_initialized.set()

        self.root.mainloop()

        try:
            self.root.destroy()
        except Exception:
            pass
        self.root = None

    
    
    
    def _build_button_window(self):
        self.btn_win = tk.Toplevel(self.root)
        self.btn_win.overrideredirect(True)
        self.btn_win.attributes("-topmost", True)
        self.btn_win.attributes("-alpha", 0.75)

        trans_key = "#010203"
        self.btn_win.config(bg=trans_key)
        self.btn_win.wm_attributes("-transparentcolor", trans_key)

        canvas = tk.Canvas(
            self.btn_win,
            width=self.btn_size,
            height=self.btn_size,
            bg=trans_key,
            highlightthickness=0,
            cursor="hand2",
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        try:
            im = Image.open("assets/floating_eye.png").convert("RGBA")
            arr = np.array(im)
            alpha = arr[:, :, 3]
            mask = alpha >= 60
            rows = np.where(mask.any(axis=1))[0]
            cols = np.where(mask.any(axis=0))[0]
            if len(rows) and len(cols):
                arr[alpha < 60] = 0
                cleaned = Image.fromarray(arr).crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))
            else:
                cleaned = im

            resized = cleaned.resize((self.btn_size, self.btn_size), Image.Resampling.LANCZOS)
            arr_res = np.array(resized)
            a = arr_res[:, :, 3]
            arr_res[a < 90] = [1, 2, 3, 0]
            arr_res[a >= 90, 3] = 255
            final_img = Image.fromarray(arr_res)

            self._eye_photo = ImageTk.PhotoImage(final_img)
            canvas.create_image(self.btn_size // 2, self.btn_size // 2, image=self._eye_photo)
        except Exception:
            canvas.create_oval(3, 3, self.btn_size - 3, self.btn_size - 3, fill="#0D1B2A", outline="#FFFFFF", width=2)
            canvas.create_oval(18, 18, self.btn_size - 18, self.btn_size - 18, fill="#1D5CD4")

        canvas.bind("<ButtonPress-1>", self._on_btn_press)
        canvas.bind("<B1-Motion>", self._on_btn_drag)
        canvas.bind("<ButtonRelease-1>", self._on_btn_release)
        canvas.bind("<Enter>", self._on_btn_enter)
        canvas.bind("<Leave>", self._on_btn_leave)
        canvas.bind("<ButtonPress-3>", lambda e: self.stop())

        self._update_btn_geometry()

    def _update_btn_geometry(self):
        if not self.btn_win:
            return
        self.btn_win.geometry(f"{self.btn_size}x{self.btn_size}+{self.btn_x}+{self.btn_y}")

    def _on_btn_press(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging_btn = False

    def _on_btn_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        if abs(dx) > 3 or abs(dy) > 3:
            self.is_dragging_btn = True

        self.btn_x += dx
        self.btn_y += dy

        self.btn_x = max(10, min(self.btn_x, self.sw - self.btn_size - 10))
        self.btn_y = max(10, min(self.btn_y, self.sh - self.btn_size - 10))

        self.btn_win.attributes("-alpha", 1.0)
        self._update_btn_geometry()

        if self.is_menu_open:
            self._reposition_options()
        if self.mode:
            self._reposition_pill()

    def _on_btn_release(self, event):
        if not self.is_dragging_btn:
            self.toggle_options()
        else:
            if self.btn_x > self.sw // 2:
                self.dock_side = "right"
            else:
                self.dock_side = "left"

            self.btn_x = max(10, min(self.btn_x, self.sw - self.btn_size - 10))
            self.btn_y = max(10, min(self.btn_y, self.sh - self.btn_size - 10))

            if not self.mode and not self.is_menu_open:
                self.btn_win.attributes("-alpha", 0.75)

            self._update_btn_geometry()
            if self.is_menu_open:
                self._reposition_options()
            if self.mode:
                self._reposition_pill()

    def _on_btn_enter(self, event):
        if self.btn_win:
            self.btn_win.attributes("-alpha", 1.0)

    def _on_btn_leave(self, event):
        if not self.mode and not self.is_menu_open and not self.is_dragging_btn:
            if self.btn_win:
                self.btn_win.attributes("-alpha", 0.75)

    
    
    
    def _build_options_window(self):
        self.options_win = tk.Toplevel(self.root)
        self.options_win.overrideredirect(True)
        self.options_win.attributes("-topmost", True)

        trans_key = "#010203"
        self.options_win.config(bg=trans_key)
        self.options_win.wm_attributes("-transparentcolor", trans_key)

        self.opt_canvas = tk.Canvas(
            self.options_win,
            width=self.opt_w,
            height=self.opt_h,
            bg=trans_key,
            highlightthickness=0,
        )
        self.opt_canvas.pack(fill=tk.BOTH, expand=True)

        self._render_options_card()
        self.options_win.withdraw()

    def _render_options_card(self):
        self.opt_canvas.delete("all")

        is_clique_active = self.mode == "clique"
        is_sel_active = self.mode == "selecao"

        self.opt_w = 280

        title1 = self.i18n.t("tab_clique") + (self.i18n.t("active_badge") if is_clique_active else "")
        desc1 = self.i18n.t("opt_clique_desc")
        title2 = self.i18n.t("tab_selecao") + (self.i18n.t("active_badge") if is_sel_active else "")
        desc2 = self.i18n.t("opt_selecao_desc")

        f_title = ("Segoe UI", 10, "bold")
        f_desc = ("Segoe UI", 8)
        text_w = self.opt_w - 76

        
        t1_temp = self.opt_canvas.create_text(62, 10, text=title1, font=f_title, anchor="nw")
        t1_box = self.opt_canvas.bbox(t1_temp)
        t1_h = (t1_box[3] - t1_box[1]) if t1_box else 18

        d1_temp = self.opt_canvas.create_text(62, 10 + t1_h + 3, text=desc1, font=f_desc, anchor="nw", width=text_w)
        d1_box = self.opt_canvas.bbox(d1_temp)
        d1_h = (d1_box[3] - d1_box[1]) if d1_box else 14

        t2_temp = self.opt_canvas.create_text(62, 10, text=title2, font=f_title, anchor="nw")
        t2_box = self.opt_canvas.bbox(t2_temp)
        t2_h = (t2_box[3] - t2_box[1]) if t2_box else 18

        d2_temp = self.opt_canvas.create_text(62, 10 + t2_h + 3, text=desc2, font=f_desc, anchor="nw", width=text_w)
        d2_box = self.opt_canvas.bbox(d2_temp)
        d2_h = (d2_box[3] - d2_box[1]) if d2_box else 14

        self.opt_canvas.delete("all")

        
        card1_h = max(72, 14 + t1_h + 3 + d1_h + 16)
        card2_h = max(72, 14 + t2_h + 3 + d2_h + 16)

        y1 = 12
        y2 = y1 + card1_h + 10
        self.opt_h = y2 + card2_h + 12

        self.opt_canvas.config(width=self.opt_w, height=self.opt_h)

        
        self._draw_rounded_rect(
            self.opt_canvas, 2, 2, self.opt_w - 2, self.opt_h - 2, radius=16, fill="#FFFFFF", outline="#E2E8F0", width=1.5
        )

        
        clique_bg = "#EEF4FE" if is_clique_active else "#F8FAFC"
        clique_border = "#1D5CD4" if is_clique_active else "#E2E8F0"
        self._draw_rounded_rect(
            self.opt_canvas, 10, y1, self.opt_w - 10, y1 + card1_h, radius=12, fill=clique_bg, outline=clique_border, width=1.5
        )

        icon1_y = y1 + (card1_h - 36) // 2
        self.opt_canvas.create_oval(18, icon1_y, 54, icon1_y + 36, fill="#FFFFFF", outline="#E2E8F0", width=1)
        self.opt_canvas.create_text(
            36, icon1_y + 18, text="✛", font=("Segoe UI", 13, "bold"), fill="#1D5CD4"
        )

        self.opt_canvas.create_text(
            62, y1 + 13, text=title1,
            font=f_title, fill="#0F172A", anchor="nw"
        )
        self.opt_canvas.create_text(
            62, y1 + 13 + t1_h + 3, text=desc1,
            font=f_desc, fill="#64748B", anchor="nw", width=text_w
        )

        
        sel_bg = "#EEF4FE" if is_sel_active else "#F8FAFC"
        sel_border = "#1D5CD4" if is_sel_active else "#E2E8F0"
        self._draw_rounded_rect(
            self.opt_canvas, 10, y2, self.opt_w - 10, y2 + card2_h, radius=12, fill=sel_bg, outline=sel_border, width=1.5
        )

        icon2_y = y2 + (card2_h - 36) // 2
        self.opt_canvas.create_oval(18, icon2_y, 54, icon2_y + 36, fill="#FFFFFF", outline="#E2E8F0", width=1)
        self.opt_canvas.create_text(
            36, icon2_y + 18, text="⬚", font=("Segoe UI", 13, "bold"), fill="#1D5CD4"
        )

        self.opt_canvas.create_text(
            62, y2 + 13, text=title2,
            font=f_title, fill="#0F172A", anchor="nw"
        )
        self.opt_canvas.create_text(
            62, y2 + 13 + t2_h + 3, text=desc2,
            font=f_desc, fill="#64748B", anchor="nw", width=text_w
        )

        def on_options_click(event):
            x, y = event.x, event.y
            if 10 <= x <= self.opt_w - 10:
                if y1 <= y <= y1 + card1_h:
                    self.toggle_mode("clique")
                elif y2 <= y <= y2 + card2_h:
                    self.toggle_mode("selecao")

        self.opt_canvas.bind("<ButtonPress-1>", on_options_click)

    def _reposition_options(self):
        if not self.options_win:
            return
        if self.dock_side == "right":
            ox = self.btn_x - self.opt_w - 10
        else:
            ox = self.btn_x + self.btn_size + 10

        oy = max(10, min(self.btn_y - (self.opt_h - self.btn_size) // 2, self.sh - self.opt_h - 20))
        self.options_win.geometry(f"{self.opt_w}x{self.opt_h}+{ox}+{oy}")

    def toggle_options(self):
        """Abre ou fecha o menu popup de opções."""
        self.is_menu_open = not self.is_menu_open
        if self.is_menu_open:
            self.btn_win.attributes("-alpha", 1.0)
            self._render_options_card()
            self._reposition_options()
            self.options_win.deiconify()
            self.options_win.lift()
        else:
            self.options_win.withdraw()
            if not self.mode:
                self._on_btn_leave(None)

    def toggle_mode(self, selected_mode: str):
        """Alterna ou desliga uma função."""
        if self.mode == selected_mode:
            self.deactivate_current_mode()
            self._render_options_card()
            return

        self.deactivate_current_mode()
        self.mode = selected_mode
        self.area_colors = []
        self._render_options_card()

        self.is_menu_open = False
        self.options_win.withdraw()

        self.show_pill()

        if self.mode == "clique":
            self.current_name = self.i18n.t("waiting_click")
            self.current_detail = self.i18n.t("waiting_click_desc")
            self._start_global_click_mode()
        elif self.mode == "selecao":
            self.current_name = self.i18n.t("waiting_select")
            self.current_detail = self.i18n.t("waiting_select_desc")
            self._start_selection_mode()

    def deactivate_current_mode(self):
        """Desliga o modo ativo e oculta as janelas de inspeção."""
        if self.mouse_listener and self.mouse_listener.is_alive():
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
            self.mouse_listener = None

        if self.reticle_win:
            try:
                self.reticle_win.withdraw()
            except Exception:
                pass

        if self.overlay_win:
            try:
                if self.overlay_canvas:
                    self.overlay_canvas.delete("all")
                    self.area_rect_id = None
                self.overlay_win.withdraw()
            except Exception:
                pass

        self.is_drawing_area = False
        self.sel_start_x = None
        self.sel_start_y = None
        self.mode = None
        self.area_colors = []
        self.hide_pill()

        if self.btn_win and not self.is_menu_open:
            self.btn_win.attributes("-alpha", 0.75)

    
    
    
    def _build_pill_window(self):
        self.pill_win = tk.Toplevel(self.root)
        self.pill_win.overrideredirect(True)
        self.pill_win.attributes("-topmost", True)

        trans_key = "#010203"
        self.pill_win.config(bg=trans_key)
        self.pill_win.wm_attributes("-transparentcolor", trans_key)

        self.pill_canvas = tk.Canvas(
            self.pill_win,
            width=self.pill_w,
            height=self.pill_h,
            bg=trans_key,
            highlightthickness=0,
            cursor="hand2",
        )
        self.pill_canvas.pack(fill=tk.BOTH, expand=True)

        self.pill_win.withdraw()

    def _render_pill_card(self):
        self.pill_canvas.delete("all")

        
        
        
        if self.mode == "selecao" and self.area_colors:
            num_items = len(self.area_colors)
            self.pill_w = 272
            row_step = 68
            item_h = 60
            self.pill_h = 44 + num_items * row_step
            self.pill_canvas.config(width=self.pill_w, height=self.pill_h)

            
            self._draw_rounded_rect(
                self.pill_canvas, 2, 2, self.pill_w - 2, self.pill_h - 2, radius=16, fill="#FFFFFF", outline="#E2E8F0", width=1.5
            )

            
            self.pill_canvas.create_text(
                16, 20, text=self.i18n.t("area_colors_title").upper(),
                font=("Segoe UI", 8, "bold"), fill="#64748B", anchor="w"
            )

            
            for i, item in enumerate(self.area_colors):
                y = 36 + i * row_step

                
                self._draw_rounded_rect(
                    self.pill_canvas, 8, y, self.pill_w - 8, y + item_h, radius=12, fill="#F8FAFC", outline="#E2E8F0", width=1
                )

                
                swatch_y = y + (item_h - 36) // 2
                self._draw_rounded_rect(
                    self.pill_canvas, 16, swatch_y, 52, swatch_y + 36, radius=9, fill=item["hex"], outline="#CBD5E1", width=1
                )

                
                t_id = self.pill_canvas.create_text(
                    58, y + 8, text=item["name"],
                    font=("Segoe UI", 10, "bold"), fill="#0F172A", anchor="nw"
                )
                t_box = self.pill_canvas.bbox(t_id)
                sub_y = (t_box[3] + 2) if t_box else (y + 30)
                self.pill_canvas.create_text(
                    58, sub_y, text=f"{item['specific_name']} · {item['hex'].upper()}",
                    font=("Segoe UI", 7), fill="#64748B", anchor="nw", width=self.pill_w - 118
                )

                
                badge_w = 40
                badge_h = 24
                bx2 = self.pill_w - 14
                bx1 = bx2 - badge_w
                by1 = y + (item_h - badge_h) // 2
                self._draw_rounded_rect(
                    self.pill_canvas, bx1, by1, bx2, by1 + badge_h, radius=6, fill="#EEF4FE", outline="#D0E1FD", width=1
                )
                self.pill_canvas.create_text(
                    (bx1 + bx2) // 2, by1 + badge_h // 2, text=f"{item['pct']:.0f}%",
                    font=("Segoe UI", 8, "bold"), fill="#1D5CD4", anchor="center"
                )

        
        
        
        elif self.mode == "selecao" and not self.area_colors:
            title_text = self.i18n.t("select_area_hint")
            detail_text = self.i18n.t("drag_hint")

            f_title = ("Segoe UI", 10, "bold")
            f_detail = ("Segoe UI", 7)

            temp_t = self.pill_canvas.create_text(58, 22, text=title_text, font=f_title, anchor="nw")
            box_t = self.pill_canvas.bbox(temp_t)
            w_t = (box_t[2] - box_t[0]) if box_t else 120

            temp_d = self.pill_canvas.create_text(58, 42, text=detail_text, font=f_detail, anchor="nw")
            box_d = self.pill_canvas.bbox(temp_d)
            w_d = (box_d[2] - box_d[0]) if box_d else 120
            self.pill_canvas.delete("all")

            self.pill_w = max(240, min(360, 58 + max(w_t, w_d) + 24))
            self.pill_h = 80
            self.pill_canvas.config(width=self.pill_w, height=self.pill_h)

            self._draw_rounded_rect(
                self.pill_canvas, 2, 2, self.pill_w - 2, self.pill_h - 2, radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1.5
            )

            
            self.pill_canvas.create_oval(14, 22, 50, 58, fill="#EEF4FE", outline="#D0E1FD", width=1)
            self.pill_canvas.create_text(
                32, 40, text="⬚", font=("Segoe UI", 13, "bold"), fill="#1D5CD4", anchor="center"
            )

            t_id = self.pill_canvas.create_text(
                58, 22, text=title_text,
                font=f_title, fill="#0F172A", anchor="nw"
            )
            t_box = self.pill_canvas.bbox(t_id)
            d_y = (t_box[3] + 4) if t_box else 42
            self.pill_canvas.create_text(
                58, d_y, text=detail_text,
                font=f_detail, fill="#64748B", anchor="nw", width=self.pill_w - 68
            )

        
        
        
        else:
            is_waiting = self.current_name in ("Aguardando clique", "Waiting for click", "")
            if is_waiting:
                title_text = self.i18n.t("waiting_click")
                detail_text = self.i18n.t("waiting_click_desc")
                swatch_fill = "#CBD5E1"
            else:
                title_text = self.i18n.translate_color(self.current_name)
                detail_text = self.current_detail
                swatch_fill = self.current_hex

            f_title = ("Segoe UI", 10, "bold")
            f_detail = ("Segoe UI", 7)

            temp_t = self.pill_canvas.create_text(58, 22, text=title_text, font=f_title, anchor="nw")
            box_t = self.pill_canvas.bbox(temp_t)
            w_t = (box_t[2] - box_t[0]) if box_t else 120

            temp_d = self.pill_canvas.create_text(58, 42, text=detail_text, font=f_detail, anchor="nw", width=280)
            box_d = self.pill_canvas.bbox(temp_d)
            w_d = (box_d[2] - box_d[0]) if box_d else 120
            h_d_bottom = box_d[3] if box_d else 54
            self.pill_canvas.delete("all")

            self.pill_w = max(240, min(360, 58 + max(w_t, w_d) + 36))
            self.pill_h = max(80, h_d_bottom + 16)
            self.pill_canvas.config(width=self.pill_w, height=self.pill_h)

            self._draw_rounded_rect(
                self.pill_canvas, 2, 2, self.pill_w - 2, self.pill_h - 2, radius=20, fill="#FFFFFF", outline="#E2E8F0", width=1.5
            )

            # Swatch de cor
            swatch_top = (self.pill_h - 38) // 2
            self._draw_rounded_rect(
                self.pill_canvas, 12, swatch_top, 50, swatch_top + 38, radius=9, fill=swatch_fill, outline="#CBD5E1", width=1
            )

            # Botão fechar (X)
            close_x = self.pill_w - 18
            close_y = 18
            self.pill_canvas.create_text(
                close_x, close_y, text="✕", font=("Segoe UI", 9, "bold"), fill="#94A3B8"
            )

            t_id = self.pill_canvas.create_text(
                58, 22, text=title_text,
                font=f_title, fill="#0F172A", anchor="nw"
            )
            t_box = self.pill_canvas.bbox(t_id)
            d_y = (t_box[3] + 4) if t_box else 42

            self.pill_canvas.create_text(
                58, d_y, text=detail_text,
                font=f_detail, fill="#64748B", anchor="nw", width=self.pill_w - 74
            )

            def on_pill_click(event):
                if event.x >= self.pill_w - 32 and event.y <= 32:
                    self.deactivate_current_mode()

            self.pill_canvas.bind("<ButtonPress-1>", on_pill_click)

        if self.pill_win and self.pill_win.state() != "withdrawn":
            self._reposition_pill()

    def _reposition_pill(self):
        if not self.pill_win:
            return
        if self.dock_side == "right":
            px = self.btn_x - self.pill_w - 10
        else:
            px = self.btn_x + self.btn_size + 10

        py = max(10, min(self.btn_y + (self.btn_size - self.pill_h) // 2, self.sh - self.pill_h - 20))
        self.pill_win.geometry(f"{self.pill_w}x{self.pill_h}+{px}+{py}")

    def show_pill(self):
        self._render_pill_card()
        self._reposition_pill()
        self.pill_win.deiconify()
        self.pill_win.lift()

    def hide_pill(self):
        if self.pill_win:
            self.pill_win.withdraw()

    def update_pill_color(self, hex_code: str, name: str, detail: str):
        """Atualiza os dados de cor única na barrinha flutuante."""
        self.current_hex = hex_code
        self.current_name = name
        self.current_detail = detail
        if self.pill_win and self.pill_win.state() != "withdrawn":
            self.show_pill()

    def update_area_colors(self, colors: list[dict]):
        """Atualiza a lista vertical de cores encontradas na área selecionada."""
        self.area_colors = colors
        if colors:
            self.current_hex = colors[0]["hex"]
            self.current_name = colors[0]["name"]
            self.current_detail = f"{colors[0]['specific_name']} · {colors[0]['hex']}"
        self.show_pill()

    
    
    
    def _build_reticle_window(self):
        self.reticle_win = tk.Toplevel(self.root)
        self.reticle_win.overrideredirect(True)
        self.reticle_win.attributes("-topmost", True)

        trans_key = "#010203"
        self.reticle_win.config(bg=trans_key)
        self.reticle_win.wm_attributes("-transparentcolor", trans_key)

        self.ret_canvas = tk.Canvas(
            self.reticle_win, width=self.ret_size, height=self.ret_size, bg=trans_key, highlightthickness=0
        )
        self.ret_canvas.pack(fill=tk.BOTH, expand=True)

        c = self.ret_size // 2
        r = 11
        self.ret_canvas.create_oval(c - r, c - r, c + r, c + r, outline="#FFFFFF", width=2)
        self.ret_canvas.create_oval(c - r + 1, c - r + 1, c + r - 1, c + r - 1, outline="#000000", width=1)
        self.ret_canvas.create_line(c, 1, c, c - r + 2, fill="#FFFFFF", width=1.5)
        self.ret_canvas.create_line(c, c + r - 2, c, self.ret_size - 1, fill="#FFFFFF", width=1.5)
        self.ret_canvas.create_line(1, c, c - r + 2, c, fill="#FFFFFF", width=1.5)
        self.ret_canvas.create_line(c + r - 2, c, self.ret_size - 1, c, fill="#FFFFFF", width=1.5)

        self.reticle_win.withdraw()
        self._reticle_hide_timer = None

        _make_window_click_through(self.reticle_win)

    def _show_reticle_at(self, screen_x: int, screen_y: int):
        if not self.reticle_win:
            return
        half = self.ret_size // 2
        self.reticle_win.geometry(f"{self.ret_size}x{self.ret_size}+{screen_x - half}+{screen_y - half}")
        self.reticle_win.deiconify()
        self.reticle_win.lift()

        if self._reticle_hide_timer:
            try:
                self.root.after_cancel(self._reticle_hide_timer)
            except Exception:
                pass
        self._reticle_hide_timer = self.root.after(2000, self._hide_reticle)

    def _hide_reticle(self):
        if self.reticle_win and self.reticle_win.state() != "withdrawn":
            self.reticle_win.withdraw()

    def _start_global_click_mode(self):
        """Inicia escuta global do mouse para o modo Clique com sincronia 1:1 e sem ocultar o cursor."""
        is_pressed = False
        last_update_time = [0.0]

        def on_click(x, y, button, pressed):
            nonlocal is_pressed
            if not self.is_running or self.mode != "clique":
                return False

            if button == mouse.Button.left:
                is_pressed = pressed
                if self._is_point_on_our_windows(x, y):
                    return

                if pressed:
                    if self.root:
                        self.root.after(0, self._hide_reticle)
                    self._sample_screen_pixel(int(x), int(y), is_final=False)
                else:
                    self._sample_screen_pixel(int(x), int(y), is_final=True)

        def on_move(x, y):
            nonlocal is_pressed
            if not self.is_running or self.mode != "clique" or not is_pressed:
                return

            now = time.time()
            if now - last_update_time[0] > 0.025:
                last_update_time[0] = now
                if not self._is_point_on_our_windows(x, y):
                    self._sample_screen_pixel(int(x), int(y), is_final=False)

        if self.mouse_listener and self.mouse_listener.is_alive():
            try:
                self.mouse_listener.stop()
            except Exception:
                pass

        self.mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
        self.mouse_listener.start()

    def _is_point_on_our_windows(self, x, y):
        """Verifica se o ponto (x,y) está sobre as janelas do próprio IRIS."""
        if self.btn_win and self.btn_win.state() != "withdrawn":
            bx = self.btn_win.winfo_rootx()
            by = self.btn_win.winfo_rooty()
            if bx <= x <= bx + self.btn_size and by <= y <= by + self.btn_size:
                return True

        if self.options_win and self.options_win.state() != "withdrawn":
            ox = self.options_win.winfo_rootx()
            oy = self.options_win.winfo_rooty()
            if ox <= x <= ox + self.opt_w and oy <= y <= oy + self.opt_h:
                return True

        if self.pill_win and self.pill_win.state() != "withdrawn":
            px = self.pill_win.winfo_rootx()
            py = self.pill_win.winfo_rooty()
            if px <= x <= px + self.pill_w and py <= y <= py + self.pill_h:
                return True

        return False

    def _sample_screen_pixel(self, x: int, y: int, is_final: bool = False):
        """Captura o pixel da tela nas coordenadas físicas (x, y) e classifica a cor."""
        try:
            if self.reticle_win and self.reticle_win.state() != "withdrawn":
                self.reticle_win.withdraw()

            res = self._grab_screen_pixel(x, y)
            if res is None:
                return
            r, g, b = res
            family, tone_detail, hex_code = self.dataset.classify_color(r, g, b)

            if self.root:
                self.root.after(0, self._apply_sampled_color, hex_code, family, tone_detail, x, y, is_final)
        except Exception as e:
            print(f"Erro ao capturar pixel da tela: {e}")

    def _apply_sampled_color(self, hex_code: str, name: str, detail: str, x: int, y: int, is_final: bool = False):
        self.update_pill_color(hex_code, name, detail)
        if is_final:
            self._show_reticle_at(x, y)

    
    
    
    def _build_overlay_window(self):
        self.overlay_win = tk.Toplevel(self.root)
        self.overlay_win.overrideredirect(True)
        self.overlay_win.attributes("-topmost", True)
        self.overlay_win.geometry(f"{self.sw}x{self.sh}+0+0")

        trans_key = "#010203"
        self.overlay_win.config(bg=trans_key)
        self.overlay_win.wm_attributes("-transparentcolor", trans_key)

        self.overlay_canvas = tk.Canvas(
            self.overlay_win,
            width=self.sw,
            height=self.sh,
            bg=trans_key,
            highlightthickness=0,
        )
        self.overlay_canvas.pack(fill=tk.BOTH, expand=True)
        self.overlay_win.withdraw()

        _make_window_click_through(self.overlay_win)

    def _start_selection_mode(self):
        """Inicia o modo Seleção com escuta global via pynput e desenho em tempo real."""
        self.is_drawing_area = False
        self.sel_start_x = None
        self.sel_start_y = None

        if self.overlay_win:
            self.overlay_canvas.delete("all")
            self.area_rect_id = None
            self.overlay_win.deiconify()
            self.overlay_win.lift()

        self._sel_drawing_loop()

        def on_click(x, y, button, pressed):
            if not self.is_running or self.mode != "selecao":
                return False

            if button == mouse.Button.left:
                if self._is_point_on_our_windows(x, y):
                    return

                if pressed:
                    self.sel_start_x = int(x)
                    self.sel_start_y = int(y)
                    self.sel_cur_x = int(x)
                    self.sel_cur_y = int(y)
                    self.is_drawing_area = True
                else:
                    if not self.is_drawing_area or self.sel_start_x is None or self.sel_start_y is None:
                        return
                    self.is_drawing_area = False
                    end_x, end_y = int(x), int(y)
                    x1 = min(self.sel_start_x, end_x)
                    y1 = min(self.sel_start_y, end_y)
                    x2 = max(self.sel_start_x, end_x)
                    y2 = max(self.sel_start_y, end_y)
                    w, h = x2 - x1, y2 - y1
                    self.sel_start_x = None
                    self.sel_start_y = None

                    if self.root:
                        self.root.after(0, self._clear_selection_rect)
                        if w > 12 and h > 12:
                            self.root.after(25, self._sample_screen_area, x1, y1, w, h)

        def on_move(x, y):
            if not self.is_running or self.mode != "selecao":
                return
            if self.is_drawing_area:
                self.sel_cur_x = int(x)
                self.sel_cur_y = int(y)

        if self.mouse_listener and self.mouse_listener.is_alive():
            try:
                self.mouse_listener.stop()
            except Exception:
                pass

        self.mouse_listener = mouse.Listener(on_click=on_click, on_move=on_move)
        self.mouse_listener.start()

    def _clear_selection_rect(self):
        if self.overlay_canvas:
            self.overlay_canvas.delete("all")
            self.area_rect_id = None

    def _sel_drawing_loop(self):
        """Loop de 60 FPS para desenhar o retângulo de seleção em tempo real."""
        if not self.is_running or self.mode != "selecao":
            return

        if self.is_drawing_area and self.overlay_canvas and self.sel_start_x is not None and self.sel_cur_x is not None:
            if not self.area_rect_id:
                self.area_rect_id = self.overlay_canvas.create_rectangle(
                    self.sel_start_x, self.sel_start_y,
                    self.sel_cur_x, self.sel_cur_y,
                    outline="#1D5CD4", width=2, dash=(6, 3)
                )
            else:
                self.overlay_canvas.coords(
                    self.area_rect_id,
                    self.sel_start_x, self.sel_start_y,
                    self.sel_cur_x, self.sel_cur_y,
                )
        else:
            if self.area_rect_id and self.overlay_canvas:
                self.overlay_canvas.delete(self.area_rect_id)
                self.area_rect_id = None

        if self.root:
            self.root.after(16, self._sel_drawing_loop)

    def _sample_screen_area(self, x: int, y: int, w: int, h: int):
        """Captura região da tela e identifica a lista de cores predominantes."""
        try:
            if self.overlay_canvas:
                self.overlay_canvas.delete("all")
                self.area_rect_id = None
            if self.root:
                self.root.update_idletasks()

            pixels_rgb = None

            
            try:
                import mss
                with mss.mss() as sct:
                    region = {"top": y, "left": x, "width": w, "height": h}
                    shot = sct.grab(region)
                    arr = np.array(shot)  
                    pixels_rgb = arr[:, :, [2, 1, 0]].reshape(-1, 3)
            except Exception:
                pass

            
            if pixels_rgb is None or len(pixels_rgb) == 0:
                try:
                    from PIL import ImageGrab
                    bbox = (x, y, x + w, y + h)
                    img = ImageGrab.grab(bbox=bbox)
                    pixels_rgb = np.array(img.convert("RGB")).reshape(-1, 3)
                except Exception:
                    pass

            if pixels_rgb is None or len(pixels_rgb) == 0:
                return

            from collections import Counter
            if len(pixels_rgb) > 2500:
                idx = np.random.choice(len(pixels_rgb), 2500, replace=False)
                pixels_rgb = pixels_rgb[idx]

            distances, indices = self.dataset.query(pixels_rgb)
            if indices is not None:
                labels = self.dataset.names[indices]
                counter = Counter(labels)
                total = len(labels)

                top_colors = []
                for label, count in counter.most_common(5):
                    pct = (count / total) * 100.0
                    
                    if pct < 3.0 and len(top_colors) >= 1:
                        continue
                    sel = labels == label
                    mean_rgb = pixels_rgb[sel].mean(axis=0).astype(int)
                    mr, mg, mb = int(mean_rgb[0]), int(mean_rgb[1]), int(mean_rgb[2])

                    family, _, hex_code = self.dataset.classify_color(mr, mg, mb)
                    top_colors.append({
                        "name": family,
                        "specific_name": label,
                        "hex": hex_code,
                        "pct": pct,
                    })

                if self.root:
                    self.root.after(0, self.update_area_colors, top_colors)
        except Exception as e:
            print(f"Erro na análise de área da tela: {e}")

    
    
    
    def _grab_screen_pixel(self, x: int, y: int) -> tuple[int, int, int] | None:
        """Captura cor RGB de um único pixel na tela de forma 1:1 (ordem R, G, B correta)."""
        # 1. Tenta MSS
        try:
            import mss
            with mss.mss() as sct:
                monitor = {"top": int(y), "left": int(x), "width": 1, "height": 1}
                s = sct.grab(monitor)
                r, g, b = s.pixel(0, 0)[:3]
                return int(r), int(g), int(b)
        except Exception:
            pass

        # 2. Tenta PIL ImageGrab com all_screens=True (suporta múltiplos monitores)
        try:
            from PIL import ImageGrab
            im = ImageGrab.grab(bbox=(int(x), int(y), int(x) + 1, int(y) + 1), all_screens=True)
            r, g, b = im.getpixel((0, 0))[:3]
            return int(r), int(g), int(b)
        except Exception:
            pass

        # 3. Tenta ctypes Windows GDI GetPixel com HDC do display
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            user32.GetDC.restype = wintypes.HDC
            user32.GetDC.argtypes = [wintypes.HWND]
            user32.ReleaseDC.restype = ctypes.c_int
            user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
            gdi32.GetPixel.restype = wintypes.COLORREF
            gdi32.GetPixel.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]

            hdc = user32.GetDC(None)
            if hdc:
                pixel = gdi32.GetPixel(hdc, int(x), int(y))
                user32.ReleaseDC(None, hdc)
                if pixel != -1 and pixel != 0xFFFFFFFF:
                    r = pixel & 0xFF
                    g = (pixel >> 8) & 0xFF
                    b = (pixel >> 16) & 0xFF
                    return int(r), int(g), int(b)
        except Exception:
            pass

        # Retorna None caso a captura de tela física não tenha sido possível (NUNCA azul fixo!)
        return None

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius=16, **kwargs):
        """Desenha um retângulo com cantos arredondados no Canvas do Tkinter."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)
