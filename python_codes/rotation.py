import mathutils
import numpy as np
import ifcopenshell
from ifcopenshell.util import placement
from ifcopenshell.api import run

path = '/home/arun/work/ai.k/Lab/ifctesting/translation.ifc'
f = ifcopenshell.open(path)

beam = f.by_type('IfcBeam')[0]
beam_plc = placement.get_local_placement(beam.ObjectPlacement)

beam_matrix = mathutils.Matrix(beam_plc)

phi = -np.pi/2
psi = np.pi/2

rotX = mathutils.Matrix([[1,0,0],[0, m.cos(phi), -m.sin(phi)], [0, m.sin(phi), m.cos(phi)]])
rotZ = mathutils.Matrix([[m.cos(psi), -m.sin(psi), 0], [m.sin(psi), m.cos(psi), 0], [0,0,1]])

rotation = rotX@rotZ

translation = np.array([0, -0.08, 2.04])
last_row = np.array([0.,0.,0.,1.])

rotation_matrix = np.vstack((np.hstack((np.matrix(rotation), translation.reshape(-1,1))), last_row))
new_matrix = mathutils.Matrix(rotation_matrix.tolist())

run('geometry.edit_object_placement', f, product=beam, matrix = new_matrix_02)

f.write('/home/arun/work/ai.k/Lab/ifctesting/rotation.ifc')

# https://www.meccanismocomplesso.org/en/3d-rotations-and-euler-angles-in-python/