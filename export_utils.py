"""
Утилиты для экспорта конечных автоматов
"""

from fsm import FiniteStateMachine


def export_to_dot_enhanced(fsm: FiniteStateMachine, filename: str = "finite_automaton.dot") -> None:
    """
    Улучшенный экспорт автомата в формат DOT для Graphviz

    Args:
        fsm: Конечный автомат
        filename (str): Имя выходного файла
    """
    if not fsm.states:
        return

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("digraph finite_automaton {\n")
        f.write("    rankdir=LR;\n")
        f.write("    node [shape = circle, fontname = \"Arial\"];\n")
        f.write("    edge [fontname = \"Arial\"];\n\n")

        # Стили для разных типов состояний
        f.write("    // Стили для состояний\n")
        f.write("    node [shape = circle];\n")
        f.write("    node [shape = doublecircle]; // для конечных состояний\n\n")

        # Добавляем невидимый узел для стрелки к начальному состоянию
        if fsm.start_state:
            f.write("    // Начальное состояние\n")
            f.write(f'    "__start__" [shape = none, label = "", width = 0, height = 0];\n')
            f.write(f'    "__start__" -> "{fsm.start_state.name}" [label = "start"];\n\n')

        # Добавляем состояния
        f.write("    // Состояния\n")
        for state_name, state in fsm.states.items():
            label = state_name

            # Добавляем маркеры в подпись
            markers = []
            if state.is_start:
                markers.append("S")
            if state.is_final:
                markers.append("F")

            if markers:
                label = f"{state_name}\\n({','.join(markers)})"

            if state.is_final:
                f.write(f'    "{state_name}" [label = "{label}", shape = doublecircle];\n')
            else:
                f.write(f'    "{state_name}" [label = "{label}"];\n')

        f.write("\n")

        # Добавляем переходы
        f.write("    // Переходы\n")
        transitions_added = set()

        for state_name, state in fsm.states.items():
            for transition in state.out_transitions:
                trans_key = (transition.from_state, transition.to_state, transition.symbol)
                if trans_key not in transitions_added:
                    label = transition.symbol
                    if label == 'epsilon':
                        label = 'ε'

                    # Настройки стиля для epsilon-переходов
                    edge_style = ""
                    if transition.symbol == 'epsilon':
                        edge_style = " [style = dashed, color = purple]"

                    f.write(f'    "{transition.from_state}" -> "{transition.to_state}" [label = "{label}"{edge_style}];\n')
                    transitions_added.add(trans_key)

        f.write("}\n")


def generate_dot_command(input_file: str, output_file: str = "automaton.png", format: str = "png") -> str:
    """
    Генерация команды Graphviz для визуализации

    Args:
        input_file (str): Входной DOT файл
        output_file (str): Выходной файл изображения
        format (str): Формат вывода (png, svg, pdf)

    Returns:
        str: Команда для выполнения
    """
    return f"dot -T{format} {input_file} -o {output_file}"


def save_visualization_pipeline(fsm: FiniteStateMachine, base_filename: str = "automaton"):
    """
    Полный пайплайн сохранения и визуализации

    Args:
        fsm: Конечный автомат
        base_filename (str): Базовое имя файла
    """
    dot_file = f"{base_filename}.dot"
    png_file = f"{base_filename}.png"

    # Экспорт в DOT
    export_to_dot_enhanced(fsm, dot_file)

    # Генерация команды
    command = generate_dot_command(dot_file, png_file)

    return dot_file, png_file, command