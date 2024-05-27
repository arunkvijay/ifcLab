# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import argparse
import os.path

import ifcopenshell
import ifcopenshell.api

def create_library(library_file, unit='metric'):
    library_name = library_file.split('/')[-1]
    library = ifcopenshell.api.run('project.create_file', file_name=library_file)
    root = ifcopenshell.api.run('root.create_entity', library, ifc_class='IfcProject', name='Library')
    context = ifcopenshell.api.run('root.create_entity', library, ifc_class='IfcProjectLibrary', name='Library')

    ifcopenshell.api.run('project.assign_declaration', library, definition=context, relating_context=root)

    if unit=='metric':
        ifcopenshell.api.run('unit.assign_unit', library)
    else:
        length = ifcopenshell.api.run('unit.add_conversion_based_unit', library, name='inch')
        area = ifcopenshell.api.run('unit.add_conversion_based_unit', library, name='square foot')
        ifcopenshell.api.run('unit.assign_unit', library, units=[length, area])
    library.write(library_file)

#parser = argparse.ArgumentParser(description='CLI argument for creating library')
#parser.add_argument('--org_config', required=True, help='path to org_config.json file')
# parser.add_argument('--project_config', required=True, help='path to project_config.json file')
# args = parser.parse_args()

# library
library_file = '/home/library.ifc'
create_library(library_file)

