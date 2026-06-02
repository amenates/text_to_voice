import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import re
import numpy as np
import torch
import soundfile as sf
from pathlib import Path

# --- НАСТРОЙКИ ИЗ ВАШЕГО СКРИПТА ---
MAX_LEN = 900
SAMPLE_RATE = 48000
SPEAKER = "eugene"


def split_text(text, max_len=MAX_LEN):
    chunks = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    for paragraph in paragraphs:
        if len(paragraph) <= max_len:
            chunks.append(paragraph)
            continue

        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_len:
                current += sentence + " "
                continue

            if current:
                chunks.append(current.strip())

            if len(sentence) > max_len:
                parts = sentence.split(",")
                current2 = ""

                for part in parts:
                    if len(current2) + len(part) + 1 <= max_len:
                        current2 += part + ","
                    else:
                        if current2:
                            chunks.append(current2.rstrip(","))

                        if len(part) > max_len:
                            for i in range(0, len(part), max_len):
                                chunks.append(part[i:i + max_len])
                            current2 = ""
                        else:
                            current2 = part + ","

                current = current2
            else:
                current = sentence + " "

        if current.strip():
            chunks.append(current.strip())

    return chunks


# --- ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ---
class TTSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎙️ Silero TTS Конвертер")
        self.geometry("550x400")
        self.resizable(False, False)

        self.file_path = ""
        self.model = None

        # Настройка темы
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.create_widgets()

        # Запускаем загрузку модели в фоновом потоке сразу после отрисовки окна
        self.after(100, self.load_model_background)

    def create_widgets(self):
        self.title_label = ctk.CTkLabel(self, text="🎙️ Конвертер текста в речь (Silero)", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=15)

        self.select_btn = ctk.CTkButton(self, text="📂 Выбрать TXT файл", command=self.select_file)
        self.select_btn.pack(pady=10)

        self.file_label = ctk.CTkLabel(self, text="Файл не выбран", text_color="gray", wraplength=450)
        self.file_label.pack(pady=5)

        # Прогресс-бар (изначально скрыт)
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0)
        self.progress.pack(pady=15)
        self.progress.pack_forget()

        self.convert_btn = ctk.CTkButton(self, text="🔄 Конвертировать в аудио", command=self.start_conversion,
                                         state="disabled")
        self.convert_btn.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="⏳ Загрузка нейросети...", text_color="orange",
                                         font=("Arial", 12, "bold"))
        self.status_label.pack(pady=10)

    def load_model_background(self):
        """Загружает модель в отдельном потоке, чтобы не замораживать интерфейс"""
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        try:
            self.model, _ = torch.hub.load(
                'snakers4/silero-models',
                'silero_tts',
                language='ru',
                speaker='v5_5_ru',
                trust_repo=True
            )
            # Обновляем GUI из основного потока
            self.after(0, lambda: self.status_label.configure(text="✅ Модель загружена. Готов к работе!",
                                                              text_color="green"))
            self.after(0, lambda: self.convert_btn.configure(state="normal"))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"❌ Ошибка загрузки модели: {e}", text_color="red"))

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path = file_path
            file_name = os.path.basename(file_path)
            self.file_label.configure(text=f"Выбран: {file_name}", text_color="white")
            if self.model is not None:
                self.convert_btn.configure(state="normal")
            self.status_label.configure(text="Готов к конвертации", text_color="gray")

    def start_conversion(self):
        if not self.file_path or self.model is None:
            return

        # Блокируем кнопку и показываем прогресс-бар
        self.convert_btn.configure(state="disabled")
        self.progress.pack(pady=15)
        self.status_label.configure(text="⏳ Обработка текста...", text_color="orange")

        # Запускаем тяжелую задачу в фоновом потоке
        threading.Thread(target=self._convert_process, daemon=True).start()

    def _convert_process(self):
        try:
            # 1. Чтение файла
            with open(self.file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()

            if not text:
                self.after(0, lambda: self.show_error("Файл пуст!"))
                return

            # 2. Разбивка на чанки
            chunks = split_text(text)
            total_chunks = len(chunks)

            self.after(0, lambda: self.status_label.configure(
                text=f"⏳ Найдено фрагментов: {total_chunks}. Начинаю озвучку...", text_color="orange"))

            audio_parts = []

            # 3. Озвучивание по частям
            for i, chunk in enumerate(chunks, start=1):
                # Обновляем прогресс-бар и текст (безопасно из потока)
                progress_val = i / total_chunks
                self.after(0, lambda p=progress_val, idx=i, tot=total_chunks: self.update_progress(p,
                                                                                                   f"Озвучивание: {idx}/{tot}"))

                audio = self.model.apply_tts(
                    text=chunk,
                    speaker=SPEAKER,
                    sample_rate=SAMPLE_RATE
                )
                audio_parts.append(audio)
                # Пауза 0.4 сек
                audio_parts.append(np.zeros(int(SAMPLE_RATE * 0.4)))

            # 4. Склейка и сохранение
            self.after(0, lambda: self.status_label.configure(text="💾 Сохранение файла...", text_color="orange"))
            result = np.concatenate(audio_parts)

            wav_file = Path(self.file_path).with_suffix('.wav')
            sf.write(str(wav_file), result, SAMPLE_RATE)

            # 5. Успешное завершение
            self.after(0, lambda: self.on_success(str(wav_file)))

        except Exception as e:
            self.after(0, lambda: self.show_error(str(e)))

    def update_progress(self, value, text):
        self.progress.set(value)
        self.status_label.configure(text=text)

    def on_success(self, filepath):
        self.progress.pack_forget()  # Скрываем прогресс-бар
        self.convert_btn.configure(state="normal")
        self.status_label.configure(text="✅ Готово!", text_color="green")
        messagebox.showinfo("Успех", f"Аудиофайл успешно создан:\n{filepath}")

    def show_error(self, error_msg):
        self.progress.pack_forget()
        self.convert_btn.configure(state="normal")
        self.status_label.configure(text="❌ Произошла ошибка", text_color="red")
        messagebox.showerror("Ошибка", f"Не удалось конвертировать файл:\n{error_msg}")


if __name__ == "__main__":
    app = TTSApp()
    app.mainloop()