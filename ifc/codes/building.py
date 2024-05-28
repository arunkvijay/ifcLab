# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import argparse
import json
import os
import os.path

import ifcopenshell

import mathutils

import project_template
import super_structure
import modify_entity
import geometry_tree

import time 
start_time = time.time()

def element_z_translation(element, height):
    element_plc = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
    element_plc[:,3][2] = height 

    element_matrix = mathutils.Matrix(element_plc)
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=element, matrix=element_matrix, is_si=False)

def order_height_calculation(container, project_data):
    if 'NEG' in container.Name:
        container_order = int(container.Name.split()[-1][3:]) #to be modified for multiple basement
        lvl = 'LEVEL_NEG'+ str(container_order)
        return -1 * int(project_data['storeys_dict'][lvl]['height'])
    else:
        container_order = int(container.Name.split()[-1])

    if container_order == 0:
        return 0
    elif container_order > 0:
        order_height = 0
        while container_order > 0:
            lvl = 'LEVEL_'+ str(container_order-1)
            try: 
                order_height += int(project_data['storeys_dict'][lvl]['height'])
            except ValueError:
                break
            container_order -= 1
        return order_height

def container_z_translation(container, height, project_data):
    plinth_lvl = project_data['plinth_lvl']
    container_plc = ifcopenshell.util.placement.get_local_placement(container.ObjectPlacement)
    container_plc[:,3][2] = int(plinth_lvl) + order_height_calculation(container, project_data)

    container_matrix = mathutils.Matrix(container_plc)
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=container, matrix=container_matrix, is_si=False, should_transform_children=True)

def entity_height_calculation(storey_name, project_data):
    s_name = storey_name.Name.replace(' ', '_')
    storeys_dict = project_data['storeys_dict']
    for k, v in storeys_dict.items():
        if k == s_name:
            return int(v['height'])
        elif 'REPEAT' in k:
            return int(v['height'])

def create_stuff(storey_name, file_name):
    lintel_lvl = int(project_data['lintel_level'])

    if file_name.split('.')[-1] == 'csv':
        if 'SLAB' in file_name.split('.')[0]:
            if 'FLOOR' in file_name.split('.')[0]:
                csv_file = os.path.join(processing_folder, file_name)
                depth = file_name.split('.')[0].split('_')[-1]
                if 'CUTOUT' in file_name:
                    super_structure.create_slab(f, library, body, storey_name, csv_file, depth=int(depth), predefined_type='USERDEFINED', object_type='FLOORCUTOUT')
                elif file_name.split('+')[0].split('_', maxsplit=1)[1] == 'LEVEL_0': #CHANGE THIS TO THE LOWEST SLAB
                    #super_structure.create_slab(f, library, body, storey_name, csv_file, depth=int(project_data['plinth_lvl']), predefined_type='BASESLAB', object_type=None) #TO CHANGE THE DEPTH FROM PLINTH TO WHEREEVER REQUIRED
                    super_structure.create_slab(f, library, body, storey_name, csv_file, depth=int(depth), predefined_type='BASESLAB', object_type=None) #TO CHANGE THE DEPTH FROM PLINTH TO WHEREEVER REQUIRED
                else:
                    super_structure.create_slab(f, library, body, storey_name, csv_file, depth=int(depth), predefined_type='FLOOR', object_type=None)
            elif 'ROOF' in file_name.split('.')[0]:
                csv_file = os.path.join(processing_folder, file_name)
                depth = file_name.split('.')[0].split('_')[-1]
                if 'CUTOUT' in file_name:
                    super_structure.create_slab(f, library, body, storey_name, csv_file, depth=int(depth), predefined_type='USERDEFINED', object_type='ROOFCUTOUT')
                else:
                    super_structure.create_slab(f, library, body, storey_name, csv_file, depth=int(depth), predefined_type='ROOF', object_type=None)

        if 'COLUMN' in file_name.split('.')[0]:
            csv_file = os.path.join(processing_folder, file_name)
            height = entity_height_calculation(storey_name, project_data)
            #super_structure.create_pline_column(f, body, storey_name, csv_file, height=height, predefined_type='COLUMN')

    elif file_name.split('.')[-1] == 'json':
        if 'BEAM' in file_name.split('.')[0]:
            if 'PLINTH' in file_name.split('.')[0]:
                json_file = os.path.join(processing_folder, file_name)
                depth = file_name.split('.')[0].split('_')[-1]
                super_structure.create_beam(f, library, ifc_library_file, body, storey_name, json_file, depth=int(depth), predefined_type='USERDEFINED', object_type='PLINTHBEAM') #to be incorporated in the json file
            else:
                json_file = os.path.join(processing_folder, file_name)
                depth = file_name.split('.')[0].split('_')[-1]
                super_structure.create_beam(f, library, ifc_library_file, body, storey_name, json_file, depth=int(depth), predefined_type='BEAM') #to be incorporated in the json file
            modify_entity.give_entity_name(f, entity_type='IfcBeamType')
        #elif 'BASEPLATE' in file_name.split('.')[0]:
            #json_file = os.path.join(processing_folder, file_name)
            #height = entity_height_calculation(storey_name, project_data)
            #super_structure.create_baseplate(f, library, ifc_library_file, body, storey_name, json_file, height=height, predefined_type='COLUMN')
            modify_entity.give_entity_name(f, entity_type='IfcColumnType')
        elif 'COLUMN' in file_name.split('.')[0]:
            json_file = os.path.join(processing_folder, file_name)
            height = entity_height_calculation(storey_name, project_data)
            super_structure.create_column(f, library, ifc_library_file, body, storey_name, json_file, height=height, predefined_type='COLUMN')
            modify_entity.give_entity_name(f, entity_type='IfcColumnType')
        elif 'DOOR' in file_name.split('.')[0]:
            json_file = os.path.join(processing_folder, file_name)
            super_structure.create_door_window('DOOR', f, library, body, storey_name, json_file, predefined_type='DOOR', lintel_lvl=lintel_lvl)
            modify_entity.give_entity_name(f, entity_type='IfcDoorType')
        elif 'FOOTING' in file_name.split('.')[0]:
            json_file = os.path.join(processing_folder, file_name)
            z_level = -(int(project_data['footing_lvl_below_ngl']) + int(project_data['plinth_lvl']))
            if 'PAD' in file_name.split('.')[0]:
                predefined_type = 'PAD_FOOTING'
            #depth = int(file_name.split('.')[0].split('x')[-1])
            #super_structure.create_footing_pad(f, library, ifc_library_file, body, storey_name, json_file, z_level=z_level, depth=depth, predefined_type=predefined_type)
            super_structure.create_footing_pad(f, library, ifc_library_file, body, storey_name, json_file, z_level=z_level, predefined_type=predefined_type)
            modify_entity.give_entity_name(f, entity_type='IfcFootingType')
        elif 'FURNITURE' in file_name.split('.')[0]:
            json_file = os.path.join(processing_folder, file_name)
            super_structure.create_furniture(f, library, body, storey_name, json_file)
            modify_entity.give_entity_name(f, entity_type='IfcFurnitureType')
        elif 'PLATE' in file_name.split('.')[0]:
            json_file = os.path.join(processing_folder, file_name)
            if 'GLASS' in file_name.split('.')[0]:
                predefined_type = 'CURTAIN_PANEL'
            height = entity_height_calculation(storey_name, project_data) #- int(project_data['slab_thickness'])#CHANGE SLAB THICKNESS TO TAKE FROM LAYER NAME
            super_structure.create_plate_entity(f, library, body, storey_name, json_file, height=height, predefined_type=predefined_type)
            modify_entity.give_entity_name(f, entity_type='IfcPlateType')
        elif 'ANGLED' in file_name.split('.')[0]:
            json_file = os.path.join(processing_folder, file_name)
            height = entity_height_calculation(storey_name, project_data) - int(project_data['slab_thickness']) #CHANGE SLAB THICKNESS TO TAKE FROM LAYER NAME
            thickness = 200 #to be incorporated in the json file also wall type to be assigned like how it is done for below 
            super_structure.create_angled_entity(f, library, body, storey_name, json_file, entity='IfcWall', height=height, thickness=thickness, predefined_type='SOLIDWALL')
        elif 'WALL' in file_name.split('.')[0]:
            if 'PARAPET' in file_name.split('.')[0]:
                json_file = os.path.join(processing_folder, file_name)
                height = int(project_data['parapet_height'])
                super_structure.create_wall(f, library, ifc_library_file, body, storey_name, json_file, height=height, predefined_type='PARAPET')
            elif 'SHEAR' in file_name.split('.')[0]:
                json_file = os.path.join(processing_folder, file_name)
                height = entity_height_calculation(storey_name, project_data) - int(project_data['slab_thickness'])#CHANGE SLAB THICKNESS TO TAKE FROM LAYER NAME
                super_structure.create_wall(f, library, ifc_library_file, body, storey_name, json_file, height=height, predefined_type='SHEAR')
            else:
                json_file = os.path.join(processing_folder, file_name)
                if 'DWARF' in file_name.split('.')[0]:
                    height = int(file_name.split('.')[0].split('_')[-1])
                else:
                    height = entity_height_calculation(storey_name, project_data) - int(project_data['slab_thickness'])#CHANGE SLAB THICKNESS TO TAKE FROM LAYER NAME
                super_structure.create_wall(f, library, ifc_library_file, body, storey_name, json_file, height=height, predefined_type='SOLIDWALL')
            modify_entity.give_entity_name(f, entity_type='IfcWallType')
        elif 'WINDOW' in file_name.split('.')[0]:
            json_file = os.path.join(processing_folder, file_name)
            super_structure.create_door_window('WINDOW', f, library, body, storey_name, json_file, predefined_type='WINDOW', lintel_lvl=lintel_lvl)
            modify_entity.give_entity_name(f, entity_type='IfcWindowType')

parser = argparse.ArgumentParser(description='CLI arguments for main.py python file')
parser.add_argument('--org_config', required=True, help='path to org_config.json file')
parser.add_argument('--project_config', required=True, help='path to project_config.json file')
args = parser.parse_args()

org_json_file = args.org_config
project_json_file = args.project_config

with open(org_json_file) as oj:
    org_data = json.load(oj)

with open(project_json_file) as pj:
    project_data = json.load(pj)

if 'identification' not in org_data:
    import uuid
    identification = str(uuid.uuid5(uuid.NAMESPACE_X500, org_data['telecom_address']['ElectronicMailAddresses'][0]))
    org_data['identification'] = identification
    with open(org_json_file, 'w') as oj:
        json.dump(org_data, oj, indent=4)

unit = project_data['unit']

ifc_file_name = project_data['project_name'].replace(' ','_').lower()+'.ifc'
ifc_path = os.path.join('/home/',project_data['project_name'].replace(' ','_').lower(),project_data['ifc_path'],ifc_file_name) 

if project_data['unit'] == 'metric':
    ifc_library_file = os.path.join('/home/library/library_metric.ifc')
    furn_library_file = os.path.join('/home/library/furn_library_metric.ifc')
else:
    ifc_library_file = os.path.join('/home/ibrary/library_imperial.ifc')
library = ifcopenshell.open(ifc_library_file)
furn_library = ifcopenshell.open(furn_library_file)

f, project, model3d, plan, body = project_template.new_project(project_data, unit) 
project_template.owner_history(f, org_data, project_data)
project_template.create_spatial_structure(f, project, project_data)

storeys = f.by_type('IfcBuildingStorey')

processing_folder = os.path.join('/home/project_data['project_name'].replace(' ','_').lower(),project_data['cad_processing_path'])
processed_file_list = os.listdir(processing_folder)

for file_name in processed_file_list:
    repeat_storey_names = []
    f_names = []
    if 'REPEAT' in file_name:
        repeat_start_level = int(os.path.splitext(file_name)[0].split('+')[0].split('_')[-2]) 
        repeat_end_level = int(os.path.splitext(file_name)[0].split('+')[0].split('_')[-1]) 
        for i in range(repeat_start_level, repeat_end_level+1):
            repeat_storey_names.append('LEVEL ' + str(i))
            # f_names.append('FLOW_LEVEL_' + str(i) + '+' + file_name.split('+')[-1])
            for s_name in repeat_storey_names:
                storey_name = [_ for _ in storeys if _.Name == s_name][0]
                create_stuff(storey_name, file_name)
    else:
        st_name_list = os.path.splitext(file_name)[0].split('+')[0].split('_')[1:]
        s_name = ' '.join(st_name_list)
        storey_name = [_ for _ in storeys if _.Name == s_name][0]
        create_stuff(storey_name, file_name)

lintel_lvl = int(project_data['lintel_level'])
super_structure.window_z_translation(f, lintel_lvl=lintel_lvl)

plinth_beam_elements = [e for e in f.by_type('IfcBeam') if e.PredefinedType=='USERDEFINED'] #need to add PLINTHBEAM to this. modify super_structure first
for plinth_beam in plinth_beam_elements:
    element_z_translation(plinth_beam, height=-plinth_beam.Representation.Representations[0].Items[0].SweptArea.YDim/2) #to be incorporated in the json file

roof_elements = [e for e in f.by_type('IfcSlab') if e.PredefinedType=='ROOF' or e.ObjectType=='ROOFCUTOUT']
for roof in roof_elements: #TO BE CORRECTED IMMEDIATELY. STOREY HEIGT TO BE FROM THE INDIVIDUAL STOREY LVL
    storey_lvl_name = ifcopenshell.util.element.get_container(roof).Name.replace(' ', '_')
    height = int(project_data['storeys_dict'][storey_lvl_name]['height'])
    element_z_translation(roof, height=height-int(project_data['slab_thickness']))

beam_elements = [e for e in f.by_type('IfcBeam') if e.PredefinedType=='BEAM']
for beam in beam_elements:
    storey_lvl_name = ifcopenshell.util.element.get_container(beam).Name.replace(' ', '_')
    height = int(project_data['storeys_dict'][storey_lvl_name]['height'])
    element_z_translation(beam, height=height - beam.Representation.Representations[0].Items[0].SweptArea.YDim/2) 

for s in storeys: 
    c_height = entity_height_calculation(s, project_data)
    container_z_translation(s, c_height, project_data)

#tree = geometry_tree.create_geometry_tree(f) below codes to be refactored using this
modify_entity.create_wall_openings(f, body, processing_folder, processed_file_list)
super_structure.create_voids(f)

tree = geometry_tree.create_geometry_tree(f)
modify_entity.clash_detection_wall_plate(f, tree)
f.write(ifc_path)

end_time = time.time()
print(f"\nExecution time: {end_time - start_time}")
print(f"Finish time: {time.strftime('%H:%M:%S', time.localtime(time.time()))}\n")
