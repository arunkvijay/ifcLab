# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import numpy as np
import csv
import mathutils
import ifcopenshell
#from enum import Enum


def create_storeys(num_storeys):
    for i in range(num_storeys): #for creating storeys programmically along with enum
        storey = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcBuildingStorey', name=storeys_dict.get(i).title().replace('_',' '))
        ifcopenshell.api.run('aggregate.assign_object', f, relating_object = building, product=storey)

def polyline_coords(csv_row):
    return [(float(csv_row[i]), float(csv_row[i+1])) for i in range(0,len(csv_row)-1,2)]
     
def slab_coords(csv_file):
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        rows = list(csv_reader)
    return tuple(polyline_coords(rows[0]))

def create_element(element_type, ifc_class): #add predefined type
    element = ifcopenshell.api.run('root.create_entity', f, ifc_class=ifc_class)
    ifcopenshell.api.run('type.assign_type', f, related_object=element, relating_type=element_type)
    return element

def create_base_slab(library, storey, csv_file, depth=300):
    lib_base_slab_type = [_ for _ in library.by_type('IfcSlabType') if _.PredefinedType == 'BASESLAB'][0]
    base_slab_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_base_slab_type)

    base_slab = create_element(base_slab_type, 'IfcSlab')

    ifcopenshell.api.run('spatial.assign_container', f, product=base_slab, relating_structure=storey)
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=base_slab)
    points = slab_coords(csv_file)

    representation = ifcopenshell.api.run('geometry.add_slab_representation', f, context=body, points=points, depth=depth/1000)
    ifcopenshell.api.run('geometry.assign_representation', f, product=base_slab, representation=representation)

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

def create_baseplate(bp_type, relating_object):
    bp = create_element(bp_type, 'IfcDiscreteAccessory')
    ifcopenshell.api.run('aggregate.assign_object', f, product=bp, relating_object=relating_object)
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=bp)

def create_hub(hub_type, relating_object):
    hub = create_element(hub_type, 'IfcDiscreteAccessory')
    ifcopenshell.api.run('aggregate.assign_object', f, product=hub, relating_object=relating_object)
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=hub)
    return hub

def create_craddle():
    lib_craddle_type = [_ for _ in library.by_type('IfcDiscreteAccessoryType') if _.Name == 'Craddle'][0]
    craddle_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_craddle_type)
    craddle = create_element(craddle_type, 'IfcDiscreteAccessory')
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=craddle)
    return craddle

def create_sleeve():
    lib_sleeve_type = [_ for _ in library.by_type('IfcDiscreteAccessoryType') if _.Name == 'Sleeve'][0]
    sleeve_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_sleeve_type)
    sleeve = create_element(sleeve_type, 'IfcDiscreteAccessory')
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=sleeve)
    return sleeve

def create_assembly(json_file, library, storey, z_offset):
    assembly_type = ifcopenshell.api.run('root.create_entity', f, ifc_class="IfcElementAssemblyType")
    assembly_coords = element_plc(json_file)
    
    lib_bp_type = [_ for _ in library.by_type('IfcDiscreteAccessoryType') if _.Name == 'Base Plate'][0]
    bp_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_bp_type)

    lib_hub_type = [_ for _ in library.by_type('IfcDiscreteAccessoryType') if _.Name == 'Hub'][0]
    hub_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_hub_type)

    # lib_craddle_type = [_ for _ in library.by_type('IfcDiscreteAccessoryType') if _.Name == 'Craddle'][0]
    # craddle_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_craddle_type)

    for coord in assembly_coords:
        x = coord[0][0]
        y = coord[0][1]

        assembly = create_element(assembly_type, 'IfcElementAssembly')
        ifcopenshell.api.run('spatial.assign_container', f, product=assembly, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=assembly)

        base_plate = create_baseplate(bp_type, assembly)
        hub = create_hub(hub_type, assembly)
        # create_craddle(craddle_type, assembly)

        hub_plc = ifcopenshell.util.placement.get_local_placement(hub.ObjectPlacement)
        hub_plc[:,3][2] = 5
        hub_matrix = mathutils.Matrix(hub_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=hub, matrix=hub_matrix, is_si=False)

        assembly_plc = ifcopenshell.util.placement.get_local_placement(assembly.ObjectPlacement)
        assembly_plc[:,3][0] = x
        assembly_plc[:,3][1] = y
        assembly_plc[:,3][2] = z_offset 
        assembly_mat = mathutils.Matrix(assembly_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=assembly, matrix=assembly_mat, is_si=False, should_transform_children=True)


def create_column_assemblies(json_file, library, storey, z_offset=465, storey_floor_to_floor_ht=3000):
    depth = storey_floor_to_floor_ht-165-160
    assembly_type = ifcopenshell.api.run('root.create_entity', f, ifc_class="IfcElementAssemblyType")
    lib_column_type = [_ for _ in library.by_type('IfcColumnType') if _.Name == '80x80'][0]
    column_type = ifcopenshell.api.run('project.append_asset', f, library=library, element=lib_column_type)
    col_profile = [_ for _ in f.by_type('IfcRectangleHollowProfileDef') if _.ProfileName == '80x80'][0]
    col_representation_body = ifcopenshell.api.run("geometry.add_profile_representation", f, context=body, profile=col_profile, depth=depth/1000)

    assembly_coords = element_plc(json_file)

    for coord in assembly_coords:
        x = coord[0][0]
        y = coord[0][1]

        assembly = create_element(assembly_type, "IfcElementAssembly")
        ifcopenshell.api.run('spatial.assign_container', f, product=assembly, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=assembly)

        col = create_element(column_type, 'IfcColumn')
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=col)
        ifcopenshell.api.run('geometry.assign_representation', f, product=col, representation=col_representation_body)

        ifcopenshell.api.run('aggregate.assign_object', f, product=col, relating_object=assembly)

        craddle_base = create_craddle()
        craddle_top = create_craddle()
        ifcopenshell.api.run('aggregate.assign_object', f, product=craddle_base, relating_object=assembly)
        ifcopenshell.api.run('aggregate.assign_object', f, product=craddle_top, relating_object=assembly)
        craddle_top_plc = ifcopenshell.util.placement.get_local_placement(craddle_top.ObjectPlacement)
        col_height = col_representation_body.Items[0].Depth 
        craddle_top_plc[:,3][2] = col_height
        craddle_top_mat = mathutils.Matrix(craddle_top_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=craddle_top, matrix=craddle_top_mat, is_si=False)

        sleeve_base = create_sleeve()
        sleeve_top = create_sleeve()
        ifcopenshell.api.run('aggregate.assign_object', f, product=sleeve_base, relating_object=assembly)
        ifcopenshell.api.run('aggregate.assign_object', f, product=sleeve_top, relating_object=assembly)
        sleeve_top_plc = ifcopenshell.util.placement.get_local_placement(sleeve_top.ObjectPlacement)
        col_height = col_representation_body.Items[0].Depth 
        sleeve_top_plc[:,3][2] = col_height
        sleeve_top_mat = mathutils.Matrix(sleeve_top_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=sleeve_top, matrix=sleeve_top_mat, is_si=False)

        assembly_plc = ifcopenshell.util.placement.get_local_placement(assembly.ObjectPlacement)
        assembly_plc[:,3][0] = x
        assembly_plc[:,3][1] = y
        assembly_plc[:,3][2] = z_offset
        assembly_mat = mathutils.Matrix(assembly_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=assembly, matrix=assembly_mat, is_si=False, should_transform_children=True)
        
def create_beam_assemblies(json_file, storey, z_offset=300):
    assembly_type = ifcopenshell.api.run('root.create_entity', f, ifc_class="IfcElementAssemblyType")
    lib_beam_type = [_ for _ in library.by_type("IfcBeamType") if _.Name == "80x160"][0]
    beam_type = ifcopenshell.api.run("project.append_asset", f, library=library, element=lib_beam_type)
    beam_profile = [_ for _ in f.by_type('IfcRectangleHollowProfileDef') if _.ProfileName == '80x160'][0]
    beam_representation_body = ifcopenshell.api.run("geometry.add_profile_representation", f, context=body, profile=beam_profile, depth=0.1)

    assembly_coords = element_plc(json_file)
    for coord in assembly_coords:
        width = coord[1][0]
        height = coord[1][1]
        x = coord[0][0] - beam_profile.XDim/2 
        y = coord[0][1]
        if storey.Name == "Ground Floor":
            z = z_offset + beam_profile.YDim/2 + 5 #for baseplate thickness
        else:
            z = z_offset + beam_profile.YDim + 60 #for roof 

        assembly = create_element(assembly_type, "IfcElementAssembly")
        ifcopenshell.api.run('spatial.assign_container', f, product=assembly, relating_structure=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=assembly)
        assembly_plc = ifcopenshell.util.placement.get_local_placement(assembly.ObjectPlacement)

        beam = create_element(beam_type, 'IfcBeam')
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=beam)
        beam_plc = ifcopenshell.util.placement.get_local_placement(beam.ObjectPlacement)
        beam_plc[:,3][2] = 80
        #have taken the z-axis here. need to understand how this translation is happening due to rotation
        beam_mat = mathutils.Matrix(beam_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=beam, matrix=beam_mat, is_si=False)
        ifcopenshell.api.run('aggregate.assign_object', f, product=beam, relating_object=assembly)
        beam_representation_body.Items[0].Depth = height - (80+80)
        ifcopenshell.api.run('geometry.assign_representation', f, product=beam, representation=beam_representation_body)

        craddle_base = create_craddle()
        craddle_top = create_craddle()
        ifcopenshell.api.run('aggregate.assign_object', f, product=craddle_base, relating_object=assembly)
        ifcopenshell.api.run('aggregate.assign_object', f, product=craddle_top, relating_object=assembly)
        craddle_top_plc = ifcopenshell.util.placement.get_local_placement(craddle_top.ObjectPlacement)
        # beam_height = beam_representation_body.Items[0].Depth NOT WORKING 
        # beam_height = beam.Representation.Representations[0].Items[0].Depth NOT WORKING
        craddle_top_plc[:,3][2] = 1040 #hard-coded here. need to figure out the exact formula
        craddle_top_mat = mathutils.Matrix(craddle_top_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=craddle_top, matrix=craddle_top_mat, is_si=False)
        #translation is not happening. need to check on this

        sleeve_base = create_sleeve()
        sleeve_top = create_sleeve()
        ifcopenshell.api.run('aggregate.assign_object', f, product=sleeve_base, relating_object=assembly)
        ifcopenshell.api.run('aggregate.assign_object', f, product=sleeve_top, relating_object=assembly)
        sleeve_top_plc = ifcopenshell.util.placement.get_local_placement(sleeve_top.ObjectPlacement)
        sleeve_top_plc[:,3][2] = 1040 #hard-coded here. need to figure out the exact formula
        sleeve_top_mat = mathutils.Matrix(sleeve_top_plc)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=sleeve_top, matrix=sleeve_top_mat, is_si=False)


        translation = np.array([x, y, z])
        last_row = np.array([0.,0.,0.,1.])

        psi = np.pi/2
        rotX = mathutils.Matrix([[1, 0, 0],
                                 [0, np.cos(psi), -np.sin(psi)],
                                 [0, np.sin(psi), np.cos(psi)]])
        rot_negX = mathutils.Matrix([[1, 0, 0],
                                  [0, np.cos(psi), np.sin(psi)],
                                  [0, -np.sin(psi), np.cos(psi)]])
        #rot_X is rotation matrix around x-axis through negative psi. cosine is an even function (cos(-θ) = cos(θ)) & sine is an odd function (sin(-θ) = -sin(θ))
        rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0],
                                [np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        if width > height:
            rot_mat = rotZ @ rotX
        else:
            rot_mat = rot_negX
        rotation_m4 = np.vstack((np.hstack((np.matrix(rot_mat), translation.reshape(-1,1))), last_row))
        new_matrix = assembly_plc @ rotation_m4
        matrix = mathutils.Matrix(new_matrix.tolist())
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=assembly, matrix=matrix, is_si=False, should_transform_children=True)
        
def create_walls(json_file, storey):
    lib_wall_type = [_ for _ in library.by_type("IfcWallType") if _.Name == "Wall"][0]
    wall_type = ifcopenshell.api.run("project.append_asset", f, library=library, element=lib_wall_type)
    wall_coords = element_plc(json_file)
    for coord in wall_coords:
        width = coord[1][0]
        height = coord[1][1]
        x = coord[0][0] # - beam_profile.XDim/2 
        y = coord[0][1]
        z = 300 + 160 #for slab + bueam height#+ beam_profile.YDim/2 + 5 #for baseplate thickness

        wall = create_element(wall_type, "IfcWall")
        ifcopenshell.api.run("spatial.assign_container", f, product=wall, relating_structure=storey)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=wall)
        wall_plc = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)

        translation = np.array([x, y, z])
        last_row = np.array([0.,0.,0.,1.])

        psi = np.pi/2
        # rotX = mathutils.Matrix([[1, 0, 0],
        #                          [0, np.cos(psi), -np.sin(psi)],
        #                          [0, np.sin(psi), np.cos(psi)]])
        # rot_negX = mathutils.Matrix([[1, 0, 0],
        #                           [0, np.cos(psi), np.sin(psi)],
        #                           [0, -np.sin(psi), np.cos(psi)]])
        #rot_X is rotation matrix around x-axis through negative psi. cosine is an even function (cos(-θ) = cos(θ)) & sine is an odd function (sin(-θ) = -sin(θ))
        rot_negZ = mathutils.Matrix([[np.cos(psi), np.sin(psi), 0],
                                [-np.sin(psi), np.cos(psi), 0],
                                [0,0,1]])
        if width > height:
            rot_mat = rot_negZ #@ rotX
            rotation_m4 = np.vstack((np.hstack((np.matrix(rot_mat), translation.reshape(-1,1))), last_row))
        else:
            # rot_mat = rot_negX
            rot_mat = mathutils.Matrix(wall_plc[:3,:3])
            rotation_m4 = np.vstack((np.hstack((np.matrix(rot_mat), translation.reshape(-1,1))), last_row))
        new_matrix = wall_plc @ rotation_m4
        matrix = mathutils.Matrix(new_matrix.tolist())
        # ifcopenshell.api.run('geometry.edit_object_placement', f, product=assembly, matrix=matrix, is_si=False, should_transform_children=True)
        # wall_plc[:,3][2] = z #refer the beam_plc
        # wall_mat = mathutils.Matrix(wall_plc)
        ifcopenshell.api.run("geometry.edit_object_placement", f, product=wall, matrix=matrix, is_si=False)

# f = IfcStore.file
# path = IfcStore.path

# path = "D:\TEST.ifc"
path = "/home/TEST.ifc"

storeys_dict = {0: 'ground_floor', 1: 'first_floor', 2: 'second_floor', 3: 'third_floor', 4:'fourth_floor'}

project_name = 'My Project' # to be obtained from user
site_name = 'My Site' #to be obtained from user
building_name = 'My Building' # to be obtained from user
num_storeys = 5 #to be obtained from user

# library = ifcopenshell.open("D:\old_library.ifc")
library = ifcopenshell.open("/home/old_library.ifc")

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
ff_storey = [_ for _ in storeys if _.Name == 'First Floor'][0]

# csv_file = "D:\modified Floor Plan - 0-1 Level 0.csv"
csv_file = "/home/modified 1-0 E1 6x7 - Floor Plan - 0-1 Level 0.csv"

base_slab_depth = 300
create_base_slab(library, gf_storey, csv_file, base_slab_depth)

create_assembly(json_file_column, library, gf_storey, z_offset=base_slab_depth)
create_column_assemblies(json_file_column, library, gf_storey, z_offset=base_slab_depth+165, storey_floor_to_floor_ht=3000)

create_beam_assemblies(json_file_beam, gf_storey)
create_walls(json_file_beam, gf_storey)
create_beam_assemblies(json_file_beam, ff_storey, z_offset=3000)

f.write(path)
