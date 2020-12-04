'''
    MIT License
    
    Copyright (c) 2020 OpenSeesPro
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    Developed by:
        Ayush Singhania (ayushs@stanford.edu)
        Pearl Ranchal (ranchal@berkeley.edu)
      
    Publication:
        Goings, C. B., Singhania, A., Ranchal, P., Weaver B., 2020, “Industrial 
        Scale NLRH Analysis Using OpenSees and Comparison with Perform3D,” 
        Proceedings of 2020 SEAOC Virtual Convention, SEAOC, CA

    Introduction of this script - 
        This is the main script that the user is supposed to execute to use E20
        library. All other files are supporting scripts. This script first looks
        for a result folder and if not present creats it. Then it extracts data
        from ETBAS using the etabs_utilities function. Followed by execution of 
        setup_opensees_model method to generate the opensees model.Finally it 
        executes the analysis in opensses using the run_opensees_model method.

'''

from general_utilities import start_time, end_time
from etabs_utilities import get_etabs_data
from opensees_utilities import setup_opensees_model, perform_modal_analysis_and_comparison, run_opensees_model
from opensees_postprocessor import post_process, base_shear
import time
import os

if __name__ == '__main__':
    start = start_time()
    working_dir = os.path.join(os.path.dirname(os.getcwd()), 'results')
    
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
        
    print(''.center(100, '-'))
    print(':: GET ETABS MODEL DATA ::'.center(100))
    print(''.center(100, '-'))
    joints_df, pts_loads_df, frames_df, mass_df, frame_props_df, dict_of_hinges, dict_of_hinges_2, list_new_joints, dict_of_disp_nodes, dict_of_rxn_nodes, etabs_periods = get_etabs_data(units=3)
    print('Done!\n')
    
    print(''.center(100, '-'))
    print(':: SET UP OPENSEES MODEL USING ETABS DATA ::'.center(100))
    print(''.center(100, '-'))
    setup_opensees_model(joints_df, frames_df, frame_props_df, pts_loads_df, mass_df, dict_of_hinges, dict_of_hinges_2, list_new_joints)
    print('OpenSees Model Created!')
    end_time(start, final=False)
    
    print(''.center(100, '-'))
    print(':: RUN OPENSEES MODEL ::'.center(100))
    print(''.center(100, '-'))
    
    print(f'Destination Directory: {working_dir}'); 
    time.sleep(1)
    
    # PERFORM MODAL ANALYSIS COMPARISON B/W ETABS AND OPENSEES
    perform_modal_analysis_and_comparison(etabs_periods)
    
    # RUN OPENSEES MODEL
    zeta = 0.05
    initialOrTangent = 'tangent'
    periods, eigenValues = run_opensees_model(dict_of_hinges, dict_of_disp_nodes, dict_of_rxn_nodes, zeta, initialOrTangent, working_dir)
    
    # POST-PROCESS ANALYSIS DATA
    df = post_process(initialOrTangent, working_dir)
    base_shear(working_dir, dict_of_rxn_nodes, initialOrTangent)
    
    # FINISH
    end_time(start)
    time.sleep(1.0)
