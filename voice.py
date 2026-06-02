import re
import numpy as np
import torch
import soundfile as sf
from pathlib import Path

MAX_LEN = 900
SAMPLE_RATE = 48000
SPEAKER = "eugene"


def split_text(text, max_len=MAX_LEN):
    chunks = []

    # Разбиваем на абзацы
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    for paragraph in paragraphs:

        # Если абзац помещается целиком
        if len(paragraph) <= max_len:
            chunks.append(paragraph)
            continue

        # Разбиваем на предложения
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)

        current = ""

        for sentence in sentences:

            if len(current) + len(sentence) + 1 <= max_len:
                current += sentence + " "
                continue

            if current:
                chunks.append(current.strip())

            # Если само предложение слишком длинное
            if len(sentence) > max_len:

                parts = sentence.split(",")

                current2 = ""

                for part in parts:

                    if len(current2) + len(part) + 1 <= max_len:
                        current2 += part + ","
                    else:
                        if current2:
                            chunks.append(current2.rstrip(","))

                        # Совсем крайний случай
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


# Загружаем модель
model, _ = torch.hub.load(
    'snakers4/silero-models',
    'silero_tts',
    language='ru',
    speaker='v5_5_ru',
    trust_repo=True,
    speed=0.7
)

# Читаем файлы из папки
for txt_file in Path('the_rules_of_dark_waters').glob('*.txt'):
    with open(txt_file, 'r', encoding='utf-8') as f:
        text = f.read()

    chunks = split_text(text)

    print(f"Получилось {len(chunks)} фрагментов")

    audio_parts = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"[{i}/{len(chunks)}] Озвучивание...")

        audio = model.apply_tts(
            text=chunk,
            speaker=SPEAKER,
            sample_rate=SAMPLE_RATE
        )

        audio_parts.append(audio)

        # Пауза между кусками
        audio_parts.append(np.zeros(int(SAMPLE_RATE * 0.4)))

    # Склеиваем
    result = np.concatenate(audio_parts)

    wav_file = txt_file.with_suffix('.wav')
    sf.write(str(wav_file), result, SAMPLE_RATE)

    print(f'Создан: {wav_file}')