# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import pandas as pd

import argparse

import ifcopenshell
import ifcopenshell.api

def entity_df(ifc_class):
    try:
        entities = f.by_type(ifc_class)
    except ValueError:
        entities = []
    if entities:
        if ifc_class=='IfcFooting':
            return create_footing_df(entities)
        elif ifc_class=='IfcColumn':
            return create_col_df(entities)
        elif ifc_class=='IfcBeam':
            return create_beam_df(entities)
        elif ifc_class=='IfcSlab':
            return create_slab_df(entities)
        elif ifc_class=='IfcWall':
            return create_wall_df(entities)
        elif ifc_class=='IfcDoor':
            return create_door_df(entities)
        elif ifc_class=='IfcWindow':
            return create_window_df(entities)
        elif ifc_class=='IfcPlate':
            return create_plate_df(entities)
        elif ifc_class=='IfcRailing':
            return create_railing_df(entities)
        elif ifc_class=='IfcStair':
            return create_stair_df(entities)
        elif ifc_class=='IfcFurniture':
            return create_furniture_df(entities)
        elif ifc_class=='IfcLightFixture':
            return create_light_fixture_df(entities)
        elif ifc_class=='IfcSanitaryTerminal':
            return create_sanitary_fittings_df(entities)
        elif ifc_class=='IfcBuildingElementProxy':
            pass
            #return create_proxy_df(entities)
    else:
        return pd.DataFrame()

def create_footing_df(footings):
    df = pd.DataFrame(columns=['guid', 'type_name', 'material_category', 'category_name', 'volume']) #TO INCLUDE M25,...
    for footing in footings:
        footing_dict = {column: None for column in df.columns}
        footing_dict['guid'] = footing.GlobalId
        footing_dict['type_name'] = ifcopenshell.util.element.get_type(footing).Name
        footing_dict['material_category'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(footing)) if _.is_a('IfcMaterial')][0].Category
        footing_dict['category_name'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(footing)) if _.is_a('IfcMaterial')][0].Name
        footing_dict['volume'] = ifcopenshell.util.element.get_pset(footing, 'Qto_FootingBaseQuantities', 'NetVolume')
        df.loc[len(df)] = [v for k, v in footing_dict.items()]
    return df

def create_wall_df(walls):
    df = pd.DataFrame(columns=['guid', 'type_name', 'material_category', 'thickness', 'area'])
    for wall in walls:
        wall_dict = {col: None for col in df.columns}
        wall_dict['guid'] = wall.GlobalId
        wall_dict['type_name'] = ifcopenshell.util.element.get_type(wall).Name
        wall_dict['material_category'] = ifcopenshell.util.element.get_material(wall).ForLayerSet.MaterialLayers[0].Material.Category
        wall_dict['thickness'] = ifcopenshell.util.element.get_material(wall).ForLayerSet.MaterialLayers[0].LayerThickness
        wall_dict['area'] = ifcopenshell.util.element.get_pset(wall, 'Qto_WallBaseQuantities', 'NetSideArea')
        df.loc[len(df)] = [v for k, v in wall_dict.items()]
    return df

def create_col_df(cols):
    df = pd.DataFrame(columns=['guid', 'type_name', 'material_category', 'category_name', 'volume']) #TO INCLUDE M25,...
    for col in cols:
        col_dict = {column: None for column in df.columns}
        col_dict['guid'] = col.GlobalId
        col_dict['type_name'] = ifcopenshell.util.element.get_type(col).Name
        col_dict['material_category'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(col)) if _.is_a('IfcMaterial')][0].Category
        col_dict['category_name'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(col)) if _.is_a('IfcMaterial')][0].Name
        col_dict['volume'] = ifcopenshell.util.element.get_pset(col, 'Qto_ColumnBaseQuantities', 'NetVolume')
        df.loc[len(df)] = [v for k, v in col_dict.items()]
    return df

def create_beam_df(beams):
    df = pd.DataFrame(columns=['guid', 'type_name', 'material_category', 'category_name', 'volume']) #TO INCLUDE M25,...
    for beam in beams:
        beam_dict = {column: None for column in df.columns}
        beam_dict['guid'] = beam.GlobalId
        beam_dict['type_name'] = ifcopenshell.util.element.get_type(beam).Name
        beam_dict['material_category'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(beam)) if _.is_a('IfcMaterial')][0].Category
        beam_dict['category_name'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(beam)) if _.is_a('IfcMaterial')][0].Name
        beam_dict['volume'] = ifcopenshell.util.element.get_pset(beam, 'Qto_BeamBaseQuantities', 'NetVolume')
        df.loc[len(df)] = [v for k, v in beam_dict.items()]
    return df

def create_slab_df(slabs):
    #df = pd.DataFrame(columns=['guid', 'type_name', 'material_category', 'category_name', 'volume']) #TO INCLUDE M25,...
    df = pd.DataFrame(columns=['guid', 'type_name', 'material_category', 'category_name', 'volume']) #TO INCLUDE M25,...
    for slab in slabs:
        slab_dict = {column: None for column in df.columns}
        slab_dict['guid'] = slab.GlobalId
        slab_dict['type_name'] = ifcopenshell.util.element.get_type(slab).Name
        #slab_dict['material_category'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(slab)) if _.is_a('IfcMaterial')][0].Category
        #slab_dict['category_name'] = [_ for _ in f.traverse(ifcopenshell.util.element.get_material(slab)) if _.is_a('IfcMaterial')][0].Name
        slab_dict['volume'] = ifcopenshell.util.element.get_pset(slab, 'Qto_SlabBaseQuantities', 'NetVolume')
        df.loc[len(df)] = [v for k, v in slab_dict.items()]
    return df

def create_door_df(doors):
    df = pd.DataFrame(columns=['guid', 'type_name'])
    for door in doors:
        door_dict = {column:None for column in df.columns}
        door_dict['guid'] = door.GlobalId
        door_dict['type_name'] = ifcopenshell.util.element.get_type(door).Name
        df.loc[len(df)] = [v for k, v in door_dict.items()]
    return df

def create_window_df(windows):
    df = pd.DataFrame(columns=['guid', 'type_name'])
    for window in windows:
        window_dict = {column:None for column in df.columns}
        window_dict['guid'] = window.GlobalId
        window_dict['type_name'] = ifcopenshell.util.element.get_type(window).Name
        df.loc[len(df)] = [v for k, v in window_dict.items()]
    return df

def create_plate_df(plates):
    pass

def create_railing_df(railings):
    pass

def create_stair_df(stairs):
    pass

def create_furniture_df(furniture):
    df = pd.DataFrame(columns=['guid', 'type_name'])
    for furn in furniture:
        furn_dict = {column:None for column in df.columns}
        furn_dict['guid'] = furn.GlobalId
        furn_dict['type_name'] = ifcopenshell.util.element.get_type(furn).Name
        df.loc[len(df)] = [v for k, v in furn_dict.items()]
    return df

def create_light_fixture_df(fixtures):
    df = pd.DataFrame(columns=['guid', 'type_name'])
    for fixt in fixtures:
        fixt_dict = {column:None for column in df.columns}
        fixt_dict['guid'] = fixt.GlobalId
        fixt_dict['type_name'] = ifcopenshell.util.element.get_type(fixt).Name
        df.loc[len(df)] = [v for k, v in fixt_dict.items()]
    return df

def create_sanitary_fittings_df(fittings):
    df = pd.DataFrame(columns=['guid', 'type_name'])
    for fit in fittings:
        fit_dict = {column:None for column in df.columns}
        fit_dict['guid'] = fit.GlobalId
        fit_dict['type_name'] = ifcopenshell.util.element.get_type(fit).Name
        df.loc[len(df)] = [v for k, v in fit_dict.items()]
    return df

def create_boq_df(all_df):
    df = pd.DataFrame(columns=['Description', 'Unit', 'Quantity', 'Rate', 'Amount'])
    col_dict = {column: None for column in df.columns}

    if not all_df['IfcFooting'].empty:
        grouped_df = all_df['IfcFooting'].groupby(['type_name', 'material_category', 'category_name'])['volume'].sum()
        grouped_df = grouped_df.rename('sum').reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and Constructing Footings done in {grouped_df['material_category'].iloc[i].capitalize()} of type {grouped_df['category_name'].iloc[i]}"
            col_dict['Unit'] = 'M^3'
            col_dict['Quantity'] = round(grouped_df['sum'].iloc[i], 2)
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcFooting')

    if not all_df['IfcColumn'].empty:
        grouped_df = all_df['IfcColumn'].groupby(['type_name', 'material_category', 'category_name'])['volume'].sum()
        grouped_df = grouped_df.rename('sum').reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and Constructing Columns done in {grouped_df['material_category'].iloc[i].capitalize()} of type {grouped_df['category_name'].iloc[i]}"
            col_dict['Unit'] = 'M^3'
            col_dict['Quantity'] = round(grouped_df['sum'].iloc[i], 2)
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcColumn')

    if not all_df['IfcBeam'].empty:
        grouped_df = all_df['IfcBeam'].groupby(['type_name', 'material_category', 'category_name'])['volume'].sum()
        grouped_df = grouped_df.rename('sum').reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and Constructing Beams done in {grouped_df['material_category'].iloc[i].capitalize()} of type {grouped_df['category_name'].iloc[i]}"
            col_dict['Unit'] = 'M^3'
            col_dict['Quantity'] = round(grouped_df['sum'].iloc[i], 2)
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcBeam')

    if not all_df['IfcSlab'].empty:
        #grouped_df = all_df['IfcSlab'].groupby(['type_name', 'material_category', 'category_name'])['volume'].sum() #TO CORRECT WITH MATERIAL CATEGORY AND NAME. ATM this is not available in the model
        grouped_df = all_df['IfcSlab'].groupby(['type_name'])['volume'].sum()
        grouped_df = grouped_df.rename('sum').reset_index()
        for i in grouped_df.index:
            #col_dict['Description'] = f"Providing and Constructing Slabs done in {grouped_df['material_category'].iloc[i].capitalize()} of type {grouped_df['category_name'].iloc[i]}" TO BE CORRECTED AFTER THE MATERIAL CORRECTION IS DONE. 
            col_dict['Description'] = f"Providing and Constructing Slabs"
            col_dict['Unit'] = 'M^3'
            col_dict['Quantity'] = round(grouped_df['sum'].iloc[i], 2)
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcSlab')

    if not all_df['IfcWall'].empty:
        grouped_df = all_df['IfcWall'].groupby(['type_name', 'material_category', 'thickness'])['area'].sum()
        grouped_df = grouped_df.rename('sum').reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and Constructing Walls done in {grouped_df['material_category'].iloc[i].capitalize()} Masonry of thickness {round(grouped_df['thickness'].iloc[i])}"
            col_dict['Unit'] = 'M^2'
            col_dict['Quantity'] = round(grouped_df['sum'].iloc[i], 2)
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcWall')

    if not all_df['IfcDoor'].empty:
        grouped_df = all_df['IfcDoor'].groupby(['type_name']).count()
        grouped_df = grouped_df.reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and installing Door of Type {grouped_df['type_name'].iloc[i]}"
            col_dict['Unit'] = 'No.s'
            col_dict['Quantity'] = grouped_df['guid'].iloc[i]
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcDoor')

    if not all_df['IfcWindow'].empty:
        grouped_df = all_df['IfcWindow'].groupby(['type_name']).count()
        grouped_df = grouped_df.reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and installing Window of Type {grouped_df['type_name'].iloc[i]}"
            col_dict['Unit'] = 'No.s'
            col_dict['Quantity'] = grouped_df['guid'].iloc[i]
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcWindow')

    if not all_df['IfcFurniture'].empty:
        grouped_df = all_df['IfcFurniture'].groupby(['type_name']).count()
        grouped_df = grouped_df.reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and supplying Furniture of Type {grouped_df['type_name'].iloc[i]}"
            col_dict['Unit'] = 'No.s'
            col_dict['Quantity'] = grouped_df['guid'].iloc[i]
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcFurniture')

    if not all_df['IfcLightFixture'].empty:
        grouped_df = all_df['IfcLightFixture'].groupby(['type_name']).count()
        grouped_df = grouped_df.reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and supplying Light Fixture of Type {grouped_df['type_name'].iloc[i]}"
            col_dict['Unit'] = 'No.s'
            col_dict['Quantity'] = grouped_df['guid'].iloc[i]
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcLightFixture')

    if not all_df['IfcSanitaryTerminal'].empty:
        grouped_df = all_df['IfcSanitaryTerminal'].groupby(['type_name']).count()
        grouped_df = grouped_df.reset_index()
        for i in grouped_df.index:
            col_dict['Description'] = f"Providing and supplying Sanitary Terminal of Type {grouped_df['type_name'].iloc[i]}"
            col_dict['Unit'] = 'No.s'
            col_dict['Quantity'] = grouped_df['guid'].iloc[i]
            col_dict['Rate'] = 1
            col_dict['Amount'] = col_dict['Quantity']*col_dict['Rate']
            df.loc[len(df)] = [v for k, v in col_dict.items()]
    else:
        print('No IfcSanitaryTerminal')

    #df = df.style.set_caption('Top 10')
    df.reset_index(inplace=True, drop=True)
    df.index += 1
    df.index.name = 'Sl. No.'
    df.to_excel('boq.xlsx')


parser = argparse.ArgumentParser(description='CLI arguments for boq generation')
parser.add_argument('--ifc_file', required=True, help='path to ifc file')
args = parser.parse_args()

ifc_file_path = args.ifc_file

f = ifcopenshell.open(ifc_file_path)

df_footings = entity_df('IfcFooting')
df_cols = entity_df('IfcColumn')
df_beams = entity_df('IfcBeam')
df_slabs = entity_df('IfcSlab') #WHAT ABOUT SLABS PART OF STAIRS
df_walls = entity_df('IfcWall')
df_doors = entity_df('IfcDoor')
df_windows = entity_df('IfcWindow')
df_plates = entity_df('IfcPlate')
df_railings = entity_df('IfcRailing')
df_stairs = entity_df('IfcStair') #WHAT ABOUT INDEPENDENT STEPS
df_furniture = entity_df('IfcFurniture')
df_light_fixture = entity_df('IfcLightFixture')
df_sanitary_fittings = entity_df('IfcSanitaryTerminal')
df_proxy = entity_df('IfcBuildingElementProxy')

#beams = f.by_type('IfcBeam') #NEED TO OPT OUT PLINTH BEAM
#df_beams = create_beam_df(beams)
#plinth_beams = f.by_type('IfcSlab') #ONLY PLINTH BEAM
#df_plinth_beams = create_beam_df(plinth_beams)

#print(df_walls)
#print(df_walls.groupby(['type_name', 'material_category', 'thickness'])['area'].sum())

#all_df = [df_footings, df_cols, df_slabs, df_walls, df_doors, df_windows, df_railings, df_stairs] 
all_df = {'IfcFooting':df_footings, 
          'IfcColumn':df_cols, 
          'IfcBeam':df_beams, 
          'IfcSlab':df_slabs,
          'IfcWall':df_walls,
          'IfcDoor':df_doors,
          'IfcWindow':df_windows,
          'IfcPlate':df_plates,
          'IfcRailing':df_railings,
          'IfcStair':df_stairs,
          'IfcFurniture':df_furniture,
          'IfcLightFixture':df_light_fixture,
          'IfcSanitaryTerminal':df_sanitary_fittings,
          'IfcBuildingElementProxy':df_proxy}
df_boq = create_boq_df(all_df)
