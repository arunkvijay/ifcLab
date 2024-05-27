# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import ifcopenshell
import ifcopenshell.api

def new_project(project_data, unit):
    project_name = project_data['project_name']
    f = ifcopenshell.api.run('project.create_file', file_name=project_name.replace(' ','_').lower()+'.ifc')
    project = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcProject', name=project_name)    

    if unit=='metric':
        ifcopenshell.api.run('unit.assign_unit', f)
    else:
        length = ifcopenshell.api.run('unit.add_conversion_based_unit', f, name='inch')
        area = ifcopenshell.api.run('unit.add_conversion_based_unit', f, name='square foot')
        ifcopenshell.api.run('unit.assign_unit', f, units=[length, area])

    model3d = ifcopenshell.api.run('context.add_context', f, context_type='Model')
    plan = ifcopenshell.api.run('context.add_context', f, context_type='Plan')
    body = ifcopenshell.api.run('context.add_context', f, context_type='Model', context_identifier='Body', target_view='MODEL_VIEW', parent=model3d)
    ifcopenshell.api.run('context.add_context', f, context_type='Plan', context_identifier='Profile', target_view='ELEVATION_VIEW', parent=plan)
    return f, project, model3d, plan, body

def owner_history(f, org_data, project_data):
    application = ifcopenshell.api.run("owner.add_application", f)
    org_identification=org_data['identification']
    org = ifcopenshell.api.run("owner.add_organisation", f, identification=org_identification, name=org_data["org_name"]) 
    ifcopenshell.api.run("owner.add_role", f, assigned_object=org, role=org_data["org_role"]) #role to be from IfcRoleEnum
    # postal/telecom address if required to be added later 
    person_identification = project_data['creator']['identification']
    family_name = project_data['creator']['family_name'].title() 
    given_name = project_data['creator']['given_name'].title()
    person = ifcopenshell.api.run("owner.add_person", f, identification=person_identification,family_name=family_name, given_name=given_name) 
    ifcopenshell.api.run("owner.add_role",f, assigned_object=person, role=project_data['creator']['role'])
    user = ifcopenshell.api.run("owner.add_person_and_organisation", f, person=person, organisation=org)
    # ifcopenshell.api.owner.settings.get_user = lambda x:user
    # ifcopenshell.api.owner.settings.get_application = lambda x:application

def create_storeys(f, building, project_data):
    storeys_dict = project_data['storeys_dict']
    repeat_lvls = []
    storey_names = []

    for k, v in storeys_dict.items():
        if 'REPEAT' in k:
            for k, v in storeys_dict.items():
                if 'REPEAT' in k:
                    repeat_start_level = int(k.split('_')[-2])
                    repeat_end_level = int(k.split('_')[-1])
                    for i in range(repeat_start_level, repeat_end_level+1):
                        storey_name = 'LEVEL ' + str(i)
                        repeat_lvls.append(storey_name)
        else: 
            storey_name = ' '.join([word.upper() for word in v['name'].split('_')])
            storey_names.append(storey_name)

    storey_names.extend(repeat_lvls)
    for s in storey_names:
        storey = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcBuildingStorey', name=s) 
        ifcopenshell.api.run('aggregate.assign_object', f, relating_object = building, product=storey)
        ifcopenshell.api.run('geometry.edit_object_placement', f, product=storey)
    
    return repeat_lvls

def create_spatial_structure(f, project, project_data):
    site_name = project_data['site_name']
    building_name = project_data['building_name']

    site = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcSite', name=site_name)
    ifcopenshell.api.run('aggregate.assign_object', f, relating_object=project, product=site)
    building = ifcopenshell.api.run('root.create_entity', f, ifc_class='IfcBuilding', name=building_name)    
    ifcopenshell.api.run('aggregate.assign_object', f, relating_object=site, product=building)

    ifcopenshell.api.run('geometry.edit_object_placement', f, product=site)
    ifcopenshell.api.run('geometry.edit_object_placement', f, product=building)

    create_storeys(f, building, project_data)
