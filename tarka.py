
from dataclasses import dataclass


# ============================================================
# TARKA v0.5
# Lexer + Parser + Interpreter
# ============================================================


# -------------------- ERRORS --------------------

class TarkaError(Exception):
    pass


class LexerError(TarkaError):
    pass


class ParserError(TarkaError):
    pass


class InterpreterError(TarkaError):
    pass


# -------------------- LEXER --------------------

@dataclass
class Token:
    type: str
    value: object
    line: int
    column: int


KEYWORDS = {
    "mana": "MANA",
    "mudraya": "MUDRAYA",
    "pravesha": "PRAVESHA",
    "yadi": "YADI",
    "anyatha": "ANYATHA",
    "yavat": "YAVAT",
    "avartta": "AVARTTA",
    "kriya": "KRIYA",
    "pratyarpanam": "RETURN",
    "virama": "BREAK",
    "anuvartta": "CONTINUE",
    "satyam": "TRUE",
    "asatyam": "FALSE",
    "shunyam": "NULL",
    "cha": "AND",
    "va": "OR",
    "na": "NOT",
}


class Lexer:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.current = 0
        self.line = 1
        self.column = 1

    def scan(self):
        while self.current < len(self.source):
            char = self.source[self.current]

            if char in " \t\r":
                self.advance()
                continue

            if char == "\n":
                self.add("NEWLINE", None)
                self.advance()
                continue

            if char == "/" and self.peek(1) == "/":
                while (
                    self.current < len(self.source)
                    and self.source[self.current] != "\n"
                ):
                    self.advance()
                continue

            start_line = self.line
            start_column = self.column

            if char.isdigit():
                self.number(start_line, start_column)
            elif char.isalpha() or char == "_":
                self.identifier(start_line, start_column)
            elif char == '"':
                self.string(start_line, start_column)
            else:
                self.symbol(start_line, start_column)

        self.tokens.append(
            Token("EOF", None, self.line, self.column)
        )
        return self.tokens

    def advance(self):
        char = self.source[self.current]
        self.current += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def peek(self, offset=0):
        position = self.current + offset

        if position >= len(self.source):
            return "\0"

        return self.source[position]

    def add(self, token_type, value):
        self.tokens.append(
            Token(token_type, value, self.line, self.column)
        )

    def number(self, line, column):
        start = self.current

        while self.peek().isdigit():
            self.advance()

        is_float = False

        if self.peek() == "." and self.peek(1).isdigit():
            is_float = True
            self.advance()

            while self.peek().isdigit():
                self.advance()

        text = self.source[start:self.current]
        value = float(text) if is_float else int(text)

        self.tokens.append(Token("NUMBER", value, line, column))

    def identifier(self, line, column):
        start = self.current

        while self.peek().isalnum() or self.peek() == "_":
            self.advance()

        word = self.source[start:self.current]

        token_type = KEYWORDS.get(word, "IDENTIFIER")

        self.tokens.append(
            Token(token_type, word, line, column)
        )

    def string(self, line, column):
        # Consume the opening quote, then read until the matching quote.
        self.advance()
        value = ""

        escape_map = {
            "n": "\n",
            "t": "\t",
            '"': '"',
            "\\": "\\",
        }

        while self.current < len(self.source):
            char = self.advance()

            if char == '"':
                self.tokens.append(
                    Token("STRING", value, line, column)
                )
                return

            if char == "\n":
                raise LexerError(
                    f"Unterminated string at line {line}, column {column}."
                )

            if char == "\\":
                if self.current >= len(self.source):
                    raise LexerError(
                        f"Unterminated escape sequence at line {self.line}, "
                        f"column {self.column}."
                    )

                escaped = self.advance()
                if escaped not in escape_map:
                    raise LexerError(
                        f"Unknown escape sequence '\\{escaped}' at "
                        f"line {self.line}, column {self.column - 1}."
                    )
                value += escape_map[escaped]
            else:
                value += char

        raise LexerError(
            f"Unterminated string at line {line}, column {column}."
        )

    def symbol(self, line, column):
        char = self.advance()

        symbols = {
            "(": "LEFT_PAREN",
            ")": "RIGHT_PAREN",
            "{": "LEFT_BRACE",
            "}": "RIGHT_BRACE",
            "[": "LEFT_BRACKET",
            "]": "RIGHT_BRACKET",
            ",": "COMMA",
            ":": "COLON",
            ";": "SEMICOLON",
            "+": "PLUS",
            "-": "MINUS",
            "*": "STAR",
            "/": "SLASH",
            "%": "PERCENT",
        }

        if char == "=":
            token_type = (
                "EQUAL_EQUAL" if self.peek() == "=" else "EQUAL"
            )
            if token_type == "EQUAL_EQUAL":
                self.advance()

        elif char == "!":
            token_type = (
                "BANG_EQUAL" if self.peek() == "=" else "BANG"
            )
            if token_type == "BANG_EQUAL":
                self.advance()

        elif char == "<":
            token_type = (
                "LESS_EQUAL" if self.peek() == "=" else "LESS"
            )
            if token_type == "LESS_EQUAL":
                self.advance()

        elif char == ">":
            token_type = (
                "GREATER_EQUAL" if self.peek() == "=" else "GREATER"
            )
            if token_type == "GREATER_EQUAL":
                self.advance()

        elif char in symbols:
            token_type = symbols[char]

        else:
            raise LexerError(
                f"Unexpected character '{char}' "
                f"at line {line}, column {column}"
            )

        self.tokens.append(
            Token(token_type, char, line, column)
        )

        # Preserve the full operator spelling.
        if token_type in (
            "EQUAL_EQUAL", "BANG_EQUAL",
            "LESS_EQUAL", "GREATER_EQUAL"
        ):
            self.tokens[-1].value = char + "="


# -------------------- PARSER --------------------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []
        self.skip_newlines()

        while not self.check("EOF"):
            statements.append(self.statement())
            self.skip_newlines()

        return statements

    def statement(self):
        if self.match("MANA"):
            return self.variable_declaration()

        if self.match("PRAVESHA"):
            name = self.consume(
                "IDENTIFIER", "Expected a variable name."
            ).value
            self.end_statement()
            return ("input", name)

        if self.match("MUDRAYA"):
            expression = self.expression()
            self.end_statement()
            return ("print", expression)

        if self.match("YADI"):
            return self.if_statement()

        if self.match("YAVAT"):
            return self.while_statement()

        if self.match("AVARTTA"):
            return self.for_statement()

        if self.match("KRIYA"):
            return self.function_declaration()

        if self.match("RETURN"):
            expression = None

            if not self.check("NEWLINE") and not self.check("RIGHT_BRACE"):
                expression = self.expression()

            self.end_statement()
            return ("return", expression)

        if self.match("BREAK"):
            self.end_statement()
            return ("break",)

        if self.match("CONTINUE"):
            self.end_statement()
            return ("continue",)

        expression = self.expression()
        self.end_statement()

        return ("expression", expression)

    def variable_declaration(self, consume_end=True):
        name = self.consume(
            "IDENTIFIER", "Expected a variable name."
        ).value

        self.consume("EQUAL", "Expected '=' after variable name.")
        value = self.expression()

        if consume_end:
            self.end_statement()

        return ("var", name, value)

    def if_statement(self):
        self.consume("LEFT_PAREN", "Expected '(' after yadi.")
        condition = self.expression()
        self.consume("RIGHT_PAREN", "Expected ')' after condition.")

        self.skip_newlines()
        then_branch = self.block()

        self.skip_newlines()
        else_branch = []

        if self.match("ANYATHA"):
            self.skip_newlines()
            else_branch = self.block()

        return ("if", condition, then_branch, else_branch)

    def while_statement(self):
        self.consume("LEFT_PAREN", "Expected '(' after yavat.")
        condition = self.expression()
        self.consume("RIGHT_PAREN", "Expected ')' after condition.")

        self.skip_newlines()
        body = self.block()

        return ("while", condition, body)

    def for_statement(self):
        self.consume("LEFT_PAREN", "Expected '(' after avartta.")

        self.skip_newlines()

        initializer = None

        if not self.check("SEMICOLON"):
            if self.match("MANA"):
                initializer = self.variable_declaration(False)
            else:
                initializer = ("expression", self.expression())

        self.consume("SEMICOLON", "Expected ';' after initializer.")
        self.skip_newlines()

        condition = None

        if not self.check("SEMICOLON"):
            condition = self.expression()

        self.consume("SEMICOLON", "Expected ';' after condition.")
        self.skip_newlines()

        increment = None

        if not self.check("RIGHT_PAREN"):
            increment = self.expression()

        self.consume("RIGHT_PAREN", "Expected ')' after loop header.")

        self.skip_newlines()
        body = self.block()

        return ("for", initializer, condition, increment, body)

    def function_declaration(self):
        name = self.consume(
            "IDENTIFIER", "Expected a function name."
        ).value

        self.consume("LEFT_PAREN", "Expected '(' after function name.")

        parameters = []

        if not self.check("RIGHT_PAREN"):
            while True:
                parameters.append(
                    self.consume(
                        "IDENTIFIER", "Expected parameter name."
                    ).value
                )

                if not self.match("COMMA"):
                    break

        self.consume("RIGHT_PAREN", "Expected ')' after parameters.")

        if len(parameters) != len(set(parameters)):
            raise ParserError("Duplicate function parameter.")

        self.skip_newlines()
        body = self.block()

        return ("function", name, parameters, body)

    def block(self):
        self.consume("LEFT_BRACE", "Expected '{'.")

        statements = []
        self.skip_newlines()

        while not self.check("RIGHT_BRACE") and not self.check("EOF"):
            statements.append(self.statement())
            self.skip_newlines()

        self.consume("RIGHT_BRACE", "Expected '}' after block.")

        return statements

    def end_statement(self):
        if self.match("NEWLINE"):
            self.skip_newlines()
            return

        if self.check("RIGHT_BRACE") or self.check("EOF"):
            return

        raise self.error(self.peek(), "Expected end of statement.")

    # ---------- EXPRESSIONS ----------

    def expression(self):
        return self.assignment()

    def assignment(self):
        expression = self.or_expression()

        if self.match("EQUAL"):
            value = self.assignment()

            if expression[0] not in ("variable", "index"):
                raise self.error(
                    self.previous(),
                    "Invalid assignment target."
                )

            return ("assign", expression, value)

        return expression

    def or_expression(self):
        expression = self.and_expression()

        while self.match("OR"):
            expression = (
                "binary", expression, "OR", self.and_expression()
            )

        return expression

    def and_expression(self):
        expression = self.equality()

        while self.match("AND"):
            expression = (
                "binary", expression, "AND", self.equality()
            )

        return expression

    def equality(self):
        expression = self.comparison()

        while self.match("EQUAL_EQUAL", "BANG_EQUAL"):
            operator = self.previous().type
            expression = (
                "binary", expression, operator, self.comparison()
            )

        return expression

    def comparison(self):
        expression = self.term()

        while self.match(
            "GREATER", "GREATER_EQUAL", "LESS", "LESS_EQUAL"
        ):
            operator = self.previous().type
            expression = (
                "binary", expression, operator, self.term()
            )

        return expression

    def term(self):
        expression = self.factor()

        while self.match("PLUS", "MINUS"):
            operator = self.previous().type
            expression = (
                "binary", expression, operator, self.factor()
            )

        return expression

    def factor(self):
        expression = self.unary()

        while self.match("STAR", "SLASH", "PERCENT"):
            operator = self.previous().type
            expression = (
                "binary", expression, operator, self.unary()
            )

        return expression

    def unary(self):
        if self.match("NOT", "BANG", "MINUS"):
            operator = self.previous().type
            return ("unary", operator, self.unary())

        return self.postfix()

    def postfix(self):
        expression = self.primary()

        while True:
            if self.match("LEFT_PAREN"):
                arguments = []

                if not self.check("RIGHT_PAREN"):
                    while True:
                        arguments.append(self.expression())

                        if not self.match("COMMA"):
                            break

                self.consume(
                    "RIGHT_PAREN", "Expected ')' after arguments."
                )

                expression = ("call", expression, arguments)

            elif self.match("LEFT_BRACKET"):
                index = self.expression()

                self.consume(
                    "RIGHT_BRACKET", "Expected ']' after index."
                )

                expression = ("index", expression, index)

            else:
                break

        return expression

    def primary(self):
        if self.match("NUMBER"):
            return ("literal", self.previous().value)

        if self.match("STRING"):
            return ("literal", self.previous().value)

        if self.match("TRUE"):
            return ("literal", True)

        if self.match("FALSE"):
            return ("literal", False)

        if self.match("NULL"):
            return ("literal", None)

        if self.match("IDENTIFIER"):
            return ("variable", self.previous().value)

        if self.match("LEFT_PAREN"):
            expression = self.expression()
            self.consume(
                "RIGHT_PAREN", "Expected ')' after expression."
            )
            return expression

        if self.match("LEFT_BRACKET"):
            elements = []
            self.skip_newlines()

            if not self.check("RIGHT_BRACKET"):
                while True:
                    elements.append(self.expression())
                    self.skip_newlines()

                    if not self.match("COMMA"):
                        break

                    self.skip_newlines()
                    if self.check("RIGHT_BRACKET"):
                        break

            self.consume(
                "RIGHT_BRACKET", "Expected ']' after list."
            )
            return ("list", elements)

        if self.match("LEFT_BRACE"):
            pairs = []
            self.skip_newlines()

            if not self.check("RIGHT_BRACE"):
                while True:
                    key = self.expression()
                    self.skip_newlines()
                    self.consume("COLON", "Expected ':' in dictionary.")
                    self.skip_newlines()
                    value = self.expression()
                    pairs.append((key, value))
                    self.skip_newlines()

                    if not self.match("COMMA"):
                        break

                    self.skip_newlines()
                    if self.check("RIGHT_BRACE"):
                        break

            self.consume(
                "RIGHT_BRACE", "Expected '}' after dictionary."
            )
            return ("dict", pairs)

        raise self.error(self.peek(), "Expected an expression.")

    # ---------- PARSER HELPERS ----------

    def skip_newlines(self):
        while self.match("NEWLINE"):
            pass

    def match(self, *types):
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True

        return False

    def consume(self, token_type, message):
        if self.check(token_type):
            return self.advance()

        raise self.error(self.peek(), message)

    def check(self, token_type):
        return self.peek().type == token_type

    def advance(self):
        if not self.check("EOF"):
            self.current += 1

        return self.previous()

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def error(self, token, message):
        return ParserError(
            f"{message} Line {token.line}, column {token.column}."
        )


# -------------------- ENVIRONMENT --------------------

class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def define(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]

        if self.parent:
            return self.parent.get(name)

        raise InterpreterError(f"Undefined variable '{name}'.")

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return

        if self.parent:
            self.parent.assign(name, value)
            return

        raise InterpreterError(f"Undefined variable '{name}'.")


# -------------------- CONTROL FLOW --------------------

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


# -------------------- FUNCTIONS --------------------

class TarkaFunction:
    def __init__(self, name, parameters, body, closure):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.closure = closure

    def call(self, interpreter, arguments):
        if len(arguments) != len(self.parameters):
            raise InterpreterError(
                f"Function '{self.name}' expects "
                f"{len(self.parameters)} arguments, "
                f"but received {len(arguments)}."
            )

        environment = Environment(self.closure)

        for name, value in zip(self.parameters, arguments):
            environment.define(name, value)

        try:
            interpreter.execute_block(self.body, environment)
        except ReturnSignal as signal:
            return signal.value

        return None

    def __repr__(self):
        return f"<function {self.name}>"


# -------------------- INTERPRETER --------------------

class Interpreter:
    def __init__(self):
        self.environment = Environment()
        self.loop_depth = 0
        self.install_builtins()

    def install_builtins(self):
        builtins = {
            "len": lambda x: len(x),
            "str": lambda x: self.display(x),
            "int": self.to_int,
            "float": self.to_float,
            "type": self.type_name,
            "append": self.append_value,
            "remove": self.remove_value,
            "keys": lambda x: list(x.keys()) if type(x) is dict
                else self.bad_builtin("keys"),
            "values": lambda x: list(x.values()) if type(x) is dict
                else self.bad_builtin("values"),
            "range": self.make_range,
        }

        for name, function in builtins.items():
            self.environment.define(name, function)

    @staticmethod
    def to_int(value):
        if type(value) not in (int, float, str):
            raise InterpreterError("int() requires a number or string.")
        return int(value)

    @staticmethod
    def to_float(value):
        if type(value) not in (int, float, str):
            raise InterpreterError("float() requires a number or string.")
        return float(value)

    @staticmethod
    def type_name(value):
        if value is None:
            return "Null"
        if type(value) is bool:
            return "Boolean"
        if type(value) is int:
            return "Integer"
        if type(value) is float:
            return "Float"
        if type(value) is str:
            return "String"
        if type(value) is list:
            return "List"
        if type(value) is dict:
            return "Dictionary"
        if isinstance(value, TarkaFunction):
            return "Function"
        return "Builtin"

    @staticmethod
    def append_value(target, value):
        if type(target) is not list:
            raise InterpreterError("append() requires a list.")
        target.append(value)
        return None

    @staticmethod
    def remove_value(target, value):
        if type(target) is not list:
            raise InterpreterError("remove() requires a list.")
        target.remove(value)
        return None

    @staticmethod
    def make_range(*args):
        if not 1 <= len(args) <= 3:
            raise InterpreterError("range() accepts 1 to 3 arguments.")
        if not all(type(x) is int for x in args):
            raise InterpreterError("range() requires integer arguments.")
        return list(range(*args))

    @staticmethod
    def bad_builtin(name):
        raise InterpreterError(f"{name}() requires a dictionary.")

    def interpret(self, statements):
        try:
            for statement in statements:
                self.execute(statement)
        except ReturnSignal:
            raise InterpreterError(
                "pratyarpanam can only be used inside a function."
            )

    def execute_block(self, statements, environment):
        previous = self.environment
        self.environment = environment

        try:
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def execute(self, statement):
        kind = statement[0]

        if kind == "var":
            value = self.evaluate(statement[2])
            self.environment.define(statement[1], value)

        elif kind == "input":
            try:
                value = input(f"{statement[1]}: ")
            except EOFError:
                raise InterpreterError("No input was provided.")
            self.environment.define(statement[1], value)

        elif kind == "print":
            print(self.display(self.evaluate(statement[1])))

        elif kind == "expression":
            self.evaluate(statement[1])

        elif kind == "if":
            condition = self.evaluate(statement[1])
            self.require_boolean(condition, "if condition")

            if condition:
                self.execute_block(
                    statement[2], Environment(self.environment)
                )
            else:
                self.execute_block(
                    statement[3], Environment(self.environment)
                )

        elif kind == "while":
            self.execute_while(statement)

        elif kind == "for":
            self.execute_for(statement)

        elif kind == "function":
            function = TarkaFunction(
                statement[1],
                statement[2],
                statement[3],
                self.environment,
            )
            self.environment.define(statement[1], function)

        elif kind == "return":
            raise ReturnSignal(
                self.evaluate(statement[1])
                if statement[1] is not None else None
            )

        elif kind == "break":
            if self.loop_depth == 0:
                raise InterpreterError(
                    "virama can only be used inside a loop."
                )
            raise BreakSignal()

        elif kind == "continue":
            if self.loop_depth == 0:
                raise InterpreterError(
                    "anuvartta can only be used inside a loop."
                )
            raise ContinueSignal()

    def execute_while(self, statement):
        _, condition, body = statement

        while True:
            value = self.evaluate(condition)
            self.require_boolean(value, "while condition")

            if not value:
                break

            self.loop_depth += 1

            try:
                self.execute_block(
                    body, Environment(self.environment)
                )
            except ContinueSignal:
                continue
            except BreakSignal:
                break
            finally:
                self.loop_depth -= 1

    def execute_for(self, statement):
        _, initializer, condition, increment, body = statement

        previous = self.environment
        loop_environment = Environment(previous)
        self.environment = loop_environment

        try:
            if initializer is not None:
                if initializer[0] == "var":
                    self.execute(initializer)
                else:
                    self.evaluate(initializer[1])

            while True:
                if condition is not None:
                    value = self.evaluate(condition)
                    self.require_boolean(value, "for condition")

                    if not value:
                        break

                self.loop_depth += 1

                try:
                    self.execute_block(
                        body, Environment(loop_environment)
                    )
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                finally:
                    self.loop_depth -= 1

                if increment is not None:
                    self.evaluate(increment)

        finally:
            self.environment = previous

    # ---------- EXPRESSION EVALUATION ----------

    def evaluate(self, expression):
        kind = expression[0]

        if kind == "literal":
            return expression[1]

        if kind == "variable":
            return self.environment.get(expression[1])

        if kind == "list":
            return [self.evaluate(x) for x in expression[1]]

        if kind == "dict":
            result = {}

            for key_expr, value_expr in expression[1]:
                key = self.evaluate(key_expr)
                value = self.evaluate(value_expr)

                try:
                    result[key] = value
                except TypeError:
                    raise InterpreterError(
                        "Dictionary keys must be hashable."
                    )

            return result

        if kind == "unary":
            value = self.evaluate(expression[2])

            if expression[1] in ("NOT", "BANG"):
                self.require_boolean(value, "na")
                return not value

            if expression[1] == "MINUS":
                self.require_number(value, "Unary minus")
                return -value

        if kind == "binary":
            return self.evaluate_binary(expression)

        if kind == "assign":
            value = self.evaluate(expression[2])
            self.assign_target(expression[1], value)
            return value

        if kind == "index":
            obj = self.evaluate(expression[1])
            index = self.evaluate(expression[2])

            try:
                return obj[index]
            except (IndexError, KeyError, TypeError):
                raise InterpreterError(
                    f"Invalid index or missing key: {index!r}."
                )

        if kind == "call":
            function = self.evaluate(expression[1])
            arguments = [
                self.evaluate(arg) for arg in expression[2]
            ]

            if isinstance(function, TarkaFunction):
                return function.call(self, arguments)

            if callable(function):
                try:
                    return function(*arguments)
                except InterpreterError:
                    raise
                except Exception as error:
                    raise InterpreterError(
                        f"Function call failed: {error}"
                    )

            raise InterpreterError("This value is not callable.")

        raise InterpreterError(f"Unknown expression type: {kind}")

    def assign_target(self, target, value):
        if target[0] == "variable":
            self.environment.assign(target[1], value)
            return

        if target[0] == "index":
            obj = self.evaluate(target[1])
            index = self.evaluate(target[2])

            try:
                obj[index] = value
            except (IndexError, KeyError, TypeError):
                raise InterpreterError(
                    f"Cannot assign to index {index!r}."
                )
            return

        raise InterpreterError("Invalid assignment target.")

    def evaluate_binary(self, expression):
        _, left_expr, operator, right_expr = expression

        left = self.evaluate(left_expr)

        if operator == "AND":
            self.require_boolean(left, "cha")
            if not left:
                return False

            right = self.evaluate(right_expr)
            self.require_boolean(right, "cha")
            return right

        if operator == "OR":
            self.require_boolean(left, "va")
            if left:
                return True

            right = self.evaluate(right_expr)
            self.require_boolean(right, "va")
            return right

        right = self.evaluate(right_expr)

        if operator == "EQUAL_EQUAL":
            return left == right

        if operator == "BANG_EQUAL":
            return left != right

        if operator in (
            "GREATER", "GREATER_EQUAL", "LESS", "LESS_EQUAL"
        ):
            if type(left) != type(right):
                if not (
                    self.is_number(left) and self.is_number(right)
                ):
                    raise InterpreterError(
                        "Comparison requires compatible types."
                    )

            try:
                if operator == "GREATER":
                    return left > right
                if operator == "GREATER_EQUAL":
                    return left >= right
                if operator == "LESS":
                    return left < right
                return left <= right
            except TypeError:
                raise InterpreterError("Values cannot be compared.")

        if operator == "PLUS":
            if type(left) is str and type(right) is str:
                return left + right

            if type(left) is list and type(right) is list:
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

        raise InterpreterError(f"Unknown operator: {operator}")

    @staticmethod
    def is_number(value):
        return type(value) in (int, float)

    def require_number(self, value, operation):
        if not self.is_number(value):
            raise InterpreterError(
                f"{operation} requires a numeric value."
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

        if value is True:
            return "satyam"

        if value is False:
            return "asatyam"

        if type(value) is list:
            return "[" + ", ".join(
                Interpreter.display(x) for x in value
            ) + "]"

        if type(value) is dict:
            return "{" + ", ".join(
                f"{Interpreter.display(k)}: {Interpreter.display(v)}"
                for k, v in value.items()
            ) + "}"

        return str(value)


# -------------------- RUNNER --------------------

def run(source):
    tokens = Lexer(source).scan()
    statements = Parser(tokens).parse()

    interpreter = Interpreter()
    interpreter.interpret(statements)


# -------------------- DEMONSTRATION --------------------

DEMO = r'''
// Tarka v0.5 demonstration

mudraya "===== TARKA v0.5 ====="

mana name = "Tarka"
mana age = 20
mana price = 99.50

mudraya name
mudraya age
mudraya price

// Variable reassignment

age = 21
mudraya age

// Conditions and logical operators

yadi (age >= 18 cha satyam) {
    mudraya "Adult"
} anyatha {
    mudraya "Minor"
}

// For loop

mudraya "For loop:"

avartta (mana i = 1; i <= 5; i = i + 1) {
    mudraya i
}

// While loop

mudraya "While loop:"

mana count = 1

yavat (count <= 3) {
    mudraya count
    count = count + 1
}

// Lists

mana numbers = [10, 20, 30, 40]

mudraya numbers
mudraya numbers[0]

numbers[1] = 25
mudraya numbers

append(numbers, 50)
mudraya numbers
mudraya len(numbers)

// Dictionaries

mana person = {
    "name": "Tarka",
    "age": 21
}

mudraya person
mudraya person["name"]

person["age"] = 22
mudraya person

// Functions

kriya add(a, b) {
    pratyarpanam a + b
}

mana result = add(10, 20)
mudraya result

// Recursion

kriya factorial(n) {
    yadi (n <= 1) {
        pratyarpanam 1
    }

    pratyarpanam n * factorial(n - 1)
}

mudraya factorial(5)

// Break

avartta (mana j = 1; j <= 10; j = j + 1) {
    yadi (j == 4) {
        virama
    }

    mudraya j
}

// Continue

avartta (mana k = 1; k <= 5; k = k + 1) {
    yadi (k == 3) {
        anuvartta
    }

    mudraya k
}

// Input

pravesha city
mudraya "Welcome from:"
mudraya city

mudraya "===== DEMO COMPLETE ====="
'''


if __name__ == "__main__":
    import sys

    try:
        if len(sys.argv) > 1:
            filename = sys.argv[1]

            with open(filename, "r", encoding="utf-8") as file:
                source = file.read()
        else:
            print("Tarka v0.5 - Experimental Interpreter\n")
            source = DEMO

        run(source)

    except TarkaError as error:
        print(f"\nTarka Error: {error}")

    except KeyboardInterrupt:
        print("\nTarka execution interrupted.")
