"""
AmhaPy Transpiler and Runner.

This script provides a simple transpiler that converts code written in AmhaPy
(an Amharic-based programming language) into equivalent Python 3 code, and
then executes the generated Python code.

AmhaPy aims to make programming concepts accessible to Amharic speakers by
using Amharic keywords and following a Python-like syntax structure
with significant indentation.
"""

import re
import io
import sys
from typing import List, Tuple, Optional, Dict, Any, Pattern, Match
from pathlib import Path

# --- Constants ---

# Keyword mapping: AmhaPy (Amharic) to Python
# Keys are raw Amharic strings
KEYWORD_MAP: Dict[str, str] = {
    'አሳይ': 'print',             # To show/display
    'ከሆነ': 'if',                 # If it is
    'ያለበለዚያ': 'else',           # Otherwise
    'ያለበለዚያ_ከሆነ': 'elif',       # Otherwise if (for else-if condition) - ADDED
    'ለ': 'for',                  # For
    'በ': 'in',                   # In
    'ክልል': 'range',           # Region/Area (for range function)
    'እስከሆነ': 'while',            # Until it happens/becomes (for while loop)
    'ሥራ': 'def',               # Work (for function definition) - Using 'ሥራ' as requested
    'መመለስ': 'return',            # To return
    'እውነት': 'True',             # Truth
    'ሐሰት': 'False',              # Falsehood
    'እና': 'and',                 # Logical AND
    'ወይም': 'or',                 # Logical OR
    'አይደለም': 'not',             # Logical NOT
    'እኩል': '==',                 # Equal to
    'እኩል_አይደለም': '!=',         # Not equal to
    'ትልቅ': '>',                  # Greater than
    'ትንሽ': '<',                  # Less than than
    'ትልቅ_ወይም_እኩል': '>=',       # Greater than or equal to
    'ትንሽ_ወይም_እኩል': '<=',       # Less than or equal to
}

# Valid keywords for validation (using raw strings)
VALID_AMHAPY_KEYWORDS: set[str] = set(KEYWORD_MAP.keys())

# Regex for identifying different token types
# Ordered by priority: longer matches first (like >= before >)
# and specific types before general identifiers.
TOKEN_SPEC: List[Tuple[str, str]] = [
    ('STRING', r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''), # Strings (handles escaped quotes)
    ('COMMENT', r'#.*'),                                 # Comments
    ('OPERATOR', r'>=|<=|==|!=|>|<|\+|-|\*|/|%'),        # Operators (multi-char first)
    ('PUNCTUATION', r'[:(),=]'),                         # Punctuation
    ('NUMBER', r'\d+'),                                  # Numbers
    ('AMHA_IDENTIFIER', r'[\u1200-\u137F_][\u1200-\u137F0-9_]*'), # Amharic identifiers
    ('PYTHON_IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),     # Latin identifiers (for mixing or literals)
    ('WHITESPACE', r'[ \t]+'),                          # Whitespace (within lines, ignored)
    ('NEWLINE', r'\n')                                   # Newline
]

# Compile the main token regex
TOKEN_REGEX: Pattern[str] = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
)

# Standard indentation size (in spaces)
INDENT_SIZE: int = 4

# Token types for internal use
TOKEN_TYPE = Tuple[str, str]
TOKEN_LIST = List[TOKEN_TYPE]

# --- Lexer (Tokenization) ---

def tokenize(code: str) -> Tuple[Optional[TOKEN_LIST], Optional[str]]:
    """
    Tokenizes the input AmhaPy code string.

    Splits the code into a sequence of tokens, identifies their types,
    and processes indentation levels. Handles indentation errors and
    unexpected characters.

    Args:
        code: A string containing the AmhaPy source code.

    Returns:
        A tuple containing:
        - A list of tokens as (type, value) tuples, or None if an error occurred.
        - An error message string if tokenization failed, or None if successful.
    """
    tokens: TOKEN_LIST = []
    lines: List[str] = code.splitlines()
    # Stack to track indentation levels (storing the actual space count). Starts with base 0.
    indent_stack: List[int] = [0]
    line_num: int = 0

    for line in lines:
        line_num += 1

        # 1. Handle Indentation
        leading_whitespace: str = ''
        indent_char_index: int = 0
        while indent_char_index < len(line) and line[indent_char_index].isspace():
            leading_whitespace += line[indent_char_index]
            indent_char_index += 1

        line_content: str = line[indent_char_index:] # Rest of the line after indentation

        # Convert tabs to spaces (standard practice: 4 spaces per tab)
        # Use expandtabs for simplicity
        indent_whitespace = leading_whitespace.expandtabs(INDENT_SIZE)
        indent_count: int = len(indent_whitespace)


        # Skip empty lines or lines containing only whitespace/comments after potential indent
        # These lines do not affect indentation levels
        if not line_content or line_content.strip().startswith('#'):
             continue

        # Check for inconsistent indentation size (must be a multiple of INDENT_SIZE)
        if indent_count % INDENT_SIZE != 0:
            return None, f"Error (line {line_num}): Indentation must be a multiple of {INDENT_SIZE} spaces."

        # --- INDENTATION LOGIC (Corrected) ---
        current_indent_level = indent_count # Use the actual space count

        if current_indent_level > indent_stack[-1]:
            # Indentation increased - must be by exactly one level
            if current_indent_level != indent_stack[-1] + INDENT_SIZE:
                 return None, f"Error (line {line_num}): Indentation increased by more than one level ({INDENT_SIZE} spaces)."
            indent_stack.append(current_indent_level) # Push the new indent level (space count)
            tokens.append(('INDENT', ''))

        elif current_indent_level < indent_stack[-1]:
            # Indentation decreased - must match a previous level on the stack
            # Pop levels from the stack until the current indent_level is matched or exceeded
            while current_indent_level < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(('DEDENT', ''))

            # After popping, check if the current indent_level matches the new top of the stack
            # This means the dedent landed on a level that was not previously an indentation point
            if current_indent_level != indent_stack[-1]:
                return None, f"Error (line {line_num}): Indentation decreased to an inconsistent level."

        # If current_indent_level == indent_stack[-1], the indentation is the same as the previous level.
        # No INDENT/DEDENT is needed for this line's level change.

        # --- END OF INDENTATION LOGIC ---


        # 2. Tokenize the rest of the line content
        # Remove comment part first
        comment_start = line_content.find('#')
        if comment_start != -1:
            line_content = line_content[:comment_start]

        pos: int = 0
        line_tokens: TOKEN_LIST = []
        # Use finditer to find all tokens in the line content
        for match in TOKEN_REGEX.finditer(line_content):
            tok_type: str = match.lastgroup # Type is the name of the matched group
            tok_value: str = match.group(tok_type) # Value is the matched text

            # Check if there is any non-whitespace text between the end of the last token (pos)
            # and the start of the current match. If so, it's an error.
            if match.start() > pos:
                 error_substring = line_content[pos : match.start()]
                 return None, f"Error (line {line_num}): Unexpected characters or sequence '{error_substring.strip()}'"

            # Process the matched token based on its type
            if tok_type == 'WHITESPACE':
                # Ignore whitespace within the line content
                pass
            elif tok_type == 'COMMENT':
                 # Ignore comments (already stripped the main part, but just in case)
                 pass
            elif tok_type in ['AMHA_IDENTIFIER', 'PYTHON_IDENTIFIER']:
                # Check if the identifier token is actually a keyword
                if tok_value in VALID_AMHAPY_KEYWORDS:
                    line_tokens.append(('KEYWORD', tok_value))
                else:
                    # It's a user-defined identifier (variable or function name)
                    line_tokens.append(('IDENTIFIER', tok_value))
            else:
                # Other token types (STRING, NUMBER, OPERATOR, PUNCTUATION) are added directly
                line_tokens.append((tok_type, tok_value))

            # Update the position to the end of the current matched token
            pos = match.end(0)

        # After iterating through all matches, check if there's any remaining non-whitespace
        # text at the end of the line that didn't match any token.
        if pos < len(line_content) and line_content[pos:].strip():
            error_substring = line_content[pos:].strip()
            return None, f"Error (line {line_num}): Unexpected characters or sequence '{error_substring}' at end of line."

        # Add the tokens found on this line to the main list
        tokens.extend(line_tokens)
        # Add a newline token to signify the end of processing for this logical line
        tokens.append(('NEWLINE', ''))

    # After processing all lines, generate final DEDENT tokens for any remaining open indentation levels.
    # This ensures blocks opened at the end of the file are properly closed.
    while len(indent_stack) > 1: # Stop when only the base level (0 spaces) remains
        indent_stack.pop()
        tokens.append(('DEDENT', ''))

    # Final check: the indent stack should contain only the base level (0) at the end.
    # If not, there's an internal logic error in indentation tracking.
    if len(indent_stack) != 1 or indent_stack[0] != 0:
         # This case should ideally not be reachable with correct indentation logic,
         # but it's a safeguard.
         # print(f"Internal Warning: Indent stack not reset correctly: {indent_stack}", file=sys.stderr)
         pass # Could raise an internal error here if preferred


    return tokens, None

# --- Transpiler ---

def transpile_amhapy_to_python(tokens: TOKEN_LIST) -> Tuple[Optional[str], Optional[str]]:
    """
    Transpiles a list of AmhaPy tokens into a single string of Python 3 code.

    Processes tokens sequentially, mapping AmhaPy keywords to Python, handling
    indentation based on INDENT/DEDENT tokens, and applying Python-specific
    syntax rules (like print function calls).

    Args:
        tokens: A list of tokens generated by the tokenize function.

    Returns:
        A tuple containing:
        - A string with the transpiled Python 3 code, or None if an error occurred.
        - An error message string if transpilation failed, or None if successful.
    """
    python_code_lines: List[str] = [] # List to store each assembled line of Python code
    current_line_tokens: TOKEN_LIST = [] # Buffer for tokens belonging to the current logical line
    indent_level: int = 0 # Current logical indentation level (number of INDENT_SIZE blocks)

    def assemble_line(tokens_list: TOKEN_LIST, level: int) -> str:
        """
        Helper function to assemble a list of content tokens for a single AmhaPy line
        into a formatted Python code string with appropriate indentation and spacing.

        Handles keyword mapping and special syntax formatting, such as the Python 3
        print() function call.

        Args:
            tokens_list: A list of tokens (excluding NEWLINE, INDENT, DEDENT)
                         representing the content of one line.
            level: The current logical indentation level (number of INDENT_SIZE blocks).

        Returns:
            A string containing the formatted and indented Python code line.
        """
        # If the token list is empty (e.g., a line contained only ignorable tokens before processing),
        # return an empty string with the correct indentation.
        if not tokens_list:
            return ' ' * level * INDENT_SIZE

        # Map AmhaPy keyword tokens to their Python equivalents. Other token types
        # keep their original string value.
        mapped_tokens: List[str] = []
        for tok_type, tok_value in tokens_list:
            if tok_type == 'KEYWORD':
                 # Look up the Python equivalent from the keyword map
                 mapped_tokens.append(KEYWORD_MAP.get(tok_value, tok_value)) # Should always find keyword
            else:
                # For non-keyword tokens (identifiers, literals, operators, punctuation), use the value directly
                mapped_tokens.append(tok_value)

        # Re-check if mapped_tokens became empty after processing (e.g., if only comments were on the line initially, unlikely with current tokenizing)
        if not mapped_tokens:
             return ' ' * level * INDENT_SIZE


        # --- Special Handling for the Python 3 print() function ---
        # In AmhaPy, print arguments are typically space-separated: `አሳይ arg1 arg2`
        # In Python 3, print arguments are comma-separated *inside parentheses*: `print(arg1, arg2, ...)`
        # This logic converts the AmhaPy argument list format into the Python 3 function call format.
        first_mapped_token: str = mapped_tokens[0]
        if first_mapped_token == 'print':
            # Take all tokens *after* the 'print' token. These are the arguments.
            args_tokens = mapped_tokens[1:]

            # Join the argument tokens into a single string. Start by joining with space.
            args_string = ' '.join(args_tokens)

            # Apply simple replacements to fix spacing around punctuation *within* the argument string.
            # This handles cases like `(1, 4)`, `[a, b]`, `func(x)`, `obj.attribute`, `a + b`.
            # Note: This simple replace might not cover all complex expressions perfectly,
            # but it works for common beginner patterns.
            args_string = args_string.replace(' :', ':').replace(' ,', ',').replace(' )', ')').replace('( ', '(')
            args_string = args_string.replace('[ ', '[').replace(' ]', ']') # Lists
            args_string = args_string.replace('. ', '.').replace(' .', '.') # Attribute access

            # Construct the final Python 3 print() function call string
            line_content_str = f"print({args_string})"

        # --- Standard Line Assembly for other statements ---
        else:
            # For all other statements (assignments, conditionals, loops, function definitions, etc.),
            # join the mapped tokens with a single space.
            line_content_str = ' '.join(mapped_tokens)

            # Apply the same punctuation spacing cleanup.
            line_content_str = line_content_str.replace(' :', ':').replace(' ,', ',').replace(' )', ')').replace('( ', '(')
            line_content_str = line_content_str.replace('[ ', '[').replace(' ]', ']')
            line_content_str = line_content_str.replace('. ', '.').replace(' .', '.')

        # Add the required indentation at the beginning of the fully assembled line.
        indented_line = ' ' * level * INDENT_SIZE + line_content_str

        return indented_line

    try:
        # Iterate through the list of tokens from the lexer
        for tok_type, tok_value in tokens:
            if tok_type == 'INDENT':
                # Increase the current logical indentation level.
                # The INDENT token is emitted *before* the line it applies to is processed for content.
                indent_level += 1
            elif tok_type == 'DEDENT':
                # Decrease the current logical indentation level.
                # DEDENT tokens indicate the end of a block. The subsequent lines
                # will be at a lower indentation level.
                # DEDENT tokens are emitted *after* the block content lines and *before* the newline
                # or before the next line at the lower level.
                indent_level -= 1
                # Note: The assemble_line function, when called for the next line,
                # will use this new, decreased indent_level.
            elif tok_type == 'NEWLINE':
                 # Encountering a NEWLINE token signifies the end of a logical line of code.
                 # Assemble the tokens collected for this line into a Python string.
                 if current_line_tokens:
                     # If there were content tokens collected for this line, assemble and add it.
                     # Use the current indent_level BEFORE processing the next line.
                     python_code_lines.append(assemble_line(current_line_tokens, indent_level))
                     current_line_tokens = [] # Reset the buffer for the next line's tokens
                 else:
                      # If the line was effectively empty (only indentation, whitespace, or comment before NEWLINE),
                      # decide whether to add a blank line in the output Python code.
                      # We add a blank line only if the previous line in the output was *not* already blank
                      # and if the current indentation level requires it to maintain structure readability.
                      # This avoids excessive blank lines in the output for empty source lines.
                      # Ensure we only add a blank line if it's meaningful (e.g., not the very first line,
                      # or following a DEDENT/INDENT token without content).
                      if python_code_lines and python_code_lines[-1].strip():
                           # If the previous line in the output had content, add an indented blank line.
                           # This preserves blank lines that separate code blocks.
                           python_code_lines.append(' ' * indent_level * INDENT_SIZE)
                      # Note: Not explicitly handling blank lines after INDENT/DEDENT tokens here.
                      # The structure relies on assemble_line adding indentation based on the *current* level.


            else:
                # If the token is not INDENT, DEDENT, or NEWLINE, it's part of the line's content.
                # Add it to the buffer for the current logical line.
                current_line_tokens.append((tok_type, tok_value))

        # After the loop, check if there are any remaining tokens in the buffer.
        # This can happen if the input code doesn't end with a newline.
        if current_line_tokens:
             # Assemble the last line if it wasn't followed by a newline token
             python_code_lines.append(assemble_line(current_line_tokens, indent_level))

        # Join all the assembled Python code lines into a single string, separated by newlines.
        python_code_string = '\n'.join(python_code_lines)

        return python_code_string, None

    except Exception as e:
        # Catch any unexpected exceptions that occur during the transpilation process.
        # This is a general catch-all for errors not specifically handled by the logic.
        return None, f"Transpilation Assembly Error: {str(e)}"


# --- Execution ---

def run_amhapy_code(file_path: str) -> None:
    """
    Reads an AmhaPy source file, transpiles it to Python, and executes the result.

    This function orchestrates the entire process: reading the file, tokenizing,
    transpiling, printing the generated code, executing it, and displaying the output.
    Includes basic error handling for file reading, tokenization, transpilation,
    and execution. Error messages are printed to standard error (stderr).

    Args:
        file_path: The string path to the .amha source file.
    """
    # Use pathlib for robust file path handling
    source_file: Path = Path(file_path)

    # Check if the source file exists
    if not source_file.exists():
        print(f"Error: File not found at '{file_path}'. Please provide a valid file path.", file=sys.stderr)
        return

    try:
        # 1. Read the AmhaPy source code from the file
        # Use read_text with utf-8 encoding for Amharic characters
        amha_code: str = source_file.read_text(encoding='utf-8')

        # 2. Tokenize the source code
        print(f"Tokenizing code from {source_file}...")
        tokens, tokenize_error = tokenize(amha_code)
        if tokenize_error:
            # If tokenization fails, print the error and stop
            print(f"Tokenization Error: {tokenize_error}", file=sys.stderr)
            return
        print("Tokenization successful.")

        # Optional: Print tokens for debugging by uncommenting the lines below
        # print("--- Tokens ---")
        # print(tokens)
        # print("--------------")

        # 3. Transpile tokens to Python code
        print("Transpiling tokens to Python code...")
        python_code, transpile_error = transpile_amhapy_to_python(tokens)
        if transpile_error:
            # If transpilation fails, print the error and stop
            print(f"Transpilation Error: {transpile_error}", file=sys.stderr)
            return
        print("Transpilation successful.")

        # 4. Print the generated Python code
        print("\n--- Transpiled Python Code ---")
        print(python_code)
        print("------------------------------")

        # 5. Execute the transpiled Python code and capture output
        print("\n--- Program Output ---")

        # Temporarily redirect standard output to capture the output from exec()
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output

        try:
            # Execute the Python code string. Errors within the executed code
            # will be caught as exceptions here.
            exec(python_code)
        except Exception as e:
            # Catch any exception raised during the execution of the transpiled code.
            # Print the execution error message to the original standard error stream.
            print(f"Execution Error: {str(e)}", file=sys.__stdout__) # Use sys.__stdout__ to print to console even if sys.stdout is redirected
        finally:
            # Always restore standard output, even if an exception occurred
            sys.stdout = old_stdout

        # Print the captured standard output from the program
        print(redirected_output.getvalue())
        print("----------------------")

    except IOError as e:
         # Catch specific IOError if reading the file fails
         print(f"File Input/Output Error: {e}", file=sys.stderr)
    except Exception as e:
        # Catch any other unexpected exceptions during the overall process (excluding exec)
        print(f"An unexpected error occurred: {str(e)}", file=sys.stderr)


# --- Main Execution Block ---

if __name__ == "__main__":
    # Define the sample AmhaPy code as a string
    # Updated the conditional statement using 'ያለበለዚያ_ከሆነ' for 'elif'
    sample_code: str = """# Sample AmhaPy Program demonstrating core features

አሳይ "እንኳን ደህና መጡ ወደ አምሃፓይ ምሳሌ!"

# Variables and Assignment
የተማሪ_ስም = "አበበ"
ፈተና_ውጤት = 85
ዕድሜ = 22

አሳይ "የተማሪ ስም:", የተማሪ_ስም
አሳይ "ውጤት:", ፈተና_ውጤት
አሳይ "ዕድሜ:", ዕድሜ

# Conditional Statement (if/elif/else) - Using the new keyword
ከሆነ ፈተና_ውጤት ትልቅ_ወይም_እኩል 50:
    አሳይ የተማሪ_ስም, "ፈተናውን አልፏል!"
    ከሆነ ዕድሜ ትልቅ 18: # Nested if
        አሳይ "ዕድሜውም ለዩኒቨርሲቲ ብቁ ነው"
ያለበለዚያ_ከሆነ አይደለም ፈተና_ውጤት ትልቅ_ወይም_እኩል 50: # Use elif (Otherwise if)
    አሳይ የተማሪ_ስም, "ፈተናውን ወድቋል!"
ያለበለዚያ: # Final else
    አሳይ "ሌላ ሁኔታ (ለምሳሌ እድሜው አልደረሰም ግን ውጤቱ ጥሩ ነው)።"


# While Loop
ቆጣሪ = 3
አሳይ "የመውረጃ ቆጣሪ ምሳሌ:"
እስከሆነ ቆጣሪ ትልቅ 0:
    አሳይ "ቁጥር:", ቆጣሪ
    ቆጣሪ = ቆጣሪ - 1 # Decrementing the counter

# For Loop and Range
አሳይ "የክልል ሉፕ ምሳሌ:"
ለ ቁጥር በ ክልል(1, 4): # Iterates from 1 up to (but not including) 4
    አሳይ "ሉፕ:", ቁጥር

# Function Definition (using 'ሥራ' as requested)
ሥራ ድምር_አስላ(ቁጥር1, ቁጥር2):
    # Calculates the sum of two numbers
    ውጤት = ቁጥር1 + ቁጥር2
    መመለስ ውጤት # Return the result

# Function Call
የመጨረሻ_ድምር = ድምር_አስላ(15, 25)
አሳይ "የድምር ስሌት ውጤት:", የመጨረሻ_ድምር

# Using Boolean values and logical operators with if/elif/else
ብቁ_ከሆነ = እውነት
ሙሉ_ዕድሜ = ዕድሜ ትልቅ_ወይም_እኩል 18

ከሆነ ብቁ_ከሆነ እና ሙሉ_ዕድሜ:
    አሳይ "ለፕሮግራሙ ብቁ ነዎት።"
ያለበለዚያ_ከሆነ አይደለም ብቁ_ከሆነ: # Check if NOT eligible
    አሳይ "ብቁ አይደሉም (ብቁነት መስፈርት አላሟላም)።"
ያለበለዚያ: # Handles the case where ብቁ_ከሆነ is True but ሙሉ_ዕድሜ is False
    አሳይ "ብቁ አይደሉም (ዕድሜያቸው አልደረሰም)።"

"""
    # Define the file name for the sample code
    sample_file_name: str = "sample.amha"
    sample_file_path: Path = Path(sample_file_name)

    # Write the sample code string to the specified file
    try:
        sample_file_path.write_text(sample_code, encoding='utf-8')
        print(f"Sample code written to {sample_file_path}")
    except IOError as e:
        # Handle potential errors during file writing
        print(f"Error writing sample file: {e}", file=sys.stderr)
        sys.exit(1) # Exit the script if the sample file cannot be written

    # Run the sample AmhaPy code by calling the main runner function
    print(f"\nRunning AmhaPy code from {sample_file_path}...\n")
    run_amhapy_code(str(sample_file_path)) # Pass the path as a string

  
