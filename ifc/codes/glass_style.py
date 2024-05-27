import ifcopenshell
f = ifcopenshell.open('/home/library_metric.ifc')

body_context = ifcopenshell.util.representation.get_context(f, context='Model', subcontext='Body')

glass_material = ifcopenshell.api.run('material.add_material', f, name='GLASS01', category='glass')
glass_style = ifcopenshell.api.run('style.add_style', f, name='Glass 01', ifc_class='IfcSurfaceStyle')
ifcopenshell.api.run('style.add_surface_style', f, style=glass_style, ifc_class='IfcSurfaceStyleRendering', attributes={
    'SurfaceColour': {'Name':'Glass Colour RGB', 'Red':0.1, 'Green':0.5, 'Blue':0.9},
    'Transparency': 0.9,
    'ReflectanceMethod': 'NOTDEFINED',
    'DiffuseColour':{'Name':'Glass Colour RGB', 'Red':0.1, 'Green':0.5, 'Blue':0.9},
    'SpecularColour':0.1,
    'SpecularHighlight':{'SpecularRoughness':0.1}
    })
ifcopenshell.api.run('style.assign_material_style', f, material=glass_material, style=glass_style, context=body_context)
