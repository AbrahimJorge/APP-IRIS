import os

_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_candidate_paths = [
    os.path.join(_base_dir, "assets", "colors.csv"),
    os.path.join(os.getcwd(), "assets", "colors.csv"),
    os.path.join("assets", "colors.csv"),
]

CSV_PATH = next((p for p in _candidate_paths if os.path.exists(p)), _candidate_paths[0])
GITHUB_URL = "https://raw.githubusercontent.com/codebrainz/color-names/master/output/colors.csv"