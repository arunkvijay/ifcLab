# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import os.path

import ifcopenshell
import ifcopenshell.api

def create_library(library_name, unit):
    library = ifcopenshell.api.run('project.create_file', file_name=library_name)
    root = ifcopenshell.api.run('root.create_entity', library, ifc_class='IfcProject', name='Library')
    context = ifcopenshell.api.run('root.create_entity', library, ifc_class='IfcProjectLibrary', name='Library')

    ifcopenshell.api.run('project.assign_declaration', library, definition=context, relating_context=root)

    # ifcopenshell.api.run('unit.assign_unit', library) #CHANGE THE UNIT IMMEDIATELY
    if unit=='metric':
        ifcopenshell.api.run('unit.assign_unit', library)
    else:
        length = ifcopenshell.api.run('unit.add_conversion_based_unit', library, name='inch')
        area = ifcopenshell.api.run('unit.add_conversion_based_unit', library, name='square foot')
        ifcopenshell.api.run('unit.assign_unit', library, units=[length, area])
#

    """
    # CHECK THE CODE BELOW BEFORE PUTTING IN PRODUCTION https://blenderbim.org/docs-python/autoapi/ifcopenshell/api/project/assign_declaration/index.html  
    # LIBRARY CREATION ALSO TO HAVE USER INPUTS LIKE IN SNAPTRUDE, EX DEFINE BEAM HT (beam thickness is anyways from the dwg)

    wall_type = ifcopenshell.api.run('root.create_entity', library, ifc_class='IfcWallType', name='WAL01')
    concrete = ifcopenshell.api.run('material.add_material', library, name='CON', category='concrete')
    rel = ifcopenshell.api.run('material.assign_material', library, product=wall_type, type='IfcMaterialLayerSet')
    layer = ifcopenshell.api.run('material.add_layer', library, layer_set=rel.RelatingMaterial, material=concrete)
    layer.Name = 'Structure'
    layer.LayerThickness = 200 #TO BE TAKEN FROM THE DWG THROUGH BOUNDING B0X

    ifcopenshell.api.run('project.assign_declaration', library, definition=wall_type, relating_context=context)
    """
    library.write(library_name)

library_name = 'library.ifc'
library_file = os.path.join('/home/20f82c13-9880-5efc-a643-e85321dbd70c/library', library_name)
create_library(library_file, unit='imperial')


"""
if not wall_type.HasContext:
    ifcopenshell.api.run('project.assign_declaration', library, definition=wall_type, relating_context=context)
"""

"""
ifcopenshell.api.run('root.create_entity', library, )
slab_material_layer_set = ifcopenshell.api.run('material.add_material_set', library, )
"""

"""

"""
