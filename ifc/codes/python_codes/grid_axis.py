def uaxis(grid, start_char, end_char):
    for char_code in range(ord(start_char), ord(end_char) + 1):
        ifcopenshell.api.run("grid.create_grid_axis", f, axis_tag=chr(char_code), uvw_axes="UAxes", grid=grid)

def vaxis(grid, start_num, end_num):
    for i in range(start_num, end_num + 1):
        ifcopenshell.api.run("grid.create_grid_axis", f, axis_tag=str(i), uvw_axes="VAxes", grid=grid)