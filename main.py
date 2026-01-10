from fsm import FiniteStateMachine
from fsm_io import input_fsm_from_console
from console_view import print_adjacency_matrix, print_transition_table, print_fsm_summary


def display_menu() -> None:
    """Отображение главного меню"""
    print("\n" + "=" * 50)
    print("ГЛАВНОЕ МЕНЮ - КОНЕЧНЫЕ АВТОМАТЫ")
    print("=" * 50)
    print("1. Создать новый автомат")
    print("2. Показать матрицу смежности")
    print("3. Показать таблицу переходов")
    print("4. Показать сводную информацию")
    print("5. Экспортировать в DOT формат (для Graphviz)")
    print("6. Создать тестовый автомат")
    print("7. Выход")
    print("=" * 50)


def export_to_dot(fsm, filename: str = "finite_automaton.dot") -> None:
    """
    Экспорт автомата в формат DOT для Graphviz

    Args:
        fsm: Конечный автомат
        filename (str): Имя выходного файла
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
                f.write(f"    \"\" [shape = none];\n")
                f.write(f"    \"\" -> \"{fsm.start_state.name}\";\n\n")

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
        print("Для визуализации используйте команду:")
        print(f"  dot -Tpng {filename} -o automaton.png")

    except Exception as e:
        print(f"Ошибка при экспорте: {e}")


def main() -> None:
    """Основная функция программы"""
    fsm = None

    while True:
        display_menu()

        try:
            choice = input("\nВыберите действие (1-7): ").strip()

            if choice == "1":
                fsm = input_fsm_from_console()
                print("\n Автомат успешно создан!")

            elif choice == "6":
                print("\n Создание автомата...")

                fsm = FiniteStateMachine()

                number_of_states = 3
                for i in range (number_of_states):
                    if i == 0:
                        fsm.add_state(f"q{i}", True, False)
                    elif i == number_of_states - 1:
                        fsm.add_state(f"q{i}", False, True)
                    else:
                        fsm.add_state(f"q{i}")

                fsm.add_transition("q0", "q1", "a")
                fsm.add_transition("q0", "q2", "epsilon")
                fsm.add_transition("q1", "q2", "b")
                fsm.add_transition("q2", "q0", "a")
                fsm.add_transition("q2", "q1", "z")

                print("\n Автомат успешно создан!")

            elif choice in ["2", "3", "4", "5"]:
                if fsm is None:
                    print("\n Сначала создайте или загрузите автомат!")
                    continue

                if choice == "2":
                    print_adjacency_matrix(fsm)
                elif choice == "3":
                    print_transition_table(fsm)
                elif choice == "4":
                    print_fsm_summary(fsm)
                elif choice == "5":
                    filename = input("Введите имя файла для экспорта (по умолчанию: automaton.dot): ").strip()
                    if not filename:
                        filename = "automaton.dot"
                    export_to_dot(fsm, filename)

            elif choice == "7":
                print("\nДо свидания!")
                break

            else:
                print("\n Неверный выбор. Пожалуйста, выберите от 1 до 7.")

        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем.")
            break
        except Exception as e:
            print(f"\n Произошла ошибка: {e}")


if __name__ == "__main__":
    main()