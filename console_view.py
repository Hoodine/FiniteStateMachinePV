from fsm import FiniteStateMachine


def print_adjacency_matrix(fsm: FiniteStateMachine) -> None:
    """
    Вывод матрицы смежности в консоль

    Args:
        fsm (FiniteStateMachine): Конечный автомат
    """
    print("\n" + "=" * 50)
    print("МАТРИЦА СМЕЖНОСТИ")
    print("=" * 50)

    if not fsm.states:
        print("Автомат не содержит состояний")
        return

    matrix, state_names = fsm.get_adjacency_matrix()

    # Определяем ширину колонок
    col_width = max(len(name) for name in state_names) + 2
    first_col_width = max(8, col_width)

    # Вывод заголовка
    print("\n" + " " * first_col_width, end="")
    for name in state_names:
        print(f"{name:^{col_width}}", end="")
    print()

    # Вывод разделителя
    print("-" * (first_col_width + col_width * len(state_names)))

    # Вывод строк матрицы
    for i, name in enumerate(state_names):
        # Добавляем маркеры для стартового и конечного состояний
        state_marker = ""
        if fsm.states[name].is_start:
            state_marker += "→"
        if fsm.states[name].is_final:
            state_marker += "*"

        if state_marker:
            print(f"{name}{state_marker}:{''.ljust(first_col_width - len(name) - len(state_marker) - 1)}", end="")
        else:
            print(f"{name}:{''.ljust(first_col_width - len(name) - 1)}", end="")

        for j in range(len(state_names)):
            value = matrix[i][j]
            marker = "1" if value else "0"
            print(f"{marker:^{col_width}}", end="")
        print()


def print_transition_table(fsm: FiniteStateMachine) -> None:
    """
    Вывод таблицы переходов в консоль

    Args:
        fsm (FiniteStateMachine): Конечный автомат
    """
    print("\n" + "=" * 50)
    print("ТАБЛИЦА ПЕРЕХОДОВ")
    print("=" * 50)

    if not fsm.states:
        print("Автомат не содержит состояний")
        return

    table, alphabet = fsm.get_transition_table()

    if not alphabet:
        print("Автомат не содержит переходов с символами алфавита")
        return

    # Определяем ширину колонок
    state_width = max(len(name) for name in fsm.states.keys()) + 2
    symbol_width = max(len(str(symbol)) for symbol in alphabet) + 2

    # Вывод заголовка
    print(f"\n{'Сост.':^{state_width}}", end="")
    for symbol in alphabet:
        print(f"{symbol:^{symbol_width}}", end="")
    print()

    # Вывод разделителя
    print("-" * (state_width + symbol_width * len(alphabet)))

    # Вывод строк таблицы
    for state_name in fsm.states.keys():
        # Добавляем маркеры для стартового и конечного состояний
        state_marker = ""
        if fsm.states[state_name].is_start:
            state_marker += "→"
        if fsm.states[state_name].is_final:
            state_marker += "*"

        if state_marker:
            print(f"{state_name}{state_marker}".ljust(state_width), end="")
        else:
            print(f"{state_name}".ljust(state_width), end="")

        for symbol in alphabet:
            targets = table[state_name][symbol]
            if targets:
                cell_content = ", ".join(targets)

                print(f"{cell_content:^{symbol_width}}", end="")
            else:
                print(f"{'-':^{symbol_width}}", end="")
        print()


def print_fsm_summary(fsm: FiniteStateMachine) -> None:
    """
    Вывод сводной информации об автомате

    Args:
        fsm (FiniteStateMachine): Конечный автомат
    """
    print("\n" + "=" * 50)
    print("СВОДНАЯ ИНФОРМАЦИЯ")
    print("=" * 50)

    print(str(fsm))

    # Статистика по переходам
    print("\nПодробная информация о состояниях:")
    for state_name, state in fsm.states.items():
        type_info = []
        if state.is_start:
            type_info.append("стартовое")
        if state.is_final:
            type_info.append("конечное")

        type_str = f" ({', '.join(type_info)})" if type_info else ""

        print(f"  {state_name}{type_str}:")
        print(f"    Входящих переходов: {len(state.in_transitions)}")
        print(f"    Исходящих переходов: {len(state.out_transitions)}")

        if state.out_transitions:
            transitions_by_symbol = {}
            for trans in state.out_transitions:
                if trans.symbol not in transitions_by_symbol:
                    transitions_by_symbol[trans.symbol] = []
                transitions_by_symbol[trans.symbol].append(trans.to_state)

            for symbol, targets in transitions_by_symbol.items():
                print(f"    По '{symbol}' → {', '.join(targets)}")

    # Подсчет типов переходов
    epsilon_count = 0
    regular_count = 0

    for state in fsm.states.values():
        for transition in state.out_transitions:
            if transition.symbol == 'epsilon':
                epsilon_count += 1
            else:
                regular_count += 1

    print(f"\nСтатистика переходов:")
    print(f"  Обычные переходы: {regular_count}")
    print(f"  epsilon-переходы: {epsilon_count}")