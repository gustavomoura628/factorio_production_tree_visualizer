from treelib import Node, Tree
import json

with open('recipes.json', 'r') as file:
    recipes = json.load(file)

print("Recipes:")
for thing in recipes:
    print(f"- {thing}")



def build_tree_recursive(tree, total_resources, parent, item, quantity):
    node_id = parent+"_"+item

    # Fix decimal weirdness
    qty_rounded = round(quantity+0.004,2)
    if isinstance(qty_rounded, float) and qty_rounded.is_integer():
        qty_display = int(qty_rounded)
    else:
        qty_display = qty_rounded


    tree.create_node(f"{qty_display} {item}", node_id, parent=parent)

    # Add to total resources count
    if item in total_resources:
        total_resources[item]+=quantity
    else:
        total_resources[item]=quantity

    if item not in recipes:
        raise Exception("FATAL ERROR: ["+item+"] DOES NOT HAVE A RECIPE DEFINED")

    if recipes[item]["type"] == "base_material":
        return
    else:
        for child in recipes[item]["ingredients"]:
            child_qty = recipes[item]["ingredients"][child]
            build_tree_recursive(tree, total_resources, node_id, child, quantity*child_qty)
    
    return tree

def build_tree(item, quantity):
    tree = Tree()
    total_resources = {}
    tree.create_node(f"temporary string", "total_resources")

    # Fix decimal weirdness
    qty_rounded = round(quantity+0.004,2)
    if isinstance(qty_rounded, float) and qty_rounded.is_integer():
        qty_display = int(qty_rounded)
    else:
        qty_display = qty_rounded

    node_id = item
    tree.create_node(f"{qty_display} {item}", node_id, parent="total_resources")

    # Add to total resources count
    if item in total_resources:
        total_resources[item]+=quantity
    else:
        total_resources[item]=quantity

    if item not in recipes:
        raise Exception("FATAL ERROR: ["+item+"] DOES NOT HAVE A RECIPE DEFINED")

    if recipes[item]["type"] == "base_material":
        return
    else:
        for child in recipes[item]["ingredients"]:
            child_qty = recipes[item]["ingredients"][child]
            build_tree_recursive(tree, total_resources, node_id, child, quantity*child_qty)

    # Build final count for total resources

    total_resources_str = "Total Resources for building "+str(quantity)+" "+item+"\n"
    for item in total_resources:
        # Fix decimal weirdness
        qty_rounded = round(total_resources[item]+0.004,2)
        if isinstance(qty_rounded, float) and qty_rounded.is_integer():
            qty_display = int(qty_rounded)
        else:
            qty_display = qty_rounded
        total_resources_str+=f"{item}: {qty_display}\n"

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

from InquirerPy import inquirer

# List of items
items = ["item1", "item2", "item3"]
items = [key for key, value in recipes.items() if value["type"] == "manufactured_item"]

# Create a fuzzy-searchable menu
selected_item = inquirer.fuzzy(
    message="Select an item:",
    choices=items
).execute()

print(f"You selected: {selected_item}")

quantity = float(input("Enter the amount: "))


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
