
import unittest
import json
import tempfile
import os
from config_parser import parse_config


class TestConfigParser(unittest.TestCase):
    
    def test_single_comment(self):
        config = """
        ; Это комментарий
        42
        """
        result = parse_config(config)
        self.assertEqual(result, [42])
    
    def test_multi_comment(self):
        config = """
        =begin
        Это многострочный
        комментарий
        =end
        3.14
        """
        result = parse_config(config)
        self.assertEqual(result, [3.14])
    
    def test_integer_number(self):
        config = "123"
        result = parse_config(config)
        self.assertEqual(result, [123])
    
    def test_negative_number(self):
        config = "-456"
        result = parse_config(config)
        self.assertEqual(result, [-456])
    
    def test_float_number(self):
        config = "3.14159"
        result = parse_config(config)
        self.assertAlmostEqual(result[0], 3.14159)
    
    def test_scientific_notation(self):
        config = "1.5e10"
        result = parse_config(config)
        self.assertAlmostEqual(result[0], 1.5e10)
    
    def test_scientific_notation_negative_exp(self):
        config = "2.5e-3"
        result = parse_config(config)
        self.assertAlmostEqual(result[0], 2.5e-3)
    
    def test_empty_array(self):
        config = "()"
        result = parse_config(config)
        self.assertEqual(result, [[]])
    
    def test_simple_array(self):
        config = "(1, 2, 3)"
        result = parse_config(config)
        self.assertEqual(result, [[1, 2, 3]])
    
    def test_nested_array(self):
        config = "(1, (2, 3), 4)"
        result = parse_config(config)
        self.assertEqual(result, [[1, [2, 3], 4]])
    
    def test_array_with_floats(self):
        config = "(1.1, 2.2, 3.3)"
        result = parse_config(config)
        self.assertEqual(len(result[0]), 3)
        self.assertAlmostEqual(result[0][0], 1.1)
        self.assertAlmostEqual(result[0][1], 2.2)
        self.assertAlmostEqual(result[0][2], 3.3)
    
    def test_constant_definition(self):
        config = """
        def x = 10
        x
        """
        result = parse_config(config)
        self.assertEqual(result, [10])
    
    def test_constant_in_array(self):
        config = """
        def x = 5
        (x, 10, x)
        """
        result = parse_config(config)
        self.assertEqual(result, [[5, 10, 5]])
    
    def test_const_expr_addition(self):
        config = """
        def x = 10
        .[x + 5].
        """
        result = parse_config(config)
        self.assertEqual(result, [15])
    
    def test_const_expr_subtraction(self):
        config = """
        def y = 20
        .[y - 7].
        """
        result = parse_config(config)
        self.assertEqual(result, [13])
    
    def test_const_expr_multiplication(self):
        config = """
        def z = 6
        .[z * 7].
        """
        result = parse_config(config)
        self.assertEqual(result, [42])
    
    def test_const_expr_division(self):
        config = """
        def a = 100
        .[a / 4].
        """
        result = parse_config(config)
        self.assertEqual(result, [25.0])
    
    def test_const_expr_complex(self):
        config = """
        def x = 10
        def y = 5
        .[x + y * 2].
        """
        result = parse_config(config)
        self.assertEqual(result, [20])
    
    def test_len_function_array(self):
        config = """
        def arr = (1, 2, 3, 4, 5)
        .[len(arr)].
        """
        result = parse_config(config)
        self.assertEqual(result, [5])
    
    def test_len_function_number(self):
        config = """
        def num = 42
        .[len(num)].
        """
        result = parse_config(config)
        self.assertEqual(result, [1])
    
    def test_multiple_statements(self):
        config = """
        def x = 10
        5
        (1, 2, 3)
        .[x + 5].
        """
        result = parse_config(config)
        self.assertEqual(result, [5, [1, 2, 3], 15])
    
    def test_division_by_zero(self):
        config = """
        def x = 10
        .[x / 0].
        """
        with self.assertRaises(ValueError) as context:
            parse_config(config)
        self.assertIn("Division by zero", str(context.exception))
    
    def test_undefined_constant(self):
        config = """
        undefined_var
        """
        with self.assertRaises(ValueError) as context:
            parse_config(config)
        self.assertIn("Undefined constant", str(context.exception))
    
    def test_complex_nested_structure(self):
        config = """
        def base = 10
        def multiplier = 3
        
        ; Главный массив конфигурации
        (
            .[base * multiplier].,
            (1, 2, (3, 4)),
            .[len((1, 2, 3, 4, 5))].
        )
        """
        result = parse_config(config)
        self.assertEqual(result, [[30, [1, 2, [3, 4]], 5]])


class TestConfigParserEdgeCases(unittest.TestCase):
    
    def test_empty_input(self):
        config = ""
        result = parse_config(config)
        self.assertIsNone(result)
    
    def test_only_comments(self):
        config = """
        ; Комментарий 1
        =begin
        Многострочный комментарий
        =end
        ; Комментарий 2
        """
        result = parse_config(config)
        self.assertIsNone(result)
    
    def test_underscore_in_name(self):
        config = """
        def my_var = 42
        def _private = 10
        (my_var, _private)
        """
        result = parse_config(config)
        self.assertEqual(result, [[42, 10]])
    
    def test_expression_with_parentheses(self):
        config = """
        def a = 2
        def b = 3
        def c = 4
        .[a * (b + c)].
        """
        result = parse_config(config)
        self.assertEqual(result, [14])


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestConfigParser))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigParserEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())