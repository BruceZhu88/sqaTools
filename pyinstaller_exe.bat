::pyinstaller --icon=static\images\sound_speaker_48px.ico --name=run run.py
::rd /s /q .\dist\
pyinstaller run_bruce.spec
::pause