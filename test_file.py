from cst_interface.cst_driver import CSTDriver

drier = CSTDriver()
drier.run_command(
    "define sphere",
    solid_name="sphere1",
    component_name="comp1",
    material="PEC",
    axis="z",
    cradius="5",
    tradius="5",
    bradius="5",
    center_x="5",
    center_y="5",
    center_z="2.5",
    segments="32"
)
