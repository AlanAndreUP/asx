from flask import Flask, render_template, request, jsonify
from anytree import Node, RenderTree
import re
import operator

app = Flask(__name__)

# Operadores soportados con precedencia
OPERATORS = {
    '+': (1, operator.add),
    '-': (1, operator.sub),
    '*': (2, operator.mul),
    '/': (2, operator.truediv),
}

def build_expression_tree(expression):
    """Construye un árbol de expresión matemática considerando precedencia de operadores."""
    def tokenize(expr):
        """Divide la expresión en tokens (números y operadores)."""
        tokens = re.findall(r'\d+|[+*/()-]', expr)
        return tokens

    def parse(tokens):
        """Convierte una lista de tokens en un árbol binario."""
        def precedence(op):
            return OPERATORS[op][0] if op in OPERATORS else -1

        def apply_operator(operators, values):
            """Aplica un operador al árbol usando los valores y nodos del stack."""
            op = operators.pop()
            right = values.pop()
            left = values.pop()
            node = Node(op)
            right.parent = node
            left.parent = node
            values.append(node)

        operators = []  # Stack de operadores
        values = []     # Stack de valores o subárboles

        for token in tokens:
            if token.isdigit():
                # Asegurarnos de que estamos creando un Node
                new_node = Node(token)
                values.append(new_node)  # Siempre crear un Node
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    apply_operator(operators, values)
                operators.pop()  # Eliminar '('
            elif token in OPERATORS:
                while (operators and precedence(operators[-1]) >= precedence(token)):
                    apply_operator(operators, values)
                operators.append(token)

        # Procesar operadores restantes
        while operators:
            apply_operator(operators, values)

        return values[0] if values else None

    tokens = tokenize(expression)
    return parse(tokens)


def evaluate_tree(node):
    """Evalúa el valor de un árbol de operaciones."""
    if node.name.isdigit():
        return int(node.name)
    
    # Evaluar los hijos
    left = evaluate_tree(node.children[0])
    right = evaluate_tree(node.children[1])
    
    # Evaluar la operación
    return OPERATORS[node.name][1](left, right)


def generate_tree_hierarchy(tree):
    """Genera la jerarquía del árbol de expresión."""
    if tree is None:
        return []

    return [
        {"name": node.name, "parent": node.parent.name if node.parent else None}
        for node in RenderTree(tree)
    ]

@app.route("/", methods=["GET"])
def render_calculator():
    """Renderiza la página de la calculadora."""
    return render_template("index.html", expression="", tree_data=None)

@app.route("/calculate", methods=["POST"])
def calculate():
    """Procesa la entrada de la calculadora y retorna el resultado."""
    expression = request.form.get("expression", "")
    action = request.form.get("action", "")
    tree_hierarchy = None

    if action == "C":
        expression = ""
    elif action == "=":
        try:
            # Construir árbol de la expresión
            tree = build_expression_tree(expression)

            if tree:
                # Evaluar la expresión a partir del árbol
                evaluated_result = evaluate_tree(tree)

                # Generar la jerarquía del árbol
                tree_hierarchy = generate_tree_hierarchy(tree)
                
                expression = str(evaluated_result)
            else:
                expression = "Error"
        except Exception as e:
            print("Error al evaluar la expresión:", e)
            expression = "Error"
    else:
        expression += action

    return jsonify({
        "expression": expression,
        "tree_hierarchy": tree_hierarchy
    })

if __name__ == "__main__":
    app.run(debug=True)
