# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import csv
import json
import multiprocessing
import numpy as np
import re

import mathutils

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.unit
import ifcopenshell.geom

def json_process(json_file):
    with open(json_file) as jf:
        json_data = json.load(jf)
    return json_data

def element_plc (json_file, selection_type):
    json_data = json_process(json_file)
    element_coords = []
    for element in json_data:
        element_props = element.get('props')
        if selection_type == 'block':
            x = element_props['x']
            y = element_props['y']
            rotation = element_props['rotation']
            scaleX = element_props['scaleX']
            scaleY = element_props['scaleY']
            block_name = element.get('BlockName')
            element_type = element.get('LayerName').split('_')[-1]
            if 'FURNITURE' in json_file:
                block_name = block_name.split('_',maxsplit=1)[1]
                element_coords.append((x, y, rotation, scaleX, scaleY, block_name))
            else:
                element_coords.append((x, y, rotation, scaleX, scaleY, block_name, element_type))
        elif selection_type == 'bbox':
            min_value = min(element_props['width'], element_props['length'])
            if element_props['width'] == element_props['length']:
                x = element_props['x'] + element_props['width']/2
                y = element_props['y'] + element_props['length']/2
            elif element_props['width'] < element_props['length']:
                x = element_props['x'] + min_value/2        
                y = element_props['y']
            else:
                x = element_props['x']
                y = element_props['y'] + min_value/2
            element_coords.append(((x,y), (element_props['width'], element_props['length']))) 
        elif selection_type == 'line':
            x1 = element_props['x1']
            y1 = element_props['y1']
            x2 = element_props['x2']
            y2 = element_props['y2']
            element_coords.append(((x1, y1), (x2, y2)))
    return element_coords

def create_element(f, element_type, ifc_class, predefined_type): 
    element = ifcopenshell.api.run('root.create_entity', f, ifc_class=ifc_class, predefined_type=predefined_type)
    ifcopenshell.api.run('type.assign_type', f, related_object=element, relating_type=element_type)
    return element

def element_z_translation(f, element, z_translation):
    ele_plc = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement) 
    ele_plc[:,3][2] = z_translation

    element_matrix = mathutils.Matrix(ele_plc)
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=element, matrix=element_matrix, is_si=False)

def get_polyline_list(csv_file):
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        polyline_list = list(csv_reader)
    return polyline_list

def polyline_coords(csv_xy):
    return tuple([(float(csv_xy[i]), float(csv_xy[i+1])) for i in range(0,len(csv_xy)-1,2)])

def create_slab(f, library, body, storey, csv_file, depth, predefined_type, object_type=None):
    lib_slab_type = [_ for _ in library.by_type('IfcSlabType') if _.PredefinedType == predefined_type][0] #change to name instead of predifined ADD MATERIALS PROGRAMMICALLY AS DONE FOR COLUMNS. PREDEFINEDTYPE REQD FOR ROOF VS BASE SLAB

    slab_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_slab_type)

    slab_list = get_polyline_list(csv_file)
    for slab_xy in slab_list:
        slab = create_element(f, slab_type, 'IfcSlab', predefined_type)

        if predefined_type == 'USERDEFINED':
            slab.ObjectType = object_type

        ifcopenshell.api.run('spatial.assign_container', f, product=slab, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=slab)
        points = polyline_coords(slab_xy)

        slab_depth = depth*ifcopenshell.util.unit.calculate_unit_scale(f) #check the depth calculation for metric projects too
        representation = ifcopenshell.api.run('geometry.add_slab_representation', f, context=body, points=points, depth=slab_depth)
        ifcopenshell.api.run('geometry.assign_representation', f, product=slab, representation=representation)

        element_z_translation(f, slab, -depth)

def create_voids(f):
    tree = create_geometry_tree(f)

    all_openings = f.by_type('IfcOpeningElement')
    for o in all_openings:
        wall = geometry_iterator(f, tree, o)
        if wall is None:
            continue
        ifcopenshell.api.run('void.add_opening', f, opening=o, element=wall)

    all_doors_windows = [e for e in f if e.is_a() in ['IfcWindow', 'IfcDoor']]
    for ent in all_doors_windows: 
        wall = geometry_iterator(f, tree, ent) 
        if wall is None:
            continue
        opening_element = create_opening_element(f, ent)
        ifcopenshell.api.run('void.add_opening', f, opening=opening_element, element=wall)
        ifcopenshell.api.run('void.add_filling', f, opening=opening_element, element=ent)

    slab_cutouts = [e for e in f.by_type('IfcSlab') if e.PredefinedType=='USERDEFINED' and 'CUTOUT' in e.ObjectType]
    for s in slab_cutouts:
        slab_selection = geometry_iterator(f, tree, s)
        slab_opening_element = create_opening_element(f, s)
        ifcopenshell.api.run('void.add_opening', f, opening=slab_opening_element, element=slab_selection)

def create_door_window(element, f, library, body, storey, json_file, predefined_type, lintel_lvl):
    element_coords = element_plc(json_file, selection_type='block')

    for coord in element_coords:
        if coord[-1] == 'WINDOW':
            element_type_name = 'IfcWindowType'
            ifc_class = 'IfcWindow'
        elif coord[-1] == 'DOOR':
            element_type_name = 'IfcDoorType'
            ifc_class = 'IfcDoor'

        x = coord[0]
        y = coord[1]
        rotation = coord[2]
        scaleX = coord[3]
        scaleY = coord[4]
        
        if not [el for el in f.by_type(element_type_name) if el.Name == coord[-2]]:
            lib_type = [el for el in library.by_type(element_type_name) if el.Name == coord[-2]][0]
            ele_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_type)
        else:
            ele_type = [_ for _ in f.by_type(element_type_name) if _.Name == coord[-2]][0]

        door_or_window = create_element(f, ele_type, ifc_class, predefined_type)
        door_or_window_add_property(door_or_window, coord[-2], lintel_lvl)

        ifcopenshell.api.run('spatial.assign_container', f, product=door_or_window, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=door_or_window)

        door_or_window_plc = ifcopenshell.util.placement.get_local_placement(door_or_window.ObjectPlacement)

        psi = rotation
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        door_or_window_plc[:,3][0] = x
        door_or_window_plc[:,3][1] = y
        door_or_window_plc[:3,:3] = rotZ
        matrix = mathutils.Matrix(door_or_window_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=door_or_window, matrix=matrix, is_si=False)

def create_furniture(f, library, body, storey, json_file):
    element_coords = element_plc(json_file, selection_type='block')

    for coord in element_coords:
        x = coord[0]
        y = coord[1]
        rotation = coord[2]
        scaleX = coord[3]
        scaleY = coord[4]
        
        if not [el for el in f.by_type('IfcFurnitureType') if el.Name == coord[-1]]:
            lib_type = [el for el in library.by_type('IfcFurnitureType') if el.Name == coord[-1]][0]
            ele_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_type)
        else:
            ele_type = [_ for _ in f.by_type('IfcFurnitureType') if _.Name == coord[-1]][0]

        furniture_element = create_element(f, ele_type, ifc_class='IfcFurniture', predefined_type=coord[-1].split('_')[0])

        ifcopenshell.api.run('spatial.assign_container', f, product=furniture_element, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=furniture_element)

        furniture_element_plc = ifcopenshell.util.placement.get_local_placement(furniture_element.ObjectPlacement)

        psi = rotation
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        rot_negZ = mathutils.Matrix([[np.cos(psi), np.sin(psi), 0],
                                [-np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        furniture_element_plc[:,3][0] = x
        furniture_element_plc[:,3][1] = y
        if scaleY == -1:
            furniture_element_plc[:3,:3] = rot_negZ# @ rotZ
        else:
            furniture_element_plc[:3,:3] = rotZ
        matrix = mathutils.Matrix(furniture_element_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=furniture_element, matrix=matrix, is_si=False)

def window_z_translation(f, lintel_lvl):
    windows = f.by_type('IfcWindow')
    for win in windows:
        element_z_translation(f, win, z_translation=max(lintel_lvl, win.OverallHeight)-win.OverallHeight)

def door_or_window_add_property(element, property, lintel_level):
    element.Name = property #THIS HAS TO BE RUN ON ANOTHER LOOP TO HAVE THE LAST INCREMENT NUM https://chat.openai.com/share/68fbacec-ff23-487b-8e24-4b37694534fe
    if 'D750' in property:
        element.OverallWidth = 750 #TO AUTOMATE THIS. TO HAVE DOORS/WINDOWS TO HAVE SIZE LIKE 750x2100
        element.OverallHeight = lintel_level
    elif 'D900' in property:
        element.OverallWidth = 900
        element.OverallHeight = lintel_level
    elif 'D1200' in property:
        element.OverallWidth = 1200
        if 'x' in element.Name:
            ele_ht = int(element.Name.split('_')[0].split('x')[-1])
            element.OverallHeight = ele_ht
        else:
            element.OverallHeight = lintel_level
    elif 'D1260' in property:
        element.OverallWidth = 1260
        if 'x' in element.Name:
            ele_ht = int(element.Name.split('_')[0].split('x')[-1])
            element.OverallHeight = ele_ht
        else:
            element.OverallHeight = lintel_level
    elif 'D1500' in property:
        element.OverallWidth = 1500
        element.OverallHeight = lintel_level
    elif 'D1800' in property:
        element.OverallWidth = 1800
        element.OverallHeight = lintel_level
    elif 'D2000' in property:
        element.OverallWidth = 2000
        element.OverallHeight = lintel_level
    elif 'D1850' in property:
        element.OverallWidth = 1850
        element.OverallHeight = lintel_level

    elif 'V450' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'V600' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'V760' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'V880' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'V900' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'V1380' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'V1430' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W600' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W750' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W840' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1040' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1135' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1200' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1385' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1750' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1800' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1840' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        if '-' in element.Name:
            element.OverallHeight = int(element.Name.split('-')[0].split('x')[-1])
        else:
            element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W1960' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        if '-' in element.Name:
            element.OverallHeight = int(element.Name.split('-')[0].split('x')[-1])
        else:
            element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W2060' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        if '-' in element.Name:
            element.OverallHeight = int(element.Name.split('-')[0].split('x')[-1])
        else:
            element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W2150' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W2400' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        if '-' in element.Name:
            element.OverallHeight = int(element.Name.split('-')[0].split('x')[-1])
        else:
            element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W2515' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        if '-' in element.Name:
            element.OverallHeight = int(element.Name.split('-')[0].split('x')[-1])
        else:
            element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W2700' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W2830' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W3330' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])
    elif 'W4210' in property:
        element.OverallWidth = int(element.Name.split('x')[0][1:])
        element.OverallHeight = int(element.Name.split('x')[-1])

    elif "D2'6" in property:
        element.OverallWidth = 30
        element.OverallHeight = 84
    elif "D3'" in property:
        element.OverallWidth = 36
        element.OverallHeight = 84
    elif "D4'10" in property:
        element.OverallWidth = 58
        ELEMENT.oVerallHeight = 84
    elif "FW4'" in property:
        element.OverallWidth = 48
        element.OverallHeight = 78
    elif "FW6'" in property:
        element.OverallWidth = 72
        element.OverallHeight = 78
    elif "KW3'" in property:
        element.OverallWidth = 36
        element.OverallHeight = 42
    elif "W4'" in property:
        element.OverallWidth = 48
        element.OverallHeight = 60

def geometry_iterator(f, tree, element):
    if element.is_a('IfcOpeningElement'):
        selections = tree.select_box(element)     
        selected_elements = [s for s in selections if s.is_a('IfcWall')]
        if len(selected_elements) == 1: 
            selected_element = selected_elements[0]
        else:
            selected_element = None
    if element.is_a() in ['IfcWindow', 'IfcDoor']:
        unit_factor = ifcopenshell.util.unit.calculate_unit_scale(f)
        element_location = tuple(map(float, ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)[:3,3] * unit_factor))
        selected_elements = [_ for _ in tree.select(element_location, extend=0.001) if _.is_a('IfcWall')] 
        if len(selected_elements) == 1:
            selected_element = selected_elements[0]
        else:
            selected_element = None
        
        if not selected_element:
            selected_elements = [_ for _ in tree.select_box(element) if _.is_a('IfcWall')]
            if len(selected_elements) == 1:
                selected_element = selected_elements[0]
            else:
                selected_element = None
    elif element.is_a('IfcSlab'):
        selections = tree.select_box(element, completely_within=True)
        selected_element = [s for s in selections if s.is_a('IfcSlab') and s.PredefinedType!='USERDEFINED'][0]
    return selected_element

def create_geometry_tree(f): #TO CHECK ON ALL THESE CODES
    settings = ifcopenshell.geom.settings()
    iterator = ifcopenshell.geom.iterator(settings, f, multiprocessing.cpu_count())
    tree = ifcopenshell.geom.tree()
    if iterator.initialize():
        while True:
            tree.add_element(iterator.get_native())
            if not iterator.next():
                break
    return tree

def create_opening_element(f, element):
    if element.is_a() in ['IfcWindow', 'IfcDoor']:
        unit_factor = ifcopenshell.util.unit.calculate_unit_scale(f)
        opening = ifcopenshell.api.run('root.create_entity',f, ifc_class='IfcOpeningElement', predefined_type='OPENING')
        element_plc = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
        matrix = mathutils.Matrix(element_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=opening, matrix=matrix, is_si=False)
        body_context = ifcopenshell.util.representation.get_context(f, context='Model', subcontext='Body')
        length = element.OverallWidth*unit_factor
        height = element.OverallHeight*unit_factor
        opening_representation = ifcopenshell.api.run('geometry.add_wall_representation', f, context=body_context, length=length, height=height, offset=-0.1, thickness=0.4) #opening is first offset from the wall and added a thickness of 400mm
        ifcopenshell.api.run('geometry.assign_representation', f, product=opening, representation=opening_representation)
    elif element.is_a('IfcSlab'):
        ifcopenshell.api.run('spatial.unassign_container', f, product=element)
        opening = ifcopenshell.api.run('root.reassign_class', f, product=element, ifc_class='IfcOpeningElement', predefined_type='OPENING')
    return opening

def create_wall(f, library, ifc_library_file, body, storey, json_file, height, predefined_type):
    wall_coords = element_plc(json_file, selection_type='bbox')
    for coord in wall_coords:
        wall_xdirection = coord[1][0]
        wall_ydirection = coord[1][1]
        x = coord[0][0] 
        y = coord[0][1]

        wall_thickness = min(wall_xdirection, wall_ydirection)
        wall_length = max(wall_xdirection, wall_ydirection)

        if 'DWARF' in json_file:
            profile_name = f"DWF_{wall_thickness}"
        else:
            profile_name = f"{wall_thickness}"

        lib_wall_type = check_beam_column_footing_wall_type('IfcWallType', profile_name, library, ifc_library_file, predefined_type)
        wall_type = ifcopenshell.api.run("project.append_asset", f, library=library, element=lib_wall_type)
        wall = create_element(f, wall_type, 'IfcWall', predefined_type=wall_type.PredefinedType)
        ifcopenshell.api.run("spatial.assign_container", f, product=wall, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=wall)

        wall_height = height*ifcopenshell.util.unit.calculate_unit_scale(f)
        representation = ifcopenshell.api.run('geometry.add_wall_representation', f, context=body, length=wall_length*ifcopenshell.util.unit.calculate_unit_scale(f), height=wall_height, thickness=wall_thickness*ifcopenshell.util.unit.calculate_unit_scale(f)
        #representation = ifcopenshell.api.run('geometry.add_wall_representation', f, context=body, length=wall_ydirection*ifcopenshell.util.unit.calculate_unit_scale(f), height=wall_height, thickness=wall_xdirection*ifcopenshell.util.unit.calculate_unit_scale(f)
) #WHILE CHANGING THE WALL TYPE THICKNESS DOESNT CHANGE IN THE CORRECT DIRECTION WHEN THE WALL IS X-AXIS ALIGNED
        ifcopenshell.api.run('geometry.assign_representation', f, product=wall, representation=representation)

        wall_plc = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)

        psi = np.pi/2
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        rot_negZ = mathutils.Matrix([[np.cos(psi), np.sin(psi), 0],
                                [-np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])

        if wall_xdirection > wall_ydirection:
            wall_plc[:,3][0] = x
            wall_plc[:,3][1] = y - wall_ydirection/2
        else:
            wall_plc[:,3][0] = x + wall_xdirection/2
            wall_plc[:,3][1] = y 
            rot_mat = rotZ
            wall_plc[:3,:3] = rot_mat 

        matrix = mathutils.Matrix(wall_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=wall, matrix=matrix, is_si=False)

def create_opening_wall(f, body, height, json_file):
    opening_coords = element_plc(json_file, selection_type='bbox')
    for coord in opening_coords:
        opening_thickness = coord[1][0] #x-direction
        opening_length = coord[1][1] #y-direction
        opening_sill_lvl= int(json_file.split('.')[0].split('_')[-2])
        opening_lintel_lvl = int(json_file.split('.')[0].split('_')[-1])
        opening_height = opening_lintel_lvl - opening_sill_lvl
        x = coord[0][0] 
        y = coord[0][1]
        z = height+opening_sill_lvl

        opening = ifcopenshell.api.run('root.create_entity',f, ifc_class='IfcOpeningElement', predefined_type='OPENING')
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=opening)
        opening_plc = ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement)
        
        unit_scale = ifcopenshell.util.unit.calculate_unit_scale(f) 

        opening_representation = ifcopenshell.api.run('geometry.add_wall_representation', f, context=body, length=opening_length*unit_scale, height=opening_height*unit_scale, thickness=opening_thickness*unit_scale)
        ifcopenshell.api.run('geometry.assign_representation', f, product=opening, representation=opening_representation)

        psi = np.pi/2
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        rot_negZ = mathutils.Matrix([[np.cos(psi), np.sin(psi), 0],
                                [-np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])

        opening_plc[:,3][2] = z
        if opening_thickness > opening_length:
            opening_plc[:,3][0] = x
            opening_plc[:,3][1] = y + opening_length/2
            rot_mat = rot_negZ
        else:
            opening_plc[:,3][0] = x + opening_thickness/2
            opening_plc[:,3][1] = y 
            rot_mat = rotZ

        opening_plc[:3,:3] = rot_mat
        rotation_m4 = np.matrix(opening_plc)
        matrix = mathutils.Matrix(opening_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=opening, matrix=matrix, is_si=False)

def create_angled_entity(f, library, body, storey, json_file, entity, height, thickness, predefined_type):
    entity_class = entity
    if entity_class == 'IfcWall':
        lib_type = [t for t in library.by_type('IfcWallType') if t.PredefinedType == predefined_type][0]
    entity_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_type)

    entity_coords = element_plc(json_file, selection_type='line')
    height = height*ifcopenshell.util.unit.calculate_unit_scale(f)
    thickness = thickness*ifcopenshell.util.unit.calculate_unit_scale(f)
    for coord in entity_coords:
        p1 = coord[0]
        p2 = coord[1]

        ele = create_element(f, entity_type, entity_class, predefined_type)
        ifcopenshell.api.run('spatial.assign_container', f, product=ele, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=ele)

        representation = ifcopenshell.api.run('geometry.create_2pt_wall', f, element=ele, context=body, p1=p1, p2=p2, elevation=0, height=height, thickness=thickness)
        ifcopenshell.api.run('geometry.assign_representation', f, product=ele, representation=representation)

def check_beam_column_footing_wall_type(element_type, profile_name, library, ifc_library_file, predefined_type, object_type=None):
    if element_type == 'IfcBeamType':
        new_ele_type_name = f"B_{profile_name}"
    elif element_type == 'IfcColumnType':
        new_ele_type_name = f"COL_{profile_name}"
    #elif element_type == 'IfcBuildingElementProxyType':
        #new_ele_type_name = f"PCC{profile_name}"
    elif element_type == 'IfcFootingType':
        new_ele_type_name = f"FT_{profile_name}"
    elif element_type == 'IfcWallType':
        new_ele_type_name = f"WAL_{profile_name}"
    for e_type in library.by_type(element_type):
        if e_type.Name == new_ele_type_name:
            return e_type
    return create_new_beam_column_footing_wall_type(new_ele_type_name, element_type, library, ifc_library_file, predefined_type, object_type=None)

def create_new_beam_column_footing_wall_type(new_ele_type_name, element_type, library, ifc_library_file, predefined_type, object_type=None):
    #rcc = [_ for _ in library.by_type('IfcMaterial') if _.Name=='RCC'][0] #THIS NEEDS TO BE CHANGED TO concrete
    con = [m for m in library.by_type('IfcMaterial') if m.Category=='concrete' and m.Name=='CON'][0]
    pcc = [m for m in library.by_type('IfcMaterial') if m.Category=='concrete' and m.Name=='PCC'][0]
    blk = [m for m in library.by_type('IfcMaterial') if m.Category=='block'][0]
    brick = [m for m in library.by_type('IfcMaterial') if m.Category=='brick'][0]
    #SHOULD ADD MATERIAL NAME IN JSON FILE??? LIKE BLOCK OR BRICK OR M25 OR PCC
    if element_type=='IfcWallType':
        wall_thickness = new_ele_type_name.split('_')[-1]
        material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialLayerSet')
        if 'BRICK' in new_ele_type_name:
            new_ele_layer = ifcopenshell.api.run('material.add_layer', library, layer_set=material_set, material=brick)
        else:
            new_ele_layer = ifcopenshell.api.run('material.add_layer', library, layer_set=material_set, material=blk)
        #ifcopenshell.api.run('material.edit_layer', library, layer=new_ele_layer, attributes={"LayerThickness":float(wall_thickness)})
        material_set.MaterialLayers[0].LayerThickness = float(wall_thickness)
    elif element_type=='IfcBeamType':
        profile = list(map(int, new_ele_type_name.split('_')[-1].split('x')))
        x = profile[0]    
        y = profile[1]
        new_ele_profile = ifcopenshell.api.run('profile.add_parameterized_profile', library, ifc_class='IfcRectangleProfileDef')
        new_ele_profile.XDim = x
        new_ele_profile.YDim = y
        new_ele_profile.ProfileType = 'AREA'
        new_ele_profile.ProfileName = f"{x}x{y} Rectangle Profile"
        material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
        ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=new_ele_profile)
    elif element_type=='IfcColumnType':
        if 'LSHAPE' in new_ele_type_name:
            profile = list(map(int, new_ele_type_name.split('_')[-1].split('x')))
            width = profile[0]    
            depth = profile[1]
            thickness = profile[2]
            new_ele_profile = ifcopenshell.api.run('profile.add_parameterized_profile', library, ifc_class='IfcLShapeProfileDef')
            new_ele_profile.Width = width
            new_ele_profile.Depth = depth 
            new_ele_profile.Thickness = thickness
            new_ele_profile.ProfileType = 'AREA'
            new_ele_profile.ProfileName = f"{width}x{depth}x{thickness} L Shape Profile"
            material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
            ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=new_ele_profile)
        elif 'RECTANGLE' in new_ele_type_name: #add pcc course incase of ifcfooting
            profile = list(map(int, new_ele_type_name.split('_')[-1].split('x')))
            x = profile[0]    
            y = profile[1]
            for rec_profile in library.by_type('IfcRectangleProfileDef'):
                if rec_profile.ProfileName == f"{x}x{y} Rectangle Profile":
                    material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
                    ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=rec_profile)
                else:
                    new_ele_profile = ifcopenshell.api.run('profile.add_parameterized_profile', library, ifc_class='IfcRectangleProfileDef')
                    new_ele_profile.XDim = x
                    new_ele_profile.YDim = y
                    new_ele_profile.ProfileType = 'AREA'
                    new_ele_profile.ProfileName = f"{x}x{y} Rectangle Profile"
                    material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
                    ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=new_ele_profile)
        elif 'CIRCLE' in new_ele_type_name: #add pcc course incase of ifcfooting
            #profile = list(map(int, new_ele_type_name.split('_')[-1].split('x')))
            profile = int(new_ele_type_name.split('_')[-1])
            #y = profile[1]
            #for circle_profile in library.by_type('IfcCircleProfileDef'):
            #    if circle_profile.ProfileName == f"{profile} Circle Profile":
            #        material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
            #        ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=circle_profile)
            #    else:
            #        new_ele_profile = ifcopenshell.api.run('profile.add_parameterized_profile', library, ifc_class='IfcCircleProfileDef')
            #        new_ele_profile.Radius = profile/2
            #        new_ele_profile.ProfileType = 'AREA'
            #        new_ele_profile.ProfileName = f"{profile} Circle Profile"
            #        material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
            #        ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=new_ele_profile)
            new_ele_profile = ifcopenshell.api.run('profile.add_parameterized_profile', library, ifc_class='IfcCircleProfileDef')
            new_ele_profile.Radius = profile/2
            new_ele_profile.ProfileType = 'AREA'
            new_ele_profile.ProfileName = f"{profile} Circle Profile"
            material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
            ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=new_ele_profile)
    elif element_type=='IfcFootingType':
        profile = list(map(int, new_ele_type_name.split('_')[-1].split('x')))        
        x = profile[0]
        y = profile[1]
        new_ele_profile = ifcopenshell.api.run('profile.add_parameterized_profile', library, ifc_class='IfcRectangleProfileDef')
        new_ele_profile.XDim = x
        new_ele_profile.YDim = y
        new_ele_profile.ProfileType = 'AREA'
        new_ele_profile.ProfileName = f"{x}x{y} Rectangle Profile"
        material_set = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
        ifcopenshell.api.run('material.add_profile', library, profile_set=material_set, material=con, profile=new_ele_profile)
        material_set_pcc = ifcopenshell.api.run('material.add_material_set', library, name=new_ele_type_name, set_type='IfcMaterialProfileSet')
        ifcopenshell.api.run('material.add_profile', library, profile_set=material_set_pcc, material=pcc, profile=new_ele_profile)

    # context = library.by_type('IfcProjectLibrary')[0]
    # ifcopenshell.api.run('project.assign_declaration', library, definition=new_ele_profile, relating_context=context)
    #PROJECT LIBRARY CONTEXT TO BE ASSIGNED DECLARATION - THIS IS PENDING

    e_type = ifcopenshell.api.run('root.create_entity', library, ifc_class=element_type, predefined_type=predefined_type, name=new_ele_type_name)
    ifcopenshell.api.run('material.assign_material', library, product=e_type, material=material_set)
    #if material_set_pcc:
    #    e_type_name = re.sub(r'x\d+$','x40', new_ele_type_name).replace('FT', 'PCC')
    #    e_type_pcc = ifcopenshell.api.run('root.create_entity', library, ifc_class='IfcBuildingElementProxyType', predefined_type='PCC', name=e_type_name)
    #    ifcopenshell.api.run('material.assign_material', library, product=e_type_pcc, material=material_set_pcc)
    # TO BE CORRECTED
    library.write(ifc_library_file)
    return e_type
    
def create_pline_column(f, body, storey, csv_file, height, predefined_type):
    column_list = get_polyline_list(csv_file)
    for column_xy in column_list:
        column = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcColumn', predefined_type=predefined_type)

        if predefined_type == 'USERDEFINED':
            column.ObjectType = object_type

        ifcopenshell.api.run('spatial.assign_container', f, product=column, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=column)
        points = polyline_coords(column_xy)

        column_height = height*ifcopenshell.util.unit.calculate_unit_scale(f) #check the depth calculation for metric projects too
        representation = ifcopenshell.api.run('geometry.add_slab_representation', f, context=body, points=points, depth=column_height)
        ifcopenshell.api.run('geometry.assign_representation', f, product=column, representation=representation)
        #element_z_translation(f, column, -depth)

def create_column(f, library, ifc_library_file, body, storey, json_file, height, predefined_type):
    column_coords = element_plc(json_file, selection_type='block')
    for coord in column_coords:
        #column_thickness = coord[1][0] #x-direction
        #column_length = coord[1][1] #y-direction
        x = coord[0]
        y = coord[1]
        rotation = coord[2]
        scaleX = coord[3]
        scaleY = coord[4]
        
        block_name = coord[-2]
        profile_size = list(map(int, block_name.split('_')[-1].split('x')))
        if 'LSHAPE' in block_name:
            profile_name = f"LSHAPE_{profile_size[0]}x{profile_size[1]}x{profile_size[2]}"
        elif 'RECTANGLE' in block_name:
            profile_name = f"RECTANGLE_{profile_size[0]}x{profile_size[1]}"
        elif 'CIRCLE' in block_name:
            profile_name = f"CIRCLE_{profile_size[0]}"

        lib_col_type = check_beam_column_footing_wall_type('IfcColumnType', profile_name, library, ifc_library_file, predefined_type) 
        col_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_col_type) 
        column = create_element(f, col_type, 'IfcColumn', predefined_type=col_type.PredefinedType)
        ifcopenshell.api.run("spatial.assign_container", f, product=column, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=column)

        column_height = height*ifcopenshell.util.unit.calculate_unit_scale(f) 

        profile=col_type.HasAssociations[0].RelatingMaterial.MaterialProfiles[0].Profile
        representation = ifcopenshell.api.run('geometry.add_profile_representation', f, context=body, profile=profile, depth=column_height)

        ifcopenshell.api.run('geometry.assign_representation', f, product=column, representation=representation)

        column_plc = ifcopenshell.util.placement.get_local_placement(column.ObjectPlacement)

        psi = rotation
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        column_plc[:,3][0] = x
        column_plc[:,3][1] = y
        column_plc[:3,:3] = rotZ
        matrix = mathutils.Matrix(column_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=column, matrix=matrix, is_si=False)

def create_beam(f, library, ifc_library_file, body, storey, json_file, depth, predefined_type, object_type=None):
    beam_coords = element_plc(json_file, selection_type='bbox')
    for coord in beam_coords:
        beam_xdirection = coord[1][0] #x-direction
        beam_ydirection = coord[1][1] #y-direction
        x = coord[0][0] 
        y = coord[0][1]

        beam_width = min(beam_xdirection, beam_ydirection)
        beam_depth = depth
        profile_size = (beam_width, beam_depth)
        profile_name = f"{profile_size[0]}x{profile_size[1]}"
        lib_beam_type = check_beam_column_footing_wall_type('IfcBeamType', profile_name, library, ifc_library_file, predefined_type, object_type=object_type) #TO ADD CHECK_BEAM_TYPE
        beam_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_beam_type) 
        beam = create_element(f, beam_type, 'IfcBeam', predefined_type=beam_type.PredefinedType)
        ifcopenshell.api.run("spatial.assign_container", f, product=beam, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=beam)

        length_of_beam = max(beam_xdirection, beam_ydirection) * ifcopenshell.util.unit.calculate_unit_scale(f)

        profile=beam_type.HasAssociations[0].RelatingMaterial.MaterialProfiles[0].Profile
        representation = ifcopenshell.api.run('geometry.add_profile_representation', f, context=body, profile=profile, depth=length_of_beam)
        ifcopenshell.api.run('geometry.assign_representation', f, product=beam, representation=representation)

        beam_plc = ifcopenshell.util.placement.get_local_placement(beam.ObjectPlacement)

        psi = np.pi/2
        rot_X = mathutils.Matrix([[1, 0, 0],
                                [0, np.cos(psi), -np.sin(psi)],
                                [0, np.sin(psi), np.cos(psi)]])
        rot_Z = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        rot_2Z = mathutils.Matrix([[np.cos(2*psi), -np.sin(2*psi), 0],
                                [np.sin(2*psi), np.cos(2*psi), 0],
                                [0,0,1]])

        beam_plc[:,3][0] = x
        beam_plc[:,3][1] = y 
        # beam_plc[:,3][2] = -beam_depth/2

        if beam_xdirection > beam_ydirection:
            rot_mat = rot_Z @ rot_X
            beam_plc[:3,:3] = rot_mat
        else:
            rot_mat = rot_2Z @ rot_X
            beam_plc[:3,:3] = rot_mat

        matrix = mathutils.Matrix(beam_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=beam, matrix=matrix, is_si=False)

def create_footing_pad(f, library, ifc_library_file, body, storey, json_file, z_level, predefined_type):
    footing_coords = element_plc(json_file, selection_type='block')
    for coord in footing_coords:
        #footing_xlength = coord[1][0] #x-direction
        #footing_ylength = coord[1][1] #y-direction
        x = coord[0]
        y = coord[1]
        rotation = coord[2]
        scaleX = coord[3]
        scaleY = coord[4]

        block_name = coord[-2]
        profile_size = list(map(int, block_name.split('_')[-1].split('x')))
        #profile_size = (min(int(footing_xlength), int(footing_ylength)), max(int(footing_xlength),int(footing_ylength)))
        footing_profile_name = f"{profile_size[0]}x{profile_size[1]}x{profile_size[2]}"
        #pcc_profile_name = f"FT_{footing_profile_name}"

        #lib_pcc_course_type = check_beam_column_footing_type('IfcBuildingElementProxyType', pcc_profile_name, library, ifc_library_file) 
        #pcc_course_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_footing_type) 
        #pcc_course = create_element(f, footing_type, 'IfcFooting', predefined_type)

        lib_footing_type = check_beam_column_footing_wall_type('IfcFootingType', footing_profile_name, library, ifc_library_file, predefined_type) 
        footing_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_footing_type) 
        footing = create_element(f, footing_type, 'IfcFooting', predefined_type=footing_type.PredefinedType)
        ifcopenshell.api.run("spatial.assign_container", f, product=footing, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=footing)
        ft_depth = profile_size[2]
        footing_depth = ft_depth*ifcopenshell.util.unit.calculate_unit_scale(f)
        footing_profile=footing_type.HasAssociations[0].RelatingMaterial.MaterialProfiles[0].Profile
        footing_representation = ifcopenshell.api.run('geometry.add_profile_representation', f, context=body, profile=footing_profile, depth=footing_depth)
        ifcopenshell.api.run('geometry.assign_representation', f, product=footing, representation=footing_representation)
        footing_plc = ifcopenshell.util.placement.get_local_placement(footing.ObjectPlacement)

        lib_pcc_type = [_ for _ in library.by_type('IfcBuildingElementProxyType') if f"{profile_size[0]}x{profile_size[1]}" in _.Name][0]
        pcc_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_pcc_type) 
        pcc_course = create_element(f, pcc_type, 'IfcBuildingElementProxy', predefined_type=pcc_type.ElementType)
        ifcopenshell.api.run("spatial.assign_container", f, product=pcc_course, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=pcc_course)
        pcc_depth = int(pcc_type.Name.split('x')[-1])
        pcc_course_depth = pcc_depth*ifcopenshell.util.unit.calculate_unit_scale(f)
        pcc_profile=pcc_type.HasAssociations[0].RelatingMaterial.MaterialProfiles[0].Profile
        pcc_representation = ifcopenshell.api.run('geometry.add_profile_representation', f, context=body, profile=pcc_profile, depth=pcc_course_depth)
        ifcopenshell.api.run('geometry.assign_representation', f, product=pcc_course, representation=pcc_representation)
        pcc_plc = ifcopenshell.util.placement.get_local_placement(pcc_course.ObjectPlacement)

        psi = np.pi/2
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        rot_negZ = mathutils.Matrix([[np.cos(psi), np.sin(psi), 0],
                                [-np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])

        #if footing_xlength == footing_ylength:
        if profile_size[0] == profile_size[1]:
            footing_plc[:,3][0] = x 
            footing_plc[:,3][1] = y
            pcc_plc[:,3][0] = x 
            pcc_plc[:,3][1] = y
        #elif footing_xlength > footing_ylength:
        elif profile_size[0] > profile_size[1]:
            #footing_plc[:,3][0] = x + footing_xlength/2
            rot_mat = rot_negZ
            footing_plc[:,3][0] = x + profile_size[0]/2
            footing_plc[:,3][1] = y 
            footing_plc[:3,:3] = rot_mat
            pcc_plc[:,3][0] = x + profile_size[0]/2
            pcc_plc[:,3][1] = y 
            pcc_plc[:3,:3] = rot_mat
        else:
            footing_plc[:,3][0] = x 
            #footing_plc[:,3][1] = y + footing_ylength/2
            footing_plc[:,3][1] = y + profile_size[1]/2
            pcc_plc[:,3][0] = x 
            pcc_plc[:,3][1] = y + profile_size[1]/2

        footing_plc[:,3][2] = z_level + pcc_depth
        pcc_plc[:,3][2] = z_level
        footing_rotation_m4 = np.matrix(footing_plc)
        footing_matrix = mathutils.Matrix(footing_plc)
        pcc_rotation_m4 = np.matrix(pcc_plc)
        pcc_matrix = mathutils.Matrix(pcc_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=footing, matrix=footing_matrix, is_si=False)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=pcc_course, matrix=pcc_matrix, is_si=False)

def create_plate_entity(f, library, body, storey, json_file, height, predefined_type):
    lib_plate_type = [_ for _ in library.by_type('IfcPlateType') if _.PredefinedType == 'CURTAIN_PANEL'][0]
    plate_type = ifcopenshell.api.run("project.append_asset", f, library=library, element=lib_plate_type)

    plate_coords = element_plc(json_file, selection_type='bbox')
    for coord in plate_coords:
        plate_thickness = coord[1][0] #x-direction
        plate_length = coord[1][1] #y-direction
        x = coord[0][0] 
        y = coord[0][1]

        plate = create_element(f, plate_type, 'IfcPlate', predefined_type)
        ifcopenshell.api.run("spatial.assign_container", f, product=plate, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=plate)

        plate_height = height*ifcopenshell.util.unit.calculate_unit_scale(f) #check the depth calculation for metric projects too
        representation = ifcopenshell.api.run('geometry.add_wall_representation', f, context=body, length=plate_length*ifcopenshell.util.unit.calculate_unit_scale(f), height=plate_height, thickness=plate_thickness*ifcopenshell.util.unit.calculate_unit_scale(f))
        ifcopenshell.api.run('geometry.assign_representation', f, product=plate, representation=representation)

        plate_plc = ifcopenshell.util.placement.get_local_placement(plate.ObjectPlacement)

        psi = np.pi/2
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        rot_negZ = mathutils.Matrix([[np.cos(psi), np.sin(psi), 0],
                                [-np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])

        if plate_thickness > plate_length:
            plate_plc[:,3][0] = x
            plate_plc[:,3][1] = y + plate_length/2
            rot_mat = rot_negZ
        else:
            plate_plc[:,3][0] = x + plate_thickness/2
            plate_plc[:,3][1] = y 
            rot_mat = rotZ

        plate_plc[:3,:3] = rot_mat
        rotation_m4 = np.matrix(plate_plc)
        matrix = mathutils.Matrix(plate_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=plate, matrix=matrix, is_si=False)

def create_accessory():
    element_coords = element_plc(json_file, selection_type='block')

    for coord in element_coords:
        element_type_name = 'IfcDiscreteAccessoryType'
        ifc_class = 'IfcDiscreteAccessory'
        #if coord[-1] == 'WINDOW':
        #    element_type_name = 'IfcDiscreteAccessoryType'
        #    ifc_class = 'IfcWindow'
        #elif coord[-1] == 'DOOR':
        #    element_type_name = 'IfcDoorType'
        #    ifc_class = 'IfcDoor'

        x = coord[0]
        y = coord[1]
        rotation = coord[2]
        scaleX = coord[3]
        scaleY = coord[4]
        
        ele_type = [_ for _ in f.by_type(element_type_name) if _.Name == coord[-2]][0]
        accessory = create_element(f, ele_type, ifc_class, predefined_type)

        #ifcopenshell.api.run('spatial.assign_container', f, product=door_or_window, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=accessory)

        accessory_plc = ifcopenshell.util.placement.get_local_placement(accessory.ObjectPlacement)

        psi = rotation
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        accessory_plc[:,3][0] = x
        accessory_plc[:,3][1] = y
        accessory_plc[:3,:3] = rotZ
        matrix = mathutils.Matrix(accessory_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=accessory, matrix=matrix, is_si=False)

