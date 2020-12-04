#    MIT License
#    
#    Copyright (c) 2020 OpenSeesPro
#    
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the Software is
#    furnished to do so, subject to the following conditions:
#    
#    The above copyright notice and this permission notice shall be included in all
#    copies or substantial portions of the Software.
#    
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#    SOFTWARE.
# 
#    Developed by:
#       Ayush Singhania (ayushs@stanford.edu)
#       Pearl Ranchal (ranchal@berkeley.edu)

import openseespy.opensees as op
import openseespy.postprocessing.Get_Rendering as opp
import pandas as pd
import numpy as np
import math
import os, shutil
from tqdm import tqdm

g = 386.4 
M = 0
E = 29000
G = 11153.846
numEigen = 3
rigid_dia = True

col_transf_tag  = 1 
beam_transf_tag = 2

coordTransf = "Linear"  # Linear, PDelta, Corotational
massType = "-lMass"     # -lMass, -cMass

tol = 1e-3

def initiate_model():
    op.wipe()                       # remove existing model
    op.model('basic', '-ndm', 3)    # set modelbuilder
    return

def add_nodes(joints_df, mass_df, list_new_joints, dict_of_hinges):
    points_df = joints_df[joints_df.IsAuto == 'Yes'].copy()
    
    joints_df.apply(lambda row: op.node(row.UniqueName, row.X, row.Y, row.Z), axis='columns')
    joints_df.apply(lambda row: op.fix (row.UniqueName, *[int(r) for r in row.Restraints]), axis='columns')
    points_df.apply(lambda row: op.fix (row.UniqueName, *[0, 0, 1, 1, 1, 0]), axis='columns')
    
    op.constraints('Transformation')
    if rigid_dia:
        floor_list = set(joints_df[joints_df.Z > joints_df.Z.min()].Z)
        for floor in floor_list:
            nodes_list = list(joints_df.loc[joints_df.Z == floor]['UniqueName'])
            remove_list = list(set(nodes_list) & set(list_new_joints)) + list(dict_of_hinges.keys())
            nodes = [i for i in nodes_list if i not in remove_list] 
            op.rigidDiaphragm(3, *nodes)
    mass_df.apply(lambda row: op.mass(row.PointElm, row.UX, row.UY, row.UZ, row.RX, row.RY, row.RZ), axis = 'columns')
    return

def add_frames(frames_df, frame_props_df):

    def determine_tag(label):
        if 'C' in label:
            tag = col_transf_tag
        else:
            tag = beam_transf_tag
        return tag
    
    op.geomTransf(coordTransf, col_transf_tag,  1, 0, 0)
    op.geomTransf(coordTransf, beam_transf_tag, 0, 0, 1)
    frames_df[frames_df.Angle == 0.00].apply(lambda row: op.element('ElasticTimoshenkoBeam'     , row.UniqueName,                           \
                                                         row.PointI                             , row.PointJ,                               \
                                                         E, G                                   , frame_props_df.loc[row.Prop, 'Area'],     \
                                                         frame_props_df.loc[row.Prop, 'J']      , frame_props_df.loc[row.Prop, 'I33'] ,     \
                                                         frame_props_df.loc[row.Prop, 'I22']    , frame_props_df.loc[row.Prop, 'As3'] ,     \
                                                         frame_props_df.loc[row.Prop, 'As2']    , determine_tag(row.Label)            ,     \
                                                         '-mass'                                , M, massType), axis='columns')
    frames_df[frames_df.Angle == 90.0].apply(lambda row: op.element('ElasticTimoshenkoBeam'     , row.UniqueName,                           \
                                                         row.PointI                             , row.PointJ,                               \
                                                         E, G                                   , frame_props_df.loc[row.Prop, 'Area'],     \
                                                         frame_props_df.loc[row.Prop, 'J']      , frame_props_df.loc[row.Prop, 'I22'] ,     \
                                                         frame_props_df.loc[row.Prop, 'I33']    , frame_props_df.loc[row.Prop, 'As2'] ,     \
                                                         frame_props_df.loc[row.Prop, 'As3']    , determine_tag(row.Label)            ,     \
                                                         '-mass'                                , M, massType), axis='columns')
    return

def add_nodal_loads(loads_df):
    op.timeSeries('Linear', 1) # create TimeSeries
    op.pattern('Plain', 1, 1)  # create a plain load pattern
    loads_df.apply(lambda row: op.load(*row[['UniqueName', 'F1', 'F2', 'F3', 'M1', 'M2', 'M3']].tolist()), axis='columns')
    return

def modal_response(numEigen):
    # calculate eigenvalues    
    eigenValues = op.eigen('-genBandArpack', numEigen) # one of: '-genBandArpack', '-fullGenLapack'
    return eigenValues

# POST-PROCESS MODEL
def plot_opensees_mode_shapes():
    opp.plot_model()
    for i in range(1, numEigen+1):
        opp.plot_modeshape(i, 50)
    return

def add_beam_hinges(dict_of_hinges, dict_of_hinges_2):
    
    data = read_nonlinear_hinge_properties()
    
    """
    dict_of_hinges = {real joint: (new joint, zero length element ID, orientation)}
    """
    
    for key, value in dict_of_hinges.items():
        node_R = key
        node_C = value[0]
        matTag = value[1]
        dirn = value[2]
        
        row = data.loc[data['Hinge NAME'] == dict_of_hinges_2[matTag]]
        K0 = row['K0'].values[0]
        as_Plus = row['as_Plus'].values[0]
        as_Neg = row['as_Neg'].values[0]
        My_Plus = row['My_Plus'].values[0]
        My_Neg = row['My_Neg'].values[0]
        Lamda_S = row['Lamda_S'].values[0]
        Lamda_C = row['Lamda_C'].values[0]
        Lamda_A = row['Lamda_A'].values[0]
        Lamda_K = row['Lamda_K'].values[0]
        c_S = row['c_S'].values[0]
        c_C = row['c_C'].values[0]
        c_A = row['c_A'].values[0]
        c_K = row['c_K'].values[0]
        theta_p_Plus = row['theta_p_Plus'].values[0]
        theta_p_Neg = row['theta_p_Neg'].values[0]
        theta_pc_Plus = row['theta_pc_Plus'].values[0]
        theta_pc_Neg = row['theta_pc_Neg'].values[0]
        Res_Pos = row['Res_Pos'].values[0]
        Res_Neg = row['Res_Neg'].values[0]
        theta_u_Plus = row['theta_u_Plus'].values[0]
        theta_u_Neg = row['theta_u_Neg'].values[0]
        D_Plus = row['D_Plus'].values[0]
        D_Neg = row['D_Neg'].values[0]
        nFactor = row['nFactor'].values[0]
        
        op.uniaxialMaterial('Bilin'     ,   matTag      ,   K0          ,   as_Plus         ,   as_Neg      ,   My_Plus ,   My_Neg      ,
                            Lamda_S     ,   Lamda_C     ,   Lamda_A     ,   Lamda_K         ,   c_S         ,   c_C     ,   c_A         ,
                            c_K         ,   theta_p_Plus,   theta_p_Neg ,   theta_pc_Plus   ,   theta_pc_Neg,   Res_Pos ,   Res_Neg     ,
                            theta_u_Plus,   theta_u_Neg ,   D_Plus      ,   D_Neg           ,   nFactor
                            )
        
        op.element('zeroLength', matTag, node_R, node_C, '-mat', matTag, '-dir', dirn, '-doRayleigh', 1)
        op.equalDOF(node_R, node_C, 1,2,3,int(9-dirn),6)
        op.region(key, matTag)
    return

def setup_recorders(dict_of_disp_nodes, dict_of_rxn_nodes, dict_of_hinges, initialOrTangent, parent_dir):
    # set up node displacement recorders   
    dict_of_disp_nodes = [61, 62, 63, 64, 65, 241, 242, 243, 244, 245]
    for node in dict_of_disp_nodes:
        op.recorder('Node', '-file', f'node_{node}_disp_{initialOrTangent}.out', '-node', node, '-dof', 1,2,3,4,5,6, 'disp')
        
    # set up node rxn recorders    
    for node in dict_of_rxn_nodes.keys():
        op.recorder('Node', '-file', f'node_{node}_rxn_{initialOrTangent}.out', '-node', node, '-dof', 1,2,3,4,5,6, 'reaction')
    
    # setup rot spring recorders
    list_of_hinges = [20271, 20275, 20279, 20283, 20253, 20672, 20673, 20674, 20675, 20676]
    for rec in list_of_hinges:
        op.recorder('Element', '-file', f'ele_def_{rec}_{initialOrTangent}.out', '-ele', rec, 'deformations')
        op.recorder('Element', '-file', f'ele_frc_{rec}_{initialOrTangent}.out', '-ele', rec, '-dof', 1,2,3,4,5,6, 'force')
    return

def read_nonlinear_hinge_properties():
    """
    This function creates a uniaxial material spring with deterioration
    Spring follows: Bilinear Response based on Modified Ibarra Krawinkler Deterioration Model 
    Written by: Dimitrios G. Lignos, Ph.D.
    
    matTag              integer tag identifying material
    K0                  elastic  stiffness
    as_Plus             strain hardening ratio for positive loading direction
    as_Neg              strain hardening ratio for negative loading direction
    My_Plus             effective yield strength for positive loading direction
    My_Neg              effective yield strength for negative loading direction (negative value)
    Lamda_S             Cyclic deterioration parameter for strength deterioration
    Lamda_C             Cyclic deterioration parameter for post-capping strength deterioration
    Lamda_A             Cyclic deterioration parameter for acceleration reloading stiffness deterioration (is not a deterioration mode for a component with Bilinear hysteretic response).
    Lamda_K             Cyclic deterioration parameter for unloading stiffness deterioration
    c_S                 rate of strength deterioration. The default value is 1.0.
    c_C                 rate of post-capping strength deterioration. The default value is 1.0.
    c_A                 rate of accelerated reloading deterioration. The default value is 1.0.
    c_K                 rate of unloading stiffness deterioration. The default value is 1.0.
    theta_p_Plus        pre-capping rotation for positive loading direction (often noted as plastic rotation capacity)
    theta_p_Neg         pre-capping rotation for negative loading direction (often noted as plastic rotation capacity) (positive value)
    theta_pc_Plus       post-capping rotation for positive loading direction
    theta_pc_Neg        post-capping rotation for negative loading direction (positive value)
    Res_Pos             residual strength ratio for positive loading direction
    Res_Neg             residual strength ratio for negative loading direction (positive value)
    theta_u_Plus        ultimate rotation capacity for positive loading direction
    theta_u_Neg         ultimate rotation capacity for negative loading direction (positive value)
    D_Plus              rate of cyclic deterioration in the positive loading direction (this parameter is used to create assymetric hysteretic behavior for the case of a composite beam). For symmetric hysteretic response use 1.0.
    D_Neg               rate of cyclic deterioration in the negative loading direction (this parameter is used to create assymetric hysteretic behavior for the case of a composite beam). For symmetric hysteretic response use 1.0.
    nFactor             elastic stiffness amplification factor, mainly for use with concentrated plastic hinge elements (optional, default = 0).
    """
    
    # read properties from Excel
    data = pd.read_excel(os.path.join(os.path.dirname(os.getcwd()), 'worksheets', 'NL Properties Summary.xlsx'), sheet_name = 'WUF hinge')
    data.drop(columns = ['IO (θy)','LS (θy)','CP (θy)', 'Beam Standard Section?'], inplace = True)
    
    # generate properties for OpenSees Input
    data['K0'] = 1e7
#    data.loc[data['Beam Section'].isin(['W24X68', 'W24X84']), 'K0'] = 1e6

    data['as_Plus'] = (data["FU (k-in)"] - data["FY (k-in)"]) / data["DL (θy)"] / data['K0']
    # data['as_Plus']   = 0.0
    data['as_Neg'] = data['as_Plus']
    
    data['My_Plus'] = data["FY (k-in)"].astype(float)
    data['My_Neg'] = - data["FY (k-in)"].astype(float)
    
    data['Lamda_S'] = 1000.0   # ignore degradation
    data['Lamda_C'] = 1000.0   # ignore degradation
    data['Lamda_A'] = 1000.0   # ignore degradation
    data['Lamda_K'] = 1000.0   # ignore degradation
    
    data['c_S'] = 1.0
    data['c_C'] = 1.0
    data['c_A'] = 1.0
    data['c_K'] = 1.0
    
    data['theta_p_Plus'] = data["DL (θy)"] - data['My_Plus'] / data['K0']
    data['theta_p_Neg'] = data["theta_p_Plus"]
    
    data['theta_pc_Plus'] = (data["DR (θy)"] - data["DL (θy)"]) / (1 - data["FR/FU"])
    data['theta_pc_Neg'] = data['theta_pc_Plus']
    
    data['Res_Pos'] = data["FR/FU"]
    data['Res_Neg'] = data["FR/FU"]
    
    data['theta_u_Plus'] = 0.2
    data['theta_u_Neg'] = 0.2
    
    data['D_Plus'] = 1.0
    data['D_Neg'] = 1.0
    
    data['nFactor'] = 0.0
    
    return data

def run_dynamic_analysis_w_rayleigh_damping(dict_of_hinges, dict_of_disp_nodes, dict_of_rxn_nodes, zeta, initialOrTangent='initial', parent_dir=os.getcwd()):
    op.wipeAnalysis ()
    
    op.timeSeries('Path', 2, '-dt', 0.01, '-filePath', 'BM68elc.acc', '-factor', 3.0*g)
    op.pattern('UniformExcitation', 2, 1, '-accel', 2)
    
#    op.timeSeries('Path', 3, '-dt', 0.01, '-filePath', 'BM68elc.acc', '-factor', 1.0*g)
#    op.pattern('UniformExcitation', 3, 2, '-accel', 3)
    
    op.constraints('Transformation')
    op.numberer('RCM')
    op.system('UmfPack')
#    op.test('NormDispIncr', 1e-2, 100000, 0, 0)
    op.test('EnergyIncr', 1e-4, 1e4, 0, 2)

    backup_algos = {'Modified Newton w/ Initial Stiffness': ['ModifiedNewton', '-initial'],
                    'Newton with Line Search': ['NewtonLineSearch', 'tol', 1e-3, 'maxIter', 1e5, 'maxEta', 10, 'minEta', 1e-2],
                    }    
    op.algorithm('KrylovNewton', 'maxDim', 3)
    
    alpha = 0.67
    op.integrator('HHT', alpha)
#    op.integrator('Newmark', 0.5, 0.25)

    op.analysis('Transient')
    
    eigenValues = modal_response(numEigen)
    periods = 2 * math.pi / np.sqrt(eigenValues)

    w1 = (eigenValues[0]**0.5)
    w2 = (eigenValues[0]**0.5)/0.384
    a0 = zeta*2*w1*w2/(w1+w2)
    a1 = zeta*2/(w1+w2)
    
    print('\nRayleigh Damping Coefficients:')
    print(f'\talpha: {a0}')
    print(f'\tbeta : {a1}\n')
    
    if initialOrTangent == 'tangent':
        op.rayleigh(a0, a1, 0, 0)
    else: 
        op.rayleigh(a0, 0, a1, 0)
    
    setup_recorders(dict_of_disp_nodes, dict_of_rxn_nodes, dict_of_hinges, initialOrTangent, parent_dir)
    
#    op.analyze(5000, 0.01)
    
    total_run_time = 50 # seconds
    time_step = 0.01 # seconds
    total_num_of_steps = total_run_time / time_step
    
    failed = 0
    time = 0
    algo = 'Krylov-Newton'
    pbar = tqdm(total=total_num_of_steps)
    
    # execution loop
    while time <= total_run_time and failed == 0:
        failed = op.analyze(1, time_step)
        
        if failed:
            print(f'\n{algo} failed. Trying other algorithms...')
            
            for alg, algo_args in backup_algos.items():
                print(f'\nTrying {alg}...')
                op.algorithm(*algo_args)
                failed = op.analyze(1, time_step)
                
                if failed:
                    continue
                else:
                    algo = 'Krylov-Newton'
                    print(f'\n{alg} worked.\n\nMoving back to {algo}')
                    op.algorithm('KrylovNewton', 'maxDim', 3)
                    break
                
            print(''.center(100, '-'))
            
        pbar.update(1)
        time = op.getTime()
    
    op.wipe()
    
    # move output files to results directory
    list_of_out_files = [fname for fname in os.listdir() if fname.endswith('.out')]
    for fname in list_of_out_files:
        shutil.move(os.path.join(os.getcwd(), fname), os.path.join(parent_dir, fname))
    
    return periods, eigenValues

def perform_modal_analysis_and_comparison(etabs_periods):
    eigenValues = modal_response(len(etabs_periods))
    periods = 2 * math.pi / np.sqrt(eigenValues)
    
    # compare modal analysis results
    print('\nETABS Periods: ')
    print(etabs_periods)
    print('\nOpenSees Periods: ')
    print([round(n, 3) for n in list(periods)])
    print('\nAgreement: (ETABS Periods/OpenSees Periods)')
    print(etabs_periods/periods)
    op.wipeAnalysis()
    return

def run_opensees_model(dict_of_hinges={}, dict_of_disp_nodes={}, dict_of_rxn_nodes={}, zeta=0.05, initialOrTangent='', parent_dir=os.getcwd()):
#    opp.plot_model()
    periods, eigenValues = run_dynamic_analysis_w_rayleigh_damping(dict_of_hinges, dict_of_disp_nodes, dict_of_rxn_nodes, zeta, initialOrTangent, parent_dir)
    return periods, eigenValues

# SETUP OPENSEES MODEL
def setup_opensees_model(joints_df, frames_df, frame_props_df, pts_loads_df, mass_df, dict_of_hinges, dict_of_hinges_2, list_new_joints):
    initiate_model()
    add_nodes(joints_df.copy(), mass_df.copy(), list_new_joints, dict_of_hinges)
    add_frames(frames_df.copy(), frame_props_df.copy())
    add_beam_hinges(dict_of_hinges, dict_of_hinges_2)
    return
