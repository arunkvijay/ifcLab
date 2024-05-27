# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import numpy as np
import csv
import mathutils
import ifcopenshell
import ifcopenshell.api

def element_plc (json_file):
    element_coords = []
    for element in json_file:
        element_props = element.get('props')
        min_value = min(json_file[0].get('props')['width'], json_file[0].get('props')['height'])
        if element_props['width'] == element_props['height']:
            x = element_props['x'] + element_props['width']/2
            y = element_props['y'] + element_props['height']/2
        elif element_props['width'] < element_props['height']:
            x = element_props['x'] + min_value/2        
            y = element_props['y']
        else:
            x = element_props['x']
            y = element_props['y'] + min_value/2
        element_coords.append(((x,y), (element_props['width'], element_props['height']))) #have modified this to include width and height
    return element_coords

def create_storeys(num_storeys):
    for i in range(num_storeys): #for creating storeys programmically along with enum
        storey = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcBuildingStorey', name=storeys_dict.get(i).title().replace('_',' '))
        ifcopenshell.api.run('aggregate.assign_object', f, relating_object = building, product=storey)

def create_element(element_type, ifc_class): #add predefined type
    element = ifcopenshell.api.run('root.create_entity', f, ifc_class=ifc_class)
    ifcopenshell.api.run('type.assign_type', f, related_object=element, relating_type=element_type)
    return element

def create_walls(json_file, storey):
    lib_wall_type = [_ for _ in library.by_type("IfcWallType") if _.Name == "WALL"][0]
    wall_type = ifcopenshell.api.run("project.append_asset", f, library=library, element=lib_wall_type)
    wall_coords = element_plc(json_file)
    for coord in wall_coords:
        # width = coord[1][0]
        # height = coord[1][1]
        # x = coord[0][0]
        # y = coord[0][1]
        wall = create_element(wall_type, "IfcWall")
        ifcopenshell.api.run("spatial.assign_container", f, product=wall, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=wall)
        create_voids(json_file, storey, wall)

def create_voids(json_file, storey, element):
    opening_coords = element_plc(json_file)
    for coord in opening_coords:
        opening = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcOpeningElement")
        width = coord[1][0]
        height = coord[1][1]
        x = coord[0][0]
        y = coord[0][1]

        matrix = np.identity(4)
        matrix[:,3] = [0,0,750,0]
        representation=ifcopenshell.api.run("geometry.add_wall_representation", f, context=body, length=0.1, height=1.35, thickness=.64)
        ifcopenshell.api.run("geometry.assign_representation", f, product=opening, representation=representation)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=opening, matrix=matrix, is_si=False)
        ifcopenshell.api.run("void.add_opening", f, opening=opening, element=element)

# path = "D:\WALL_TEST.ifc"
path = '/home/wall.ifc'
storeys_dict = {0: 'ground_floor', 1: 'first_floor', 2: 'second_floor', 3: 'third_floor', 4:'fourth_floor'}

project_name = 'My Project' 
site_name = 'My Site' 
building_name = 'My Building' 
num_storeys = 1 

# library = ifcopenshell.open("D:\old_library.ifc")
library = ifcopenshell.open('/home/20f82c13-9880-5efc-a643-e85321dbd70c/library/library_metric.ifc')

f = ifcopenshell.api.run('project.create_file')

project = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcProject', name=project_name)    
site = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcSite', name=site_name)
ifcopenshell.api.run('aggregate.assign_object', f, relating_object=project, product=site)
building = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcBuilding', name=building_name)    
ifcopenshell.api.run('aggregate.assign_object', f, relating_object=site, product=building)

ifcopenshell.api.run('unit.assign_unit', f)

model3d = ifcopenshell.api.run('context.add_context', f, context_type='Model')
plan = ifcopenshell.api.run('context.add_context', f, context_type='Plan')
body = ifcopenshell.api.run('context.add_context', f, context_type='Model', context_identifier='Body', target_view='MODEL_VIEW', parent=model3d)

create_storeys(num_storeys)

storeys = f.by_type('IfcBuildingStorey')
gf_storey = [_ for _ in storeys if _.Name == 'Ground Floor'][0]
gf_floor_to_floor_ht = 3000

create_walls(wall_json_file, gf_storey)

f.write(path)
