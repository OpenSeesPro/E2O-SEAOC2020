# -*- coding: utf-8 -*-
"""
Created on Mon May 11 21:54:02 2020

@author: PRANCHAL
"""
from general_utilities import start_time, end_time
from etabs_utilities import get_etabs_data
from opensees_utilities import setup_opensees_model, run_opensees_model, post_process_opensees_model
from opensees_postprocessor import post_process, base_shear
import openseespy.opensees as op, openseespy.postprocessing.Get_Rendering as opp, time, os, numpy as np, pandas as pd

"""
Input for running opensees analysis below:
"""

# for future dev
#dict_of_algos = {'KN': ['Krylov-Newton, 3],
#                 'NLS': ['NewtonLineSearch', ]}

dict_of_dir     = {'dynamic w rayleigh' : 'Dyn-Rayleigh'    ,
                   'dynamic w modal'    : 'Dyn-Modal'       ,
                   'pushover'           : 'Pushover'        ,}

""" Select on of the following Algorithms for Dynamic analysis
Algorithm options available:
    Newton
    Newton w Line Search [NLS]
    Modified Newton
    Krylov-Newton [KN]
    Secant Newton
    Raphson Newton
    Periodic Newton
    BFGS
    Broyden
"""
algorithm           = 'NLS'
initialOrTangent    = 'tangent'    # for dynamic w rayleigh only
zeta                = 0.05
"""
Transient Integrator options available:
    Newmark
    HHT
    Generalized-Alpha
    TRBDF2
    Explicit Difference
"""
integrator = 'HHT'

"""
Functional calls required for creating opensees model and analysis:
"""

start = start_time()
print('__________________________GET ETABS MODEL DATA__________________________')
joints_df, pts_loads_df, frames_df, mass_df, frame_props_df, dic_hinge, dic_hinge_1, dic_hinge_2, list_new_joints, dict_of_disp_nodes, dict_of_rxn_nodes = get_etabs_data(units=3)

print('________________SET UP OPENSEES MODEL USING ETABS DATA__________________')
setup_opensees_model(joints_df, frames_df, frame_props_df, pts_loads_df, mass_df, dic_hinge, dic_hinge_1, dic_hinge_2, list_new_joints)
end_time(start, final=False)

print('__________________________RUN OPENSEES MODEL__________________________'); time.sleep(1)
for analysis in ['dynamic w rayleigh']:

    start   = start_time()
    dir_    = dict_of_dir[analysis] + '-' + algorithm + '-' + integrator + '-5.0x+0.03'
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    
    print('Destination Directory: ' + dir_); time.sleep(1)
    
    # RUN OPENSEES MODEL
    if 'rayleigh' in analysis:
        periods, eigenValues = run_opensees_model(analysis, zeta, initialOrTangent, dir_ , algorithm, integrator, dic_hinge, dict_of_disp_nodes, dict_of_rxn_nodes)
    else:
        periods, eigenValues = run_opensees_model(analysis, dir_)
    print('\nThe analysis finished. Modal periods are: ', periods)
    
    op.wipe()
    df = post_process(analysis, initialOrTangent, dir_)
    base_shear(analysis, dir_, dict_of_rxn_nodes, initialOrTangent)
    
    end_time(start); time.sleep(1.0)
