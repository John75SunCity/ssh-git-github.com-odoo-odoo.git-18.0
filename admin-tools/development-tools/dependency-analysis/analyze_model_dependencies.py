import os
import ast
import networkx as nx
from collections import defaultdict
import argparse

class OdooModelParser(ast.NodeVisitor):
    """AST visitor to parse Odoo models and their dependencies."""
    def __init__(self):
        self.model_name = None
        self.dependencies = set()
        self.field_definitions = {}

    def visit_ClassDef(self, node):
        """Visit class definitions to find Odoo models."""
        for base in node.bases:
            if isinstance(base, ast.Attribute) and base.attr == 'Model':
                self.generic_visit(node)
                break

    def visit_Assign(self, node):
        """Visit assignments to find model name and fields."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            if target_name == '_name' and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                self.model_name = node.value.value

            elif target_name == '_inherit':
                self.is_inherit = True
                if isinstance(node.value, ast.Str):
                    self.dependencies.add(node.value.s)
                elif isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Str):
                            self.dependencies.add(elt.s)

            elif isinstance(node.value, ast.Call) and hasattr(node.value, 'func'):
                func = node.value.func
                # Check for fields.Something()
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == 'fields':
                    field_type = func.attr
                    comodel = self._get_comodel(node.value)

                    # Only consider Many2one for dependency graph to avoid cycles with One2many
                    if field_type == 'Many2one' and comodel:
                        self.dependencies.add(comodel)

                    self.field_definitions[target_name] = {'type': field_type, 'comodel': comodel}
        self.generic_visit(node)

    def _get_comodel(self, call_node):
        """Extract comodel from field definition."""
        if call_node.args and isinstance(call_node.args[0], ast.Str):
            return call_node.args[0].s
        for keyword in call_node.keywords:
            if keyword.arg == 'comodel_name' and isinstance(keyword.value, ast.Str):
                return keyword.value.s
        return None

def analyze_dependencies(start_path):
    """Analyze model dependencies and build a dependency graph."""
    graph = nx.DiGraph()
    model_files = {}
    model_definitions = {}

    for root, _, files in os.walk(start_path):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=file_path)
                        parser = OdooModelParser()
                        parser.visit(tree)
                        if parser.model_name:
                            graph.add_node(parser.model_name)
                            model_files[parser.model_name] = file_path
                            model_definitions[parser.model_name] = parser.field_definitions
                            for dep in parser.dependencies:
                                if parser.model_name != dep:
                                    graph.add_edge(parser.model_name, dep)
                    except SyntaxError as e:
                        print(f"Syntax error in {file_path}: {e}")

    return graph, model_files, model_definitions

def find_circular_dependencies(graph, highlight=None):
    """Find and report circular dependencies in the graph."""
    cycles = list(nx.simple_cycles(graph))
    if cycles:
        print(f"🔥 {len(cycles)} Circular Dependencies Detected! These must be fixed.")

        # Write all cycles to a file
        with open('dependency_cycles.txt', 'w') as f:
            for i, cycle in enumerate(cycles, 1):
                f.write(f"Cycle #{i}: {' -> '.join(cycle + [cycle[0]])}\n")
        print("\n📝 Full list of cycles written to dependency_cycles.txt")

        highlight_cycles = []
        if highlight:
            for cycle in cycles:
                if any(model in cycle for model in highlight):
                    highlight_cycles.append(cycle)

        if highlight_cycles:
            print(f"\n🚨 Found {len(highlight_cycles)} cycles involving: {', '.join(highlight)}")
            for i, cycle in enumerate(highlight_cycles, 1):
                print(f"\nHighlighted Cycle #{i}:")
                print(" -> ".join(cycle + [cycle[0]]))
        else:
            # If no highlighted cycles are found, you might want to print all cycles or a message.
            # For now, let's just print a selection to avoid overwhelming the output.
            print("\nNo specific cycles found for highlighted models. Showing a sample of all cycles.")
            for i, cycle in enumerate(cycles[:10], 1): # Print first 10 as a sample
                print(f"\nCycle Sample #{i}:")
                print(" -> ".join(cycle + [cycle[0]]))

        return cycles
    else:
        print("✅ No circular dependencies found.")
        return []

def get_import_order(init_file):
    """Get the current import order from __init__.py."""
    with open(init_file, 'r') as f:
        imports = [line.split('import')[1].strip() for line in f if line.strip().startswith('from . import')]
    return imports

def suggest_import_order(graph, existing_order):
    """Suggest a new import order based on topological sort."""
    try:
        sorted_models = list(nx.topological_sort(graph))
        print("\n🚀 Suggested Import Order (Topological Sort):")
        for model in sorted_models:
            if model in existing_order:
                print(f"  - {model}")
        return sorted_models
    except nx.NetworkXUnfeasible:
        print("\n❌ Cannot determine a valid import order due to cycles.")
        return None

def generate_init_file(graph, model_files):
    """Generate the content for __init__.py based on topological sort."""
    try:
        sorted_models = list(nx.topological_sort(graph))

        # Create a mapping from file path to a list of models in that file
        file_to_models = defaultdict(list)
        for model, path in model_files.items():
            file_to_models[path].append(model)

        # Create a mapping from model name to its file's basename
        model_to_basename = {model: os.path.splitext(os.path.basename(path))[0] for model, path in model_files.items()}

        # Get a unique, ordered list of file basenames
        sorted_basenames = []
        seen_basenames = set()
        for model in sorted_models:
            if model in model_to_basename:
                basename = model_to_basename[model]
                if basename not in seen_basenames:
                    sorted_basenames.append(basename)
                    seen_basenames.add(basename)

        print("# -*- coding: utf-8 -*-")
        print("# Auto-generated by dependency-analysis script.")
        print("# Do not edit manually, as it will be overwritten.")
        print("\n".join(f"from . import {basename}" for basename in sorted_basenames))

    except nx.NetworkXUnfeasible:
        print("# Cannot generate __init__.py due to circular dependencies.", file=sys.stderr)


def main():
    """Main function to run the dependency analysis."""
    parser = argparse.ArgumentParser(description="Analyze Odoo model dependencies and find cycles.")
    parser.add_argument(
        '--generate-init',
        action='store_true',
        help='Generate the __init__.py file content to stdout.'
    )
    args = parser.parse_args()

    module_path = 'records_management/models'
    init_file = os.path.join(module_path, '__init__.py')
    highlight_models = ['advanced.billing', 'advanced.billing.line']

    if not args.generate_init:
        print("="*50)
        print("🔍 Starting Odoo Model Dependency Analysis...")
        print(f"Highlighting cycles involving: {', '.join(highlight_models)}")
        print("="*50)

    graph, model_files, _ = analyze_dependencies(module_path)

    if not args.generate_init:
        print(f"\n📊 Found {len(graph.nodes)} models and {len(graph.edges)} dependencies.")

    cycles = find_circular_dependencies(graph, highlight=highlight_models)

    if not cycles:
        if args.generate_init:
            generate_init_file(graph, model_files)
        else:
            if os.path.exists(init_file):
                existing_order = get_import_order(init_file)
                suggest_import_order(graph, existing_order)
            else:
                print(f"\n⚠️  __init__.py not found at {init_file}. Cannot compare order.")
                print("Run with --generate-init to create it.")
    elif not args.generate_init:
        print("\nFix cycles before an import order can be suggested.")

if __name__ == "__main__":
    main()
