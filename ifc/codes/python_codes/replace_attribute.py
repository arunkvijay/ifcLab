for ele in f.traverse(wall):
    if hasattr(ele, 'Depth'):
        ifcopenshell.util.element.replace_attribute(ele, 1500, 600)