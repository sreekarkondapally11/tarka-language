
import sys

from tarka_lexer import Lexer, LexerError
from tarka_parser import (
    Parser,
    ParserError,
    Number,
    String,
    Boolean,
    Null,
    Variable,
    Binary,
    Unary,
    VariableDeclaration,
    InputStatement,
    PrintStatement,
    IfStatement,
)


class InterpreterError(Exception):
    pass


class Interpreter:
    def __init__(self):
        self.environment = {}

    def interpret(self, program):
        for statement in program.statements:
            self.execute(statement)

    def execute(self, statement):
        if isinstance(statement, VariableDeclaration):
            value = self.evaluate(statement.initializer)
            self.environment[statement.name] = value

        elif isinstance(statement, InputStatement):
            try:
                value = input(f"{statement.name}: ")
            except EOFError:
                raise InterpreterError("No input was provided.")

            # Input values are strings initially.
            self.environment[statement.name] = value

        elif isinstance(statement, PrintStatement):
            value = self.evaluate(statement.expression)
            print(self.display(value))

        elif isinstance(statement, IfStatement):
            condition = self.evaluate(statement.condition)
            self.require_boolean(condition, "If condition")

            if condition:
                self.execute_block(statement.then_branch)
            else:
                self.execute_block(statement.else_branch)

        else:
            raise InterpreterError(
                f"Unsupported statement: {type(statement).__name__}"
            )

    def execute_block(self, statements):
        for statement in statements:
            self.execute(statement)

    def evaluate(self, expression):
        if isinstance(expression, Number):
            return expression.value

        if isinstance(expression, String):
            return expression.value

        if isinstance(expression, Boolean):
            return expression.value

        if isinstance(expression, Null):
            return None

        if isinstance(expression, Variable):
            if expression.name not in self.environment:
                raise InterpreterError(
                    f"Undefined variable '{expression.name}'."
                )
            return self.environment[expression.name]

        if isinstance(expression, Unary):
            return self.evaluate_unary(expression)

        if isinstance(expression, Binary):
            return self.evaluate_binary(expression)

        raise InterpreterError(
            f"Unsupported expression: {type(expression).__name__}"
        )

    def evaluate_unary(self, expression):
        value = self.evaluate(expression.right)
        operator = expression.operator.type

        if operator in ("NOT", "BANG"):
            self.require_boolean(value, "The 'na' operator")
            return not value

        if operator == "MINUS":
            self.require_number(value, "Unary minus")
            return -value

        raise InterpreterError(
            f"Unknown unary operator '{expression.operator.lexeme}'."
        )

    def evaluate_binary(self, expression):
        operator = expression.operator.type

        # Logical operators use short-circuit evaluation.
        left = self.evaluate(expression.left)

        if operator == "OR":
            self.require_boolean(left, "The 'va' operator")
            if left:
                return True

            right = self.evaluate(expression.right)
            self.require_boolean(right, "The 'va' operator")
            return right

        if operator == "AND":
            self.require_boolean(left, "The 'cha' operator")
            if not left:
                return False

            right = self.evaluate(expression.right)
            self.require_boolean(right, "The 'cha' operator")
            return right

        right = self.evaluate(expression.right)

        if operator == "EQUAL_EQUAL":
            if self.is_number(left) and self.is_number(right):
                return left == right
            return type(left) is type(right) and left == right

        if operator == "BANG_EQUAL":
            if self.is_number(left) and self.is_number(right):
                return left != right
            return type(left) is not type(right) or left != right

        if operator in ("GREATER", "GREATER_EQUAL", "LESS", "LESS_EQUAL"):
            self.require_number(left, "Comparison")
            self.require_number(right, "Comparison")

            if operator == "GREATER":
                return left > right
            if operator == "GREATER_EQUAL":
                return left >= right
            if operator == "LESS":
                return left < right
            if operator == "LESS_EQUAL":
                return left <= right

        if operator == "PLUS":
            if type(left) is str and type(right) is str:
                return left + right

            self.require_number(left, "Addition")
            self.require_number(right, "Addition")
            return left + right

        if operator == "MINUS":
            self.require_number(left, "Subtraction")
            self.require_number(right, "Subtraction")
            return left - right

        if operator == "STAR":
            self.require_number(left, "Multiplication")
            self.require_number(right, "Multiplication")
            return left * right

        if operator == "SLASH":
            self.require_number(left, "Division")
            self.require_number(right, "Division")

            if right == 0:
                raise InterpreterError("Division by zero.")

            return left / right

        if operator == "PERCENT":
            self.require_number(left, "Modulo")
            self.require_number(right, "Modulo")

            if right == 0:
                raise InterpreterError("Modulo by zero.")

            return left % right

        raise InterpreterError(
            f"Unknown operator '{expression.operator.lexeme}'."
        )

    @staticmethod
    def is_number(value):
        # bool is a subclass of int in Python, so exclude it.
        return type(value) in (int, float)

    def require_number(self, value, operation):
        if not self.is_number(value):
            raise InterpreterError(
                f"{operation} requires numeric values, "
                f"but received {type(value).__name__}."
            )

    @staticmethod
    def require_boolean(value, operation):
        if type(value) is not bool:
            raise InterpreterError(
                f"{operation} requires a boolean value."
            )

    @staticmethod
    def display(value):
        if value is None:
            return "shunyam"
        return str(value)


def run(source):
    tokens = Lexer(source).scan_tokens()
    program = Parser(tokens).parse()
    interpreter = Interpreter()
    interpreter.interpret(program)


DEMO_PROGRAM = '''
mana age = 20
mana price = 99.50
mana name = "Tarka"
mana ready = satyam

mudraya age
mudraya price
mudraya name

yadi (age >= 18 cha ready) {
    mudraya "You are an adult"
} anyatha {
    mudraya "You are a minor"
}

yadi (na asatyam va age < 10) {
    mudraya "Logical operators work!"
}

pravesha city
mudraya "Welcome from:"
mudraya city
'''


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            filename = sys.argv[1]

            with open(filename, "r", encoding="utf-8") as file:
                source = file.read()
        else:
            print("Tarka v0.2 - Experimental Interpreter")
            print("Running demonstration program...\n")
            source = DEMO_PROGRAM

        run(source)

    except FileNotFoundError as error:
        print(f"Tarka Error: File not found: {error.filename}")

    except (LexerError, ParserError, InterpreterError) as error:
        print(f"Tarka Error: {error}")

    except KeyboardInterrupt:
        print("\nTarka execution interrupted.")
