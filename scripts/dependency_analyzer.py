"""
Dependency Analyzer for Report Variables

This script analyzes the dependencies between variables to determine:
1. Calculation order (which variables must be calculated first)
2. Dependency depth (how many levels of calculation)
3. Circular dependencies (if any exist)
4. Critical path variables (those that many others depend on)
"""

import os
from pyairtable import Api
import json
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict, deque

print("Script started...")

# Load environment variables
load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get('AIRTABLE_API_KEY')
BASE_ID = os.environ.get('AIRTABLE_BASE_ID')
REPORT_VARIABLES_TABLE = 'Report_Variables'

# Check for required environment variables
if not AIRTABLE_API_KEY:
    raise ValueError("Missing AIRTABLE_API_KEY environment variable.")
if not BASE_ID:
    raise ValueError("Missing AIRTABLE_BASE_ID environment variable.")

# Initialize Airtable API
api = Api(AIRTABLE_API_KEY)
base = api.base(BASE_ID)


def parse_dependencies(report_variables):
    """
    Parse dependencies from Report_Variables into a graph structure
    Returns:
        dependency_graph: {variable_id: [list of dependencies]}
        variable_info: {variable_id: full variable data}
    """
    dependency_graph = {}
    reverse_graph = defaultdict(list)  # What depends on each variable
    variable_info = {}
    
    for record in report_variables:
        var = record['fields']
        var_id = var.get('Variable_ID')
        if not var_id:
            continue
        # Store full variable info
        variable_info[var_id] = {
            'display_name': var.get('Display_Name', ''),
            'formula': var.get('Formula', ''),
            'dependencies': var.get('Dependencies Variable_ID', ''),  # Updated field name
            'dependents': var.get('Dependents Variable_ID', ''),     # New field
            'source_type': var.get('Source_Type', ''),
            'data_type': var.get('Data_Type', '')
        }
        # Parse dependencies from lookup field
        deps_string = var.get('Dependencies Variable_ID', '')
        dependencies = []
        if isinstance(deps_string, str):
            if deps_string:
                dependencies = [d.strip() for d in deps_string.split(',') if d.strip()]
        elif isinstance(deps_string, list):
            dependencies = [str(d).strip() for d in deps_string if str(d).strip()]
        dependency_graph[var_id] = dependencies
        # Build reverse graph from dependents lookup field
        dependents_string = var.get('Dependents Variable_ID', '')
        if isinstance(dependents_string, str) and dependents_string:
            dependents = [d.strip() for d in dependents_string.split(',') if d.strip()]
            for dependent in dependents:
                reverse_graph[var_id].append(dependent)
        elif isinstance(dependents_string, list):
            for dependent in dependents_string:
                dep_val = str(dependent).strip()
                if dep_val:
                    reverse_graph[var_id].append(dep_val)
        # Also build reverse graph from dependencies (for completeness)
        for dep in dependencies:
            reverse_graph[dep].append(var_id)
    print("Parsed dependencies and built graphs.")
    return dependency_graph, reverse_graph, variable_info

def main():
    print("Main function entered...")
    print("Loading Report_Variables from Airtable...")
    report_vars_table = base.table(REPORT_VARIABLES_TABLE)
    report_vars = report_vars_table.all()
    print(f"✓ Found {len(report_vars)} variables in Report_Variables")
    print("Parsing dependencies...")
    dependency_graph, reverse_graph, variable_info = parse_dependencies(report_vars)
    print("Dependencies parsed.")
    
    # Analysis and processing logic here...
    # Example placeholder implementations for missing variables and circular dependency detection

    # Placeholder: compute total_vars, input_vars, calculated_vars, max_level, levels, variable_levels, critical_vars
    total_vars = len(variable_info)
    input_vars = [var_id for var_id, info in variable_info.items() if not dependency_graph[var_id]]
    calculated_vars = [var_id for var_id in variable_info if dependency_graph[var_id]]
    max_level = 0
    levels = {}
    variable_levels = {}
    critical_vars = []
    
    # Calculate dependency levels using topological sort
    def calculate_dependency_levels(dependency_graph):
        levels = defaultdict(list)
        variable_levels = {}
        in_degree = {var: len(deps) for var, deps in dependency_graph.items()}
        queue = deque([var for var, deg in in_degree.items() if deg == 0])
        for var in queue:
            levels[0].append(var)
            variable_levels[var] = 0
        while queue:
            current = queue.popleft()
            current_level = variable_levels[current]
            for var, deps in dependency_graph.items():
                if current in deps:
                    in_degree[var] -= 1
                    if in_degree[var] == 0:
                        variable_levels[var] = current_level + 1
                        levels[current_level + 1].append(var)
                        queue.append(var)
        return dict(levels), variable_levels

    print("Dependency graph:")
    for k, v in dependency_graph.items():
        print(f"  {k}: {v}")
    levels, variable_levels = calculate_dependency_levels(dependency_graph)
    print("\nLevels after calculation:")
    for lvl, vars in levels.items():
        print(f"  Level {lvl}: {vars}")
    max_level = max(levels.keys()) if levels else 0

    # Detect circular dependencies using DFS
    def find_circular_dependencies(graph):
        visited = set()
        stack = set()
        cycles = []

        def visit(node, path):
            if node in stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            for neighbor in graph.get(node, []):
                visit(neighbor, path + [neighbor])
            stack.remove(node)

        for node in graph:
            visit(node, [node])
        return cycles

    circular_deps = find_circular_dependencies(dependency_graph)

    # At the end, save the results to dependency_analysis.json
    results = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_variables': total_vars,
            'input_variables': input_vars,
            'calculated_variables': calculated_vars,
            'max_depth': max_level,
            'circular_dependencies': len(circular_deps)
        },
        'calculation_order': {
            f'level_{k}': v for k, v in levels.items()
        },
        'variable_levels': variable_levels,
        'critical_variables': critical_vars,
        'circular_dependencies': circular_deps,
        'dependency_graph': dependency_graph,
        'reverse_dependencies': dict(reverse_graph)
    }
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dependency_analysis.json'))
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Full analysis saved to {output_path}")

if __name__ == "__main__":
    main()
