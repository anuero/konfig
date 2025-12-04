#!/usr/bin/env python3
"""
Configuration Language Parser - Variant 16
Парсер учебного конфигурационного языка с поддержкой констант и выражений
"""

import sys
import json
import argparse
from typing import Any, Dict, List
from lark import Lark, Transformer, Token, exceptions

# --- Грамматика языка с корректной поддержкой float, scinotation, и массивов ---
GRAMMAR = r"""
    start: statement*

    statement: constant_def
             | value

    constant_def: "def" NAME "=" value

    value: NUMBER
         | array
         | const_expr
         | NAME

    // Числовой литерал распознаётся как NUMBER
    NUMBER: /-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?/

    // Массивы поддерживают как круглые скобки, так и запятую для разделения элементов
    array: "(" ")"
         | "(" value ("," value)* ")"

    const_expr: ".[" expr "]."

    ?expr: term

    ?term: term "+" factor   -> add
         | term "-" factor   -> sub
         | factor

    ?factor: factor "*" power   -> mul
           | factor "/" power   -> div
           | power

    ?power: atom

    ?atom: "len" "(" expr ")"  -> len_func
         | array
         | "(" expr ")"
         | NUMBER
         | NAME

    NAME: /[_a-zA-Z][_a-zA-Z0-9]*/

    SINGLE_COMMENT: /;[^\n]*/
    MULTI_COMMENT: /=begin.*?=end/s

    %import common.WS
    %ignore WS
    %ignore SINGLE_COMMENT
    %ignore MULTI_COMMENT
"""


class ConfigTransformer(Transformer):
    """Трансформер для преобразования AST в структуры данных"""

    def __init__(self):
        super().__init__()
        self.constants: Dict[str, Any] = {}
        self.results: List[Any] = []

    def start(self, items):
        """Корневой элемент - возвращает все результаты"""
        return self.results if self.results else None

    def statement(self, items):
        """Обработка statement - добавляем в results только здесь"""
        if items and items[0] is not None:
            self.results.append(items[0])
        return items[0] if items else None

    def constant_def(self, items):
        """Определение константы: def имя = значение"""
        name = str(items[0])
        value = items[1]
        self.constants[name] = value
        return None

    def value(self, items):
        """Значение (число, массив, выражение, имя)"""
        item = items[0]
        if isinstance(item, Token) and item.type == "NAME":
            name = str(item)
            if name not in self.constants:
                raise ValueError(f"Undefined constant: {name}")
            return self.constants[name]
        return item

    def NUMBER(self, token):
        num_str = str(token)
        try:
            # float('1e2') and float('1.05e-6') supported
            if '.' in num_str or 'e' in num_str or 'E' in num_str:
                return float(num_str)
            else:
                return int(num_str)
        except ValueError:
            raise ValueError(f"Invalid number format: {num_str}")

    def array(self, items):
        """Обработка массива"""
        return list(items)

    def const_expr(self, items):
        """Вычисление константного выражения"""
        return items[0]

    def add(self, items):
        left, right = items
        return self._eval_value(left) + self._eval_value(right)

    def sub(self, items):
        left, right = items
        return self._eval_value(left) - self._eval_value(right)

    def mul(self, items):
        left, right = items
        return self._eval_value(left) * self._eval_value(right)

    def div(self, items):
        left, right = items
        rval = self._eval_value(right)
        if rval == 0:
            raise ValueError("Division by zero")
        return self._eval_value(left) / rval

    def len_func(self, items):
        val = self._eval_value(items[0])
        if isinstance(val, list):
            return len(val)
        elif isinstance(val, (int, float)):
            return 1
        else:
            raise ValueError(f"len() cannot be applied to {type(val)}")

    def _eval_value(self, value):
        """Вычисление значения (подстановка констант)"""
        if isinstance(value, Token):
            if value.type == "NAME":
                name = str(value)
                if name not in self.constants:
                    raise ValueError(f"Undefined constant: {name}")
                return self.constants[name]
            elif value.type == "NUMBER":
                return self.NUMBER(value)
        return value

    def NAME(self, token):
        return token


def parse_config(input_text: str) -> Any:
    """
    Парсинг конфигурационного файла

    Args:
        input_text: Текст конфигурации

    Returns:
        Распарсенная структура данных

    Raises:
        ValueError: При ошибках парсинга
    """
    try:
        # Для Earley-недопустим встроенный трансформер, поэтому парсим дерево,
        # а затем отдельно прогоняем через ConfigTransformer
        parser = Lark(GRAMMAR, parser='earley')
        tree = parser.parse(input_text)
        transformer = ConfigTransformer()
        result = transformer.transform(tree)
        return result
    except exceptions.LarkError as e:
        raise ValueError(f"Syntax error: {e}")
    except Exception as e:
        raise ValueError(f"Parse error: {e}")


def main():
    """Главная функция"""
    arg_parser = argparse.ArgumentParser(
        description="Configuration Language Parser (Variant 16)"
    )
    arg_parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output JSON file path'
    )

    args = arg_parser.parse_args()

    try:
        # Читаем из стандартного ввода
        input_text = sys.stdin.read()

        # Парсим
        result = parse_config(input_text)

        # Записываем в JSON файл
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Successfully parsed and saved to {args.output}")
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"IO Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())