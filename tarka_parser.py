
from dataclasses import dataclass
from tarka_lexer import Lexer


class ParserError(Exception):
    pass


# AST nodes: the structures representing Tarka programs.

@dataclass
class Number:
    value: object


@dataclass
class String:
    value: str


@dataclass
class Boolean:
    value: bool


@dataclass
class Null:
    pass


@dataclass
class Variable:
    name: str


@dataclass
class Binary:
    left: object
    operator: object
    right: object


@dataclass
class Unary:
    operator: object
    right: object


@dataclass
class VariableDeclaration:
    name: str
    initializer: object


@dataclass
class InputStatement:
    name: str


@dataclass
class PrintStatement:
    expression: object


@dataclass
class IfStatement:
    condition: object
    then_branch: list
    else_branch: list


@dataclass
class Program:
    statements: list


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

        return Program(statements)

    def statement(self):
        if self.match("MANA"):
            return self.variable_declaration()

        if self.match("PRAVESHA"):
            return self.input_statement()

        if self.match("MUDRAYA"):
            return self.print_statement()

        if self.match("YADI"):
            return self.if_statement()

        raise self.error(
            self.peek(),
            "Expected mana, pravesha, mudraya, or yadi."
        )

    def variable_declaration(self):
        name = self.consume(
            "IDENTIFIER", "Expected a variable name."
        )

        self.consume("EQUAL", "Expected '=' after variable name.")
        initializer = self.expression()
        self.consume_newline()

        return VariableDeclaration(name.lexeme, initializer)

    def input_statement(self):
        name = self.consume(
            "IDENTIFIER", "Expected a variable name after pravesha."
        )
        self.consume_newline()
        return InputStatement(name.lexeme)

    def print_statement(self):
        expression = self.expression()
        self.consume_newline()
        return PrintStatement(expression)

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

        return IfStatement(condition, then_branch, else_branch)

    def block(self):
        self.consume("LEFT_BRACE", "Expected '{' to begin block.")
        statements = []

        self.skip_newlines()

        while not self.check("RIGHT_BRACE") and not self.check("EOF"):
            statements.append(self.statement())
            self.skip_newlines()

        self.consume("RIGHT_BRACE", "Expected '}' after block.")
        return statements

    # Expression precedence:
    # OR -> AND -> equality -> comparison -> addition
    # -> multiplication -> unary -> primary.

    def expression(self):
        return self.or_expression()

    def or_expression(self):
        expression = self.and_expression()

        while self.match("OR"):
            operator = self.previous()
            right = self.and_expression()
            expression = Binary(expression, operator, right)

        return expression

    def and_expression(self):
        expression = self.equality()

        while self.match("AND"):
            operator = self.previous()
            right = self.equality()
            expression = Binary(expression, operator, right)

        return expression

    def equality(self):
        expression = self.comparison()

        while self.match("EQUAL_EQUAL", "BANG_EQUAL"):
            operator = self.previous()
            right = self.comparison()
            expression = Binary(expression, operator, right)

        return expression

    def comparison(self):
        expression = self.term()

        while self.match(
            "GREATER", "GREATER_EQUAL", "LESS", "LESS_EQUAL"
        ):
            operator = self.previous()
            right = self.term()
            expression = Binary(expression, operator, right)

        return expression

    def term(self):
        expression = self.factor()

        while self.match("PLUS", "MINUS"):
            operator = self.previous()
            right = self.factor()
            expression = Binary(expression, operator, right)

        return expression

    def factor(self):
        expression = self.unary()

        while self.match("STAR", "SLASH", "PERCENT"):
            operator = self.previous()
            right = self.unary()
            expression = Binary(expression, operator, right)

        return expression

    def unary(self):
        if self.match("NOT", "BANG", "MINUS"):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.primary()

    def primary(self):
        if self.match("NUMBER"):
            return Number(self.previous().literal)

        if self.match("STRING"):
            return String(self.previous().literal)

        if self.match("TRUE"):
            return Boolean(True)

        if self.match("FALSE"):
            return Boolean(False)

        if self.match("NULL"):
            return Null()

        if self.match("IDENTIFIER"):
            return Variable(self.previous().lexeme)

        if self.match("LEFT_PAREN"):
            expression = self.expression()
            self.consume(
                "RIGHT_PAREN", "Expected ')' after expression."
            )
            return expression

        raise self.error(self.peek(), "Expected an expression.")

    # Parser utilities.

    def skip_newlines(self):
        while self.match("NEWLINE"):
            pass

    def consume_newline(self):
        if not self.match("NEWLINE") and not self.check("EOF"):
            raise self.error(
                self.peek(), "Expected the statement to end with a newline."
            )

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
            f"{message} At line {token.line}, column {token.column}."
        )
