DEBUG_SERVER = "http://127.0.0.1:8000/"
TEST_SERVER = "https://schedule-app-test.dokka2.duckdns.org/"
PROD_SERVER = "https://schedule.kodamaclass.com/"

BASE_URL = ""
MATERIALS_API = ""
API_COURSES_IDS = ""
API_GUIDES_ORDER = ""
API_GUIDE_UPLOAD = ""


def set_base_url(url: str):
    global BASE_URL, MATERIALS_API, API_COURSES_IDS, API_GUIDES_ORDER, API_GUIDE_UPLOAD

    BASE_URL = url
    MATERIALS_API = BASE_URL + "materials/api/"
    API_COURSES_IDS = MATERIALS_API + "courses-with-levels/"
    API_GUIDES_ORDER = MATERIALS_API + "level-guides/"
    API_GUIDE_UPLOAD = MATERIALS_API + "upload-guide/"
