import os
import shutil
import subprocess
from datetime import datetime

# Название итогового exe
APP_NAME = "GuideUploader"
ICON_FILE = "icon.ico"
ENTRY_FILE = "gui_app.py"

# Папка, куда будет складываться билд
DIST_DIR = "dist"
BUILD_DIR = "build"


def clean_old_builds():
    """Удаляем старые сборки перед новым билдом"""
    for folder in [DIST_DIR, BUILD_DIR, f"{APP_NAME}.spec"]:
        if os.path.exists(folder):
            print(f"🧹 Удаляю {folder} ...")
            if os.path.isdir(folder):
                shutil.rmtree(folder)
            else:
                os.remove(folder)
    print("✅ Очистка завершена.\n")


def build_exe():
    """Собираем exe через PyInstaller"""
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        f"--icon={ICON_FILE}",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--add-data", "api_config.txt;.",
        "--add-data", "service_account.json;.",
        "--clean",
        ENTRY_FILE,
    ]

    print("🚀 Запускаю PyInstaller...\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ Сборка успешно завершена!")
        dist_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
        if os.path.exists(dist_path):
            new_name = f"{APP_NAME}.exe"
            new_path = os.path.join(DIST_DIR, new_name)
            os.rename(dist_path, new_path)
            print(f"📦 Файл сохранён как: {new_path}")
        else:
            print("⚠️ Внимание: .exe файл не найден в dist/")
    else:
        print("❌ Ошибка при сборке. Проверь логи выше.")


if __name__ == "__main__":
    print("=== 🏗️  Начинаю сборку GuideUploader ===\n")
    clean_old_builds()
    build_exe()
    print("\n=== ✅ Готово! ===")
