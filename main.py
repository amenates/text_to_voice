import torch
import soundfile as sf
from pathlib import Path

# Загружаем модель
model, _ = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='v5_5_ru'
)

for txt_file in Path('journal').glob('*.txt'):
    with open(txt_file, 'r', encoding='utf-8') as f:
        text = f.read()

    audio = model.apply_tts(
        text=text,
        speaker='eugene',
        sample_rate=48000
    )

    wav_file = txt_file.with_suffix('.wav')
    sf.write(str(wav_file), audio, 48000)

    print(f'Создан: {wav_file}')







# # Генерируем аудио
# audio = model.apply_tts(
#     text='''Мастерская группа Кограмат напоминает, что некоторые моменты правил проекта
# отличаются от привычных в страйкбольных и ролевых играх, поэтому знать эти правила
# обязательно всем участникам: игрокам, НПС, мутантам, фотографам и игротехам.''',
#     speaker='eugene',
#     sample_rate=48000
# )

# Сохраняем
# sf.write('test_eugene.wav', audio, 48000)