<div align="center">
  <h1>AmhaPy</h1>
  <h3>An Amharic-based Programming Language Transpiler</h3>
  <p>Bridging the Gap: Making Programming Accessible for Amharic Speakers</p>

  <a href="https://github.com/felekekinfe/AmhaPy-Amharic-based-Programming-Language-Transpiler/actions/workflows/python-app.yml">
    <img src="https://github.com/felekekinfe/AmhaPy-Amharic-based-Programming-Language-Transpiler/actions/workflows/python-app.yml/badge.svg" alt="Build Status">
  </a>
  <a href="https://github.com/felekekinfe/AmhaPy-Amharic-based-Programming-Language-Transpiler/blob/main/LICENSE">
      <img src="https://img.shields.io/github/license/felekekinfe/AmhaPy-Amharic-based-Programming-Language-Transpiler?color=blue" alt="License: MIT">
  </a>
  <!-- Add more relevant badges here in the future (e.g., Code Coverage, Contributors) -->
</div>

---

## ✨ About AmhaPy

AmhaPy is an **open-source educational initiative** aimed at significantly easing the entry into programming for individuals who are native Amharic speakers. Learning programming often requires mastering English terminology and syntax, which can be a considerable hurdle. AmhaPy seeks to remove this initial barrier.

At its heart, AmhaPy is a **transpiler**. It takes source code written using familiar Amharic keywords and a clear, Python-inspired structure, and converts it directly into standard **Python 3** code. This allows learners to focus on the fundamental concepts of programming – logic, control flow, data handling, and problem-solving – using a language they understand, before needing to fully transition to English-based syntax.

**Status:** This project is a **Proof of Concept** and is currently in its early development phase. It supports a foundational set of programming constructs and demonstrates the viability of an Amharic-based syntax.

## 🚀 Features

*   **Intuitive Amharic Keywords:** Core programming instructions are represented by meaningful Amharic words.
*   **Pythonic Syntax:** Follows Python's emphasis on readability, utilizing significant indentation for code blocks.
*   **Essential Control Flow:** Includes support for conditional logic (`if`/`elif`/`else` - `ከሆነ`/`ያለበለዚያ_ከሆነ`/`ያለበለዚያ`) and looping (`for`/`while` - `ለ`/`በ`, `እስከሆነ`).
*   **Functions:** Define reusable code blocks (`def` - `ሥራ`) and return values (`return` - `መመለስ`).
*   **Basic Data Handling:** Work with numbers, strings (text), and boolean values (`True`/`False` - `እውነት`/`ሐሰት`).
*   **Operators & Comparisons:** Use standard arithmetic operators and express comparisons (`==`, `!=`, `>`, `<`, `>=`, `<=`) using Amharic keywords.
*   **Amharic Identifiers:** Use Amharic characters (Geez script) for naming variables and functions, in addition to standard Latin letters and underscores.
*   **Readable Output:** Transpiles into clean and understandable Python 3 code.
*   **Simple Workflow:** Run your `.amha` source files directly using the main Python script.

## 🛠️ Getting Started

### Prerequisites

Ensure you have **Python 3.6 or a newer version** installed on your computer.

### Installation

AmhaPy is currently a single Python script, making installation straightforward:

1.  **Clone the repository:** Open your terminal or command prompt and execute:
    ```bash
    git clone https://github.com/felekekinfe/AmhaPy-Amharic-based-Programming-Language-Transpiler.git
    cd AmhaPy-Amharic-based-Programming-Language-Transpiler
    ```

2.  That's all! You're now set up to write and run AmhaPy code.

## ▶️ Usage

To write and run an AmhaPy program:

1.  **Write your code:** Use any plain text editor to write your AmhaPy code and save the file with the `.amha` extension (e.g., `my_first_script.amha`).
2.  **Execute the script:** Open your terminal or command prompt, navigate to the directory where you cloned the repository, and run the `amhapy_transpiler.py` script, providing the path to your `.amha` file:

    ```bash
    python amhapy_transpiler.py path/to/your/my_first_script.amha
    ```

The script will perform the following steps automatically:

1.  Reads the content of your `.amha` file.
2.  **Tokenizes** the code, identifying keywords, identifiers, operators, literals, and processing indentation.
3.  **Transpiles** the token stream into equivalent Python 3 code, mapping Amharic keywords and reconstructing indentation.
4.  **Prints** the generated Python code to your console.
5.  **Executes** the transpiled Python code using Python's built-in `exec()` function.
6.  **Displays** any output produced by your program.

## 📖 AmhaPy Language Reference

AmhaPy syntax is modeled closely after Python's, using significant indentation and a straightforward structure, but replacing keywords with Amharic terms.

### Keywords

Here are the essential keywords in AmhaPy and their Python equivalents:

| AmhaPy Keyword        | Python Equivalent | Meaning (Amharic)         | Programming Concept         |
| :-------------------- | :---------------- | :------------------------ | :-------------------------- |
| `አሳይ`                | `print`           | To show/display           | Output function             |
| `ከሆነ`                | `if`              | If it is                  | Conditional statement start |
| `ያለበለዚያ`            | `else`            | Otherwise                 | Conditional alternative (fallback) |
| `ያለበለዚያ_ከሆነ`       | `elif`            | Otherwise if              | Conditional alternative (with condition) |
| `ለ`                   | `for`             | For                       | Iteration loop start        |
| `በ`                   | `in`              | In                        | Membership/Range context    |
| `ክልል`                | `range`           | Region/Area               | Sequence generator (for loops)|
| `እስከሆነ`             | `while`           | Until it happens/becomes  | Condition-based loop start  |
| `ሥራ`                 | `def`             | Work                      | Function definition start   |
| `መመለስ`               | `return`          | To return/give back       | Function output value       |
| `እውነት`              | `True`            | Truth                     | Boolean value (True)        |
| `ሐሰት`                | `False`           | Falsehood                 | Boolean value (False)       |
| `እና`                 | `and`             | And                       | Logical AND                 |
| `ወይም`                | `or`              | Or                        | Logical OR                  |
| `አይደለም`             | `not`             | Is not                    | Logical NOT                 |
| `እኩል`                | `==`              | Equal                     | Comparison (equality)       |
| `እኩል_አይደለም`        | `!=`              | Not equal                 | Comparison (not equal)      |
| `ትልቅ`               | `>`               | Big/Large                 | Comparison (greater than)   |
| `ትንሽ`                | `<`               | Small/Little              | Comparison (less than)      |
| `ትልቅ_ወይም_እኩል`     | `>=`              | Big or equal              | Comparison (>=)             |
| `ትንሽ_ወይም_እኩል`     | `<=`              | Small or equal            | Comparison (<=)             |

### Indentation

AmhaPy, just like Python, uses **significant indentation** to define code blocks. After control flow statements or function definitions (`ከሆነ:`, `ያለበለዚያ:`, `ያለበለዚያ_ከሆነ:`, `እስከሆነ:`, `ሥራ:`), lines belonging to that block must be indented using a consistent number of spaces. The standard in AmhaPy (and Python) is **4 spaces** per indentation level. Mixing spaces and tabs, or using inconsistent indentation amounts, will result in errors.

```amhapy
ከሆነ እውነት: # Colon at the end starts a new block
    # This line is indented 4 spaces (one level)
    አሳይ "Inside the first block"
    ከሆነ 5 ትልቅ 3: # Nested block
        # This line is indented 8 spaces (two levels)
        አሳይ "Inside the nested block"
# This line is back at the base level (0 spaces)
አሳይ "Outside blocks"
