# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import os
import os.path
import mathutils

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util

import super_structure

def create_wall_openings(f, body, processing_folder, processed_file_list):
    for file_name in processed_file_list:
        if 'OPENING' in file_name.split('.')[0]:
            storey_lvl_name = file_name.split('+')[0].split('_', maxsplit=1)[-1].replace('_',' ')
            storey = [s for s in f.by_type('IfcBuildingStorey') if s.Name == storey_lvl_name][0]
            storey_height = round(ifcopenshell.util.placement.get_storey_elevation(storey))
            json_file = os.path.join(processing_folder, file_name)
            super_structure.create_opening_wall(f, body, storey_height, json_file)

'''
def clash_detection_wall_plate(f,tree):
    wall_plate_elements = [e for e in f if e.is_a() in ['IfcWall', 'IfcPlate']]
    
    for ele in wall_plate_elements:
        if ele.is_a('IfcWall'):
           pass 
        if ele.is_a('IfcPlate'):
            ele_plc = ifcopenshell.util.placement.get_local_placement(ele.ObjectPlacement)
            intersected_entities = tree.select(ele)
            wall_list = [e for e in intersected_entities if e.is_a('IfcWall')]
            beam_list = [e for e in intersected_entities if e.is_a('IfcBeam')]
            if wall_list:
                if len(wall_list) == 1:
                    #considers only wall to be as a dwarf wall at the lvl of glass bottom
                    #wall_entity_plc_z = ifcopenshell.util.placement.get_local_placement(wall_entity.ObjectPlacement)[:3,3][2]
                    wall = wall_list[0]
                    wall_body_representation = ifcopenshell.util.representation.get_representation(wall, context='Model', subcontext='Body')
                    wall_ht = wall_body_representation.Items[0].Depth
                    ele_plc[:3,3][2] += wall_ht
                    matrix = mathutils.Matrix(ele_plc)
                    ifcopenshell.api.run('geometry.edit_object_placement', f, product=ele, matrix=matrix, is_si=False)
                else:
                    print(f"\nIfcPlate:{ele.GlobalId} is not clash detected") #to output to a file instead
                    continue
            if beam_list:
                if len(beam_list) == 1: #to add a 'and' operator along this to check if the beam is at higher lvl than plate
                    beam = beam_list[0]
                    beam_body_representation = ifcopenshell.util.representation.get_representation(beam, context='Model', subcontext='Body')
                    beam_ht = beam_body_representation.Items[0].SweptArea.YDim
                    beam_plc = ifcopenshell.util.placement.get_local_placement(beam.ObjectPlacement)
                    beam_z_lvl = beam_plc[:3,3][2]-beam_ht/2

                    ele_body_representation = ifcopenshell.util.representation.get_representation(ele, context='Model', subcontext='Body')
                    ele_body_representation.Items[0].Depth = beam_z_lvl-ele_plc[:3,3][2]
                    
                else:
                    print(f"\nIfcPlate:{ele.GlobalId} is not clash detected") #to output to a file instead
                    continue
'''                    

def clash_detection_wall_plate(f,tree):
    wall_plate_elements = [e for e in f if e.is_a() in ['IfcWall', 'IfcPlate']]
    
    for ele in wall_plate_elements:
        ele_plc = ifcopenshell.util.placement.get_local_placement(ele.ObjectPlacement)
        intersected_entities = tree.select(ele)
        beam_list = [e for e in intersected_entities if e.is_a('IfcBeam')]
        if ele.is_a('IfcPlate'):
            wall_list = [e for e in intersected_entities if e.is_a('IfcWall')]
            if wall_list:
                if len(wall_list) == 1:
                    #considers only wall to be as a dwarf wall at the lvl of glass bottom
                    #wall_entity_plc_z = ifcopenshell.util.placement.get_local_placement(wall_entity.ObjectPlacement)[:3,3][2]
                    wall = wall_list[0]
                    wall_body_representation = ifcopenshell.util.representation.get_representation(wall, context='Model', subcontext='Body')
                    wall_ht = wall_body_representation.Items[0].Depth
                    ele_plc[:3,3][2] += wall_ht
                    matrix = mathutils.Matrix(ele_plc)
                    ifcopenshell.api.run('geometry.edit_object_placement', f, product=ele, matrix=matrix, is_si=False)
                else:
                    print(f"\nIfcPlate: {ele.GlobalId} is not clash detected") #to output to a file instead
                    continue
        if beam_list:
            if len(beam_list) == 1: #to add a 'and' operator along this to check if the beam is at higher lvl than plate
                beam = beam_list[0]
                beam_body_representation = ifcopenshell.util.representation.get_representation(beam, context='Model', subcontext='Body')
                beam_ht = beam_body_representation.Items[0].SweptArea.YDim
                beam_plc = ifcopenshell.util.placement.get_local_placement(beam.ObjectPlacement)
                beam_z_lvl = beam_plc[:3,3][2]-beam_ht/2

                ele_body_representation = ifcopenshell.util.representation.get_representation(ele, context='Model', subcontext='Body')
                ele_body_representation.Items[0].Depth = beam_z_lvl-ele_plc[:3,3][2]
                    
            else:
                print(f"\nIfcWall: {ele.GlobalId} is not clash detected") #to output to a file instead
                continue
                    
def give_entity_name(f, entity_type):
    all_entity_types = f.by_type(entity_type)
    for type in all_entity_types:
        entities = ifcopenshell.util.element.get_types(type)
        for i in range(len(entities)):
            entities[i].Name = f"{type.Name}-{str(i+1).zfill(4)}"
