"""
Утилиты для визуализации конечных автоматов с использованием matplotlib и networkX
с улучшенной анимацией
"""

import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Dict, Optional, Tuple, Set
from fsm import FiniteStateMachine
import matplotlib.animation as animation
import matplotlib
import numpy as np
import math

# Используем интерактивный режим для анимаций
matplotlib.use('TkAgg')


class FSMMatplotlibVisualizer:
    """Класс для визуализации конечного автомата с помощью matplotlib и networkX"""

    def __init__(self, fsm: FiniteStateMachine):
        """
        Инициализация визуализатора

        Args:
            fsm: Конечный автомат для визуализации
        """
        self.fsm = fsm
        self.graph = nx.MultiDiGraph()
        self.fig = None
        self.ax = None
        self.pos = None
        self.animation = None
        self.edge_labels = {}
        self.edge_artists = []

    def build_graph(self) -> None:
        """Построение графа из автомата"""
        self.graph.clear()
        self.edge_labels.clear()

        if not self.fsm.states:
            return

        # Добавляем узлы (состояния)
        for state_name, state in self.fsm.states.items():
            self.graph.add_node(state_name,
                              is_start=state.is_start,
                              is_final=state.is_final)

        # Собираем все переходы для группировки
        transitions_by_edge = {}
        for state_name, state in self.fsm.states.items():
            for transition in state.out_transitions:
                edge_key = (transition.from_state, transition.to_state)
                if edge_key not in transitions_by_edge:
                    transitions_by_edge[edge_key] = []
                transitions_by_edge[edge_key].append(transition.symbol)

        # Добавляем рёбра (переходы) с группировкой символов
        for (from_state, to_state), symbols in transitions_by_edge.items():
            # Группируем символы
            symbol_groups = {}
            for symbol in symbols:
                if symbol == 'epsilon':
                    symbol_display = 'ε'
                else:
                    symbol_display = symbol
                symbol_groups[symbol_display] = symbol_groups.get(symbol_display, 0) + 1

            # Создаем подписи для ребер
            labels = []
            for symbol_display, count in symbol_groups.items():
                if count > 1:
                    labels.append(f"{symbol_display} ({count})")
                else:
                    labels.append(symbol_display)

            label = ", ".join(labels)
            self.graph.add_edge(from_state, to_state, label=label, symbols=symbols)

            # Сохраняем для анимации
            self.edge_labels[(from_state, to_state)] = {
                'label': label,
                'symbols': symbols,
                'from': from_state,
                'to': to_state
            }

    def calculate_layout(self) -> Dict:
        """Вычисление позиций узлов для красивого отображения"""
        if not self.graph.nodes():
            return {}

        try:
            # Используем spring layout с настройками
            self.pos = nx.spring_layout(
                self.graph,
                k=2.5,
                iterations=100,
                seed=42,
                scale=2.0
            )
        except Exception:
            # Fallback layout
            self.pos = nx.circular_layout(self.graph, scale=2.0)

        return self.pos

    def _draw_graph(self, highlight_states: List[str] = None,
                   highlight_edges: List[Tuple[str, str, str]] = None) -> None:
        """Рисование графа на текущем axes"""
        self.ax.clear()
        self.edge_artists.clear()

        if not self.pos or not self.ax:
            return

        # Рисуем узлы
        node_colors = []
        node_sizes = []
        node_edge_colors = []
        node_edge_widths = []

        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]

            # Определяем цвет узла
            if highlight_states and node in highlight_states:
                node_colors.append('#FF6B6B')  # Красный для текущего состояния
                node_edge_colors.append('#FF0000')
                node_edge_widths.append(3)
                node_sizes.append(2000)
            elif node_data.get('is_start', False) and node_data.get('is_final', False):
                node_colors.append('#FFD700')  # Золотой для стартового+конечного
                node_edge_colors.append('#000000')
                node_edge_widths.append(2)
                node_sizes.append(1800)
            elif node_data.get('is_start', False):
                node_colors.append('#90EE90')  # Светло-зелёный для стартового
                node_edge_colors.append('#000000')
                node_edge_widths.append(2)
                node_sizes.append(1800)
            elif node_data.get('is_final', False):
                node_colors.append('#FFB6C1')  # Светло-розовый для конечного
                node_edge_colors.append('#000000')
                node_edge_widths.append(2)
                node_sizes.append(1800)
            else:
                node_colors.append('#87CEEB')  # Голубой для обычного
                node_edge_colors.append('#000000')
                node_edge_widths.append(2)
                node_sizes.append(1600)

        # Рисуем узлы
        nx.draw_networkx_nodes(
            self.graph, self.pos,
            node_color=node_colors,
            node_size=node_sizes,
            edgecolors=node_edge_colors,
            linewidths=node_edge_widths,
            ax=self.ax
        )

        # Подписи узлов
        nx.draw_networkx_labels(
            self.graph, self.pos,
            font_size=14,
            font_weight='bold',
            font_color='black',
            ax=self.ax
        )

        # Рисуем рёбра
        for edge in self.graph.edges():
            from_node, to_node = edge
            edge_data = self.graph.get_edge_data(from_node, to_node)[0]

            # Определяем стиль ребра
            edge_color = '#666666'
            edge_width = 2.5
            edge_style = 'solid'

            # Проверяем, нужно ли подсветить это ребро
            is_highlighted = False
            if highlight_edges:
                for h_from, h_to, h_symbol in highlight_edges:
                    if h_from == from_node and h_to == to_node:
                        # Проверяем символ в edge_data
                        if 'symbols' in edge_data and h_symbol in edge_data['symbols']:
                            edge_color = '#FF0000'
                            edge_width = 4.0
                            is_highlighted = True
                            break

            # Проверяем на epsilon-переходы
            if 'symbols' in edge_data and 'epsilon' in edge_data['symbols']:
                edge_style = 'dashed'
                if not is_highlighted:
                    edge_color = '#800080'  # Фиолетовый для epsilon

            # Рисуем стрелку
            edge_artist = nx.draw_networkx_edges(
                self.graph, self.pos,
                edgelist=[(from_node, to_node)],
                width=edge_width,
                style=edge_style,
                edge_color=edge_color,
                alpha=0.8,
                ax=self.ax,
                arrows=True,
                arrowsize=20,
                arrowstyle='-|>',
                connectionstyle='arc3,rad=0.1'
            )

            if edge_artist:
                self.edge_artists.extend(edge_artist)

            # Добавляем метку ребра
            if 'label' in edge_data:
                # Позиция для метки (середина ребра)
                x1, y1 = self.pos[from_node]
                x2, y2 = self.pos[to_node]

                # Вычисляем угол наклона ребра
                dx = x2 - x1
                dy = y2 - y1
                angle = math.degrees(math.atan2(dy, dx))

                # Смещение для метки
                offset_x = dy * 0.15
                offset_y = -dx * 0.15

                label_x = (x1 + x2) / 2 + offset_x
                label_y = (y1 + y2) / 2 + offset_y

                # Фон метки
                bg_color = '#FFFF99' if is_highlighted else 'white'
                edge_color_hex = '#FF0000' if is_highlighted else '#FF9900'

                label_text = self.ax.text(
                    label_x, label_y,
                    edge_data['label'],
                    fontsize=10,
                    ha='center',
                    va='center',
                    rotation=angle if abs(angle) < 90 else angle + 180,
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        facecolor=bg_color,
                        edgecolor=edge_color_hex,
                        alpha=0.9,
                        linewidth=1
                    )
                )
                self.edge_artists.append(label_text)

        # Добавляем стрелку к начальному состоянию
        if self.fsm.start_state:
            start_node = self.fsm.start_state.name
            if start_node in self.pos:
                x, y = self.pos[start_node]
                # Рисуем стрелку к начальному состоянию
                self.ax.annotate('',
                               xy=(x, y),
                               xytext=(x - 0.5, y),
                               arrowprops=dict(
                                   arrowstyle='->',
                                   color='green',
                                   linewidth=3,
                                   shrinkA=15,
                                   shrinkB=15
                               ),
                               annotation_clip=False)

    def _add_legend(self) -> None:
        """Добавление легенды"""
        if not self.ax:
            return

        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor='#90EE90', markersize=12,
                      label='Стартовое состояние'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor='#FFB6C1', markersize=12,
                      label='Конечное состояние'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor='#FFD700', markersize=12,
                      label='Стартовое и конечное'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor='#87CEEB', markersize=12,
                      label='Обычное состояние'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor='#FF6B6B', markersize=12,
                      label='Текущее состояние'),
            plt.Line2D([0], [0], color='#666666', linestyle='solid',
                      linewidth=2, label='Обычный переход'),
            plt.Line2D([0], [0], color='#800080', linestyle='dashed',
                      linewidth=2, label='Epsilon-переход'),
            plt.Line2D([0], [0], color='#FF0000', linestyle='solid',
                      linewidth=3, label='Активный переход')
        ]

        self.ax.legend(handles=legend_elements,
                      loc='upper left',
                      fontsize=9,
                      framealpha=0.95,
                      frameon=True,
                      fancybox=True,
                      shadow=True)

    def create_animation_frames(self, input_sequence: List[str]) -> List[Tuple]:
        """
        Создание кадров для анимации

        Returns:
            List[tuple]: Список кадров (текущие состояния, активные переходы, текст)
        """
        frames = []

        if not self.fsm.states or not self.fsm.start_state:
            return frames

        current_states = [self.fsm.start_state.name]
        frames.append((list(current_states), [], "Начальное состояние"))

        # Добавляем epsilon-замыкание для начального состояния
        epsilon_closure = self._get_epsilon_closure(current_states)
        if epsilon_closure != set(current_states):
            current_states = list(epsilon_closure)
            frames.append((list(current_states), [], "Epsilon-замыкание начального состояния"))

        for step, symbol in enumerate(input_sequence):
            next_states = []
            active_transitions = []

            # Обрабатываем epsilon-переходы перед каждым шагом
            for state_name in current_states:
                state = self.fsm.states[state_name]
                # Обрабатываем epsilon-переходы
                for transition in state.out_transitions:
                    if transition.symbol == 'epsilon':
                        next_states.append(transition.to_state)
                        active_transitions.append((transition.from_state,
                                                 transition.to_state,
                                                 'epsilon'))

            if active_transitions:
                frames.append((list(current_states),
                             list(active_transitions),
                             f"Шаг {step}.5: Epsilon-переходы"))

                # Обновляем текущие состояния с epsilon-замыканием
                current_states = list(set(current_states + next_states))
                next_states = []

            # Теперь обрабатываем переходы по символу
            active_transitions = []
            for state_name in current_states:
                state = self.fsm.states[state_name]
                for transition in state.out_transitions:
                    if transition.symbol == symbol:
                        next_states.append(transition.to_state)
                        active_transitions.append((transition.from_state,
                                                 transition.to_state,
                                                 symbol))

            symbol_display = 'ε' if symbol == 'epsilon' else symbol

            if active_transitions:
                frames.append((list(current_states),
                             list(active_transitions),
                             f"Шаг {step+1}: Вход '{symbol_display}'"))

                # Получаем epsilon-замыкание для новых состояний
                epsilon_closure = self._get_epsilon_closure(next_states)
                current_states = list(epsilon_closure)
                frames.append((list(current_states), [],
                             f"Шаг {step+1}: Новые состояния после epsilon-замыкания"))
            else:
                frames.append((list(current_states), [],
                             f"Шаг {step+1}: Нет перехода по '{symbol_display}'"))

        # Финальный кадр
        final_info = []
        for state_name in current_states:
            state = self.fsm.states[state_name]
            if state.is_final:
                final_info.append(f"{state_name} (конечное)")
            else:
                final_info.append(f"{state_name}")

        if final_info:
            frames.append((list(current_states), [],
                         f"Результат: {', '.join(final_info)}"))

        return frames

    def _get_epsilon_closure(self, states: List[str]) -> Set[str]:
        """Получение epsilon-замыкания для множества состояний"""
        closure = set(states)
        stack = list(states)

        while stack:
            current = stack.pop()
            state = self.fsm.states[current]

            for transition in state.out_transitions:
                if transition.symbol == 'epsilon' and transition.to_state not in closure:
                    closure.add(transition.to_state)
                    stack.append(transition.to_state)

        return closure

    def animate_workflow(self, input_sequence: List[str],
                        interval: int = 2000,
                        save_path: str = None) -> Optional[animation.FuncAnimation]:
        """
        Анимация работы автомата по входной последовательности

        Args:
            input_sequence: Последовательность входных символов
            interval: Интервал между кадрами (мс)
            save_path: Путь для сохранения анимации

        Returns:
            Объект анимации или None
        """
        if not self.fsm.states or not self.fsm.start_state:
            print("Автомат не инициализирован или не имеет начального состояния")
            return None

        # Подготавливаем граф
        self.build_graph()
        self.calculate_layout()

        # Получаем кадры анимации
        frames = self.create_animation_frames(input_sequence)
        if not frames:
            print("Не удалось создать кадры анимации")
            return None

        # Создаём фигуру
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        self.fig.patch.set_facecolor('#f0f0f0')
        self.ax.set_facecolor('#ffffff')

        # Создаём функцию обновления для анимации
        def update(frame_idx):
            self.ax.clear()
            self.ax.set_facecolor('#ffffff')

            if frame_idx >= len(frames):
                return

            current_states, active_transitions, text = frames[frame_idx]

            # Рисуем граф с подсветкой
            self._draw_graph(
                highlight_states=current_states,
                highlight_edges=active_transitions
            )

            # Добавляем легенду
            self._add_legend()

            # Информационная панель
            info_box = dict(
                boxstyle="round,pad=0.8",
                facecolor="lightyellow",
                edgecolor="orange",
                alpha=0.9,
                linewidth=2
            )

            # Отображаем историю
            history_text = "Ход работы:\n"
            for i, (states, trans, txt) in enumerate(frames[:frame_idx + 1]):
                marker = "→" if i > 0 else ""
                history_text += f"{marker} {txt}\n"

            self.ax.text(0.02, 0.98, history_text,
                       transform=self.ax.transAxes,
                       fontsize=10,
                       verticalalignment='top',
                       bbox=info_box)

            # Отображаем входную последовательность
            seq_display = []
            for symbol in input_sequence:
                if symbol == 'epsilon':
                    seq_display.append('ε')
                else:
                    seq_display.append(symbol)

            seq_text = "Входная последовательность:\n" + " → ".join(seq_display)
            current_step = min(frame_idx // 2, len(input_sequence)) if frame_idx > 0 else 0

            # Подсвечиваем текущий шаг
            seq_lines = []
            for i, symbol in enumerate(seq_display):
                if i == current_step and frame_idx % 2 == 1 and frame_idx > 0:
                    seq_lines.append(f"[{symbol}]")
                else:
                    seq_lines.append(symbol)

            seq_text = " → ".join(seq_lines)

            self.ax.text(0.02, 0.02, seq_text,
                       transform=self.ax.transAxes,
                       fontsize=11,
                       fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.5",
                                facecolor="lightblue",
                                edgecolor="blue",
                                alpha=0.8))

            # Заголовок с номером кадра
            self.ax.set_title(f"Работа конечного автомата | Кадр {frame_idx + 1}/{len(frames)}",
                            fontsize=16, fontweight='bold', pad=20)

            self.ax.axis('off')
            self.fig.tight_layout()

        # Создаём анимацию
        self.animation = animation.FuncAnimation(
            self.fig,
            update,
            frames=len(frames),
            interval=interval,
            repeat=False,
            blit=False
        )

        plt.tight_layout()

        if save_path:
            try:
                print(f"\nСоздание анимации... ({len(frames)} кадров)")
                self.animation.save(save_path,
                                  writer='pillow',
                                  fps=1000/interval,
                                  dpi=100,
                                  savefig_kwargs={'facecolor': '#f0f0f0'})
                print(f"✓ Анимация сохранена в {save_path}")
            except Exception as e:
                print(f"✗ Ошибка сохранения анимации: {e}")
                # Сохраняем последний кадр
                try:
                    update(len(frames) - 1)
                    last_frame_path = save_path.replace('.gif', '_final.png')
                    plt.savefig(last_frame_path, dpi=300, bbox_inches='tight')
                    print(f"✓ Последний кадр сохранен в {last_frame_path}")
                except:
                    pass

        plt.show()
        return self.animation


def export_to_matplotlib(fsm: FiniteStateMachine,
                        filename: str = "finite_automaton.png",
                        show: bool = True) -> str:
    """
    Экспорт автомата в изображение с использованием matplotlib

    Args:
        fsm: Конечный автомат
        filename: Имя выходного файла
        show: Показать окно с визуализацией

    Returns:
        str: Путь к сохранённому файлу
    """
    visualizer = FSMMatplotlibVisualizer(fsm)

    if not fsm.states:
        print("Автомат пуст, нечего экспортировать")
        return ""

    visualizer.build_graph()
    visualizer.calculate_layout()

    # Создаём фигуру
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('#f0f0f0')
    ax.set_facecolor('#ffffff')

    # Рисуем граф
    visualizer.ax = ax
    visualizer._draw_graph()

    # Добавляем легенду
    visualizer._add_legend()

    # Добавляем информацию об автомате
    info_text = f"Состояний: {len(fsm.states)}\n"
    info_text += f"Переходов: {sum(len(s.out_transitions) for s in fsm.states.values())}\n"

    if fsm.start_state:
        info_text += f"Начальное состояние: {fsm.start_state.name}\n"

    final_states = [name for name, state in fsm.states.items() if state.is_final]
    if final_states:
        info_text += f"Конечные состояния: {', '.join(final_states)}"

    ax.text(0.02, 0.02, info_text,
           transform=ax.transAxes,
           fontsize=10,
           bbox=dict(boxstyle="round,pad=0.5",
                    facecolor="lightblue",
                    edgecolor="blue",
                    alpha=0.8))

    ax.set_title("Конечный автомат", fontsize=18, fontweight='bold', pad=20)
    ax.axis('off')

    plt.tight_layout()

    if filename:
        try:
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='#f0f0f0')
            print(f"✓ Изображение сохранено в {filename}")
        except Exception as e:
            print(f"✗ Ошибка сохранения: {e}")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return filename


def create_animation(fsm: FiniteStateMachine,
                    input_sequence: List[str],
                    output_filename: str = "automaton_animation.gif") -> str:
    """
    Создание анимации работы автомата

    Args:
        fsm: Конечный автомат
        input_sequence: Последовательность входных символов
        output_filename: Имя выходного файла

    Returns:
        str: Путь к сохранённому файлу
    """
    visualizer = FSMMatplotlibVisualizer(fsm)
    anim = visualizer.animate_workflow(input_sequence, save_path=output_filename)
    return output_filename if anim else ""