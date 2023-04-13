import mathutils
import ifcopenshell
from ifcopenshell.util import placement
from ifcopenshell.api import run

path = '/home/arun/work/ai.k/Lab/ifctesting/translation.ifc'
f = ifcopenshell.open(path)

beam = f.by_type('IfcBeam')[0]
beam_plc = placement.get_local_placement(beam.ObjectPlacement)

beam_matrix = mathutils.Matrix(beam_plc)
translation = mathutils.Matrix([[0,0,0,0],[0,0,0,-0.08],[0,0,0,2.04],[0,0,0,0]])

# new_matrix = beam_matrix + translation
new_matrix = beam_matrix @ translation

run('geometry.edit_object_placement', f, product=beam, matrix = new_matrix)

f.write(path)
