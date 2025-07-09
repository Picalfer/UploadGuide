import shutil
from pathlib import Path


def delete_path(path):
    if not path:
        return
    try:
        p = Path(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
    except Exception as e:
        print(f"⚠️ Не удалось удалить {path}: {e}")
