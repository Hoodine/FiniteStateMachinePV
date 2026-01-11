"""
PyQt6 GUI для работы с конечными автоматами с новой системой визуализации
"""

import sys
import os
from typing import List, Optional
import matplotlib
matplotlib.use('Qt5Agg')  # Используем Qt5 backend для интеграции с PyQt6

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QMessageBox, QGroupBox, QGridLayout,
    QComboBox, QCheckBox, QSplitter, QFileDialog, QStatusBar, QToolBar,
    QMenuBar, QMenu, QDialog, QDialogButtonBox, QListWidget, QListWidgetItem,
    QScrollArea, QFrame, QSpinBox, QInputDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QFont, QColor, QPalette, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import networkx as nx
import matplotlib.lines as mlines

from fsm import FiniteStateMachine
from export_utils import FSMMatplotlibVisualizer, export_to_matplotlib, create_animation


class AnimationWorker(QThread):
    """Поток для создания анимации"""

    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, fsm, sequence, output_path):
        super().__init__()
        self.fsm = fsm
        self.sequence = sequence
        self.output_path = output_path

    def run(self):
        try:
            visualizer = FSMMatplotlibVisualizer(self.fsm)
            self.progress.emit(10)

            # Создаем кадры анимации
            frames = visualizer.create_animation_frames(self.sequence)
            self.progress.emit(30)

            if not frames:
                self.error.emit("Не удалось создать анимацию")
                return

            # Создаем фигуру для предпросмотра
            visualizer.build_graph()
            visualizer.calculate_layout()
            self.progress.emit(50)

            # Создаем и сохраняем анимацию
            anim = visualizer.animate_workflow(self.sequence, save_path=self.output_path)
            self.progress.emit(100)

            if anim:
                self.finished.emit(self.output_path)
            else:
                self.error.emit("Не удалось создать анимацию")

        except Exception as e:
            self.error.emit(f"Ошибка: {str(e)}")


class MatplotlibWidget(QWidget):
    """Виджет для отображения matplotlib графиков"""

    def __init__(self, parent=None, width=12, height=8, dpi=100):
        super().__init__(parent)

        # Создаём Figure и Canvas
        self.figure = Figure(figsize=(width, height), dpi=dpi, facecolor='#f5f5f5')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Настраиваем layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = None
        self.visualizer = None
        self.current_frame = 0
        self.total_frames = 0
        self.animation_frames = []
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_animation_frame)

    def plot_fsm(self, fsm: FiniteStateMachine, highlight_states=None, highlight_edges=None):
        """Построение графа конечного автомата"""
        if not fsm.states:
            self.clear()
            return

        # Создаём визуализатор
        self.visualizer = FSMMatplotlibVisualizer(fsm)
        self.visualizer.build_graph()
        self.visualizer.calculate_layout()

        # Очищаем предыдущий график
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#ffffff')

        # Рисуем граф с подсветкой
        self.visualizer.ax = self.ax
        self.visualizer._draw_graph(highlight_states=highlight_states, highlight_edges=highlight_edges)

        # Добавляем легенду
        self.visualizer._add_legend()

        # Добавляем заголовок
        title = "Конечный автомат"
        if highlight_states and len(highlight_states) == 1:
            title += f" | Текущее состояние: {highlight_states[0]}"
        elif highlight_states and len(highlight_states) > 1:
            title += f" | Текущие состояния: {', '.join(highlight_states[:3])}"
            if len(highlight_states) > 3:
                title += f"..."
        self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        self.ax.axis('off')

        self.figure.tight_layout()
        self.canvas.draw()

    def start_animation(self, fsm: FiniteStateMachine, input_sequence: List[str], interval: int = 1000):
        """Запуск анимации работы автомата"""
        if not fsm.states:
            return

        # Создаём визуализатор и получаем кадры анимации
        self.visualizer = FSMMatplotlibVisualizer(fsm)
        self.animation_frames = self.visualizer.create_animation_frames(input_sequence)

        if not self.animation_frames:
            QMessageBox.warning(self.parent(), "Ошибка", "Не удалось создать анимацию")
            return

        self.current_frame = 0
        self.total_frames = len(self.animation_frames)

        # Отображаем первый кадр
        self.show_animation_frame(0)

        # Запускаем таймер анимации
        self.animation_timer.start(interval)

    def show_animation_frame(self, frame_idx: int):
        """Отображение кадра анимации"""
        if not self.animation_frames or frame_idx >= len(self.animation_frames):
            return

        current_states, active_transitions, text = self.animation_frames[frame_idx]

        # Очищаем график
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#ffffff')

        # Рисуем граф с подсветкой
        if not self.visualizer:
            self.visualizer = FSMMatplotlibVisualizer(self.fsm)
            self.visualizer.build_graph()
            self.visualizer.calculate_layout()

        self.visualizer.ax = self.ax
        self.visualizer._draw_graph(
            highlight_states=current_states,
            highlight_edges=active_transitions
        )

        # Добавляем легенду
        self.visualizer._add_legend()

        # Добавляем информационную панель
        info_box = dict(boxstyle="round,pad=0.8",
                      facecolor="lightyellow",
                      edgecolor="orange",
                      alpha=0.9,
                      linewidth=2)

        self.ax.text(0.02, 0.98, text,
                   transform=self.ax.transAxes,
                   fontsize=12,
                   verticalalignment='top',
                   bbox=info_box)

        # Добавляем прогресс анимации
        progress_text = f"Кадр: {frame_idx + 1}/{self.total_frames}"
        if current_states:
            progress_text += f"\nТекущие состояния: {', '.join(current_states)}"

        self.ax.text(0.98, 0.98, progress_text,
                   transform=self.ax.transAxes,
                   fontsize=10,
                   ha='right', va='top',
                   bbox=dict(boxstyle="round,pad=0.3",
                            facecolor="white",
                            edgecolor="gray"))

        # Заголовок
        self.ax.set_title("Анимация работы автомата", fontsize=16, fontweight='bold', pad=20)
        self.ax.axis('off')

        self.figure.tight_layout()
        self.canvas.draw()

    def next_animation_frame(self):
        """Следующий кадр анимации"""
        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.animation_timer.stop()
            # Показываем финальное сообщение
            self.ax.text(0.5, 0.5, "АНИМАЦИЯ ЗАВЕРШЕНА",
                       transform=self.ax.transAxes,
                       fontsize=20, fontweight='bold',
                       ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=1",
                                facecolor="lightgreen",
                                edgecolor="green",
                                alpha=0.9))
            self.canvas.draw()
            return

        self.show_animation_frame(self.current_frame)

    def stop_animation(self):
        """Остановка анимации"""
        self.animation_timer.stop()

    def clear(self):
        """Очистка графика"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.text(0.5, 0.5, "Автомат пуст\nДобавьте состояния и переходы",
                   ha='center', va='center', fontsize=12,
                   transform=self.ax.transAxes)
        self.ax.axis('off')
        self.canvas.draw()


class AnimationControlDialog(QDialog):
    """Диалог управления анимацией"""

    def __init__(self, alphabet: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление анимацией")
        self.setModal(True)
        self.setup_ui(alphabet)

    def setup_ui(self, alphabet: List[str]):
        layout = QVBoxLayout()

        # Ввод последовательности
        input_group = QGroupBox("Входная последовательность")
        input_layout = QVBoxLayout()

        self.sequence_input = QLineEdit()
        self.sequence_input.setPlaceholderText("Введите символы через пробел (например: a b epsilon c)")
        input_layout.addWidget(QLabel("Последовательность:"))
        input_layout.addWidget(self.sequence_input)

        # Быстрые кнопки для добавления символов
        buttons_layout = QHBoxLayout()
        self.symbol_buttons = []

        # Добавляем кнопки для алфавита
        for symbol in alphabet[:8]:  # Ограничиваем количество кнопок
            btn = QPushButton(symbol)
            btn.clicked.connect(lambda checked, s=symbol: self.add_symbol(s))
            btn.setMaximumWidth(40)
            buttons_layout.addWidget(btn)
            self.symbol_buttons.append(btn)

        # Кнопка для epsilon
        if 'epsilon' in alphabet:
            epsilon_btn = QPushButton("ε")
            epsilon_btn.clicked.connect(lambda: self.add_symbol('epsilon'))
            epsilon_btn.setMaximumWidth(40)
            buttons_layout.addWidget(epsilon_btn)

        # Кнопка очистки
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_sequence)
        buttons_layout.addWidget(clear_btn)

        input_layout.addLayout(buttons_layout)

        # Примеры последовательностей
        examples_label = QLabel("Примеры:")
        examples_label.setStyleSheet("font-weight: bold;")
        input_layout.addWidget(examples_label)

        examples = ["a b c", "epsilon a", "a epsilon b", "z a b"]
        for example in examples:
            example_btn = QPushButton(example)
            example_btn.clicked.connect(lambda checked, e=example: self.sequence_input.setText(e))
            example_btn.setMaximumWidth(100)
            example_btn.setStyleSheet("font-size: 9pt;")
            input_layout.addWidget(example_btn)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Настройки анимации
        settings_group = QGroupBox("Настройки анимации")
        settings_layout = QGridLayout()

        settings_layout.addWidget(QLabel("Скорость анимации:"), 0, 0)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(500, 5000)
        self.speed_spin.setValue(1500)
        self.speed_spin.setSuffix(" мс/кадр")
        self.speed_spin.setSingleStep(500)
        settings_layout.addWidget(self.speed_spin, 0, 1)

        self.show_history_cb = QCheckBox("Показывать историю переходов")
        self.show_history_cb.setChecked(True)
        settings_layout.addWidget(self.show_history_cb, 1, 0, 1, 2)

        self.highlight_path_cb = QCheckBox("Подсвечивать пройденный путь")
        self.highlight_path_cb.setChecked(True)
        settings_layout.addWidget(self.highlight_path_cb, 2, 0, 1, 2)

        self.auto_play_cb = QCheckBox("Автоматическое воспроизведение")
        self.auto_play_cb.setChecked(True)
        settings_layout.addWidget(self.auto_play_cb, 3, 0, 1, 2)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def add_symbol(self, symbol: str):
        """Добавление символа в последовательность"""
        current = self.sequence_input.text()
        if current:
            self.sequence_input.setText(current + " " + symbol)
        else:
            self.sequence_input.setText(symbol)

    def clear_sequence(self):
        """Очистка последовательности"""
        self.sequence_input.clear()

    def get_animation_data(self):
        """Получение данных для анимации"""
        sequence_text = self.sequence_input.text().strip()
        if not sequence_text:
            return None

        sequence = sequence_text.split()
        return {
            'sequence': sequence,
            'speed': self.speed_spin.value(),
            'auto_play': self.auto_play_cb.isChecked(),
            'show_history': self.show_history_cb.isChecked(),
            'highlight_path': self.highlight_path_cb.isChecked()
        }


class FSMMainWindow(QMainWindow):
    """Главное окно приложения с новой системой визуализации"""

    def __init__(self):
        super().__init__()
        self.fsm = FiniteStateMachine()
        self.setup_ui()
        self.setWindowTitle("Finite State Machine Designer")
        self.setGeometry(100, 100, 1600, 900)

        # Таймер для анимации
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_animation_step)

        # Данные анимации
        self.animation_sequence = []
        self.animation_frames = []
        self.current_frame = 0
        self.animation_speed = 1500
        self.animation_worker = None

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая панель управления
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # Центральная панель с визуализацией
        center_splitter = QSplitter(Qt.Orientation.Vertical)

        # Matplotlib виджет для визуализации
        self.plot_widget = MatplotlibWidget(width=12, height=8)
        center_splitter.addWidget(self.plot_widget)

        # Панель информации
        self.info_tabs = QTabWidget()
        self.setup_info_tabs()
        center_splitter.addWidget(self.info_tabs)

        center_splitter.setSizes([600, 250])
        main_layout.addWidget(center_splitter, 3)

        self.create_menu()
        self.create_toolbar()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def create_left_panel(self):
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)

        # Состояния
        states_group = QGroupBox("Состояния")
        states_layout = QVBoxLayout()

        self.states_list = QListWidget()
        self.states_list.setMaximumHeight(150)
        states_layout.addWidget(self.states_list)

        states_buttons = QHBoxLayout()
        self.add_state_btn = QPushButton("➕ Добавить")
        self.add_state_btn.clicked.connect(self.add_state)
        self.edit_state_btn = QPushButton("✏️ Изменить")
        self.edit_state_btn.clicked.connect(self.edit_state)
        self.remove_state_btn = QPushButton("❌ Удалить")
        self.remove_state_btn.clicked.connect(self.remove_state)

        states_buttons.addWidget(self.add_state_btn)
        states_buttons.addWidget(self.edit_state_btn)
        states_buttons.addWidget(self.remove_state_btn)
        states_layout.addLayout(states_buttons)

        states_group.setLayout(states_layout)
        layout.addWidget(states_group)

        # Переходы
        transitions_group = QGroupBox("Переходы")
        transitions_layout = QVBoxLayout()

        self.transitions_list = QListWidget()
        self.transitions_list.setMaximumHeight(150)
        transitions_layout.addWidget(self.transitions_list)

        transitions_buttons = QHBoxLayout()
        self.add_transition_btn = QPushButton("➕ Добавить")
        self.add_transition_btn.clicked.connect(self.add_transition)
        self.remove_transition_btn = QPushButton("❌ Удалить")
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
        self.alphabet_list.setMaximumHeight(100)
        alphabet_layout.addWidget(self.alphabet_list)
        alphabet_group.setLayout(alphabet_layout)
        layout.addWidget(alphabet_group)

        # Панель анимации
        animation_group = QGroupBox("Анимация работы")
        animation_layout = QVBoxLayout()

        self.animate_btn = QPushButton("🎬 Запустить анимацию")
        self.animate_btn.clicked.connect(self.start_animation)
        self.animate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                padding: 12px;
                font-size: 11pt;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        animation_layout.addWidget(self.animate_btn)

        # Элементы управления анимацией
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        control_layout = QHBoxLayout()

        self.prev_frame_btn = QPushButton("⏮ Предыдущий")
        self.prev_frame_btn.clicked.connect(self.prev_animation_frame)
        self.prev_frame_btn.setEnabled(False)

        self.play_pause_btn = QPushButton("⏸ Пауза")
        self.play_pause_btn.clicked.connect(self.toggle_animation)
        self.play_pause_btn.setEnabled(False)

        self.next_frame_btn = QPushButton("Следующий ⏭")
        self.next_frame_btn.clicked.connect(self.next_animation_frame)
        self.next_frame_btn.setEnabled(False)

        self.stop_animation_btn = QPushButton("⏹ Стоп")
        self.stop_animation_btn.clicked.connect(self.stop_animation)
        self.stop_animation_btn.setEnabled(False)

        control_layout.addWidget(self.prev_frame_btn)
        control_layout.addWidget(self.play_pause_btn)
        control_layout.addWidget(self.next_frame_btn)
        control_layout.addWidget(self.stop_animation_btn)
        control_frame.setLayout(control_layout)

        animation_layout.addWidget(control_frame)

        # Статус анимации
        self.animation_status = QLabel("Анимация не запущена")
        self.animation_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.animation_status.setStyleSheet("""
            QLabel {
                padding: 8px; 
                background-color: #f0f0f0; 
                border-radius: 4px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
        """)
        animation_layout.addWidget(self.animation_status)

        animation_group.setLayout(animation_layout)
        layout.addWidget(animation_group)

        # Действия
        actions_group = QGroupBox("Действия")
        actions_layout = QVBoxLayout()

        self.validate_btn = QPushButton("✓ Валидация автомата")
        self.validate_btn.clicked.connect(self.validate_fsm)
        actions_layout.addWidget(self.validate_btn)

        self.export_btn = QPushButton("💾 Экспорт схемы")
        self.export_btn.clicked.connect(self.export_scheme)
        actions_layout.addWidget(self.export_btn)

        self.export_anim_btn = QPushButton("🎬 Экспорт анимации")
        self.export_anim_btn.clicked.connect(self.export_animation)
        actions_layout.addWidget(self.export_anim_btn)

        self.test_fsm_btn = QPushButton("🧪 Создать тестовый автомат")
        self.test_fsm_btn.clicked.connect(self.create_test_fsm)
        actions_layout.addWidget(self.test_fsm_btn)

        self.clear_btn = QPushButton("🗑️ Очистить всё")
        self.clear_btn.clicked.connect(self.clear_fsm)
        self.clear_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        actions_layout.addWidget(self.clear_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()
        return panel

    def setup_info_tabs(self):
        self.matrix_widget = QTableWidget()
        self.info_tabs.addTab(self.matrix_widget, "📊 Матрица смежности")

        self.table_widget = QTableWidget()
        self.info_tabs.addTab(self.table_widget, "📋 Таблица переходов")

        self.summary_widget = QTextEdit()
        self.summary_widget.setReadOnly(True)
        self.info_tabs.addTab(self.summary_widget, "📝 Сводная информация")

        # Вкладка для отладки анимации
        self.debug_widget = QTextEdit()
        self.debug_widget.setReadOnly(True)
        self.info_tabs.addTab(self.debug_widget, "🔧 Отладка")

    def create_menu(self):
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        new_action = QAction("📄 Новый автомат", self)
        new_action.triggered.connect(self.clear_fsm)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        export_action = QAction("💾 Экспорт схемы...", self)
        export_action.triggered.connect(self.export_scheme)
        file_menu.addAction(export_action)

        export_animation_action = QAction("🎬 Экспорт анимации...", self)
        export_animation_action.triggered.connect(self.export_animation)
        file_menu.addAction(export_animation_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Правка
        edit_menu = menubar.addMenu("Правка")

        add_state_action = QAction("🔘 Добавить состояние...", self)
        add_state_action.triggered.connect(self.add_state)
        edit_menu.addAction(add_state_action)

        add_transition_action = QAction("➡️ Добавить переход...", self)
        add_transition_action.triggered.connect(self.add_transition)
        edit_menu.addAction(add_transition_action)

        edit_menu.addSeparator()

        validate_action = QAction("✓ Валидировать автомат", self)
        validate_action.triggered.connect(self.validate_fsm)
        edit_menu.addAction(validate_action)

        # Меню Вид
        view_menu = menubar.addMenu("Вид")

        refresh_viz_action = QAction("🔄 Обновить визуализацию", self)
        refresh_viz_action.triggered.connect(self.refresh_visualization)
        view_menu.addAction(refresh_viz_action)

        # Меню Анимация
        animation_menu = menubar.addMenu("Анимация")

        start_animation_action = QAction("▶️ Запустить анимацию...", self)
        start_animation_action.triggered.connect(self.start_animation)
        animation_menu.addAction(start_animation_action)

        stop_animation_action = QAction("⏹ Остановить анимацию", self)
        stop_animation_action.triggered.connect(self.stop_animation)
        animation_menu.addAction(stop_animation_action)

        animation_menu.addSeparator()

        prev_frame_action = QAction("⏮ Предыдущий кадр", self)
        prev_frame_action.triggered.connect(self.prev_animation_frame)
        animation_menu.addAction(prev_frame_action)

        next_frame_action = QAction("Следующий кадр ⏭", self)
        next_frame_action.triggered.connect(self.next_animation_frame)
        animation_menu.addAction(next_frame_action)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Основные инструменты")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        new_action = QAction("📄", self)
        new_action.setToolTip("Новый автомат")
        new_action.triggered.connect(self.clear_fsm)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        add_state_action = QAction("🔘", self)
        add_state_action.setToolTip("Добавить состояние")
        add_state_action.triggered.connect(self.add_state)
        toolbar.addAction(add_state_action)

        add_transition_action = QAction("➡️", self)
        add_transition_action.setToolTip("Добавить переход")
        add_transition_action.triggered.connect(self.add_transition)
        toolbar.addAction(add_transition_action)

        toolbar.addSeparator()

        validate_action = QAction("✓", self)
        validate_action.setToolTip("Валидация")
        validate_action.triggered.connect(self.validate_fsm)
        toolbar.addAction(validate_action)

        animate_action = QAction("🎬", self)
        animate_action.setToolTip("Анимация")
        animate_action.triggered.connect(self.start_animation)
        toolbar.addAction(animate_action)

        export_action = QAction("💾", self)
        export_action.setToolTip("Экспорт")
        export_action.triggered.connect(self.export_scheme)
        toolbar.addAction(export_action)

    def refresh_display(self):
        """Обновление всех отображений"""
        self.update_states_list()
        self.update_transitions_list()
        self.update_alphabet_list()
        self.update_matrix_display()
        self.update_table_display()
        self.update_summary_display()
        self.refresh_visualization()

        # Обновление статуса
        state_count = len(self.fsm.states)
        transition_count = sum(len(state.out_transitions) for state in self.fsm.states.values())
        self.status_bar.showMessage(f"Состояний: {state_count}, Переходов: {transition_count}")

    def refresh_visualization(self):
        """Обновление визуализации графа"""
        self.plot_widget.plot_fsm(self.fsm)

    def update_states_list(self):
        self.states_list.clear()
        for state_name, state in self.fsm.states.items():
            item_text = state_name
            if state.is_start:
                item_text += " 🚩"
            if state.is_final:
                item_text += " ✅"

            item = QListWidgetItem(item_text)

            # Цвета в зависимости от типа состояния
            if state.is_start and state.is_final:
                item.setForeground(QColor(0, 100, 0))
                item.setBackground(QColor(255, 255, 200))
            elif state.is_start:
                item.setForeground(QColor(0, 0, 200))
                item.setBackground(QColor(200, 255, 200))
            elif state.is_final:
                item.setForeground(QColor(200, 0, 0))
                item.setBackground(QColor(255, 200, 200))

            self.states_list.addItem(item)

    def update_transitions_list(self):
        self.transitions_list.clear()
        transitions_added = set()

        for state in self.fsm.states.values():
            for transition in state.out_transitions:
                trans_key = (transition.from_state, transition.symbol, transition.to_state)
                if trans_key not in transitions_added:
                    symbol_display = 'ε' if transition.symbol == 'epsilon' else transition.symbol
                    item_text = f"{transition.from_state} →{symbol_display}→ {transition.to_state}"
                    item = QListWidgetItem(item_text)

                    if transition.symbol == 'epsilon':
                        item.setForeground(QColor(150, 0, 150))
                        item.setBackground(QColor(255, 230, 255))

                    self.transitions_list.addItem(item)
                    transitions_added.add(trans_key)

    def update_alphabet_list(self):
        self.alphabet_list.clear()

        # Проверяем наличие epsilon-переходов
        has_epsilon = any(
            transition.symbol == 'epsilon'
            for state in self.fsm.states.values()
            for transition in state.out_transitions
        )

        if has_epsilon:
            epsilon_item = QListWidgetItem("ε (epsilon)")
            epsilon_item.setForeground(QColor(150, 0, 150))
            self.alphabet_list.addItem(epsilon_item)

        for symbol in sorted(self.fsm.alphabet):
            item = QListWidgetItem(symbol)
            self.alphabet_list.addItem(item)

    def add_state(self):
        name, ok = QInputDialog.getText(self, "Добавить состояние",
                                       "Имя состояния:")
        if not ok or not name.strip():
            return

        is_start = False
        is_final = False

        # Спрашиваем тип состояния
        if self.fsm.start_state is None:
            reply = QMessageBox.question(self, "Стартовое состояние",
                                       f"Сделать состояние '{name}' стартовым?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                is_start = True

        reply = QMessageBox.question(self, "Конечное состояние",
                                   f"Сделать состояние '{name}' конечным?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            is_final = True

        try:
            self.fsm.add_state(name, is_start, is_final)
            self.refresh_display()
            self.status_bar.showMessage(f"Состояние '{name}' добавлено", 3000)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def edit_state(self):
        current_item = self.states_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите состояние для редактирования")
            return

        state_name = current_item.text().split()[0]
        state = self.fsm.states[state_name]

        # Переключаем конечное состояние
        state.is_final = not state.is_final
        self.refresh_display()
        self.status_bar.showMessage(f"Состояние '{state_name}' обновлено", 3000)

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

                # Удаляем связанные переходы
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
                self.status_bar.showMessage(f"Состояние '{state_name}' удалено", 3000)

    def add_transition(self):
        if not self.fsm.states:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте состояния")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить переход")
        dialog.setModal(True)
        dialog.resize(300, 200)

        layout = QVBoxLayout()

        # Выбор исходного состояния
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("Из состояния:"))
        from_combo = QComboBox()
        from_combo.addItems(list(self.fsm.states.keys()))
        from_layout.addWidget(from_combo)
        layout.addLayout(from_layout)

        # Ввод символа
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Символ:"))
        symbol_input = QLineEdit()
        symbol_input.setPlaceholderText("a, b, epsilon, ...")
        symbol_layout.addWidget(symbol_input)
        layout.addLayout(symbol_layout)

        # Выбор целевого состояния
        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("В состояние:"))
        to_combo = QComboBox()
        to_combo.addItems(list(self.fsm.states.keys()))
        to_layout.addWidget(to_combo)
        layout.addLayout(to_layout)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec():
            symbol = symbol_input.text().strip()
            if not symbol:
                QMessageBox.warning(self, "Ошибка", "Символ перехода не может быть пустым")
                return

            if symbol.lower() == 'epsilon' or symbol == 'ε':
                symbol = 'epsilon'

            try:
                self.fsm.add_transition(from_combo.currentText(),
                                      to_combo.currentText(),
                                      symbol)
                self.refresh_display()
                self.status_bar.showMessage(f"Переход добавлен: {from_combo.currentText()} →{symbol}→ {to_combo.currentText()}", 3000)
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))

    def remove_transition(self):
        current_item = self.transitions_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите переход для удаления")
            return

        item_text = current_item.text()
        # Парсим строку перехода
        parts = item_text.split('→')
        if len(parts) != 3:
            QMessageBox.warning(self, "Ошибка", "Невозможно разобрать переход")
            return

        from_state = parts[0].strip()
        symbol = parts[1].strip()
        to_state = parts[2].strip()

        # Преобразуем ε обратно в epsilon
        if symbol == 'ε':
            symbol = 'epsilon'

        # Ищем и удаляем переход
        for state_name, state in self.fsm.states.items():
            for i, trans in enumerate(state.out_transitions[:]):
                if (trans.from_state == from_state and
                    trans.to_state == to_state and
                    trans.symbol == symbol):

                    state.out_transitions.pop(i)

                    # Удаляем входящий переход
                    target_state = self.fsm.states[to_state]
                    for j, in_trans in enumerate(target_state.in_transitions[:]):
                        if (in_trans.from_state == from_state and
                            in_trans.to_state == to_state and
                            in_trans.symbol == symbol):
                            target_state.in_transitions.pop(j)
                            break

                    self.refresh_display()
                    self.status_bar.showMessage(f"Переход удален: {item_text}", 3000)
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
        dialog.resize(500, 400)

        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        result_text = ""
        if is_valid:
            result_text += "<h3><font color='green'>✓ Автомат корректен</font></h3><br>"
        else:
            result_text += "<h3><font color='red'>✗ В автомате есть ошибки</font></h3><br>"

        result_text += "<b>Сообщения:</b><br>"
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

    def start_animation(self):
        """Запуск анимации работы автомата"""
        if not self.fsm.states:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте автомат")
            return

        # Получаем алфавит для диалога
        alphabet = list(self.fsm.alphabet)
        if any(t.symbol == 'epsilon' for s in self.fsm.states.values() for t in s.out_transitions):
            if 'epsilon' not in alphabet:
                alphabet.append('epsilon')

        # Показываем диалог настроек анимации
        dialog = AnimationControlDialog(alphabet, self)
        if dialog.exec():
            animation_data = dialog.get_animation_data()
            if not animation_data:
                return

            self.animation_sequence = animation_data['sequence']
            self.animation_speed = animation_data['speed']

            # Используем визуализатор для создания кадров
            self.visualizer = FSMMatplotlibVisualizer(self.fsm)
            self.animation_frames = self.visualizer.create_animation_frames(self.animation_sequence)

            if not self.animation_frames:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать анимацию")
                return

            self.current_frame = 0

            # Включаем кнопки управления анимацией
            self.prev_frame_btn.setEnabled(True)
            self.play_pause_btn.setEnabled(True)
            self.next_frame_btn.setEnabled(True)
            self.stop_animation_btn.setEnabled(True)
            self.animate_btn.setEnabled(False)

            # Настраиваем таймер
            self.animation_timer.setInterval(self.animation_speed)

            # Показываем первый кадр
            self.show_animation_frame(0)

            # Запускаем автоматическое воспроизведение если включено
            if animation_data['auto_play']:
                self.animation_timer.start()
                self.play_pause_btn.setText("⏸ Пауза")

            # Обновляем статус
            total_frames = len(self.animation_frames)
            self.animation_status.setText(f"Анимация: 1/{total_frames} | {len(self.animation_sequence)} шагов")
            self.status_bar.showMessage(f"Анимация запущена. Кадров: {total_frames}", 3000)

    def stop_animation(self):
        """Остановка анимации"""
        self.animation_timer.stop()
        self.animation_frames = []
        self.current_frame = 0

        # Отключаем кнопки управления анимацией
        self.prev_frame_btn.setEnabled(False)
        self.play_pause_btn.setEnabled(False)
        self.next_frame_btn.setEnabled(False)
        self.stop_animation_btn.setEnabled(False)
        self.animate_btn.setEnabled(True)

        # Обновляем визуализацию
        self.refresh_visualization()

        self.animation_status.setText("Анимация не запущена")
        self.status_bar.showMessage("Анимация остановлена", 3000)

    def toggle_animation(self):
        """Переключение паузы/воспроизведения"""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.play_pause_btn.setText("▶️ Воспр.")
        else:
            if self.current_frame >= len(self.animation_frames) - 1:
                self.current_frame = 0
            self.animation_timer.start()
            self.play_pause_btn.setText("⏸ Пауза")

    def next_animation_frame(self):
        """Следующий кадр анимации"""
        if not self.animation_frames:
            return

        self.current_frame += 1
        if self.current_frame >= len(self.animation_frames):
            self.current_frame = len(self.animation_frames) - 1
            self.animation_timer.stop()
            self.play_pause_btn.setText("▶️ Воспр.")
            self.animation_status.setText(f"Анимация завершена | Кадр: {self.current_frame + 1}/{len(self.animation_frames)}")
        else:
            self.show_animation_frame(self.current_frame)

    def prev_animation_frame(self):
        """Предыдущий кадр анимации"""
        if not self.animation_frames:
            return

        self.current_frame -= 1
        if self.current_frame < 0:
            self.current_frame = 0

        self.show_animation_frame(self.current_frame)

    def next_animation_step(self):
        """Следующий шаг анимации (для таймера)"""
        self.next_animation_frame()

    def show_animation_frame(self, frame_idx: int):
        """Отображение кадра анимации"""
        if not hasattr(self, 'visualizer') or not self.animation_frames or frame_idx >= len(self.animation_frames):
            return

        # Получаем данные кадра
        current_states, active_transitions, text = self.animation_frames[frame_idx]

        # Подготавливаем визуализатор
        if not hasattr(self.plot_widget, 'visualizer'):
            self.plot_widget.visualizer = FSMMatplotlibVisualizer(self.fsm)
            self.plot_widget.visualizer.build_graph()
            self.plot_widget.visualizer.calculate_layout()

        # Очищаем график
        self.plot_widget.figure.clear()
        self.plot_widget.ax = self.plot_widget.figure.add_subplot(111)
        self.plot_widget.ax.set_facecolor('#ffffff')

        # Рисуем граф с подсветкой
        self.plot_widget.visualizer.ax = self.plot_widget.ax
        self.plot_widget.visualizer._draw_graph(
            highlight_states=current_states,
            highlight_edges=active_transitions
        )

        # Добавляем легенду
        self.plot_widget.visualizer._add_legend()

        # Информационная панель
        info_box = dict(boxstyle="round,pad=0.8",
                      facecolor="lightyellow",
                      edgecolor="orange",
                      alpha=0.9,
                      linewidth=2)

        # Отображаем текст текущего кадра
        self.plot_widget.ax.text(0.02, 0.98, text,
                               transform=self.plot_widget.ax.transAxes,
                               fontsize=12,
                               verticalalignment='top',
                               bbox=info_box)

        # Отображаем прогресс анимации
        progress_text = f"Кадр: {frame_idx + 1}/{len(self.animation_frames)}"
        if current_states:
            progress_text += f"\nТекущие состояния: {', '.join(current_states)}"

        self.plot_widget.ax.text(0.98, 0.98, progress_text,
                               transform=self.plot_widget.ax.transAxes,
                               fontsize=10,
                               ha='right', va='top',
                               bbox=dict(boxstyle="round,pad=0.3",
                                        facecolor="white",
                                        edgecolor="gray"))

        # Отображаем входную последовательность
        seq_display = []
        for symbol in self.animation_sequence:
            if symbol == 'epsilon':
                seq_display.append('ε')
            else:
                seq_display.append(symbol)

        current_step = min(frame_idx // 2, len(self.animation_sequence)) if frame_idx > 0 else 0
        seq_lines = []
        for i, symbol in enumerate(seq_display):
            if i == current_step and frame_idx % 2 == 1 and frame_idx > 0:
                seq_lines.append(f"[{symbol}]")
            else:
                seq_lines.append(symbol)

        seq_text = "Вход: " + " → ".join(seq_lines)

        self.plot_widget.ax.text(0.02, 0.02, seq_text,
                               transform=self.plot_widget.ax.transAxes,
                               fontsize=11,
                               fontweight='bold',
                               bbox=dict(boxstyle="round,pad=0.5",
                                        facecolor="lightblue",
                                        edgecolor="blue",
                                        alpha=0.8))

        # Заголовок
        self.plot_widget.ax.set_title("Анимация работы автомата", fontsize=16, fontweight='bold', pad=20)
        self.plot_widget.ax.axis('off')

        self.plot_widget.figure.tight_layout()
        self.plot_widget.canvas.draw()

        # Обновляем статус
        total_frames = len(self.animation_frames)
        self.animation_status.setText(f"Анимация: {frame_idx + 1}/{total_frames}")

        # Обновляем отладочную информацию
        debug_text = f"Текущий кадр: {frame_idx + 1}/{total_frames}\n"
        debug_text += f"Текст: {text}\n"

        if current_states:
            debug_text += f"Текущие состояния: {', '.join(current_states)}\n"

        if active_transitions:
            debug_text += f"Активные переходы: {len(active_transitions)}\n"
            for i, (from_state, to_state, symbol) in enumerate(active_transitions[:3]):
                symbol_display = 'ε' if symbol == 'epsilon' else symbol
                debug_text += f"  {from_state} →{symbol_display}→ {to_state}\n"
            if len(active_transitions) > 3:
                debug_text += f"  ... и ещё {len(active_transitions) - 3}\n"

        self.debug_widget.setText(debug_text)

    def export_scheme(self):
        """Экспорт схемы автомата в изображение"""
        if not self.fsm.states:
            QMessageBox.warning(self, "Ошибка", "Нечего экспортировать: автомат пуст")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт схемы", "finite_automaton.png",
            "PNG files (*.png);;PDF files (*.pdf);;SVG files (*.svg);;JPEG files (*.jpg)"
        )

        if not filename:
            return

        try:
            export_to_matplotlib(self.fsm, filename, show=False)
            QMessageBox.information(self, "Успех", f"Схема успешно экспортирована в:\n{filename}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при экспорте: {str(e)}")

    def export_animation(self):
        """Экспорт анимации в GIF"""
        if not self.fsm.states:
            QMessageBox.warning(self, "Ошибка", "Нечего экспортировать: автомат пуст")
            return

        # Спрашиваем последовательность для анимации
        sequence, ok = QInputDialog.getText(
            self, "Входная последовательность",
            "Введите символы через пробел (например: a b epsilon c):"
        )

        if not ok or not sequence.strip():
            return

        input_sequence = sequence.strip().split()

        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт анимации", "automaton_animation.gif",
            "GIF files (*.gif)"
        )

        if not filename:
            return

        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Создаем поток для создания анимации
        self.animation_worker = AnimationWorker(self.fsm, input_sequence, filename)
        self.animation_worker.progress.connect(self.progress_bar.setValue)
        self.animation_worker.finished.connect(self.on_animation_export_finished)
        self.animation_worker.error.connect(self.on_animation_export_error)
        self.animation_worker.start()

    def on_animation_export_finished(self, filename):
        """Завершение экспорта анимации"""
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Успех", f"Анимация успешно экспортирована в:\n{filename}")

    def on_animation_export_error(self, error_msg):
        """Ошибка при экспорте анимации"""
        self.progress_bar.setVisible(False)
        QMessageBox.warning(self, "Ошибка", f"Ошибка при экспорте анимации:\n{error_msg}")

    def clear_fsm(self):
        """Очистка автомата"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Очистить весь автомат? Все данные будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.fsm = FiniteStateMachine()
            self.plot_widget.clear()
            self.animation_frames = []
            self.current_frame = 0
            self.stop_animation()
            self.refresh_display()
            self.status_bar.showMessage("Автомат очищен", 3000)

    def create_test_fsm(self):
        """Создание тестового автомата"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Создать тестовый автомат? Текущий автомат будет заменен.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.fsm = FiniteStateMachine()

            # Создаем более интересный тестовый автомат
            self.fsm.add_state("q0", True, False)
            self.fsm.add_state("q1")
            self.fsm.add_state("q2", False, True)
            self.fsm.add_state("q3", False, False)
            self.fsm.add_state("q4", False, True)

            self.fsm.add_transition("q0", "q1", "a")
            self.fsm.add_transition("q0", "q2", "epsilon")
            self.fsm.add_transition("q1", "q2", "b")
            self.fsm.add_transition("q1", "q3", "c")
            self.fsm.add_transition("q2", "q0", "a")
            self.fsm.add_transition("q2", "q1", "z")
            self.fsm.add_transition("q3", "q2", "d")
            self.fsm.add_transition("q3", "q4", "e")
            self.fsm.add_transition("q4", "q4", "e")

            self.refresh_display()
            self.status_bar.showMessage("Тестовый автомат создан. Попробуйте анимацию с последовательностью: 'a b' или 'epsilon a'", 5000)

    def show_about(self):
        about_text = """
        <h2>Finite State Machine Designer</h2>
        <p>Приложение для работы с конечными автоматами.</p>
        <p>Версия: 1.0</p>
        <p><b>Новые возможности:</b></p>
        <ul>
            <li>Визуализация графов с помощью matplotlib и networkX</li>
            <li>Полная анимация работы автомата с подсветкой состояний и переходов</li>
            <li>Интерактивное управление анимацией (пауза, вперед, назад)</li>
            <li>Экспорт схем и анимаций в различные форматы</li>
            <li>Поддержка epsilon-переходов</li>
        </ul>
        <p><b>Инструкция:</b></p>
        <ol>
            <li>Добавьте состояния (стартовые и конечные)</li>
            <li>Добавьте переходы между состояниями</li>
            <li>Запустите анимацию с входной последовательностью</li>
            <li>Наблюдайте работу автомата</li>
        </ol>
        """
        QMessageBox.about(self, "О программе", about_text)

    def update_matrix_display(self):
        """Обновление отображения матрицы смежности"""
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
        """Обновление таблицы переходов"""
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
        """Обновление сводной информации"""
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
                    symbol_display = 'ε' if symbol == 'epsilon' else symbol
                    summary += f"  По '{symbol_display}' → {', '.join(targets)}\n"

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


def main():
    """Основная функция запуска GUI"""
    import sys

    qt_app = QApplication(sys.argv)
    qt_app.setStyle("Fusion")

    # Настраиваем палитру
    light_palette = QPalette()
    light_palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))

    qt_app.setPalette(light_palette)

    # Стили приложения
    app_style = """
        QWidget {
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 10pt;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #d0d0d0;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 12px;
            background-color: #f8f8f8;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: #333;
            font-size: 10.5pt;
        }
        
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 8px 14px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
            border-color: #aaa;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        
        QListWidget {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            color: #000;
            padding: 2px;
        }
        QListWidget::item {
            padding: 4px;
            border-radius: 3px;
        }
        QListWidget::item:selected {
            background-color: #4CAF50;
            color: white;
        }
        
        QTableWidget {
            background-color: white;
            color: #000;
            border: 1px solid #ccc;
            gridline-color: #e0e0e0;
        }
        QHeaderView::section {
            background-color: #f0f0f0;
            color: #000;
            padding: 6px;
            border: 1px solid #ccc;
            font-weight: bold;
        }
        
        QTextEdit {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            color: #000;
            padding: 4px;
        }
        
        QTabWidget::pane {
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: white;
        }
        QTabBar::tab {
            padding: 8px 16px;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom-color: white;
        }
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        
        QStatusBar {
            background-color: #f0f0f0;
            border-top: 1px solid #ccc;
        }
    """

    qt_app.setStyleSheet(app_style)

    window = FSMMainWindow()
    window.show()

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()