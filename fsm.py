from typing import List, Set, Dict, Optional, Tuple


class Transition:
    """Класс, представляющий переход в конечном автомате"""

    def __init__(self, from_state: str, to_state: str, symbol: str):
        """
        Инициализация перехода

        Args:
            from_state (str): Имя исходного состояния
            to_state (str): Имя целевого состояния
            symbol (str): Символ перехода (для ε-переходов использовать 'ε')
        """
        self.from_state = from_state
        self.to_state = to_state
        self.symbol = symbol

    def __repr__(self):
        """Строковое представление для отладки"""
        return f"Transition({self.from_state} -> {self.to_state} : '{self.symbol}')"

    def __str__(self):
        """Человекочитаемое строковое представление"""
        return f"{self.from_state} --[{self.symbol}]--> {self.to_state}"

class State:
    """Класс, представляющий состояние конечного автомата"""

    def __init__(self, name: str, is_start: bool = False, is_final: bool = False):
        """
        Инициализация состояния

        Args:
            name (str): Уникальное имя состояния
            is_start (bool): Является ли состояние начальным
            is_final (bool): Является ли состояние допускающим
        """
        self.name = name
        self.is_start = is_start
        self.is_final = is_final
        self.in_transitions: List[Transition] = []
        self.out_transitions: List[Transition] = []

    def add_transition(self, transition: Transition, is_outgoing: bool = True):
        """
        Добавление перехода к состоянию

        Args:
            transition (Transition): Объект перехода
            is_outgoing (bool): True - исходящий переход, False - входящий
        """
        if is_outgoing:
            self.out_transitions.append(transition)
        else:
            self.in_transitions.append(transition)

    def get_adjacent_states(self) -> Set[str]:
        """
        Получить множество соседних состояний (достижимых по одному переходу)

        Returns:
            Set[str]: Множество имен соседних состояний
        """
        adjacent = set()
        for transition in self.out_transitions:
            adjacent.add(transition.to_state)
        return adjacent

    def get_transitions_by_symbol(self, symbol: str) -> List[str]:
        """
        Получить список целевых состояний для заданного символа

        Args:
            symbol (str): Символ перехода

        Returns:
            List[str]: Список имен целевых состояний
        """
        targets = []
        for transition in self.out_transitions:
            if transition.symbol == symbol:
                targets.append(transition.to_state)
        return targets

    def __repr__(self):
        """Строковое представление для отладки"""
        return (f"State('{self.name}', start={self.is_start}, "
                f"final={self.is_final}, in={len(self.in_transitions)}, "
                f"out={len(self.out_transitions)})")

    def __str__(self):
        """Читаемое строковое представление"""
        type_str = ""
        if self.is_start and self.is_final:
            type_str = " (стартовое и конечное)"
        elif self.is_start:
            type_str = " (стартовое)"
        elif self.is_final:
            type_str = " (конечное)"
        return f"Состояние: {self.name}{type_str}"


class FiniteStateMachine:
    """Класс, представляющий конечный автомат"""

    def __init__(self):
        """Инициализация пустого конечного автомата"""
        self.states: Dict[str, State] = {}
        self.alphabet: Set[str] = set()
        self.start_state: Optional[State] = None

    def add_state(self, name: str, is_start: bool = False, is_final: bool = False) -> State:
        """
        Добавление состояния в автомат

        Args:
            name (str): Имя состояния
            is_start (bool): Является ли состояние начальным
            is_final (bool): Является ли состояние допускающим

        Returns:
            State: Созданное состояние

        Raises:
            ValueError: Если состояние с таким именем уже существует
        """
        if name in self.states:
            raise ValueError(f"Состояние с именем '{name}' уже существует")

        state = State(name, is_start, is_final)
        self.states[name] = state

        if is_start:
            if self.start_state is not None:
                print(f"Предупреждение: начальное состояние уже установлено ({self.start_state.name})")
            self.start_state = state

        return state

    def add_transition(self, from_name: str, to_name: str, symbol: str) -> None:
        """
        Добавление перехода между состояниями

        Args:
            from_name (str): Имя исходного состояния
            to_name (str): Имя целевого состояния
            symbol (str): Символ перехода

        Raises:
            ValueError: Если одно из состояний не существует
        """


        # Создаем переход
        transition = Transition(from_name, to_name, symbol)

        # Добавляем переход к исходному состоянию (исходящий)
        self.states[from_name].add_transition(transition, is_outgoing=True)

        # Добавляем переход к целевому состоянию (входящий)
        self.states[to_name].add_transition(transition, is_outgoing=False)

        # Добавляем символ в алфавит (если не ε)
        if symbol != 'epsilon':
            self.alphabet.add(symbol)

    def set_start_state(self, state_name: str) -> None:
        """
        Установка начального состояния

        Args:
            state_name (str): Имя состояния

        Raises:
            ValueError: Если состояние не существует
        """
        if state_name not in self.states:
            raise ValueError(f"Состояние '{state_name}' не существует")

        # Снимаем флаг стартового с предыдущего состояния
        if self.start_state:
            self.start_state.is_start = False

        # Устанавливаем новое стартовое состояние
        self.start_state = self.states[state_name]
        self.start_state.is_start = True

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Проверка корректности автомата

        Returns:
            Tuple[bool, List[str]]: (Успешность проверки, список ошибок/предупреждений)
        """
        errors = []
        warnings = []

        # Проверка наличия состояний
        if not self.states:
            errors.append("Автомат не содержит состояний")

        # Проверка наличия начального состояния
        if self.start_state is None:
            errors.append("Не указано начальное состояние")

        # Проверка уникальности имен состояний (уже гарантируется в add_state)

        # Проверка на изолированные состояния
        for state_name, state in self.states.items():
            if not state.in_transitions and not state.out_transitions:
                warnings.append(f"Состояние '{state_name}' изолировано (нет переходов)")
            elif not state.out_transitions and not state.is_final:
                warnings.append(f"Состояние '{state_name}' не имеет исходящих переходов и не является конечным")

        # Проверка на недостижимые состояния
        if self.start_state:
            reachable = self._get_reachable_states()
            unreachable = set(self.states.keys()) - reachable
            for state_name in unreachable:
                warnings.append(f"Состояние '{state_name}' недостижимо из начального состояния")

        return len(errors) == 0, errors + warnings

    def _get_reachable_states(self) -> Set[str]:
        """Получить все состояния, достижимые из начального"""
        if not self.start_state:
            return set()

        reachable = set()
        stack = [self.start_state.name]

        while stack:
            current_name = stack.pop()
            if current_name in reachable:
                continue

            reachable.add(current_name)
            current_state = self.states[current_name]

            for transition in current_state.out_transitions:
                if transition.to_state not in reachable:
                    stack.append(transition.to_state)

        return reachable

    def get_adjacency_matrix(self) -> Tuple[List[List[int]], List[str]]:
        """
        Получение матрицы смежности

        Returns:
            Tuple[List[List[int]], List[str]]: (матрица смежности, список имен состояний)
        """
        state_names = list(self.states.keys())
        n = len(state_names)

        # Создаем матрицу N x N, заполненную нулями
        matrix = [[0 for _ in range(n)] for _ in range(n)]

        # Заполняем матрицу
        for i, from_name in enumerate(state_names):
            from_state = self.states[from_name]
            for transition in from_state.out_transitions:
                j = state_names.index(transition.to_state)
                matrix[i][j] = 1

        return matrix, state_names

    def get_transition_table(self) -> Tuple[Dict[str, Dict[str, List[str]]], List[str]]:
        """
        Получение таблицы переходов

        Returns:
            Tuple[Dict, List[str]]: (таблица переходов, отсортированный алфавит)
        """
        # Сортируем алфавит, добавляя ε-переходы в начало если есть
        sorted_alphabet = sorted(self.alphabet)

        # Проверяем наличие ε-переходов
        has_epsilon = any(
            transition.symbol == 'epsilon'
            for state in self.states.values()
            for transition in state.out_transitions
        )

        if has_epsilon:
            sorted_alphabet = ['epsilon'] + sorted_alphabet

        # Создаем таблицу переходов
        table = {}

        for state_name, state in self.states.items():
            table[state_name] = {}
            for symbol in sorted_alphabet:
                table[state_name][symbol] = state.get_transitions_by_symbol(symbol)

        return table, sorted_alphabet

    def __str__(self):
        """Строковое представление автомата"""
        if not self.states:
            return "Пустой автомат"

        result = ["Конечный автомат:"]
        result.append(f"  Состояний: {len(self.states)}")
        result.append(f"  Алфавит: {sorted(self.alphabet)}")

        if self.start_state:
            result.append(f"  Начальное состояние: {self.start_state.name}")

        final_states = [name for name, state in self.states.items() if state.is_final]
        if final_states:
            result.append(f"  Конечные состояния: {', '.join(final_states)}")

        # Подсчет переходов
        total_transitions = sum(len(state.out_transitions) for state in self.states.values())
        result.append(f"  Всего переходов: {total_transitions}")

        return "\n".join(result)