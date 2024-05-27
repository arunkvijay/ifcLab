# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import argparse

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.shape
import ifcopenshell.geom

def entity_geometry(settings, entity):
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = shape.geometry
    return geometry

def generate_entity_type_psets(entity_types, name):
    for e_type in entity_types:
        ifcopenshell.api.run('pset.add_pset', f, product=e_type, name=name)

def wall_qto_values(entity):
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = shape.geometry
    net_side_area = ifcopenshell.util.shape.get_side_area(geometry)
    #to do the other properties as well
    return {'NetSideArea':net_side_area}

def column_beam_qto_values(entity): 
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = shape.geometry
    net_volume = ifcopenshell.util.shape.get_volume(geometry)
    #to do the other properties as well
    return {'NetVolume':net_volume}

def footing_qto_values(entity): 
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = shape.geometry
    net_volume = ifcopenshell.util.shape.get_volume(geometry)
    #to do the other properties as well
    return {'NetVolume':net_volume}

def slab_qto_values(entity):
    shape = ifcopenshell.geom.create_shape(settings, entity)
    geometry = shape.geometry
    net_volume = ifcopenshell.util.shape.get_volume(geometry)
    #to do the other properties as well
    return {'NetVolume':net_volume}

def generate_entity_qtos(entities, class_name):
    if class_name == 'IfcWall':
        name = 'Qto_WallBaseQuantities'
        for entity in entities:
            qto_properties = wall_qto_values(entity)
            ent_qto = ifcopenshell.api.run('pset.add_qto', f, product=entity, name=name)
            ifcopenshell.api.run('pset.edit_qto', f, qto=ent_qto, properties=qto_properties)
    if class_name == 'IfcColumn':
        name = 'Qto_ColumnBaseQuantities'
        for entity in entities:
            qto_properties = column_beam_qto_values(entity)
            ent_qto = ifcopenshell.api.run('pset.add_qto', f, product=entity, name=name)
            ifcopenshell.api.run('pset.edit_qto', f, qto=ent_qto, properties=qto_properties)
    if class_name == 'IfcBeam':
        name = 'Qto_BeamBaseQuantities'
        for entity in entities:
            qto_properties = column_beam_qto_values(entity)
            ent_qto = ifcopenshell.api.run('pset.add_qto', f, product=entity, name=name)
            ifcopenshell.api.run('pset.edit_qto', f, qto=ent_qto, properties=qto_properties)
    if class_name == 'IfcFooting':
        name = 'Qto_FootingBaseQuantities'
        for entity in entities:
            qto_properties = footing_qto_values(entity)
            ent_qto = ifcopenshell.api.run('pset.add_qto', f, product=entity, name=name)
            ifcopenshell.api.run('pset.edit_qto', f, qto=ent_qto, properties=qto_properties)
    if class_name == 'IfcSlab':
        name = 'Qto_SlabBaseQuantities'
        for entity in entities:
            qto_properties = slab_qto_values(entity)
            ent_qto = ifcopenshell.api.run('pset.add_qto', f, product=entity, name=name)
            ifcopenshell.api.run('pset.edit_qto', f, qto=ent_qto, properties=qto_properties)

parser = argparse.ArgumentParser(description='CLI arguments for qtos')
parser.add_argument('--ifc_file', required=True, help='path to ifc file')
args = parser.parse_args()

ifc_file_path = args.ifc_file

f = ifcopenshell.open(ifc_file_path)
settings = ifcopenshell.geom.settings()

wall_types = f.by_type('IfcWallType')
generate_entity_type_psets(wall_types, name='Pset_WallCommon')
walls = f.by_type('IfcWall')
generate_entity_qtos(walls, class_name='IfcWall')

col_types = f.by_type('IfcColumnType')
generate_entity_type_psets(col_types, name='Pset_ColumnCommon')
cols = f.by_type('IfcColumn')
generate_entity_qtos(cols, class_name='IfcColumn') 

beam_types = f.by_type('IfcBeamType')
generate_entity_type_psets(beam_types, name='Pset_BeamCommon')
beams = f.by_type('IfcBeam')
generate_entity_qtos(beams, class_name='IfcBeam') 

footing_types = f.by_type('IfcFootingType')
generate_entity_type_psets(footing_types, name='Pset_FootingCommon')
footings = f.by_type('IfcFooting')
generate_entity_qtos(footings, class_name='IfcFooting') 

slab_types = f.by_type('IfcSlabType')
generate_entity_type_psets(slab_types, name='Pset_SlabCommon')
slabs = f.by_type('IfcSlab')
generate_entity_qtos(slabs, class_name='IfcSlab') 

f.write(ifc_file_path)
#PROVISION TO IMPORT .XLS FILE AND RETRIEVE PSETS FROM CUSTOMER
