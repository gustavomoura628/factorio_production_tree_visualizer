import math

from treelib import Node, Tree
import json

with open('recipes.json', 'r') as file:
    recipes = json.load(file)

with open('machines.json', 'r') as file:
    machines = json.load(file)

with open('modules.json', 'r') as file:
    modules = json.load(file)

with open('main_bus.json', 'r') as file:
    main_bus = json.load(file)


from InquirerPy import inquirer
def choose_from_list(choices, message):
    # Create a fuzzy-searchable menu
    return inquirer.fuzzy(
        message=message,
        choices=choices
    ).execute()

list_of_items = [key for key, value in recipes.items() if value["type"] != "base_material"]
selected_item = choose_from_list(list_of_items, "Select an item")
print(f"You selected: {selected_item}")

quantity = float(input("Enter the amount: "))

list_of_modules = [key for key, value in modules.items()]
selected_module = choose_from_list(list_of_modules, "Choose a module: ")

list_of_assemblers = [key for key, value in machines.items() if value["type"] == "assembler"]
selected_assembly_machine = choose_from_list(list_of_assemblers, "Choose an assembler: ")
list_of_furnaces = [key for key, value in machines.items() if value["type"] == "furnace"]
selected_furnace = choose_from_list(list_of_furnaces, "Choose a furnace: ")
selected_chemical_plant = "Chemical plant"


def fix_number_display(quantity):
    # Fix decimal weirdness
    qty_rounded = round(quantity+0.003,2)
    if isinstance(qty_rounded, float) and qty_rounded.is_integer():
        qty_display = int(qty_rounded)
    else:
        qty_display = qty_rounded
    return qty_display

def add_to_total_resources(total_resources, type, item, quantity):
    if item in total_resources[type]:
        total_resources[type][item]+=quantity
    else:
        total_resources[type][item]=quantity

def figure_out_the_machine(item):
    # figuring out what machine you use to make it
    machine = selected_assembly_machine
    if machine not in recipes[item]["machine_type"]:
        machine = selected_chemical_plant
    if machine not in recipes[item]["machine_type"]:
        machine = selected_furnace
    if machine not in recipes[item]["machine_type"]:
        raise Exception("FATAL ERROR: ["+item+"] DOES NOT HAVE A CHOSEN MACHINE")
    
    return machine

def build_tree_recursive(tree, total_resources, parent, item, quantity):
    node_id = parent+"_"+item
    qty_display = fix_number_display(quantity)

    if recipes[item]["type"] == "base_material" or item in main_bus:
        tree.create_node(f"{qty_display} {item}", node_id, parent=parent)
        add_to_total_resources(total_resources, "item", item, quantity)
        return

    output_amount = recipes[item]["output_amount"]
    crafting_time = recipes[item]["crafting_time"]

    machine=figure_out_the_machine(item)

    crafting_speed = machines[machine]["crafting_speed"]

    if recipes[item]["type"] == "final_product":
        productivity_multiplier = 1
    else:
        productivity_multiplier = 1 + machines[machine]["module_slots"]*modules[selected_module]["Productivity"]

    speed_multiplier = 1 + machines[machine]["module_slots"]*modules[selected_module]["Speed"]
    print("productivity multiplier for", machine, productivity_multiplier)

    number_of_machines = (quantity / crafting_speed * crafting_time / productivity_multiplier / speed_multiplier / output_amount)
    machines_qty_display = fix_number_display(number_of_machines)
    number_of_machines_ceil = math.ceil(number_of_machines)
    add_to_total_resources(total_resources, "machine", machine, number_of_machines_ceil)
    add_to_total_resources(total_resources, "module", selected_module, number_of_machines_ceil*machines[machine]["module_slots"])


    tree.create_node(f"{qty_display} {item} \n {machines_qty_display} {machine}", node_id, parent=parent)

    add_to_total_resources(total_resources, "item", item, quantity)

    if item not in recipes:
        raise Exception("FATAL ERROR: ["+item+"] DOES NOT HAVE A RECIPE DEFINED")

    for child in recipes[item]["ingredients"]:
        child_qty = recipes[item]["ingredients"][child]
        build_tree_recursive(tree, total_resources, node_id, child, quantity*child_qty/productivity_multiplier/output_amount)

    
    return tree

def build_tree(item, quantity):
    if recipes[item]["type"] == "base_material" or item in main_bus:
        raise Exception("FATAL ERROR: ["+item+"] IS A BASE MATERIAL OR IN YOUR MAIN BUS")

    tree = Tree()
    total_resources = {}
    total_resources["item"] = {}
    total_resources["machine"] = {}
    total_resources["module"] = {}
    tree.create_node(f"temporary string", "total_resources")

    qty_display = fix_number_display(quantity)

    output_amount = recipes[item]["output_amount"]
    crafting_time = recipes[item]["crafting_time"]

    machine=figure_out_the_machine(item)

    crafting_speed = machines[machine]["crafting_speed"]
    if recipes[item]["type"] == "final_product":
        productivity_multiplier = 1
    else:
        productivity_multiplier = 1 + machines[machine]["module_slots"]*modules[selected_module]["Productivity"]
    speed_multiplier = 1 + machines[machine]["module_slots"]*modules[selected_module]["Speed"]

    number_of_machines = (quantity / crafting_speed * crafting_time / productivity_multiplier / speed_multiplier / output_amount)
    machines_qty_display = fix_number_display(number_of_machines)
    number_of_machines_ceil = math.ceil(number_of_machines)

    add_to_total_resources(total_resources, "machine", machine, number_of_machines_ceil)
    add_to_total_resources(total_resources, "module", selected_module, number_of_machines_ceil*machines[machine]["module_slots"])



    node_id = item
    tree.create_node(f"{qty_display} {item} \n {machines_qty_display} {machine}", node_id, parent="total_resources")

    add_to_total_resources(total_resources, "item", item, quantity)

    if item not in recipes:
        raise Exception("FATAL ERROR: ["+item+"] DOES NOT HAVE A RECIPE DEFINED")

    for child in recipes[item]["ingredients"]:
        child_qty = recipes[item]["ingredients"][child]
        build_tree_recursive(tree, total_resources, node_id, child, quantity*child_qty/productivity_multiplier/output_amount)


    # Build final count for total resources
    total_resources_str = "-------Total Raw Resources-------\n"
    for item in total_resources["item"]:
        qty_display=fix_number_display(total_resources["item"][item])
        if recipes[item]["type"] == "base_material" or item in main_bus:
            total_resources_str+=f"{item}: {qty_display} /s\n"

    total_resources_str += "----Total Intermediate Resources----\n"
    for item in total_resources["item"]:
        qty_display=fix_number_display(total_resources["item"][item])
        if not (recipes[item]["type"] == "base_material" or item in main_bus):
            total_resources_str+=f"{item}: {qty_display} /s\n"

    total_resources_str += "-------------Total Machines-------------\n"
    for machine in total_resources["machine"]:
        qty_display=fix_number_display(total_resources["machine"][machine])
        total_resources_str+=f"{machine}: {qty_display}\n"

    total_resources_str += "-------------Total Modules-------------\n"
    for module in total_resources["module"]:
        qty_display=fix_number_display(total_resources["module"][module])
        total_resources_str+=f"{module}: {qty_display}\n"


    root = tree.get_node("total_resources")
    root.tag = f"{total_resources_str}"
    
    return tree



# This one does not have fuzzy finding
## Select item
#from prompt_toolkit import prompt
#from prompt_toolkit.completion import WordCompleter
#
## List of strings
#items = ["item1", "item2", "item3"]
#
## Create a WordCompleter for the search functionality
#completer = WordCompleter(items, ignore_case=True)
#
## Prompt the user with the menu
#selection = prompt("Select an item: ", completer=completer)
#
#print(f"You selected: {selection}")



# Figure out the file name and clean up the characters a bit
import os
import shutil
filename=selected_item+"_x"+str(quantity)
filename = ''.join(c if c!=' ' else '_' for c in filename)
filename = ''.join(c if c!='.' else '-' for c in filename)
if not os.path.isdir("output"):
    os.mkdir("output")
if os.path.isdir("output/"+filename):
    shutil.rmtree("output/"+filename)
os.mkdir("output/"+filename)
filename="output/"+filename+"/"+filename


# Build tree
tree = build_tree(selected_item, quantity)

# Show tree on terminal
tree.to_graphviz(shape="rectangle")

# Save tree as dot file
tree.to_graphviz(filename=filename+".dot", shape="rectangle")

# Save png of tree
import pydot

(graph,) = pydot.graph_from_dot_file(filename+'.dot')
graph.write_png(filename+'.png')

# Convert tree to drawio xml
from graphviz2drawio import graphviz2drawio
xml = graphviz2drawio.convert(filename+".dot")
with open(filename+".xml","w") as file:
    file.write(xml)