import ctypes
import flet as ft

from theme import COLOR_BG
from views.home_view import HomeView
from views.camera_view import CameraView
from views.image_view import ImageView
from views.settings_view import SettingsView
from views.daltonism_test_view import DaltonismTestView
from services.i18n_service import I18nService

if hasattr(ctypes, "windll"):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main(page: ft.Page):
    i18n = I18nService.get_instance()

    page.title = i18n.t("app_title")
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = COLOR_BG

    if hasattr(page, "window") and page.window:
        try:
            page.window.icon = "assets/logo.png"
            page.window.width = 415
            page.window.height = 860
            page.window.min_width = 360
            page.window.min_height = 680
        except Exception:
            pass

    def route_change(e=None):
        page.views.clear()


        page.views.append(HomeView(page))


        if page.route == "/camera":
            page.views.append(CameraView(page))
        elif page.route == "/image":
            page.views.append(ImageView(page))
        elif page.route == "/settings":
            page.views.append(SettingsView(page))
        elif page.route == "/daltonism_test":
            page.views.append(DaltonismTestView(page))

        page.update()

    def view_pop(e: ft.ViewPopEvent):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.navigate(top_view.route)

    def on_app_close(e=None):
        try:
            from services.screen_service import ScreenFloatingService
            ScreenFloatingService.get_instance().shutdown()
        except Exception:
            pass

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.on_disconnect = on_app_close
    page.on_close = on_app_close

    def on_language_changed(lang):
        page.title = i18n.t("app_title")
        if hasattr(page, "loop") and page.loop:
            page.loop.call_soon_threadsafe(route_change)
        else:
            route_change()

    i18n.add_listener(on_language_changed)

    route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
