# reporter.py
from tqdm import tqdm


class ArchiveReporter:
    def __init__(self):
        self.optimize_pbar = None

    def start_optimization(self, total_files, total_size_kb):
        print(f"\nНайдено {total_files} изображений. Общий размер: {total_size_kb:.1f} KB")
        print("Оптимизация изображений...")
        self.optimize_pbar = tqdm(total=total_files, desc="Прогресс", unit="img")

    def update_optimize_progress(self):
        if self.optimize_pbar:
            self.optimize_pbar.update(1)

    def print_summary(self, original_size, optimized_size, zip_size):
        compression_ratio = (1 - optimized_size / original_size) * 100
        print("\n" + "=" * 50)
        print(f"ИТОГОВАЯ СТАТИСТИКА:")
        print(f"- Исходный размер: {original_size:.1f} KB")
        print(f"- После оптимизации: {optimized_size:.1f} KB")
        print(f"- Размер архива: {zip_size:.1f} KB")
        print(f"- Экономия: {compression_ratio:.1f}%")
        print("=" * 50)

    def close(self):
        if self.optimize_pbar:
            self.optimize_pbar.close()
