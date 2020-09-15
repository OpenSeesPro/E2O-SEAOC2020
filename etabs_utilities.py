# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 09:21:11 2020

@author: PRANCHAL
"""
import pandas as pd, math
from PyCSI import getSapModelFromEtabs
from database_tables import get_database_table_for_all_load_cases_and_combos as get_dbtable

# DATAFRAME COLUMNS
JOINT_DATA_COLS     = ['UniqueName', 'X', 'Y', 'Z']
FRAME_DATA_COLS     = ['UniqueName', 'Prop'    , 'Story'   , 'PointI', 'PointJ'    , 'PointIX' , 'PointIY', 'PointIZ',
                       'PointJX'   , 'PointJY' , 'PointJZ' , 'Angle' , 'OffsetIX'  , 'OffsetJX', 'OffsetIY',
                       'OffsetJY'  , 'OffsetIZ', 'OffsetJZ', 'CardinalPt']
PT_LOADS_DATA_COLS  = ['UniqueName', 'LoadPattern' , 'Step', 'CSys', 'F1', 'F2', 'F3', 'M1', 'M2', 'M3']
FRAME_PROP_COLS     = ['Name', 'Material', 'Shape', 'Area', 'As2', 'As3', 'J', 'I22', 'I33', 'S22Pos', 'S33Pos', 'Z22', 'Z33', 'R22', 'R33', 'I3Mod']
FRAME_PROP_COLS_2   = ['Area', 'As2', 'As3', 'Torsion', 'I22', 'I33', 'S22', 'S33', 'Z22', 'Z33', 'R22', 'R33']

# JOINT CONNECTIVITY #
def get_joints(SapModel=None):
    if SapModel is None:
        SapModel = getSapModelFromEtabs(True)
    
    joints_df               = get_dbtable('Point Object Connectivity', SapModel)
    joints_df['Restraints'] = joints_df.apply(lambda row: SapModel.PointObj.GetRestraint(row.UniqueName)[0], axis='columns')
    
    max_jointID             = max(joints_df[joints_df.UniqueName.str.isdigit()].UniqueName.astype('int').tolist())
    constant_joint          = 10**(int(math.log10(max_jointID))+2)
    constant_eleID          = 2 * constant_joint
    
    dic_hinge               = {}        # key - real joint
                                        # value - new joint, zero element ID
    
    dic_hinge_1             = {}        # key - 'N' + real joint
                                        # value - real joint, new joint, zero element ID
    list_new_joints         = []
    
    dummy_joints            = joints_df[~joints_df.UniqueName.str.isdigit()].UniqueName.tolist()

    for index, row in joints_df.iterrows():
        if row.UniqueName in dummy_joints:
            real_joint                          = int(str(row.UniqueName)[1:]) 
            new_joint                           = real_joint + constant_joint
            
            if joints_df.loc[joints_df.UniqueName == str(real_joint), 'X'].astype(float).values[0] == joints_df.loc[joints_df.UniqueName == row.UniqueName, 'X'].astype(float).values[0]:
                zle_dirn = 4
            else:
                zle_dirn = 5
                
            list_new_joints.append(new_joint)
            new_element                         = real_joint + constant_eleID
            joints_df.loc[index, 'UniqueName']  = new_joint
            joints_df.loc[index, 'X']           = joints_df[joints_df.UniqueName == str(real_joint)]['X'].tolist()[0]
            joints_df.loc[index, 'Y']           = joints_df[joints_df.UniqueName == str(real_joint)]['Y'].tolist()[0]
            joints_df.loc[index, 'Z']           = joints_df[joints_df.UniqueName == str(real_joint)]['Z'].tolist()[0]
            dic_hinge[real_joint]               = (new_joint, new_element, zle_dirn)
            dic_hinge_1['N'+str(real_joint)]    = (real_joint, new_joint, new_element)

    
    joints_df               = joints_df.astype({'UniqueName': int, 'X': float, 'Y': float, 'Z': float})
    return joints_df.copy(), dic_hinge, dic_hinge_1, list_new_joints

# GET NODAL LOADS #
def get_pt_loads(SapModel=None):
    if SapModel is None:
        SapModel = getSapModelFromEtabs(True)
    
    joints_df, dic_hinge, dic_hinge_1, list_new_joints = get_joints(SapModel)
    
    pts_loads_df        = pd.DataFrame(columns=PT_LOADS_DATA_COLS)
    for index, row in joints_df.iterrows():
        try:
            pt_loads_df = pd.DataFrame.from_dict({col:val for (col,val) in zip(PT_LOADS_DATA_COLS, SapModel.PointObj.GetLoadForce(str(row.UniqueName))[1:-1])})
        except:
            continue
        pts_loads_df    = pts_loads_df.append(pt_loads_df, ignore_index=True)
    pts_loads_df        = pts_loads_df.astype({'UniqueName' : int, })
    
    pts_loads_df        = pts_loads_df[pts_loads_df.LoadPattern == 'Dead'].copy()
    
    return pts_loads_df.copy()

# FRAME CONNECTIVITY #
def get_frames(dic_hinge_1, SapModel=None):
    if SapModel is None:
        SapModel = getSapModelFromEtabs(True)
        
    frame_label_data    = SapModel.FrameObj.GetLabelNameList()
    frame_labels_df     = pd.DataFrame.from_dict({col:val for (col,val) in zip(['UniqueName', 'Label', 'Story'], frame_label_data[1:-1])})
    frame_data          = SapModel.FrameObj.GetAllFrames()
    
    frames_df           = pd.DataFrame.from_dict({col:val for (col,val) in zip(FRAME_DATA_COLS, frame_data [1:-1])})
    frames_df['Label']  = frames_df['UniqueName'].replace(frame_labels_df.set_index('UniqueName')['Label'])
    
    # dictionary to get NL properties for the ZLE
    dic_hinge_2 = {}
    
    # update joint Names
    for index, row in frames_df.iterrows():
        if row.PointI in dic_hinge_1.keys():
            dic_hinge_2[dic_hinge_1[row.PointI][2]]        = frames_df.loc[index, 'Prop']
            frames_df.loc[index, 'PointI'] = dic_hinge_1[row.PointI][1]     # replace the node with new joint
            
        
        if row.PointJ in dic_hinge_1.keys():
            dic_hinge_2[dic_hinge_1[row.PointJ][2]]        = frames_df.loc[index, 'Prop']
            frames_df.loc[index, 'PointJ'] = dic_hinge_1[row.PointJ][1]     # replace the node with new joint
    
    frames_df           = frames_df.astype({'UniqueName': int, 'PointI' : int, 'PointJ' : int})
    return frames_df.copy(), dic_hinge_2

# GET NODAL LOADS #
def get_nodal_masses(SapModel=None):
    if SapModel is None:
        SapModel = getSapModelFromEtabs(True)
        
    mass_df = get_dbtable('Assembled Joint Masses', SapModel)
    mass_df = mass_df.astype({'PointElm': int  , 'UX' : float, 'UY' : float, 'UZ' : float, 'RX' : float, 
                              'RY'      : float, 'RZ' : float, 'X'  : float, 'Y'  : float, 'Z'  : float})
    return mass_df.copy()

# FRAME SECTION PROPERTIES #
def get_frame_props(dic_hinge_1, SapModel=None):
    if SapModel is None:
        SapModel = getSapModelFromEtabs(True)
    
    frames_df, dic_hinge_2 = get_frames(dic_hinge_1, SapModel)
    
    frame_props_df      = pd.DataFrame(columns=FRAME_PROP_COLS_2)
    for index, row in frames_df.iterrows():
        if row.Prop in frame_props_df.index:
            continue
        frame_prop_df   = pd.DataFrame.from_dict({row.Prop:{col:val for (col,val) in zip(FRAME_PROP_COLS_2, SapModel.PropFrame.GetSectProps(row.Prop)[:-1])}}, orient='index')
        frame_props_df  = frame_props_df.append(frame_prop_df)
    return frame_props_df.copy()

# FRAME SECTION PROPERTIES #
def get_frame_props_from_db_table(SapModel=None):
    
    FLOAT_COLS = ['Area', 'As2', 'As3', 'J', 'I22', 'I33', 'S22Pos', 'S33Pos', 'Z22', 'Z33', 'R22', 'R33', 'I3Mod']
    
    if SapModel is None:
        SapModel = getSapModelFromEtabs(True)
    frame_props_df = get_dbtable('Frame Section Property Definitions - Summary', SapModel)[FRAME_PROP_COLS]
    frame_props_df['I33'] = frame_props_df['I33'].astype(float) * frame_props_df ['I3Mod'].astype(float)
    frame_props_df.set_index('Name', inplace=True)
    frame_props_df = frame_props_df.astype({col:'float' for col in FLOAT_COLS})
    return frame_props_df.copy()

def get_node_dicts(joints_df):
    
    disp_joints_df = joints_df[joints_df.Z != joints_df.Z.min()].copy()
    rxn_joints_df  = joints_df[joints_df.Z == joints_df.Z.min()].copy()
    
    dict_of_disp_nodes = disp_joints_df[['UniqueName','X','Y','Z']].set_index('UniqueName').T.to_dict()
    dict_of_rxn_nodes  = rxn_joints_df [['UniqueName','X','Y','Z']].set_index('UniqueName').T.to_dict()
    
    return dict_of_disp_nodes, dict_of_rxn_nodes

def get_etabs_data(SapModel=None, units=None):
    if SapModel is None:
        SapModel = getSapModelFromEtabs(True)
        SapModel.SetPresentUnits(units)
    
    joints_df, dic_hinge, dic_hinge_1, list_new_joints  = get_joints(SapModel)
    dict_of_disp_nodes, dict_of_rxn_nodes               = get_node_dicts(joints_df.copy())
    pt_loads_df                                         = get_pt_loads(SapModel)
    frames_df, dic_hinge_2                              = get_frames(dic_hinge_1, SapModel)
    mass_df                                             = get_nodal_masses(SapModel)
#    frame_props_df                                      = get_frame_props(dic_hinge_1, SapModel)
    frame_props_df                                      = get_frame_props_from_db_table(SapModel)
    
    return joints_df, pt_loads_df, frames_df, mass_df, frame_props_df, dic_hinge, dic_hinge_1, dic_hinge_2, list_new_joints, dict_of_disp_nodes, dict_of_rxn_nodes
    