# Scrapbot Voice → Whisper → Claude Computer Use

Pipeline completo:

1. **Parrot Wake** — escucha el micrófono y activa el flujo con la wake word ("parrot").
2. **Whisper (OpenAI)** — transcribe el comando de voz.
3. **Claude Computer Use** — ejecuta acciones en tu computador mediante mouse, teclado y UI automation.

## Estructura

scrapbot.ia

|____main.py

|____requirements.txt

|____parrot.py

|____whisper.py

|____computer-use.py

|____README.md

|____utilities/

  |____install.sh

  |____main.sh

  |____update.sh




---

## Instalación

```bash
cd scrapbot.ia
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x utilities/*.sh
```

## Uso
```bash
source venv/bin/activate
./utilities/main.sh
```c

Cuando digas "parrot" se activa la escucha, captura tu comando y ejecuta la acción con Claude Computer Use.

## Créditos

Parrot Wake: sistema de detección simple basado en energy threshold.

Whisper: OpenAI API.

Claude Computer Use: Anthropic Tools.