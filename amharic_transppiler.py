import re
import io # Using StringIO to capture exec output

# Keyword mapping: AmhaPy (Amharic) to Python
# Keys are raw Amharic strings
keyword_map = {
    'አሳይ': 'print',           # Suggestion for print (show)
    'ከሆነ': 'if',               # If it is
    'ያለበለዚያ': 'else',         # Otherwise
    'ለ': 'for',                # For
    'በ': 'in',                 # In
    'ክልል': 'range',         # Suggestion for range (region/area) - same as original
    'እስከሆነ': 'while',          # Suggestion for while (until it happens/becomes)
    'ሥራ': 'def',             # To define
    'መመለስ': 'return',          # To return
    'እውነት': 'True',           # Truth
    'ሐሰት': 'False',            # Falsehood
    'እና': 'and',               # And
    'ወይም': 'or',               # Or
    'አይደለም': 'not',           # Is not
    'እኩል': '==',               # Equal
    'እኩል_አይደለም': '!=',       # Is not equal
    'ትልቅ': '>',                # Big/Large
    'ትንሽ': '<',                # Small/Little
    'ትልቅ_ወይም_እኩል': '>=',     # Big or equal
    'ትንሽ_ወይም_እኩል': '<=',     # Small or equal
}

# Valid keywords for validation (using raw strings)
valid_amhapy_keywords = set(keyword_map.keys())

# Regex for identifying different token types (keep this the same as before)
TOKEN_SPECIFICATION = [
    ('STRING', r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''), # Strings (handles escaped quotes)
    ('COMMENT', r'#.*'),                                # Comments
    ('OPERATOR', r'>=|<=|==|!=|>|<|\+|-|\*|/|%'),       # Operators (multi-char first)
    ('PUNCTUATION', r'[:(),=]'),                        # Punctuation
    ('NUMBER', r'\d+'),                                 # Numbers
    ('AMHA_IDENTIFIER', r'[\u1200-\u137F_][\u1200-\u137F0-9_]*'), # Amharic identifiers
    ('PYTHON_IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),    # Latin identifiers (for mixing or literals)
    ('WHITESPACE', r'[ \t]+'),                         # Whitespace (to be ignored unless indentation)
    ('NEWLINE', r'\n')                                  # Newline
]

# Compile regex
TOKEN_REGEX = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION))

# Lexer (tokenize function remains the same, using the updated keyword_map)
def tokenize(code):
    tokens = []
    lines = code.splitlines()
    indent_stack = [0]
    line_num = 0

    for line in lines:
        line_num += 1
        original_line = line

        indent = ''
        i = 0
        while i < len(line) and line[i].isspace():
            indent += line[i]
            i += 1

        line = line[i:]

        indent_count = len(indent.replace('\t', '    '))

        if not line or line.strip().startswith('#'):
             continue

        current_level = indent_count // 4

        while current_level < indent_stack[-1]:
            indent_stack.pop()
            tokens.append(('DEDENT', ''))
            if current_level > indent_stack[-1]:
                 return None, f"Error (line {line_num}): Indentation decreased to an inconsistent level."

        if current_level > indent_stack[-1]:
            if current_level != indent_stack[-1] + 1:
                 return None, f"Error (line {line_num}): Too many indentation levels (indent increase must be by 4 spaces)."
            indent_stack.append(current_level)
            tokens.append(('INDENT', ''))


        comment_start = line.find('#')
        if comment_start != -1:
            line = line[:comment_start]

        pos = 0
        line_tokens = []
        while pos < len(line):
            match = TOKEN_REGEX.match(line, pos)
            if not match:
                error_char = line[pos] if pos < len(line) else "end of line"
                return None, f"Error (line {line_num}): Unexpected character or sequence '{line[pos:]}' starting with '{error_char}'"

            tok_type = match.lastgroup
            tok_value = match.group(tok_type)

            if tok_type == 'WHITESPACE':
                pass
            elif tok_type == 'COMMENT':
                pass
            elif tok_type in ['AMHA_IDENTIFIER', 'PYTHON_IDENTIFIER']:
                # Validate if it's a keyword or a valid identifier
                if tok_value in valid_amhapy_keywords: # Use the updated set
                    line_tokens.append(('KEYWORD', tok_value))
                elif re.fullmatch(r'[\u1200-\u137F_][\u1200-\u137F0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*', tok_value):
                     line_tokens.append(('IDENTIFIER', tok_value))
                else:
                     return None, f"Error (line {line_num}): Invalid identifier '{tok_value}'"
            else:
                line_tokens.append((tok_type, tok_value))

            pos = match.end(0)

        tokens.extend(line_tokens)
        tokens.append(('NEWLINE', ''))

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(('DEDENT', ''))

    return tokens, None

# Parser/Transpiler (transpile_amhapy_to_python remains the same, using the updated keyword_map)
def transpile_amhapy_to_python(tokens):
    python_code_lines = []
    current_line_tokens = []
    indent_level = 0

    def assemble_line(tokens_list, level):
        if not tokens_list:
            return ' ' * level * 4

        mapped_tokens = []
        for tok_type, tok_value in tokens_list:
            if tok_type == 'KEYWORD':
                 mapped_tokens.append(keyword_map.get(tok_value, tok_value))
            else:
                mapped_tokens.append(tok_value)

        # Handle potential empty mapped_tokens list if line had only ignored tokens
        if not mapped_tokens:
            return ' ' * level * 4

        first_mapped_token = mapped_tokens[0]

        # Special handling for print function in Python 3
        if first_mapped_token == 'print':
            args_string = ' '.join(mapped_tokens[1:])

            # Apply punctuation fixing *within* the argument string
            args_string = args_string.replace(' :', ':').replace(' ,', ',').replace(' )', ')').replace('( ', '(')
            args_string = args_string.replace('[ ', '[').replace(' ]', ']')
            args_string = args_string.replace('. ', '.').replace(' .', '.')

            line = f"print({args_string})"

        else:
            line = ' '.join(mapped_tokens)

            # Apply punctuation fixing
            line = line.replace(' :', ':').replace(' ,', ',').replace(' )', ')').replace('( ', '(')
            line = line.replace('[ ', '[').replace(' ]', ']')
            line = line.replace('. ', '.').replace(' .', '.')

        return ' ' * level * 4 + line

    try:
        for tok_type, tok_value in tokens:
            if tok_type == 'INDENT':
                indent_level += 1
            elif tok_type == 'DEDENT':
                indent_level -= 1
            elif tok_type == 'NEWLINE':
                 if current_line_tokens:
                     python_code_lines.append(assemble_line(current_line_tokens, indent_level))
                     current_line_tokens = []
                 else:
                      if python_code_lines and python_code_lines[-1].strip():
                          python_code_lines.append(' ' * indent_level * 4)

            else:
                current_line_tokens.append((tok_type, tok_value))

        if current_line_tokens:
             python_code_lines.append(assemble_line(current_line_tokens, indent_level))

        python_code = '\n'.join(python_code_lines)
        return python_code, None

    except Exception as e:
        return None, f"Transpilation Assembly Error: {str(e)}"


# Run AmhaPy code from a file (remains the same)
def run_amhapy_code(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            amha_code = file.read()

        tokens, error = tokenize(amha_code)
        if error:
            print(f"Tokenization Error: {error}")
            return

        python_code, error = transpile_amhapy_to_python(tokens)
        if error:
            print(f"Transpilation Error: {error}")
            return

        print("--- Transpiled Python Code ---")
        print(python_code)
        print("------------------------------")
        print("\n--- Program Output ---")

        old_stdout = io.StringIO()
        import sys
        sys.stdout = old_stdout

        try:
            exec(python_code)
        finally:
            sys.stdout = sys.__stdout__

        print(old_stdout.getvalue())
        print("----------------------")

    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'. Please provide a valid .amha file.")
    except Exception as e:
        print(f"Execution Error: {str(e)}")

# Example usage with the new keywords
if __name__ == "__main__":
    sample_code = """አሳይ "እንኳን ደህና መጡ!" # Using 'አሳይ' for print
ቁጥር = 10

# Using 'እስከሆነ' for while
እስከሆነ ቁጥር ትልቅ 0:
    አሳይ "ቁጥር:", ቁጥር
    ቁጥር = ቁጥር - 1

# Using 'ክልል' for range
አሳይ "የክልል ሉፕ:"
ለ ቆጥር በ ክልል(0, 3): # for ቆጥር in range(0, 3)
    አሳይ ቆጥር * 10

# Function definition with 'መግለፅ' and 'መመለስ' (unchanged)
ሥራ መ(x, y):
    ውጤት = x + y
    መመለስ ውጤት

አሳይ "የመጨመር ውጤት:", መ(7, 8) # Calling function

"""
    file_name = "sample_new_keywords.amha"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(sample_code)

    run_amhapy_code(file_name)
