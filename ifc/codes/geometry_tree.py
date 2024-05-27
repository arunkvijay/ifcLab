import multiprocessing
import ifcopenshell.geom

def create_geometry_tree(f):
    settings = ifcopenshell.geom.settings()
    iterator = ifcopenshell.geom.iterator(settings, f, multiprocessing.cpu_count())
    tree = ifcopenshell.geom.tree()
    if iterator.initialize():
        while True:
            tree.add_element(iterator.get_native())
            if not iterator.next():
                break
    return tree

