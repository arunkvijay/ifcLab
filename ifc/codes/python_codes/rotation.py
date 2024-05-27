import mathutils
import numpy as np
import ifcopenshell
from ifcopenshell.util import placement
from ifcopenshell.api import run

path = '/home/translation.ifc'
f = ifcopenshell.open(path)

beam = f.by_type('IfcBeam')[0]
beam_plc = placement.get_local_placement(beam.ObjectPlacement)

beam_matrix = mathutils.Matrix(beam_plc)

phi = -np.pi/2
psi = np.pi/2

rotX = mathutils.Matrix([[1,0,0],[0, np.cos(phi), -np.sin(phi)], [0, np.sin(phi), np.cos(phi)]])
rotZ = mathutils.Matrix([[np.cos(psi), -np.sin(psi), 0], [np.sin(psi), np.cos(psi), 0], [0,0,1]])

rotation = rotX@rotZ

translation = np.array([0, -0.08, 2.04])
last_row = np.array([0.,0.,0.,1.])

rotation_mat = np.vstack((np.hstack((np.matrix(rotation), translation.reshape(-1,1))), last_row))
new_matrix = mathutils.Matrix(rotation_mat.tolist())

run('geometry.edit_object_placement', f, product=beam, matrix = new_matrix)

f.write('/home/rotation.ifc')
