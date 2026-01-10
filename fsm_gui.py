"""
PyQt6 GUI для работы с конечными автоматами
"""

import sys
import os
import subprocess
from typing import List, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QMessageBox, QGroupBox, QGridLayout,
    QComboBox, QCheckBox, QSplitter, QFileDialog, QStatusBar, QToolBar,
    QMenuBar, QMenu, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem,
    QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont, QColor, QPalette, QPixmap
from fsm import FiniteStateMachine, State, Transition


# КОПИРУЕМ ФУНКЦИЮ export_to_dot ИЗ main.py ПРЯМО СЮДА
def export_to_dot(fsm, filename: str = "finite_automaton.dot"):
    """
    Экспорт автомата в формат DOT для Graphviz
    ТОЧНАЯ КОПИЯ ИЗ main.py
    """
    if not fsm.states:
        print("Нечего экспортировать: автомат пуст")
        return

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("digraph finite_automaton {\n")
            f.write("    rankdir=LR;\n")
            f.write("    node [shape = circle];\n\n")

            # Добавляем невидимый узел для стрелки к начальному состоянию
            if fsm.start_state:
                f.write(f'    "" [shape = none];\n')
                f.write(f'    "" -> "{fsm.start_state.name}";\n\n')

            # Добавляем состояния
            for state_name, state in fsm.states.items():
                if state.is_final:
                    f.write(f'    "{state_name}" [shape = doublecircle];\n')
                else:
                    f.write(f'    "{state_name}" [shape = circle];\n')

            f.write("\n")

            # Добавляем переходы
            transitions_added = set()
            for state_name, state in fsm.states.items():
                for transition in state.out_transitions:
                    # Проверяем, не добавляли ли уже этот переход
                    trans_key = (transition.from_state, transition.to_state, transition.symbol)
                    if trans_key not in transitions_added:
                        label = f'label = "{transition.symbol}"'
                        if transition.symbol == 'epsilon':
                            label = 'label = "epsilon"'

                        f.write(f'    "{transition.from_state}" -> "{transition.to_state}" [{label}];\n')
                        transitions_added.add(trans_key)

            f.write("}\n")

        print(f"Автомат успешно экспортирован в файл: {filename}")

        # ГЕНЕРИРУЕМ PNG ПРЯМО ЗДЕСЬ КАК В КОНСОЛЬНОЙ ВЕРСИИ
        png_filename = filename.replace('.dot', '.png')
        try:
            subprocess.run(f'dot -Tpng "{filename}" -o "{png_filename}"',
                          shell=True, check=True, capture_output=True, text=True)
            print(f"PNG схема создана: {png_filename}")
            return png_filename  # ВОЗВРАЩАЕМ ИМЯ PNG ФАЙЛА
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при создании PNG: {e.stderr}")
            print(f"Для визуализации используйте команду вручную:")
            print(f"  dot -Tpng {filename} -o {png_filename}")
            return None

    except Exception as e:
        print(f"Ошибка при экспорте: {e}")
        return None


class AddStateDialog(QDialog):
    """Диалог добавления нового состояния"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить состояние")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Имя состояния:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: q0, s1, A")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        self.start_checkbox = QCheckBox("Стартовое состояние")
        self.final_checkbox = QCheckBox("Конечное состояние")
        layout.addWidget(self.start_checkbox)
        layout.addWidget(self.final_checkbox)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_state_data(self):
        return {
            'name': self.name_input.text().strip(),
            'is_start': self.start_checkbox.isChecked(),
            'is_final': self.final_checkbox.isChecked()
        }


class AddTransitionDialog(QDialog):
    """Диалог добавления перехода"""
    def __init__(self, state_names: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить переход")
        self.setModal(True)
        self.setup_ui(state_names)

    def setup_ui(self, state_names: List[str]):
        layout = QGridLayout()

        layout.addWidget(QLabel("Из состояния:"), 0, 0)
        self.from_combo = QComboBox()
        self.from_combo.addItems(state_names)
        layout.addWidget(self.from_combo, 0, 1)

        layout.addWidget(QLabel("Символ:"), 1, 0)
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("a, b, ε, ...")
        layout.addWidget(self.symbol_input, 1, 1)

        layout.addWidget(QLabel("В состояние:"), 2, 0)
        self.to_combo = QComboBox()
        self.to_combo.addItems(state_names)
        layout.addWidget(self.to_combo, 2, 1)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box, 3, 0, 1, 2)

        self.setLayout(layout)

    def get_transition_data(self):
        return {
            'from_state': self.from_combo.currentText(),
            'symbol': self.symbol_input.text().strip(),
            'to_state': self.to_combo.currentText()
        }


class ImageViewer(QWidget):
    """Виджет для отображения изображения схемы"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_image_path = None

    def setup_ui(self):
        layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.image_container = QLabel()
        self.image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_container.setMinimumSize(600, 400)
        self.image_container.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        self.scroll_area.setWidget(self.image_container)
        layout.addWidget(self.scroll_area)

        self.info_label = QLabel("Схема автомата будет отображаться здесь после экспорта")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("padding: 10px; color: #666;")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def load_image(self, image_path):
        """Загрузить изображение из файла"""
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.image_container.setPixmap(pixmap)
                self.info_label.setText(f"Схема загружена: {os.path.basename(image_path)}")
                self.info_label.setStyleSheet("padding: 10px; color: green;")
                self.current_image_path = image_path
                return True
            else:
                self.info_label.setText("Ошибка загрузки изображения")
                self.info_label.setStyleSheet("padding: 10px; color: red;")
        else:
            self.info_label.setText(f"Файл не найден: {os.path.basename(image_path)}")
            self.info_label.setStyleSheet("padding: 10px; color: orange;")

        self.current_image_path = None
        self.image_container.clear()
        return False

    def clear(self):
        """Очистить изображение"""
        self.image_container.clear()
        self.info_label.setText("Схема автомата будет отображаться здесь после экспорта")
        self.info_label.setStyleSheet("padding: 10px; color: #666;")
        self.current_image_path = None


class FSMMainWindow(QMainWindow):
    """Главное окно приложения"""
    def __init__(self):
        super().__init__()
        self.fsm = FiniteStateMachine()
        self.current_image_path = None
        self.setup_ui()
        self.setWindowTitle("Finite State Machine Designer")
        self.setGeometry(100, 100, 1200, 700)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая панель
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # Правая панель
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        self.image_viewer = ImageViewer()
        right_splitter.addWidget(self.image_viewer)

        self.info_tabs = QTabWidget()
        self.setup_info_tabs()
        right_splitter.addWidget(self.info_tabs)

        right_splitter.setSizes([400, 200])
        main_layout.addWidget(right_splitter, 3)

        self.create_menu()
        self.create_toolbar()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

    def create_left_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)

        # Состояния
        states_group = QGroupBox("Состояния")
        states_layout = QVBoxLayout()

        self.states_list = QListWidget()
        states_layout.addWidget(self.states_list)

        states_buttons = QHBoxLayout()
        self.add_state_btn = QPushButton("Добавить")
        self.add_state_btn.clicked.connect(self.add_state)
        self.remove_state_btn = QPushButton("Удалить")
        self.remove_state_btn.clicked.connect(self.remove_state)
        states_buttons.addWidget(self.add_state_btn)
        states_buttons.addWidget(self.remove_state_btn)
        states_layout.addLayout(states_buttons)

        states_group.setLayout(states_layout)
        layout.addWidget(states_group)

        # Переходы
        transitions_group = QGroupBox("Переходы")
        transitions_layout = QVBoxLayout()

        self.transitions_list = QListWidget()
        transitions_layout.addWidget(self.transitions_list)

        transitions_buttons = QHBoxLayout()
        self.add_transition_btn = QPushButton("Добавить")
        self.add_transition_btn.clicked.connect(self.add_transition)
        self.remove_transition_btn = QPushButton("Удалить")
        self.remove_transition_btn.clicked.connect(self.remove_transition)
        transitions_buttons.addWidget(self.add_transition_btn)
        transitions_buttons.addWidget(self.remove_transition_btn)
        transitions_layout.addLayout(transitions_buttons)

        transitions_group.setLayout(transitions_layout)
        layout.addWidget(transitions_group)

        # Алфавит
        alphabet_group = QGroupBox("Алфавит")
        alphabet_layout = QVBoxLayout()
        self.alphabet_list = QListWidget()
        alphabet_layout.addWidget(self.alphabet_list)
        alphabet_group.setLayout(alphabet_layout)
        layout.addWidget(alphabet_group)

        # Действия
        actions_group = QGroupBox("Действия")
        actions_layout = QVBoxLayout()

        self.validate_btn = QPushButton("Валидация")
        self.validate_btn.clicked.connect(self.validate_fsm)
        actions_layout.addWidget(self.validate_btn)

        self.export_btn = QPushButton("Экспорт схемы (PNG)")
        self.export_btn.clicked.connect(self.export_scheme)
        self.export_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        actions_layout.addWidget(self.export_btn)

        self.load_image_btn = QPushButton("Загрузить схему")
        self.load_image_btn.clicked.connect(self.load_scheme)
        actions_layout.addWidget(self.load_image_btn)

        self.test_fsm_btn = QPushButton("Тестовый автомат")
        self.test_fsm_btn.clicked.connect(self.create_test_fsm)
        actions_layout.addWidget(self.test_fsm_btn)

        self.clear_btn = QPushButton("Очистить всё")
        self.clear_btn.clicked.connect(self.clear_fsm)
        actions_layout.addWidget(self.clear_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()
        return panel

    def setup_info_tabs(self):
        self.matrix_widget = QTableWidget()
        self.info_tabs.addTab(self.matrix_widget, "Матрица смежности")

        self.table_widget = QTableWidget()
        self.info_tabs.addTab(self.table_widget, "Таблица переходов")

        self.summary_widget = QTextEdit()
        self.summary_widget.setReadOnly(True)
        self.info_tabs.addTab(self.summary_widget, "Сводная информация")

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")

        new_action = QAction("Новый автомат", self)
        new_action.triggered.connect(self.clear_fsm)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        export_action = QAction("Экспорт схемы (PNG)...", self)
        export_action.triggered.connect(self.export_scheme)
        file_menu.addAction(export_action)

        load_image_action = QAction("Загрузить схему...", self)
        load_image_action.triggered.connect(self.load_scheme)
        file_menu.addAction(load_image_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("Правка")

        add_state_action = QAction("Добавить состояние...", self)
        add_state_action.triggered.connect(self.add_state)
        edit_menu.addAction(add_state_action)

        add_transition_action = QAction("Добавить переход...", self)
        add_transition_action.triggered.connect(self.add_transition)
        edit_menu.addAction(add_transition_action)

        edit_menu.addSeparator()

        validate_action = QAction("Валидировать автомат", self)
        validate_action.triggered.connect(self.validate_fsm)
        edit_menu.addAction(validate_action)

        help_menu = menubar.addMenu("Помощь")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Основные инструменты")
        self.addToolBar(toolbar)

        new_action = QAction("Новый", self)
        new_action.triggered.connect(self.clear_fsm)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        add_state_action = QAction("Состояние", self)
        add_state_action.triggered.connect(self.add_state)
        toolbar.addAction(add_state_action)

        add_transition_action = QAction("Переход", self)
        add_transition_action.triggered.connect(self.add_transition)
        toolbar.addAction(add_transition_action)

        toolbar.addSeparator()

        validate_action = QAction("Валидация", self)
        validate_action.triggered.connect(self.validate_fsm)
        toolbar.addAction(validate_action)

        export_action = QAction("Экспорт", self)
        export_action.triggered.connect(self.export_scheme)
        toolbar.addAction(export_action)

    def refresh_display(self):
        self.update_states_list()
        self.update_transitions_list()
        self.update_alphabet_list()
        self.update_matrix_display()
        self.update_table_display()
        self.update_summary_display()

        state_count = len(self.fsm.states)
        transition_count = sum(len(state.out_transitions) for state in self.fsm.states.values())
        self.status_bar.showMessage(f"Состояний: {state_count}, Переходов: {transition_count}")

    def update_states_list(self):
        self.states_list.clear()
        for state_name, state in self.fsm.states.items():
            item_text = state_name
            if state.is_start:
                item_text += " →"
            if state.is_final:
                item_text += " *"

            item = QListWidgetItem(item_text)

            if state.is_start and state.is_final:
                item.setForeground(QColor(0, 100, 0))
            elif state.is_start:
                item.setForeground(QColor(0, 0, 200))
            elif state.is_final:
                item.setForeground(QColor(200, 0, 0))

            self.states_list.addItem(item)

    def update_transitions_list(self):
        self.transitions_list.clear()
        transitions_added = set()

        for state in self.fsm.states.values():
            for transition in state.out_transitions:
                trans_key = (transition.from_state, transition.symbol, transition.to_state)
                if trans_key not in transitions_added:
                    item_text = f"{transition.from_state} --[{transition.symbol}]--> {transition.to_state}"
                    item = QListWidgetItem(item_text)

                    if transition.symbol == 'epsilon':
                        item.setForeground(QColor(150, 0, 150))

                    self.transitions_list.addItem(item)
                    transitions_added.add(trans_key)

    def update_alphabet_list(self):
        self.alphabet_list.clear()
        for symbol in sorted(self.fsm.alphabet):
            item = QListWidgetItem(symbol)
            self.alphabet_list.addItem(item)

        has_epsilon = any(
            transition.symbol == 'epsilon'
            for state in self.fsm.states.values()
            for transition in state.out_transitions
        )

        if has_epsilon:
            epsilon_item = QListWidgetItem("epsilon (ε)")
            epsilon_item.setForeground(QColor(150, 0, 150))
            self.alphabet_list.insertItem(0, epsilon_item)

    def update_matrix_display(self):
        if not self.fsm.states:
            self.matrix_widget.clear()
            return

        matrix, state_names = self.fsm.get_adjacency_matrix()

        self.matrix_widget.setRowCount(len(state_names))
        self.matrix_widget.setColumnCount(len(state_names))
        self.matrix_widget.setHorizontalHeaderLabels(state_names)
        self.matrix_widget.setVerticalHeaderLabels(state_names)

        for i in range(len(state_names)):
            for j in range(len(state_names)):
                value = matrix[i][j]
                item = QTableWidgetItem("1" if value else "0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if value:
                    item.setBackground(QColor(200, 255, 200))
                    item.setForeground(QColor(0, 0, 0))
                else:
                    item.setBackground(QColor(255, 255, 255))
                    item.setForeground(QColor(0, 0, 0))

                self.matrix_widget.setItem(i, j, item)

        self.matrix_widget.resizeColumnsToContents()
        self.matrix_widget.resizeRowsToContents()

    def update_table_display(self):
        if not self.fsm.states:
            self.table_widget.clear()
            return

        table, alphabet = self.fsm.get_transition_table()

        if not alphabet:
            return

        state_names = list(self.fsm.states.keys())

        self.table_widget.setRowCount(len(state_names))
        self.table_widget.setColumnCount(len(alphabet) + 1)

        headers = ["Состояние"] + alphabet
        self.table_widget.setHorizontalHeaderLabels(headers)

        for i, state_name in enumerate(state_names):
            state_item = QTableWidgetItem(state_name)
            state_markers = []
            if self.fsm.states[state_name].is_start:
                state_markers.append("→")
            if self.fsm.states[state_name].is_final:
                state_markers.append("*")

            if state_markers:
                state_item.setText(f"{state_name} ({''.join(state_markers)})")

            if self.fsm.states[state_name].is_start and self.fsm.states[state_name].is_final:
                state_item.setBackground(QColor(255, 255, 200))
            elif self.fsm.states[state_name].is_start:
                state_item.setBackground(QColor(200, 255, 200))
            elif self.fsm.states[state_name].is_final:
                state_item.setBackground(QColor(255, 200, 200))

            state_item.setForeground(QColor(0, 0, 0))
            self.table_widget.setItem(i, 0, state_item)

            for j, symbol in enumerate(alphabet, 1):
                targets = table[state_name][symbol]
                if targets:
                    cell_content = ", ".join(targets)
                    item = QTableWidgetItem(cell_content)
                    item.setBackground(QColor(240, 240, 255))
                else:
                    item = QTableWidgetItem("-")
                    item.setBackground(QColor(255, 255, 255))

                item.setForeground(QColor(0, 0, 0))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(i, j, item)

        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()

    def update_summary_display(self):
        summary = str(self.fsm) + "\n\n"

        summary += "Подробная информация о состояниях:\n"
        summary += "-" * 50 + "\n"

        for state_name, state in self.fsm.states.items():
            type_info = []
            if state.is_start:
                type_info.append("стартовое")
            if state.is_final:
                type_info.append("конечное")

            type_str = f" ({', '.join(type_info)})" if type_info else ""

            summary += f"\n{state_name}{type_str}:\n"
            summary += f"  Входящих переходов: {len(state.in_transitions)}\n"
            summary += f"  Исходящих переходов: {len(state.out_transitions)}\n"

            if state.out_transitions:
                transitions_by_symbol = {}
                for trans in state.out_transitions:
                    if trans.symbol not in transitions_by_symbol:
                        transitions_by_symbol[trans.symbol] = []
                    transitions_by_symbol[trans.symbol].append(trans.to_state)

                for symbol, targets in transitions_by_symbol.items():
                    summary += f"  По '{symbol}' → {', '.join(targets)}\n"

        epsilon_count = 0
        regular_count = 0

        for state in self.fsm.states.values():
            for transition in state.out_transitions:
                if transition.symbol == 'epsilon':
                    epsilon_count += 1
                else:
                    regular_count += 1

        summary += f"\nСтатистика переходов:\n"
        summary += f"  Обычные переходы: {regular_count}\n"
        summary += f"  Epsilon-переходы: {epsilon_count}\n"

        self.summary_widget.setText(summary)

    def add_state(self):
        dialog = AddStateDialog(self)
        if dialog.exec():
            data = dialog.get_state_data()
            if not data['name']:
                QMessageBox.warning(self, "Ошибка", "Имя состояния не может быть пустым")
                return

            try:
                self.fsm.add_state(data['name'], data['is_start'], data['is_final'])
                self.refresh_display()
                self.status_bar.showMessage(f"Состояние '{data['name']}' добавлено")
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))

    def remove_state(self):
        current_item = self.states_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите состояние для удаления")
            return

        state_name = current_item.text().split()[0]

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить состояние '{state_name}' и все связанные переходы?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if state_name in self.fsm.states:
                del self.fsm.states[state_name]

                if self.fsm.start_state and self.fsm.start_state.name == state_name:
                    self.fsm.start_state = None

                for state in self.fsm.states.values():
                    state.out_transitions = [
                        t for t in state.out_transitions
                        if t.to_state != state_name and t.from_state != state_name
                    ]
                    state.in_transitions = [
                        t for t in state.in_transitions
                        if t.from_state != state_name and t.to_state != state_name
                    ]

                self.refresh_display()
                self.status_bar.showMessage(f"Состояние '{state_name}' удалено")

    def add_transition(self):
        if not self.fsm.states:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте состояния")
            return

        dialog = AddTransitionDialog(list(self.fsm.states.keys()), self)
        if dialog.exec():
            data = dialog.get_transition_data()

            if not data['symbol']:
                QMessageBox.warning(self, "Ошибка", "Символ перехода не может быть пустым")
                return

            try:
                symbol = data['symbol']
                if symbol.lower() == 'epsilon' or symbol == 'ε':
                    symbol = 'epsilon'

                self.fsm.add_transition(data['from_state'], data['to_state'], symbol)
                self.refresh_display()
                self.status_bar.showMessage(f"Переход добавлен: {data['from_state']} --[{symbol}]--> {data['to_state']}")
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))

    def remove_transition(self):
        current_item = self.transitions_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите переход для удаления")
            return

        item_text = current_item.text()
        parts = item_text.split("--[")
        from_state = parts[0].strip()

        symbol_part = parts[1].split("]-->")
        symbol = symbol_part[0].strip("[]")
        to_state = symbol_part[1].strip()

        for state_name, state in self.fsm.states.items():
            for i, trans in enumerate(state.out_transitions[:]):
                if (trans.from_state == from_state and
                    trans.to_state == to_state and
                    trans.symbol == symbol):

                    state.out_transitions.pop(i)

                    target_state = self.fsm.states[to_state]
                    for j, in_trans in enumerate(target_state.in_transitions[:]):
                        if (in_trans.from_state == from_state and
                            in_trans.to_state == to_state and
                            in_trans.symbol == symbol):
                            target_state.in_transitions.pop(j)
                            break

                    self.refresh_display()
                    self.status_bar.showMessage(f"Переход удален: {item_text}")
                    return

        QMessageBox.warning(self, "Ошибка", "Переход не найден")

    def validate_fsm(self):
        if not self.fsm.states:
            QMessageBox.information(self, "Валидация", "Автомат пуст")
            return

        is_valid, messages = self.fsm.validate()

        dialog = QDialog(self)
        dialog.setWindowTitle("Результаты валидации")
        dialog.setModal(True)
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        result_text = ""
        if is_valid:
            result_text += "<b><font color='green'>✓ Автомат корректен</font></b>\n\n"
        else:
            result_text += "<b><font color='red'>✗ В автомате есть ошибки</font></b>\n\n"

        result_text += "<b>Сообщения:</b>\n"
        for msg in messages:
            if "Ошибка" in msg or msg.startswith("Не"):
                result_text += f"<font color='red'>• {msg}</font><br>"
            else:
                result_text += f"<font color='orange'>• {msg}</font><br>"

        text_edit.setHtml(result_text)
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec()

    def export_scheme(self):
        """Экспорт схемы - ТОЧНО КАК В КОНСОЛЬНОЙ ВЕРСИИ"""
        if not self.fsm.states:
            QMessageBox.warning(self, "Ошибка", "Нечего экспортировать: автомат пуст")
            return

        # Спрашиваем имя DOT файла (как в консольной версии)
        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт схемы", "finite_automaton.dot", "DOT files (*.dot)"
        )

        if not filename:
            return

        # Используем нашу функцию (скопированную из main.py)
        png_filename = export_to_dot(self.fsm, filename)

        if png_filename and os.path.exists(png_filename):
            # Загружаем PNG в просмотрщик
            if self.image_viewer.load_image(png_filename):
                self.current_image_path = png_filename
                self.status_bar.showMessage(f"Схема экспортирована и загружена")

                # Показываем сообщение как в консольной версии
                QMessageBox.information(
                    self, "Экспорт завершен",
                    f"Автомат успешно экспортирован в файл:\n{filename}\n\n"
                    f"PNG схема создана:\n{png_filename}\n\n"
                    f"Для визуализации используйте команду:\n"
                    f"dot -Tpng {filename} -o {png_filename}"
                )
            else:
                QMessageBox.warning(self, "Предупреждение",
                    f"DOT файл создан: {filename}\n"
                    f"Но не удалось загрузить PNG схему.")
        else:
            QMessageBox.warning(self, "Предупреждение",
                f"DOT файл создан: {filename}\n"
                f"Но PNG схема не была создана.\n\n"
                f"Убедитесь, что Graphviz установлен.\n\n"
                f"Для ручной генерации PNG используйте команду:\n"
                f"dot -Tpng {filename} -o {filename.replace('.dot', '.png')}")

    def load_scheme(self):
        """Загрузить существующее PNG изображение схемы"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Загрузить PNG схему", "",
            "PNG files (*.png);;All files (*.*)"
        )

        if filename:
            if self.image_viewer.load_image(filename):
                self.current_image_path = filename
                self.status_bar.showMessage(f"Схема загружена: {os.path.basename(filename)}")

    def clear_fsm(self):
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Очистить весь автомат? Все данные будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.fsm = FiniteStateMachine()
            self.image_viewer.clear()
            self.current_image_path = None
            self.refresh_display()
            self.status_bar.showMessage("Автомат очищен")

    def create_test_fsm(self):
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Создать тестовый автомат? Текущий автомат будет заменен.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.fsm = FiniteStateMachine()

            self.fsm.add_state("q0", True, False)
            self.fsm.add_state("q1")
            self.fsm.add_state("q2", False, True)

            self.fsm.add_transition("q0", "q1", "a")
            self.fsm.add_transition("q0", "q2", "epsilon")
            self.fsm.add_transition("q1", "q2", "b")
            self.fsm.add_transition("q2", "q0", "a")
            self.fsm.add_transition("q2", "q1", "z")

            self.refresh_display()
            self.status_bar.showMessage("Тестовый автомат создан")

    def show_about(self):
        about_text = """
        <h2>Finite State Machine Designer</h2>
        <p>Приложение для работы с конечными автоматами.</p>
        <p>Версия: 0.2</p>
        """
        QMessageBox.about(self, "О программе", about_text)


def main():
    """Основная функция запуска GUI"""
    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")

    light_palette = QPalette()
    light_palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))

    qt_app.setPalette(light_palette)

    app_style = """
        QWidget {
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 10pt;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #d0d0d0;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #f8f8f8;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #333;
        }
        
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        
        QListWidget {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            color: #000;
        }
        
        QTableWidget {
            background-color: white;
            color: #000;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            color: #000;
            padding: 4px;
            border: 1px solid #ccc;
            font-weight: bold;
        }
        
        QTextEdit {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            color: #000;
        }
    """

    qt_app.setStyleSheet(app_style)

    window = FSMMainWindow()
    window.show()

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()