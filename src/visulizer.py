import graphviz

from parser import Node

def visualize(root: Node, pth: str) -> None:
    graph = graphviz.Digraph("AST")
    graph.attr(rankdir='TB', bgcolor="#e3e5e7", splines='spline', dpi='300')
    graph.node_attr.update(
        shape='box',
        style='filled,rounded',
        fontname='Helvetica',
        fontsize='14',
        fontcolor='#1a1a1a',
    )
    
    COLORS = \
    {
        "root":           "#b6c5d4",    

        "select-operator":"#81c784",     
        "all":            "#81c784",

        "column-list":    "#ffe082",       
        "column-list-tail":"#ffe082",
        "column":         "#ffe082",
        "comma":          "#ffe082",

        "source":         "#ffb74d",       
        "from-table":     "#ffb74d",
        "from":           "#ffb74d",
        "table":          "#ffb74d",
        "noun":           "#ffb74d",

        "conditions":     "#b39ddb",     
        "where":          "#b39ddb",
        "condition":      "#b39ddb",

        "expression":     "#f48fb1",       
        "expression-tail":"#f48fb1",
        "chain":          "#f48fb1",

        "inequality-signs":"#ef9a9a",      
        "condition-word": "#ef9a9a",

        "sort-operator":  "#4fc3f7",       
        "sort":           "#4fc3f7",
        "prep":           "#4fc3f7",
        "order":          "#4fc3f7",
        
        "limit-operator": "#a95aff",
        "limit": "#a95aff",
        "numr": "#a95aff",

        "epsilon":        "#cfd8dc",
    }
    
    queue = [(root, None)]
    node_counter = 0
    
    while queue:
        node, parent_id = queue.pop(0)
        node_id = f"node_{node_counter}"
        node_counter += 1
        
        label = f"{node.rule}\n\n{node.val.tok}\n{node.val.pos}"
        color = COLORS.get(node.rule, 'white')
        graph.node(node_id, label, fillcolor=color)
        
        if parent_id is not None:
            graph.edge(parent_id, node_id)
        
        for child in node.children:
            queue.append((child, node_id))
    
    graph.render(pth, format="png", view=False, cleanup=True, engine='dot')
            
    
    
    
    