from fsm import FiniteStateMachine


def input_fsm_from_console() -> FiniteStateMachine:
    """
    Интерактивный ввод описания конечного автомата с консоли

    Returns:
        FiniteStateMachine: Созданный конечный автомат
    """
    print("=" * 50)
    print("СОЗДАНИЕ КОНЕЧНОГО АВТОМАТА")
    print("=" * 50)

    fsm = FiniteStateMachine()

    # Ввод состояний
    print("\n--- Ввод состояний ---")
    while True:
        try:
            num_states = int(input("Введите количество состояний (минимум 1): "))
            if num_states > 0:
                break
            print("Количество состояний должно быть положительным числом!")
        except ValueError:
            print("Пожалуйста, введите целое число!")

    print("\nФормат ввода состояния: <имя> [<тип>]")
    print("Типы: '+' - стартовое, '*' - конечное, '+*' - стартовое и конечное")
    print("Примеры: q0 +, q1 *, q2, q3 +*")

    for i in range(num_states):
        while True:
            try:
                state_input = input(f"Состояние {i + 1}: ").strip()
                if not state_input:
                    print("Имя состояния не может быть пустым!")
                    continue

                parts = state_input.split()
                name = parts[0]

                # Проверяем тип состояния
                is_start = False
                is_final = False

                if len(parts) > 1:
                    type_str = parts[1]
                    if '+' in type_str:
                        is_start = True
                    if '*' in type_str:
                        is_final = True

                fsm.add_state(name, is_start, is_final)
                break

            except ValueError as e:
                print(f"Ошибка: {e}")

    # Ввод переходов
    print("\n--- Ввод переходов ---")
    while True:
        try:
            num_transitions = int(input("Введите количество переходов: "))
            if num_transitions >= 0:
                break
            print("Количество переходов не может быть отрицательным!")
        except ValueError:
            print("Пожалуйста, введите целое число!")

    print("\nФормат ввода перехода: <из> <символ> <в>")
    print("Примеры: q0 a q1, q1 ε q2, q2 b q0")
    print("Для epsilon-переходов используйте 'epsilon'")

    for i in range(num_transitions):
        while True:
            try:
                transition_input = input(f"Переход {i + 1}: ").strip()
                if not transition_input:
                    print("Ввод перехода не может быть пустым!")
                    continue

                parts = transition_input.split()
                if len(parts) != 3:
                    print("Неверный формат! Используйте: <из> <символ> <в>")
                    continue

                from_state, symbol, to_state = parts

                # Обработка epsilon-переходов
                if symbol.lower() == 'epsilon' or symbol == 'epsilon':
                    symbol = 'epsilon'

                fsm.add_transition(from_state, to_state, symbol)
                break

            except ValueError as e:
                print(f"Ошибка: {e}")

    # Валидация автомата
    print("\n--- Валидация автомата ---")
    is_valid, messages = fsm.validate()

    if messages:
        print("\nРезультаты проверки:")
        for msg in messages:
            if "Ошибка" in msg or msg.startswith("Не"):
                print(f"  КАЛЛ  {msg}")
            else:
                print(f"  !  {msg}")

    if not is_valid:
        print("\nВ автомате есть ошибки.")

    return fsm