import os
import sys
import time
import base64
import asyncio
import threading
import flet as ft
from theme import *
from components.bottom_nav import build_bottom_nav
from services.camera_service import CameraService
from services.i18n_service import I18nService

try:
    import flet_camera as fc
    HAS_FLET_CAMERA = True
except Exception:
    fc = None
    HAS_FLET_CAMERA = False

try:
    import flet_permission_handler as fph
    HAS_PERM_HANDLER = True
except Exception:
    fph = None
    HAS_PERM_HANDLER = False


class CameraUIController:
    """
    Controlador da tela de Câmera mobile e desktop integrado ao CameraService (KDTree + Flet Camera/OpenCV).
    Suporta câmera nativa em tempo real no celular (frontal e traseira), identificação instantânea ao tocar e rotação em pé.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.mode = "clique"
        self.camera_facing = "back"

        self.service = CameraService()

        # Coordenadas e seleção
        self.has_selected_color = False
        self.has_selected_area = False
        self.target_x = 180.0
        self.target_y = 190.0
        self.drag_start = None
        self.drag_cur = None

        self._last_drag_time = 0.0
        self._last_drag_pos = None
        self._is_drag_updating = False
        self._reticle_timer = None

        self.is_frame_updating = False
        self.is_flet_cam_active = False

        self.point_color_name = ""
        self.point_color_detail = ""
        self.point_color_hex = ""
        self.area_colors = []

        # Câmeras físicas detectadas
        self.available_cameras = []
        self.back_camera = None
        self.front_camera = None

        # Elementos visuais
        self.tab_clique = None
        self.tab_selecao = None
        self.badge_text = None
        self.target_ring = None
        self.selection_box = None
        self.instruction_text = None
        self.result_container = None
        self.camera_image = None
        self.camera_widget = None
        self.camera_placeholder_icon = None
        self.flip_button = None

        # Gerenciador de permissões
        self.perm_handler = None
        if HAS_PERM_HANDLER:
            try:
                self.perm_handler = fph.PermissionHandler()
                if hasattr(page, "services") and self.perm_handler not in page.services:
                    page.services.append(self.perm_handler)
            except Exception:
                self.perm_handler = None

    def _is_widget_mounted(self) -> bool:
        """Verifica com segurança se o widget de câmera já está associado à página."""
        if not self.camera_widget:
            return False
        try:
            return self.camera_widget.page is not None
        except Exception:
            return False

    def start_camera(self):
        """Inicia a câmera mobile (fc.Camera) imediatamente após a montagem da view."""
        if HAS_FLET_CAMERA and self.camera_widget:
            async def _init_mobile():
                # 1. Aguarda a montagem da view na árvore da página (até 1.5s em passos de 40ms)
                for _ in range(35):
                    if self._is_widget_mounted():
                        break
                    await asyncio.sleep(0.04)

                # 2. Requisita permissão nativa da câmera no Android
                if self.perm_handler:
                    try:
                        await self.perm_handler.request(fph.Permission.CAMERA)
                    except Exception as pe:
                        print(f"Aviso permissão da câmera: {pe}")

                # 3. Detecta lentes físicas disponíveis e inicializa com JPEG e orientação em pé
                try:
                    cams = await self.camera_widget.get_available_cameras()
                    if cams:
                        self.available_cameras = cams
                        self.back_camera = next(
                            (c for c in cams if getattr(c, "lens_direction", None) == fc.CameraLensDirection.BACK),
                            cams[0],
                        )
                        self.front_camera = next(
                            (c for c in cams if getattr(c, "lens_direction", None) == fc.CameraLensDirection.FRONT),
                            None,
                        )

                        target = self.back_camera if self.camera_facing == "back" else (self.front_camera or self.back_camera)
                        await self.camera_widget.initialize(
                            description=target,
                            resolution_preset=fc.ResolutionPreset.MEDIUM,
                            enable_audio=False,
                            image_format_group=fc.ImageFormatGroup.JPEG,
                        )
                        try:
                            await self.camera_widget.lock_capture_orientation(ft.DeviceOrientation.PORTRAIT_UP)
                        except Exception:
                            pass

                        self.is_flet_cam_active = True
                        if self.camera_placeholder_icon:
                            self.camera_placeholder_icon.visible = False
                        if self.camera_widget:
                            self.camera_widget.visible = True
                        if self.camera_image:
                            self.camera_image.visible = False
                        try:
                            self.page.update()
                        except Exception:
                            pass
                        return
                except Exception as e:
                    print(f"fc.Camera não pôde ser iniciado diretamente: {e}")
                    self.is_flet_cam_active = False

                # Fallback para stream OpenCV em ambiente Desktop
                self.start_desktop_camera()

            if hasattr(self.page, "run_task"):
                self.page.run_task(_init_mobile)
            elif self.page and hasattr(self.page, "loop") and self.page.loop:
                asyncio.run_coroutine_threadsafe(_init_mobile(), self.page.loop)
            else:
                self.start_desktop_camera()
        else:
            self.start_desktop_camera()

    def start_desktop_camera(self):
        """Inicia OpenCV VideoCapture para uso em computador (Windows/Linux/Mac)."""
        def on_new_frame(data_uri: str):
            if not self.camera_image or self.is_frame_updating:
                return
            try:
                if self.camera_image.page:
                    self.is_frame_updating = True
                    self.camera_image.src = data_uri
                    if not self.camera_image.visible:
                        self.camera_image.visible = True
                    if self.camera_placeholder_icon and self.camera_placeholder_icon.visible:
                        self.camera_placeholder_icon.visible = False
                    self.camera_image.update()
            except RuntimeError:
                pass
            finally:
                self.is_frame_updating = False

        self.service.start(on_new_frame)

    def stop_camera(self):
        """Para a câmera e libera hardware de forma segura."""
        self.service.stop()

    def toggle_camera_facing(self):
        """Alterna entre câmera frontal e traseira no celular e desktop."""
        if self.is_flet_cam_active and self.camera_widget:
            async def _switch():
                self.camera_facing = "front" if self.camera_facing == "back" else "back"
                target = self.front_camera if self.camera_facing == "front" else self.back_camera
                if not target and self.available_cameras:
                    idx = 1 if (self.camera_facing == "front" and len(self.available_cameras) > 1) else 0
                    target = self.available_cameras[idx]
                if target:
                    try:
                        await self.camera_widget.initialize(
                            description=target,
                            resolution_preset=fc.ResolutionPreset.MEDIUM,
                            enable_audio=False,
                            image_format_group=fc.ImageFormatGroup.JPEG,
                        )
                        try:
                            await self.camera_widget.lock_capture_orientation(ft.DeviceOrientation.PORTRAIT_UP)
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"Erro ao alternar câmera frontal/traseira: {e}")
                try:
                    self.page.update()
                except Exception:
                    pass

            if hasattr(self.page, "run_task"):
                self.page.run_task(_switch)
            elif self.page and hasattr(self.page, "loop") and self.page.loop:
                asyncio.run_coroutine_threadsafe(_switch(), self.page.loop)
        else:
            self.camera_facing = self.service.toggle_facing()
            self.stop_camera()
            self.start_desktop_camera()

    def sample_point_at(self, local_x: float, local_y: float, is_final: bool = False):
        """Identifica a cor nas coordenadas especificadas."""
        self._last_drag_pos = (local_x, local_y)
        self.target_x = max(10.0, min(local_x, 350.0))
        self.target_y = max(10.0, min(local_y, 370.0))

        if self.is_flet_cam_active:
            cam_scale = 1.45
            unscaled_x = 142.5 + (self.target_x - 180.0) / cam_scale
            unscaled_y = 190.0 + (self.target_y - 190.0) / cam_scale
            norm_x = max(0.0, min(unscaled_x / 285.0, 1.0))
            norm_y = max(0.0, min(unscaled_y / 380.0, 1.0))
        else:
            norm_x = max(0.0, min(self.target_x / 360.0, 1.0))
            norm_y = max(0.0, min(self.target_y / 380.0, 1.0))

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
        self.target_x = max(10.0, min(local_x, 350.0))
        self.target_y = max(10.0, min(local_y, 370.0))

    def handle_tap_up(self, local_x: float, local_y: float):
        """Ao tocar na tela, captura a cor instantaneamente no ponto exato."""
        self.target_x = max(10.0, min(local_x, 350.0))
        self.target_y = max(10.0, min(local_y, 370.0))
        self._show_reticle_at(self.target_x, self.target_y)

        if self.is_flet_cam_active and self.camera_widget:
            async def _capture_and_sample():
                try:
                    img_bytes = await self.camera_widget.take_picture()
                    if img_bytes:
                        self.service.load_frame_bytes(img_bytes)
                except Exception as e:
                    print(f"Erro na captura ao vivo da câmera: {e}")

                self.sample_point_at(self.target_x, self.target_y, is_final=True)

            if hasattr(self.page, "run_task"):
                self.page.run_task(_capture_and_sample)
            elif self.page and hasattr(self.page, "loop") and self.page.loop:
                asyncio.run_coroutine_threadsafe(_capture_and_sample(), self.page.loop)
        else:
            self.sample_point_at(self.target_x, self.target_y, is_final=True)

    def handle_drag_point(self, local_x: float, local_y: float):
        now = time.time()
        if now - self._last_drag_time < 0.03 or self._is_drag_updating:
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
        if self.mode != "selecao":
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

        if self.is_flet_cam_active:
            cam_scale = 1.45
            norm_x0 = max(0.0, min((142.5 + (x0 - 180.0) / cam_scale) / 285.0, 1.0))
            norm_x1 = max(0.0, min((142.5 + (x1 - 180.0) / cam_scale) / 285.0, 1.0))
            norm_y0 = max(0.0, min((190.0 + (y0 - 190.0) / cam_scale) / 380.0, 1.0))
            norm_y1 = max(0.0, min((190.0 + (y1 - 190.0) / cam_scale) / 380.0, 1.0))
        else:
            norm_x0, norm_x1 = x0 / 360.0, x1 / 360.0
            norm_y0, norm_y1 = y0 / 380.0, y1 / 380.0

        if self.is_flet_cam_active and self.camera_widget:
            async def _capture_area():
                try:
                    img_bytes = await self.camera_widget.take_picture()
                    if img_bytes:
                        self.service.load_frame_bytes(img_bytes)
                except Exception as e:
                    print(f"Erro captura área: {e}")

                colors = self.service.sample_area(norm_x0, norm_y0, norm_x1, norm_y1)
                if colors:
                    self.has_selected_area = True
                    self.area_colors = colors
                    self._render_result_card()
                    try:
                        self.page.update()
                    except Exception:
                        pass

            if hasattr(self.page, "run_task"):
                self.page.run_task(_capture_area)
            elif self.page and hasattr(self.page, "loop") and self.page.loop:
                asyncio.run_coroutine_threadsafe(_capture_area(), self.page.loop)
        else:
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
        self.selection_box.width = min(360 - left, width)
        self.selection_box.height = min(380 - top, height)
        self.selection_box.visible = True
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
                "Toque no ponto para identificar a cor"
                if is_clique
                else "Segure e arraste para selecionar uma área"
            )

        self._render_result_card()
        try:
            self.page.update()
        except Exception:
            pass

    def _render_result_card(self):
        if not self.result_container:
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
                                    "Aponte a câmera e toque na tela para ler a cor exata.",
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
                                    "Selecione uma área",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    "Arraste sobre a tela para ver a proporção de cores.",
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


def CameraView(page: ft.Page) -> ft.View:
    """Retorna a tela de Câmera mobile e desktop em tempo real."""
    ctrl = CameraUIController(page)

    def navigate_away(route: str):
        ctrl.stop_camera()
        page.navigate(route)

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
                "IRIS / Câmera",
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
                "Câmera",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=COLOR_TEXT_PRIMARY,
            ),
            ft.Text(
                "Aponte para o objeto e toque para identificar a cor.",
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

    # Widget nativo de câmera mobile
    if HAS_FLET_CAMERA:
        try:
            ctrl.camera_widget = fc.Camera(
                expand=True,
                preview_enabled=True,
                visible=True,
            )
        except Exception:
            ctrl.camera_widget = None

    # Imagem fallback para stream desktop
    ctrl.camera_image = ft.Image(
        src="",
        width=360,
        height=380,
        fit=ft.BoxFit.COVER,
        gapless_playback=True,
        visible=False,
    )

    ctrl.camera_placeholder_icon = ft.Container(
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.VIDEOCAM_OUTLINED, color="#475569", size=48),
                ft.Text(
                    "Conectando câmera do celular...",
                    size=12,
                    color="#64748B",
                    weight=ft.FontWeight.W_500,
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
    top_badge = ft.Container(
        left=14,
        top=14,
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border_radius=14,
        bgcolor="#00000088",
        content=ft.Row(
            spacing=6,
            tight=True,
            controls=[
                ft.Icon(ft.Icons.SENSORS_ROUNDED, color="#FFFFFF", size=13),
                ctrl.badge_text,
            ],
        ),
    )

    ctrl.flip_button = ft.Container(
        right=14,
        top=14,
        width=38,
        height=38,
        border_radius=12,
        bgcolor="#00000088",
        alignment=ft.Alignment.CENTER,
        ink=True,
        on_click=lambda _: ctrl.toggle_camera_facing(),
        content=ft.Icon(
            ft.Icons.CAMERASWITCH_ROUNDED,
            color="#FFFFFF",
            size=20,
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
        "Toque no ponto para identificar a cor",
        size=11.5,
        color="#FFFFFF",
        weight=ft.FontWeight.W_400,
    )
    bottom_hint_pill = ft.Container(
        bottom=12,
        alignment=ft.Alignment.CENTER,
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

    gesture_layer = ft.GestureDetector(
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

    viewport_controls = [ctrl.camera_placeholder_icon]
    if ctrl.camera_widget:
        ctrl.camera_wrapper = ft.Container(
            left=0,
            top=0,
            right=0,
            bottom=0,
            alignment=ft.Alignment.CENTER,
            content=ft.Container(
                content=ctrl.camera_widget,
                scale=1.45,
                alignment=ft.Alignment.CENTER,
            ),
        )
        viewport_controls.append(ctrl.camera_wrapper)
    viewport_controls.extend([
        ctrl.camera_image,
        gesture_layer,
        top_badge,
        ctrl.flip_button,
        ctrl.target_ring,
        ctrl.selection_box,
        bottom_hint_pill,
    ])

    camera_viewport = ft.Container(
        height=380,
        border_radius=24,
        bgcolor="#0F172A",
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Stack(controls=viewport_controls),
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

    disclaimer = ft.Text(
        "Luz, sombras e reflexos podem alterar a leitura.",
        size=11,
        color=COLOR_TEXT_MUTED,
        text_align=ft.TextAlign.CENTER,
    )

    bottom_nav = build_bottom_nav(page, active_tab="camera")

    body_content = ft.Container(
        width=min(420, getattr(page, "width", 400) or 400),
        padding=ft.Padding.only(left=20, right=20, top=14, bottom=6),
        content=ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                header,
                title_section,
                mode_segmented_bar,
                camera_viewport,
                ctrl.result_container,
                disclaimer,
            ],
        ),
    )

    # Inicia a câmera
    ctrl.start_camera()

    return ft.View(
        route="/camera",
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
