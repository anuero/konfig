
import sys
import json
import argparse
from typing import Any, Dict, List
from lark import Lark, Transformer, Token, exceptions

GRAMMAR = r"""
    start: statement*

    statement: constant_def
             | value

    constant_def: "def" NAME "=" value

    value: NUMBER
         | array
         | const_expr
         | NAME

    NUMBER: /-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?/

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

    def __init__(self):
        super().__init__()
        self.constants: Dict[str, Any] = {}
        self.results: List[Any] = []

    def start(self, items):
        # Возвращаем структурированный объект с константами и значениями
        result = {
            "constants": self.constants,
            "values": self.results
        }
        return result if self.results or self.constants else None

    def statement(self, items):
        if items and items[0] is not None:
            # Сохраняем statement как словарь с типом и значением
            statement_data = items[0]
            if isinstance(statement_data, dict) and statement_data.get("type") == "constant":
                # Константа уже обработана в constant_def
                pass
            else:
                # Это значение - сохраняем его
                self.results.append(statement_data)
        return items[0] if items else None

    def constant_def(self, items):
        name = str(items[0])
        value = items[1]
        self.constants[name] = value
        # Возвращаем структурированный объект для константы
        return {"type": "constant", "name": name, "value": value}

    def value(self, items):
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
            if '.' in num_str or 'e' in num_str or 'E' in num_str:
                return float(num_str)
            else:
                return int(num_str)
        except ValueError:
            raise ValueError(f"Invalid number format: {num_str}")

    def array(self, items):
        return list(items)

    def const_expr(self, items):
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
    try:
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
        input_text = sys.stdin.read()

        result = parse_config(input_text)

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
