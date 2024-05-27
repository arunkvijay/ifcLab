import ifcopenshell
import ifcopenshell.geom
from ifcopenshell.util import placement

path = '/home/translation.ifc'
f = ifcopenshell.open(path)

beam = f.by_type('IfcBeam')[0]
beam_plc = placement.get_local_placement(beam.ObjectPlacement)

# settings = ifcopenshell.geom.settings()
# settings.set(settings.USE_PYTHON_OPENCASCADE, True)
