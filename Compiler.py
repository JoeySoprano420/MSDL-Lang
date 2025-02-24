import ast
import subprocess
import ctypes
import time
import os
import platform

class PyASMCompiler(ast.NodeVisitor):
    def __init__(self):
        self.assembly_code = ["section .text"]
        self.variables = {}
        self.current_function = None

    def visit_FunctionDef(self, node):
        """Translate Python function into an Assembly label."""
        self.assembly_code.append(f"global {node.name}")
        self.assembly_code.append(f"{node.name}:")
        self.assembly_code.append("    push rbp")
        self.assembly_code.append("    mov rbp, rsp")

        # Store current function to handle nested functions or recursion
        self.current_function = node.name

        self.generic_visit(node)
        self.assembly_code.append("    pop rbp")
        self.assembly_code.append("    ret")
        self.current_function = None

    def visit_Assign(self, node):
        """Handle variable assignments and create Assembly code for each."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables[target.id] = None  # Initialize variable

        # Handle assignment with constant or binary operation
        if isinstance(node.value, ast.Constant):
            value = node.value.n
            self.assembly_code.append(f"    mov {target.id}, {value}")
        elif isinstance(node.value, ast.Name):
            self.assembly_code.append(f"    mov {target.id}, {node.value.id}")
        elif isinstance(node.value, ast.BinOp):
            self.visit(node.value)
            self.assembly_code.append(f"    mov {target.id}, rax")

    def visit_Return(self, node):
        """Handle return statements."""
        if isinstance(node.value, ast.BinOp):
            self.visit(node.value)
        elif isinstance(node.value, ast.Constant):
            self.assembly_code.append(f"    mov rax, {node.value.n}")
        elif isinstance(node.value, ast.Name):
            self.assembly_code.append(f"    mov rax, {node.value.id}")
        self.assembly_code.append("    ret")

    def visit_BinOp(self, node):
        """Generate Assembly for binary operations."""
        if isinstance(node.op, ast.Add):
            self.assembly_code.append("    add rax, rcx")
        elif isinstance(node.op, ast.Sub):
            self.assembly_code.append("    sub rax, rcx")
        elif isinstance(node.op, ast.Mult):
            self.assembly_code.append("    imul rax, rcx")
        elif isinstance(node.op, ast.Div):
            self.assembly_code.append("    cqo")
            self.assembly_code.append("    idiv rcx")
        elif isinstance(node.op, ast.Mod):
            self.assembly_code.append("    cqo")
            self.assembly_code.append("    idiv rcx")
            self.assembly_code.append("    mov rax, rdx")  # Remainder

    def visit_If(self, node):
        """Handle if-else statements."""
        self.assembly_code.append(f"    ; If condition")
        self.visit(node.test)
        self.assembly_code.append(f"    jz else_block")  # Jump if zero to else
        self.generic_visit(node.body)
        self.assembly_code.append(f"else_block:")

        if node.orelse:
            self.assembly_code.append(f"    ; Else condition")
            self.generic_visit(node.orelse)

    def visit_While(self, node):
        """Handle while loops."""
        loop_label = f"loop_{id(node)}"
        self.assembly_code.append(f"{loop_label}:")
        self.visit(node.test)
        self.assembly_code.append(f"    jz end_{loop_label}")
        self.generic_visit(node.body)
        self.assembly_code.append(f"    jmp {loop_label}")
        self.assembly_code.append(f"end_{loop_label}:")

    def visit_Compare(self, node):
        """Handle comparison operations."""
        if isinstance(node.ops[0], ast.Gt):
            self.assembly_code.append("    cmp rax, rcx")
            self.assembly_code.append("    jg comparison_true")
        elif isinstance(node.ops[0], ast.Lt):
            self.assembly_code.append("    cmp rax, rcx")
            self.assembly_code.append("    jl comparison_true")
        elif isinstance(node.ops[0], ast.Eq):
            self.assembly_code.append("    cmp rax, rcx")
            self.assembly_code.append("    je comparison_true")

        self.assembly_code.append("    jmp comparison_false")
        self.assembly_code.append("comparison_true:")
        self.assembly_code.append("    mov rax, 1")
        self.assembly_code.append("    jmp end_comparison")
        self.assembly_code.append("comparison_false:")
        self.assembly_code.append("    mov rax, 0")
        self.assembly_code.append("end_comparison:")

    def visit_List(self, node):
        """Handle list construction."""
        self.assembly_code.append("    ; Creating list")
        for elt in node.elts:
            self.visit(elt)
            # Assembly code for adding elements to the list (simplified for now)

    def visit_Dict(self, node):
        """Handle dictionary construction."""
        self.assembly_code.append("    ; Creating dictionary")
        for key, value in zip(node.keys, node.values):
            self.visit(key)
            self.visit(value)
            # Code to insert key-value pairs into the dictionary

    def visit_Attribute(self, node):
        """Handle attributes of objects."""
        # Handle object attributes for dot notation, e.g., `obj.attribute`
        self.assembly_code.append(f"    ; Handling attribute {node.attr}")

    def visit_Name(self, node):
        """Handle variable references."""
        self.assembly_code.append(f"    ; Variable {node.id}")
        # Here we assume variables are simple names; we can extend this further.

    def compile(self, python_code):
        """Parse and convert Python to Assembly."""
        tree = ast.parse(python_code)
        self.visit(tree)
        return "\n".join(self.assembly_code)

    def optimize(self):
        """Optional method for optimizing assembly code."""
        # Implement optimizations such as removing dead code,
        # replacing frequently used code patterns with more efficient instructions
        pass


# Example usage with more complex constructs
python_code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

def compute(a, b):
    if a > b:
        return a + b
    else:
        return a - b

def loop_test():
    count = 0
    while count < 10:
        count += 1
    return count

def list_test():
    my_list = [1, 2, 3, 4, 5]
    return my_list

def dict_test():
    my_dict = {'a': 1, 'b': 2, 'c': 3}
    return my_dict
"""

compiler = PyASMCompiler()
assembly = compiler.compile(python_code)
print("Generated Assembly Code:\n", assembly)

# Additional step: Save to file for external use
with open("output.asm", "w") as f:
    f.write(assembly)

# Running the assembly file and creating the binary as before
def assemble_and_link(output_file="output.bin"):
    subprocess.run(["nasm", "-f", "bin", "output.asm", "-o", output_file])
    print(f"Executable {output_file} created.")

assemble_and_link()

# Cleanup generated files
os.remove("output.asm")
os.remove("output.bin")

import ast
import ctypes
import subprocess
import os

class PyASMCompiler(ast.NodeVisitor):
    def __init__(self):
        self.assembly_code = ["section .text"]
        self.variables = {}
        self.current_function = None
        self.global_variables = set()
        self.local_variables = set()
        self.builtins = {"True", "False", "None"}

    def visit_FunctionDef(self, node):
        """Translate Python function into an Assembly label."""
        self.assembly_code.append(f"global {node.name}")
        self.assembly_code.append(f"{node.name}:")
        self.assembly_code.append("    push rbp")
        self.assembly_code.append("    mov rbp, rsp")

        # Track current function for handling recursion and variable scope
        self.current_function = node.name
        self.local_variables.clear()  # New function scope, reset local variables

        self.generic_visit(node)
        self.assembly_code.append("    pop rbp")
        self.assembly_code.append("    ret")
        self.current_function = None

    def visit_Assign(self, node):
        """Handle variable assignments and generate Assembly code."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if var_name not in self.local_variables:
                    self.local_variables.add(var_name)

                # Handle assignment with constants or binary operations
                if isinstance(node.value, ast.Constant):
                    value = node.value.n
                    self.assembly_code.append(f"    mov {var_name}, {value}")
                elif isinstance(node.value, ast.Name):
                    self.assembly_code.append(f"    mov {var_name}, {node.value.id}")
                elif isinstance(node.value, ast.BinOp):
                    self.visit(node.value)
                    self.assembly_code.append(f"    mov {var_name}, rax")

    def visit_Name(self, node):
        """Handle variable references and process both local and global names."""
        if node.id in self.builtins:
            # Built-ins are handled differently or ignored
            self.assembly_code.append(f"    ; Built-in {node.id}")
            return
        elif node.id in self.local_variables:
            # Local variables are handled directly
            self.assembly_code.append(f"    ; Local variable {node.id}")
        elif node.id in self.global_variables:
            # Global variables need special handling (memory management)
            self.assembly_code.append(f"    ; Global variable {node.id}")
        else:
            # This is a new variable, add it to the global scope
            self.global_variables.add(node.id)
            self.assembly_code.append(f"    ; Unknown variable {node.id} (adding to globals)")

    def visit_Return(self, node):
        """Handle return statements."""
        if isinstance(node.value, ast.BinOp):
            self.visit(node.value)
        elif isinstance(node.value, ast.Constant):
            self.assembly_code.append(f"    mov rax, {node.value.n}")
        elif isinstance(node.value, ast.Name):
            self.assembly_code.append(f"    mov rax, {node.value.id}")
        self.assembly_code.append("    ret")

    def visit_BinOp(self, node):
        """Handle binary operations."""
        self.visit(node.left)
        self.assembly_code.append(f"    mov rbx, rax")  # Copy left operand into rbx
        self.visit(node.right)

        # Perform the operation based on the operator
        if isinstance(node.op, ast.Add):
            self.assembly_code.append("    add rax, rbx")
        elif isinstance(node.op, ast.Sub):
            self.assembly_code.append("    sub rax, rbx")
        elif isinstance(node.op, ast.Mult):
            self.assembly_code.append("    imul rax, rbx")
        elif isinstance(node.op, ast.Div):
            self.assembly_code.append("    cqo")
            self.assembly_code.append("    idiv rbx")
        elif isinstance(node.op, ast.Mod):
            self.assembly_code.append("    cqo")
            self.assembly_code.append("    idiv rbx")
            self.assembly_code.append("    mov rax, rdx")  # Remainder

    def visit_If(self, node):
        """Handle if-else statements."""
        self.assembly_code.append(f"    ; If condition")
        self.visit(node.test)
        self.assembly_code.append(f"    jz else_block")  # Jump if zero to else
        self.generic_visit(node.body)
        self.assembly_code.append(f"else_block:")

        if node.orelse:
            self.assembly_code.append(f"    ; Else condition")
            self.generic_visit(node.orelse)

    def visit_While(self, node):
        """Handle while loops."""
        loop_label = f"loop_{id(node)}"
        self.assembly_code.append(f"{loop_label}:")
        self.visit(node.test)
        self.assembly_code.append(f"    jz end_{loop_label}")
        self.generic_visit(node.body)
        self.assembly_code.append(f"    jmp {loop_label}")
        self.assembly_code.append(f"end_{loop_label}:")

    def visit_List(self, node):
        """Handle list construction."""
        self.assembly_code.append("    ; Creating list")
        for elt in node.elts:
            self.visit(elt)
            # Code for adding elements to the list (simplified)

    def visit_Dict(self, node):
        """Handle dictionary construction."""
        self.assembly_code.append("    ; Creating dictionary")
        for key, value in zip(node.keys, node.values):
            self.visit(key)
            self.visit(value)
            # Code for adding key-value pairs to the dictionary

    def visit_Attribute(self, node):
        """Handle attributes of objects."""
        self.assembly_code.append(f"    ; Handling attribute {node.attr}")

    def compile(self, python_code):
        """Parse and convert Python to Assembly."""
        tree = ast.parse(python_code)
        self.visit(tree)
        return "\n".join(self.assembly_code)

    def optimize(self):
        """Implement optimization techniques."""
        # Implement VCAL (Verbosity Compressing Algorithm Logic)
        self.apply_vcal()
        # Implement LPIT (Lossless Performance in Translation)
        self.apply_lpit()

    def apply_vcal(self):
        """Verbosity Compressing Algorithm Logic (VCAL) - Inline Assembly."""
        # Example of simple VCAL: Eliminate redundant loads/stores
        # We could do something like identifying repeated expressions and removing them
        pass

    def apply_lpit(self):
        """Lossless Performance in Translation (LPIT)."""
        # Ensure that performance isn't lost during translation. 
        # This can be done by analyzing instruction patterns and optimizing them for the target architecture.
        pass

# Example usage with optimized and extended support
python_code = """
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

def compute(a, b):
    if a > b:
        return a + b
    else:
        return a - b
"""

compiler = PyASMCompiler()
assembly = compiler.compile(python_code)
print("Generated Assembly Code:\n", assembly)

# Save the generated assembly to file
with open("output.asm", "w") as f:
    f.write(assembly)

# Step: Assemble and link the code
def assemble_and_link(output_file="output.bin"):
    subprocess.run(["nasm", "-f", "bin", "output.asm", "-o", output_file])
    print(f"Executable {output_file} created.")

assemble_and_link()

# Cleanup
os.remove("output.asm")
os.remove("output.bin")
