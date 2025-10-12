from cst.interface import DesignEnvironment

import numpy as np
import pandas as pd

cst_de = DesignEnvironment()
mws = cst_de.new_mws()


#Create materials
fr4_macro = '''
With Material
    .Reset
    .Name "FR-4 (lossy)"
    .Folder ""
    .FrqType "static"
    .Type "Normal"
    .Epsilon "4.4"
    .Mue "1.0"
    .Sigma "0.002"
    .TanD "0.02"
    .Colour "0.5", "0.8", "0.5"
    .Create
End With
'''

copper_macro = '''
With Material
    .Reset
    .Name "Copper"
    .Folder ""
    .Type "Normal"
    .FrqType "static"
    .Rho "1.7e-8"
    .Colour "0.8", "0.5", "0.2"
    .Create
End With
'''

mws.model3d.add_to_history("Create FR-4 (lossy)", fr4_macro)
mws.model3d.add_to_history("Create Copper (lossy)", copper_macro)

#create Antenna
def create_antenna(family, shape, bandwidth, substrate, conductor, parameters):
    if family =="Microstrip Patch" and shape == "Rectangular":
        W_mm = parameters['patch_width_m'] * 1e3  # Convert to mm
        L_mm = parameters['patch_length_m'] * 1e3  # Convert to mm
        h = parameters['substrate_thickness_m'] * 1e3  # Convert to mm
        subs_w = parameters['substrate_width_m'] * 1e3  # Convert to mm
        subs_l = parameters['substrate_length_m'] * 1e3  # Convert to mm
        y0 = parameters['inset_feed_m'] * 1e3  # Convert to mm
        resonant_frequency = parameters['frequency_GHz']  # in GHz
        print("Creating Antenna with parameters:")

        substrate_macro = f'''
        With Brick
            .Reset
            .Name "substrate"
            .Component "component1"
            .Material "FR-4 (lossy)"
            .Xrange "{-subs_w/2}", "{subs_w/2}"
            .Yrange "{-subs_l/2}", "{subs_l/2}"
            .Zrange "{0}", "{h}"
            .Create
        End With
        '''

        ground_macro = f'''
        With Brick
            .Reset
            .Name "ground"
            .Component "component1"
            .Material "Copper"
            .Xrange "{-subs_w/2}", "{subs_w/2}"
            .Yrange "{-subs_l/2}", "{subs_l/2}"
            .Zrange "0", "-0.035"
            .Create
        End With
        '''

        patch_macro = f'''
        With Brick
            .Reset
            .Name "patch"
            .Component "component1"
            .Material "Copper"
            .Xrange "{-W_mm/2}", "{W_mm/2}"
            .Yrange "{-L_mm/2}", "{L_mm/2}"
            .Zrange "{h}", "{h+0.035}"
            .Create
        End With
        '''
        feed_macro = f'''
        With Brick
            .Reset
            .Name "feed"
            .Component "component1"
            .Material "Copper"
            .Xrange "{-5/2}", "{5/2}"
            .Yrange "{-subs_l/2}", "{-L_mm/2}"
            .Zrange "{h}", "{h+0.035}"
            .Create
        End With
        '''

        mws.model3d.add_to_history("Create patch", substrate_macro)
        mws.model3d.add_to_history("Create patch", ground_macro)
        mws.model3d.add_to_history("Create patch", patch_macro)
        mws.model3d.add_to_history("Create patch", feed_macro)

        boundary_macro = '''
        With Boundary
            .Xmin "open"
            .Xmax "open"
            .Ymin "open"
            .Ymax "open"
            .Zmin "open"
            .Zmax "open"
        End With
        '''
        mws.model3d.add_to_history("Set boundaries", boundary_macro)

        freq_range_macro = f'''
        With Solver
            .FrequencyRange "{resonant_frequency-2}", "{resonant_frequency+2}"
        End With
        '''
        mws.model3d.add_to_history("Frequency Range", freq_range_macro)


        port_macro = f'''
        With Port 
            .Reset 
            .PortNumber "1" 
            .Label ""
            .Folder ""
            .NumberOfModes "1"
            .AdjustPolarization "False"
            .PolarizationAngle "0.0"
            .ReferencePlaneDistance "0"
            .TextSize "50"
            .TextMaxLimit "0"
            .Coordinates "Picks"
            .Orientation "positive"
            .PortOnBound "False"
            .ClipPickedPortToBound "False"
            .Xrange "-3", "3"
            .Yrange "-19.72", "-19.72"
            .Zrange "1.6", "1.635"
            .XrangeAdd "1.6*6.78", "1.6*6.78"
            .YrangeAdd "0.0", "0.0"
            .ZrangeAdd "1.6", "1.6"
            .SingleEnded "False"
            .WaveguideMonitor "False"
            .Create 
        End With
        '''
        pick_macro = '''
        Pick.PickFaceFromId "component1:feed", "3"
        '''

        mws.model3d.add_to_history("Pick Face", pick_macro)
        mws.model3d.add_to_history("Create port", port_macro)

        run_macro = '''
        Solver.Start
        '''
        mws.model3d.add_to_history("Run Solver", run_macro)

