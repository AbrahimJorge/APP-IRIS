import random
import flet as ft
from theme import (
    COLOR_BG,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_PRIMARY,
    COLOR_ICON_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_HEADING,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_CHEVRON,
    COLOR_BORDER_SUBTLE,
)
from services.i18n_service import I18nService

ALL_ISHIHARA_PLATES = [
    # --- GRUPO 1: Demonstração / Controle (Placa 1) ---
    {
        "plate": 1,
        "group": "demo",
        "plate_file": "ishihara/plate_1.png",
        "normal": "12",
        "options_pt": ["12", "21", "Não consigo identificar"],
        "options_en": ["12", "21", "I can't identify"],
        "rg_answers": [],
        "protan_answers": [],
        "deutan_answers": [],
    },

    # --- GRUPO 2: Transformação (Placas 2 a 9) ---
    {
        "plate": 2,
        "group": "transformation",
        "plate_file": "ishihara/plate_2.png",
        "normal": "8",
        "options_pt": ["8", "3", "Não consigo identificar"],
        "options_en": ["8", "3", "I can't identify"],
        "rg_answers": ["3", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 3,
        "group": "transformation",
        "plate_file": "ishihara/plate_3.png",
        "normal": "6",
        "options_pt": ["6", "5", "Não consigo identificar"],
        "options_en": ["6", "5", "I can't identify"],
        "rg_answers": ["5", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 4,
        "group": "transformation",
        "plate_file": "ishihara/plate_4.png",
        "normal": "29",
        "options_pt": ["29", "70", "Não consigo identificar"],
        "options_en": ["29", "70", "I can't identify"],
        "rg_answers": ["70", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 5,
        "group": "transformation",
        "plate_file": "ishihara/plate_5.png",
        "normal": "57",
        "options_pt": ["57", "35", "Não consigo identificar"],
        "options_en": ["57", "35", "I can't identify"],
        "rg_answers": ["35", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 6,
        "group": "transformation",
        "plate_file": "ishihara/plate_6.png",
        "normal": "5",
        "options_pt": ["5", "2", "Não consigo identificar"],
        "options_en": ["5", "2", "I can't identify"],
        "rg_answers": ["2", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 7,
        "group": "transformation",
        "plate_file": "ishihara/plate_7.png",
        "normal": "3",
        "options_pt": ["3", "5", "Não consigo identificar"],
        "options_en": ["3", "5", "I can't identify"],
        "rg_answers": ["5", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 8,
        "group": "transformation",
        "plate_file": "ishihara/plate_8.png",
        "normal": "15",
        "options_pt": ["15", "17", "Não consigo identificar"],
        "options_en": ["15", "17", "I can't identify"],
        "rg_answers": ["17", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 9,
        "group": "transformation",
        "plate_file": "ishihara/plate_9.png",
        "normal": "74",
        "options_pt": ["74", "21", "Não consigo identificar"],
        "options_en": ["74", "21", "I can't identify"],
        "rg_answers": ["21", "Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },

    # --- GRUPO 3: Desaparecimento (Placas 10 a 17) ---
    {
        "plate": 10,
        "group": "vanishing",
        "plate_file": "ishihara/plate_10.png",
        "normal": "2",
        "options_pt": ["2", "7", "Não consigo identificar"],
        "options_en": ["2", "7", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 11,
        "group": "vanishing",
        "plate_file": "ishihara/plate_11.png",
        "normal": "6",
        "options_pt": ["6", "9", "Não consigo identificar"],
        "options_en": ["6", "9", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 12,
        "group": "vanishing",
        "plate_file": "ishihara/plate_12.png",
        "normal": "97",
        "options_pt": ["97", "47", "Não consigo identificar"],
        "options_en": ["97", "47", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 13,
        "group": "vanishing",
        "plate_file": "ishihara/plate_13.png",
        "normal": "45",
        "options_pt": ["45", "48", "Não consigo identificar"],
        "options_en": ["45", "48", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 14,
        "group": "vanishing",
        "plate_file": "ishihara/plate_14.png",
        "normal": "5",
        "options_pt": ["5", "8", "Não consigo identificar"],
        "options_en": ["5", "8", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 15,
        "group": "vanishing",
        "plate_file": "ishihara/plate_15.png",
        "normal": "7",
        "options_pt": ["7", "1", "Não consigo identificar"],
        "options_en": ["7", "1", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 16,
        "group": "vanishing",
        "plate_file": "ishihara/plate_16.png",
        "normal": "16",
        "options_pt": ["16", "18", "Não consigo identificar"],
        "options_en": ["16", "18", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 17,
        "group": "vanishing",
        "plate_file": "ishihara/plate_17.png",
        "normal": "73",
        "options_pt": ["73", "28", "Não consigo identificar"],
        "options_en": ["73", "28", "I can't identify"],
        "rg_answers": ["Não consigo identificar", "I can't identify"],
        "protan_answers": [],
        "deutan_answers": [],
    },

    # --- GRUPO 4: Ocultas (Placas 18 a 21) ---
    {
        "plate": 18,
        "group": "hidden",
        "plate_file": "ishihara/plate_18.png",
        "normal": "Não consigo identificar",
        "normal_en": "I can't identify",
        "options_pt": ["5", "8", "Não consigo identificar"],
        "options_en": ["5", "8", "I can't identify"],
        "rg_answers": ["5"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 19,
        "group": "hidden",
        "plate_file": "ishihara/plate_19.png",
        "normal": "Não consigo identificar",
        "normal_en": "I can't identify",
        "options_pt": ["2", "7", "Não consigo identificar"],
        "options_en": ["2", "7", "I can't identify"],
        "rg_answers": ["2"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 20,
        "group": "hidden",
        "plate_file": "ishihara/plate_20.png",
        "normal": "Não consigo identificar",
        "normal_en": "I can't identify",
        "options_pt": ["45", "48", "Não consigo identificar"],
        "options_en": ["45", "48", "I can't identify"],
        "rg_answers": ["45"],
        "protan_answers": [],
        "deutan_answers": [],
    },
    {
        "plate": 21,
        "group": "hidden",
        "plate_file": "ishihara/plate_21.png",
        "normal": "Não consigo identificar",
        "normal_en": "I can't identify",
        "options_pt": ["73", "28", "Não consigo identificar"],
        "options_en": ["73", "28", "I can't identify"],
        "rg_answers": ["73"],
        "protan_answers": [],
        "deutan_answers": [],
    },

    # --- GRUPO 5: Diagnóstico / Classificação Protan vs. Deutan (Placas 22 a 25) ---
    {
        "plate": 22,
        "group": "diagnostic",
        "plate_file": "ishihara/plate_22.png",
        "normal": "26",
        "options_pt": ["26", "Apenas o 6", "Apenas o 2", "Não consigo identificar"],
        "options_en": ["26", "Only 6", "Only 2", "I can't identify"],
        "rg_answers": ["Apenas o 6", "Apenas o 2", "Only 6", "Only 2", "Não consigo identificar", "I can't identify"],
        "protan_answers": ["Apenas o 6", "Only 6"],
        "deutan_answers": ["Apenas o 2", "Only 2"],
    },
    {
        "plate": 23,
        "group": "diagnostic",
        "plate_file": "ishihara/plate_23.png",
        "normal": "42",
        "options_pt": ["42", "Apenas o 2", "Apenas o 4", "Não consigo identificar"],
        "options_en": ["42", "Only 2", "Only 4", "I can't identify"],
        "rg_answers": ["Apenas o 2", "Apenas o 4", "Only 2", "Only 4", "Não consigo identificar", "I can't identify"],
        "protan_answers": ["Apenas o 2", "Only 2"],
        "deutan_answers": ["Apenas o 4", "Only 4"],
    },
    {
        "plate": 24,
        "group": "diagnostic",
        "plate_file": "ishihara/plate_24.png",
        "normal": "35",
        "options_pt": ["35", "Apenas o 5", "Apenas o 3", "Não consigo identificar"],
        "options_en": ["35", "Only 5", "Only 3", "I can't identify"],
        "rg_answers": ["Apenas o 5", "Apenas o 3", "Only 5", "Only 3", "Não consigo identificar", "I can't identify"],
        "protan_answers": ["Apenas o 5", "Only 5"],
        "deutan_answers": ["Apenas o 3", "Only 3"],
    },
    {
        "plate": 25,
        "group": "diagnostic",
        "plate_file": "ishihara/plate_25.png",
        "normal": "96",
        "options_pt": ["96", "Apenas o 6", "Apenas o 9", "Não consigo identificar"],
        "options_en": ["96", "Only 6", "Only 9", "I can't identify"],
        "rg_answers": ["Apenas o 6", "Apenas o 9", "Only 6", "Only 9", "Não consigo identificar", "I can't identify"],
        "protan_answers": ["Apenas o 6", "Only 6"],
        "deutan_answers": ["Apenas o 9", "Only 9"],
    },
]


def generate_test_questions() -> list:
    """
    Sorteia dinamicamente 10 pranchas balanceadas a partir do banco de 25 imagens:
    - 1 Prancha de Demonstração (Placa 1 - Controle)
    - 4 Pranchas de Transformação (sorteadas entre as 8 de transformação)
    - 3 Pranchas de Desaparecimento / Ocultas (sorteadas entre as 12)
    - 2 Pranchas de Diagnóstico Protan vs Deutan (sorteadas entre as 4)
    Total = exatamente 10 questões cientificamente balanceadas.
    """
    demo_pool = [q for q in ALL_ISHIHARA_PLATES if q["group"] == "demo"]
    trans_pool = [q for q in ALL_ISHIHARA_PLATES if q["group"] == "transformation"]
    vanish_pool = [q for q in ALL_ISHIHARA_PLATES if q["group"] in ("vanishing", "hidden")]
    diag_pool = [q for q in ALL_ISHIHARA_PLATES if q["group"] == "diagnostic"]

    selected = []
    selected.extend(demo_pool)
    selected.extend(random.sample(trans_pool, 4))
    selected.extend(random.sample(vanish_pool, 3))
    selected.extend(random.sample(diag_pool, 2))

    return selected


def evaluate_ishihara(questions: list, user_answers: dict) -> dict:
    """Calcula a avaliação diagnóstica com base nas 10 pranchas sorteadas."""
    normal_count = 0
    rg_count = 0
    protan_count = 0
    deutan_count = 0

    for i, q in enumerate(questions):
        ans = user_answers.get(i)
        normal_val = q.get("normal")
        normal_en = q.get("normal_en", normal_val)

        if ans in (normal_val, normal_en):
            normal_count += 1
        elif ans in q["rg_answers"]:
            rg_count += 1
            if ans in q["protan_answers"]:
                protan_count += 1
            elif ans in q["deutan_answers"]:
                deutan_count += 1

    total = len(questions)

    # Classificação diagnóstica
    if normal_count >= 8:
        category = "normal"
    elif rg_count >= 3 or normal_count <= 5:
        if protan_count > deutan_count:
            category = "protan"
        elif deutan_count > protan_count:
            category = "deutan"
        else:
            category = "rg"
    else:
        category = "inconclusive"

    return {
        "category": category,
        "normal_count": normal_count,
        "total": total,
        "rg_count": rg_count,
        "protan_count": protan_count,
        "deutan_count": deutan_count,
    }


def build_primary_btn(text: str, icon: str, on_click, width: int = None):
    return ft.Container(
        width=width,
        bgcolor=COLOR_PRIMARY,
        border_radius=13,
        padding=ft.Padding.symmetric(vertical=13, horizontal=16),
        alignment=ft.Alignment.CENTER,
        ink=True,
        on_click=on_click,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(icon, color="#FFFFFF", size=18),
                ft.Text(text, size=14, weight=ft.FontWeight.W_600, color="#FFFFFF"),
            ],
        ),
    )


def build_secondary_btn(text: str, icon: str, on_click, width: int = None):
    return ft.Container(
        width=width,
        bgcolor="#FFFFFF",
        border=ft.Border.all(1.2, COLOR_CARD_BORDER),
        border_radius=13,
        padding=ft.Padding.symmetric(vertical=13, horizontal=16),
        alignment=ft.Alignment.CENTER,
        ink=True,
        on_click=on_click,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(icon, color=COLOR_TEXT_PRIMARY, size=18),
                ft.Text(text, size=14, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
            ],
        ),
    )


def DaltonismTestView(page: ft.Page) -> ft.View:
    i18n = I18nService.get_instance()

    # Estado local do teste
    current_mode = ["MENU"]  # "MENU" | "TEST" | "RESULT"
    current_q = [0]
    active_questions = [generate_test_questions()]
    user_answers = {}
    test_result = [{}]

    main_column = ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def render():
        lang = i18n.get_language()
        mode = current_mode[0]
        main_column.controls.clear()

        if mode == "MENU":
            # --- 1. TELA PRINCIPAL: MENU DE TESTES ---
            top_bar = ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=12,
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
                        i18n.t("daltonism_breadcrumb"),
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color="#475569",
                    ),
                ],
            )

            title_section = ft.Column(
                spacing=4,
                controls=[
                    ft.Text(
                        i18n.t("daltonism_title"),
                        size=24,
                        weight=ft.FontWeight.W_700,
                        color=COLOR_TEXT_PRIMARY,
                    ),
                    ft.Text(
                        i18n.t("daltonism_subtitle"),
                        size=13,
                        color=COLOR_TEXT_MUTED,
                    ),
                ],
            )

            # Card 1: Teste de Ishihara (Disponível agora)
            def on_start_ishihara(_):
                active_questions[0] = generate_test_questions()
                current_mode[0] = "TEST"
                current_q[0] = 0
                user_answers.clear()
                render()
                page.update()

            ishihara_card = ft.Container(
                bgcolor=COLOR_CARD_BG,
                border=ft.Border.all(1.5, COLOR_PRIMARY),
                border_radius=20,
                padding=ft.Padding.all(18),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color="#152563EB",
                    offset=ft.Offset(0, 3),
                ),
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Row(
                                    spacing=10,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            width=42,
                                            height=42,
                                            border_radius=12,
                                            bgcolor=COLOR_ICON_BG,
                                            alignment=ft.Alignment.CENTER,
                                            content=ft.Icon(
                                                ft.Icons.PALETTE_ROUNDED,
                                                color=COLOR_PRIMARY,
                                                size=22,
                                            ),
                                        ),
                                        ft.Text(
                                            i18n.t("ishihara_title"),
                                            size=16,
                                            weight=ft.FontWeight.W_700,
                                            color=COLOR_TEXT_PRIMARY,
                                        ),
                                    ],
                                ),
                                ft.Container(
                                    bgcolor="#DCFCE7",
                                    border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                    content=ft.Text(
                                        "ATIVO",
                                        size=10,
                                        weight=ft.FontWeight.W_700,
                                        color="#15803D",
                                    ),
                                ),
                            ],
                        ),
                        ft.Container(
                            bgcolor=COLOR_ICON_BG,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            content=ft.Text(
                                i18n.t("ishihara_badge"),
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_PRIMARY,
                            ),
                        ),
                        ft.Text(
                            i18n.t("ishihara_desc"),
                            size=12.5,
                            color=COLOR_TEXT_MUTED,
                            height=1.35,
                        ),
                        build_primary_btn(
                            text=i18n.t("ishihara_start_btn"),
                            icon=ft.Icons.PLAY_ARROW_ROUNDED,
                            on_click=on_start_ishihara,
                        ),
                    ],
                ),
            )

            # Card 2: Teste Farnsworth D-15 (Em breve)
            d15_card = ft.Container(
                bgcolor=COLOR_CARD_BG,
                border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                border_radius=18,
                padding=ft.Padding.all(16),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    i18n.t("test_future_d15_title"),
                                    size=14.5,
                                    weight=ft.FontWeight.W_600,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Container(
                                    bgcolor="#F1F5F9",
                                    border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    content=ft.Text(
                                        i18n.t("test_future_d15_badge"),
                                        size=10,
                                        weight=ft.FontWeight.W_600,
                                        color="#64748B",
                                    ),
                                ),
                            ],
                        ),
                        ft.Text(
                            i18n.t("test_future_d15_desc"),
                            size=12,
                            color=COLOR_TEXT_MUTED,
                            height=1.3,
                        ),
                    ],
                ),
            )

            # Card 3: Teste Tritan (Em breve)
            tritan_card = ft.Container(
                bgcolor=COLOR_CARD_BG,
                border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                border_radius=18,
                padding=ft.Padding.all(16),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    i18n.t("test_future_tritan_title"),
                                    size=14.5,
                                    weight=ft.FontWeight.W_600,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                                ft.Container(
                                    bgcolor="#F1F5F9",
                                    border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    content=ft.Text(
                                        i18n.t("test_future_tritan_badge"),
                                        size=10,
                                        weight=ft.FontWeight.W_600,
                                        color="#64748B",
                                    ),
                                ),
                            ],
                        ),
                        ft.Text(
                            i18n.t("test_future_tritan_desc"),
                            size=12,
                            color=COLOR_TEXT_MUTED,
                            height=1.3,
                        ),
                    ],
                ),
            )

            main_column.controls.extend([
                top_bar,
                title_section,
                ishihara_card,
                d15_card,
                tritan_card,
            ])

        elif mode == "TEST":
            # --- 2. TELA DE EXECUÇÃO: QUIZ ISHIHARA ---
            questions = active_questions[0]
            q_idx = current_q[0]
            q_data = questions[q_idx]
            total_q = len(questions)
            progress = (q_idx + 1) / total_q

            def on_exit_test(_):
                current_mode[0] = "MENU"
                render()
                page.update()

            top_bar = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        icon_color=COLOR_TEXT_PRIMARY,
                        icon_size=20,
                        on_click=on_exit_test,
                        tooltip="Cancelar teste",
                    ),
                    ft.Container(
                        bgcolor=COLOR_ICON_BG,
                        border_radius=10,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        content=ft.Text(
                            i18n.t("ishihara_question_counter").format(current=q_idx + 1, total=total_q),
                            size=12.5,
                            weight=ft.FontWeight.W_700,
                            color=COLOR_PRIMARY,
                        ),
                    ),
                ],
            )

            # Barra de progresso linear
            progress_bar = ft.ProgressBar(
                value=progress,
                color=COLOR_PRIMARY,
                bgcolor="#E2E8F0",
                height=6,
                border_radius=3,
            )

            # Imagem da placa de Ishihara
            plate_img = ft.Container(
                bgcolor="#FFFFFF",
                border_radius=20,
                border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                padding=ft.Padding.all(12),
                alignment=ft.Alignment.CENTER,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color="#08000000",
                    offset=ft.Offset(0, 2),
                ),
                content=ft.Image(
                    src=q_data["plate_file"],
                    width=230,
                    height=230,
                    fit=ft.BoxFit.CONTAIN,
                ),
            )

            prompt_text = ft.Text(
                i18n.t("ishihara_question_prompt"),
                size=15,
                weight=ft.FontWeight.W_600,
                color=COLOR_TEXT_PRIMARY,
                text_align=ft.TextAlign.CENTER,
            )

            # Botões de opção
            options = q_data["options_en"] if lang == "en" else q_data["options_pt"]

            def make_option_btn(opt_text):
                def on_select_option(_):
                    user_answers[q_idx] = opt_text
                    if q_idx + 1 < total_q:
                        current_q[0] += 1
                        render()
                        page.update()
                    else:
                        test_result[0] = evaluate_ishihara(questions, user_answers)
                        current_mode[0] = "RESULT"
                        render()
                        page.update()

                return ft.Container(
                    width=380,
                    bgcolor=COLOR_CARD_BG,
                    border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                    border_radius=14,
                    padding=ft.Padding.symmetric(horizontal=18, vertical=13),
                    ink=True,
                    on_click=on_select_option,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=4,
                        color="#05000000",
                        offset=ft.Offset(0, 1),
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                opt_text,
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_TEXT_PRIMARY,
                            ),
                            ft.Icon(
                                ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                                size=18,
                                color=COLOR_TEXT_MUTED,
                            ),
                        ],
                    ),
                )

            options_column = ft.Column(
                spacing=9,
                controls=[make_option_btn(opt) for opt in options],
            )

            main_column.controls.extend([
                top_bar,
                progress_bar,
                plate_img,
                prompt_text,
                options_column,
            ])

        elif mode == "RESULT":
            # --- 3. TELA DE RESULTADO / DIAGNÓSTICO ---
            res = test_result[0]
            cat = res.get("category", "inconclusive")

            if cat == "normal":
                res_title = i18n.t("ishihara_result_normal_title")
                res_desc = i18n.t("ishihara_result_normal_desc")
                res_icon = ft.Icons.CHECK_CIRCLE_ROUNDED
                res_icon_color = "#059669"
                res_icon_bg = "#ECFDF5"
            elif cat == "protan":
                res_title = i18n.t("ishihara_result_protan_title")
                res_desc = i18n.t("ishihara_result_protan_desc")
                res_icon = ft.Icons.VISIBILITY_ROUNDED
                res_icon_color = "#D97706"
                res_icon_bg = "#FEF3C7"
            elif cat == "deutan":
                res_title = i18n.t("ishihara_result_deutan_title")
                res_desc = i18n.t("ishihara_result_deutan_desc")
                res_icon = ft.Icons.VISIBILITY_ROUNDED
                res_icon_color = "#2563EB"
                res_icon_bg = "#EFF6FF"
            elif cat == "rg":
                res_title = i18n.t("ishihara_result_rg_title")
                res_desc = i18n.t("ishihara_result_rg_desc")
                res_icon = ft.Icons.INFO_ROUNDED
                res_icon_color = "#EA580C"
                res_icon_bg = "#FFF7ED"
            else:
                res_title = i18n.t("ishihara_result_inconclusive_title")
                res_desc = i18n.t("ishihara_result_inconclusive_desc")
                res_icon = ft.Icons.HELP_OUTLINE_ROUNDED
                res_icon_color = "#64748B"
                res_icon_bg = "#F1F5F9"

            top_bar = ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=12,
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
                        i18n.t("ishihara_result_title"),
                        size=15,
                        weight=ft.FontWeight.W_700,
                        color=COLOR_TEXT_PRIMARY,
                    ),
                ],
            )

            # Hero Card de Diagnóstico
            hero_result = ft.Container(
                bgcolor=COLOR_CARD_BG,
                border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                border_radius=20,
                padding=ft.Padding.all(20),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color="#08000000",
                    offset=ft.Offset(0, 3),
                ),
                content=ft.Column(
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=60,
                            height=60,
                            border_radius=30,
                            bgcolor=res_icon_bg,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(res_icon, color=res_icon_color, size=32),
                        ),
                        ft.Text(
                            res_title,
                            size=17,
                            weight=ft.FontWeight.W_700,
                            color=COLOR_TEXT_PRIMARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(
                            bgcolor="#F8FAFC",
                            border_radius=10,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                            border=ft.Border.all(1, COLOR_BORDER_SUBTLE),
                            content=ft.Text(
                                f"Respostas padrão: {res.get('normal_count', 0)} / {res.get('total', 10)}",
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_TEXT_MUTED,
                            ),
                        ),
                        ft.Text(
                            res_desc,
                            size=13,
                            color=COLOR_TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                            height=1.4,
                        ),
                    ],
                ),
            )

            # Tabela de Escopo e Limitações do Ishihara
            def make_scope_row(condition, detectable, note):
                badge_bg = "#DCFCE7" if detectable == "Sim" else ("#FEF3C7" if detectable == "Parcialmente" else "#F1F5F9")
                badge_color = "#15803D" if detectable == "Sim" else ("#B45309" if detectable == "Parcialmente" else "#64748B")

                return ft.Container(
                    padding=ft.Padding.symmetric(vertical=6),
                    border=ft.Border(bottom=ft.BorderSide(1, "#F1F5F9")),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(condition, size=12.5, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
                                    ft.Text(note, size=11, color=COLOR_TEXT_MUTED),
                                ],
                            ),
                            ft.Container(
                                bgcolor=badge_bg,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                content=ft.Text(
                                    detectable,
                                    size=10.5,
                                    weight=ft.FontWeight.W_700,
                                    color=badge_color,
                                ),
                            ),
                        ],
                    ),
                )

            scope_card = ft.Container(
                bgcolor=COLOR_CARD_BG,
                border=ft.Border.all(1.2, COLOR_CARD_BORDER),
                border_radius=18,
                padding=ft.Padding.all(16),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, size=18, color=COLOR_PRIMARY),
                                ft.Text(
                                    i18n.t("ishihara_scope_title"),
                                    size=13.5,
                                    weight=ft.FontWeight.W_700,
                                    color=COLOR_TEXT_PRIMARY,
                                ),
                            ],
                        ),
                        ft.Container(height=4),
                        make_scope_row("Visão cromática normal", "Sim", "Sem alteração no eixo vermelho-verde"),
                        make_scope_row("Deficiência vermelho-verde", "Sim", "Finalidade principal do exame"),
                        make_scope_row("Protanopia / Protanomalia", "Parcialmente", "Indica tendência ao vermelho"),
                        make_scope_row("Deuteranopia / Deuteranomalia", "Parcialmente", "Indica tendência ao verde"),
                        make_scope_row("Tritanopia (Azul-Amarelo)", "Não", "Será incluído em teste futuro"),
                        make_scope_row("Acromatopsia", "Não", "Requer avaliação médica avançada"),
                    ],
                ),
            )

            # Aviso de Responsabilidade Médica
            medical_notice = ft.Container(
                bgcolor="#FFFBEB",
                border=ft.Border.all(1.2, "#FDE68A"),
                border_radius=16,
                padding=ft.Padding.all(14),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Icon(ft.Icons.MEDICAL_INFORMATION_ROUNDED, color="#D97706", size=22),
                        ft.Text(
                            i18n.t("ishihara_medical_disclaimer"),
                            size=11.5,
                            color="#92400E",
                            height=1.35,
                            expand=True,
                        ),
                    ],
                ),
            )

            # Botões de Ação
            def on_retake(_):
                active_questions[0] = generate_test_questions()
                current_mode[0] = "TEST"
                current_q[0] = 0
                user_answers.clear()
                render()
                page.update()

            def on_finish(_):
                current_mode[0] = "MENU"
                render()
                page.update()

            action_buttons = ft.Column(
                spacing=10,
                controls=[
                    build_secondary_btn(
                        text=i18n.t("ishihara_btn_retake"),
                        icon=ft.Icons.REFRESH_ROUNDED,
                        on_click=on_retake,
                        width=380,
                    ),
                    build_primary_btn(
                        text=i18n.t("ishihara_btn_finish"),
                        icon=ft.Icons.CHECK_ROUNDED,
                        on_click=on_finish,
                        width=380,
                    ),
                ],
            )

            main_column.controls.extend([
                top_bar,
                hero_result,
                scope_card,
                medical_notice,
                action_buttons,
            ])

    # Constrói a visualização
    render()

    return ft.View(
        route="/daltonism_test",
        bgcolor=COLOR_BG,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                width=400,
                padding=ft.Padding.only(left=16, right=16, top=16, bottom=28),
                content=main_column,
            )
        ],
    )
