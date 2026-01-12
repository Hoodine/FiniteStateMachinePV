import PyInstaller.__main__
import os
import shutil


def build_exe():
    # Удаляем предыдущие сборки
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # Аргументы PyInstaller
    args = [
        'run_gui.py',
        '--onefile',
        '--windowed',
        '--name=FSM_Designer',
        '--add-data=.;.',
        '--hidden-import=PyQt6.sip',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=matplotlib.backends.backend_qt5agg',
        '--hidden-import=matplotlib.backends.backend_qtagg',
        '--hidden-import=networkx',
        '--hidden-import=numpy',
        '--collect-all=matplotlib',
        '--collect-all=PyQt6',
        '--clean',
        '--noconsole',
    ]

    # Добавляем иконку если есть
    if os.path.exists('fsm_icon.ico'):
        args.append('--icon=fsm_icon.ico')

    PyInstaller.__main__.run(args)

    print("\n" + "=" * 50)
    print("Сборка завершена!")
    print(f"EXE файл: dist/FSM_Designer.exe")
    print("=" * 50)


if __name__ == '__main__':
    build_exe()