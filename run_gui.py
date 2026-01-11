#!/usr/bin/env python3
"""
Точка входа для GUI приложения конечных автоматов
"""

import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Проверяем наличие необходимых библиотек
required_libraries = ['PyQt6', 'matplotlib', 'networkx']

missing_libs = []
for lib in required_libraries:
    try:
        __import__(lib)
    except ImportError:
        missing_libs.append(lib)

if missing_libs:
    print(f"Ошибка: отсутствуют необходимые библиотеки: {', '.join(missing_libs)}")
    print("Установите их с помощью команд:")
    print(f"pip install {' '.join(missing_libs)}")
    sys.exit(1)

try:
    from fsm_gui import main
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все файлы находятся в текущей директории:")
    print("  - fsm_gui.py")
    print("  - export_utils.py")
    print("  - fsm.py")
    print("  - console_view.py (опционально)")
    print("  - fsm_io.py (опционально)")
    sys.exit(1)

if __name__ == "__main__":
    main()