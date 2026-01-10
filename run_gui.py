#!/usr/bin/env python3
"""
Точка входа для GUI приложения конечных автоматов
"""

import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fsm_gui import main
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что все необходимые модули установлены:")
    print("pip install PyQt6 graphviz")
    sys.exit(1)

if __name__ == "__main__":
    main()