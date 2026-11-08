
from dataclasses import dataclass


class LexerError(Exception):
    pass


@dataclass
class Token:
    type: str
    lexeme: str
    literal: object
    line: int
    column: int


KEYWORDS = {
    "mana": "MANA",
    "mudraya": "MUDRAYA",
    "pravesha": "PRAVESHA",
    "yadi": "YADI",
    "anyatha": "ANYATHA",
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
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_line = 1
        self.start_column = 1

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.start_line = self.line
            self.start_column = self.column
            self.scan_token()

        if not self.tokens or self.tokens[-1].type != "NEWLINE":
            self.tokens.append(
                Token("NEWLINE", "\n", None, self.line, self.column)
            )

        self.tokens.append(
            Token("EOF", "", None, self.line, self.column)
        )

        return self.tokens

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        char = self.source[self.current]
        self.current += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def peek(self):
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def match(self, expected):
        if self.is_at_end():
            return False

        if self.source[self.current] != expected:
            return False

        self.advance()
        return True

    def add_token(self, token_type, literal=None):
        lexeme = self.source[self.start:self.current]

        self.tokens.append(
            Token(
                token_type,
                lexeme,
                literal,
                self.start_line,
                self.start_column
            )
        )

    def scan_token(self):
        char = self.advance()

        # Comments: // this is a comment
        if char == "/" and self.peek() == "/":
            while self.peek() != "\n" and not self.is_at_end():
                self.advance()
            return

        single_tokens = {
            "(": "LEFT_PAREN",
            ")": "RIGHT_PAREN",
            "{": "LEFT_BRACE",
            "}": "RIGHT_BRACE",
            ",": "COMMA",
            "+": "PLUS",
            "-": "MINUS",
            "*": "STAR",
            "/": "SLASH",
            "%": "PERCENT",
        }

        if char in single_tokens:
            self.add_token(single_tokens[char])
            return

        if char == "=":
            self.add_token(
                "EQUAL_EQUAL" if self.match("=") else "EQUAL"
            )
            return

        if char == "!":
            self.add_token(
                "BANG_EQUAL" if self.match("=") else "BANG"
            )
            return

        if char == "<":
            self.add_token(
                "LESS_EQUAL" if self.match("=") else "LESS"
            )
            return

        if char == ">":
            self.add_token(
                "GREATER_EQUAL" if self.match("=") else "GREATER"
            )
            return

        if char in " \t\r":
            return

        if char == "\n":
            self.add_token("NEWLINE")
            return

        if char == '"':
            self.scan_string()
            return

        if char.isdigit():
            self.scan_number()
            return

        if char.isalpha() or char == "_":
            self.scan_identifier()
            return

        raise LexerError(
            f"Unexpected character '{char}' "
            f"at line {self.start_line}, "
            f"column {self.start_column}"
        )

    def scan_string(self):
        value = ""

        while self.peek() != '"' and not self.is_at_end():
            char = self.advance()

            if char == "\\":
                if self.is_at_end():
                    break

                escaped = self.advance()

                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    '"': '"',
                    "\\": "\\",
                }

                if escaped not in escape_map:
                    raise LexerError(
                        f"Unknown escape sequence '\\{escaped}' "
                        f"at line {self.line}, column {self.column}"
                    )

                value += escape_map[escaped]
            else:
                value += char

        if self.is_at_end():
            raise LexerError(
                f"Unterminated string at line {self.start_line}, "
                f"column {self.start_column}"
            )

        self.advance()  # Closing quotation mark
        self.add_token("STRING", value)

    def scan_number(self):
        while self.peek().isdigit():
            self.advance()

        is_float = False

        if self.peek() == "." and self.peek_next().isdigit():
            is_float = True
            self.advance()

            while self.peek().isdigit():
                self.advance()

        text = self.source[self.start:self.current]

        value = float(text) if is_float else int(text)

        self.add_token("NUMBER", value)

    def scan_identifier(self):
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()

        text = self.source[self.start:self.current]

        token_type = KEYWORDS.get(text, "IDENTIFIER")

        self.add_token(token_type)


# Standalone lexer test
if __name__ == "__main__":
    source = '''
mana age = 20
mana price = 99.50
mudraya age
// Tarka comment
'''

    try:
        tokens = Lexer(source).scan_tokens()

        for token in tokens:
            print(token)

    except LexerError as error:
        print("Lexer Error:", error)
