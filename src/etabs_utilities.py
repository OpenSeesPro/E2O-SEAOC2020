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
        
    Description of the script - 
        This is a supporting script for the main.py (user should execute main.py)
        This script is used to scrape data from ETABS and process it in a suitable 
        format to help generate the OpenSees model
'''

import pandas as pd
import math
from general_utilities import get_database_table_for_all_load_cases_and_combos as get_dbtable, get_model_from_etabs

# DEFINE DATAFRAME COLUMNS
JOINT_DATA_COLS = ['UniqueName', 'X', 'Y', 'Z']
FRAME_DATA_COLS = ['UniqueName', 'Prop'    , 'Story'   , 'PointI', 'PointJ'    , 'PointIX' , 'PointIY', 'PointIZ',
                   'PointJX'   , 'PointJY' , 'PointJZ' , 'Angle' , 'OffsetIX'  , 'OffsetJX', 'OffsetIY',
                   'OffsetJY'  , 'OffsetIZ', 'OffsetJZ', 'CardinalPt']
PT_LOADS_DATA_COLS = ['UniqueName', 'LoadPattern' , 'Step', 'CSys', 'F1', 'F2', 'F3', 'M1', 'M2', 'M3']
FRAME_PROP_COLS = ['Name', 'Material', 'Shape', 'Area', 'As2', 'As3', 'J', 'I22', 'I33', 'S22Pos', 'S33Pos', 'Z22', 
                   'Z33', 'R22', 'R33', 'I3Mod']
FRAME_PROP_COLS_2 = ['Area', 'As2', 'As3', 'Torsion', 'I22', 'I33', 'S22', 'S33', 'Z22', 'Z33', 'R22', 'R33']

# EXTRACT JOINT CONNECTIVITY DATA FROM ETABS MODEL
def get_joints(model=None):
    if model is None:
        model = get_model_from_etabs()
    
    # extract the point object connectivity from etabs using the get_dbtable method
    joints_df = get_dbtable('Point Object Connectivity', model)
    # extract the point object restraints from etabs
    joints_df['Restraints'] = joints_df.apply(lambda row: model.PointObj.GetRestraint(row.UniqueName)[0], axis='columns')
    
    # get the maximum numberical joint ID, this is required to name various new objects while modeling nonlinearity in OpenSees 
    max_jointID = max(joints_df[joints_df.UniqueName.str.isdigit()].UniqueName.astype('int').tolist())
    constant_joint = 10**(int(math.log10(max_jointID))+2)
    constant_eleID = 2 * constant_joint
    
    dict_of_hinges = {}     # key - real joint; value - new joint, zero element ID
    dict_of_hinges_1 = {}   # key - 'N' + real joint; value - real joint, new joint, zero element ID
    list_new_joints = []
    
    # list of joints where nonlinearity is introduced (link defined in ETBAS are connected to two joints one is digital 
    # say xx then other is Nxx). We would first like to extract all joints with UniqueName non-Digit (prefix: "N"). We would 
    # then use these nodes to create new node names for OpenSees model using the constant_joint to name the ID and coordinate 
    # of the xx joint to plate the new joint. (OpenSees need the two joints in the same location for defining a zero-length element). 
    dummy_joints = joints_df[~joints_df.UniqueName.str.isdigit()].UniqueName.tolist()

    # this loop go through all the joints and modifies the dummy joint with prefix "N" to the new joint in OpenSees
    for index, row in joints_df.iterrows():
        if row.UniqueName in dummy_joints:
            real_joint = int(str(row.UniqueName)[1:]) 
            new_joint = real_joint + constant_joint
            
            if joints_df.loc[joints_df.UniqueName == str(real_joint), 'X'].astype(float).values[0] == \
               joints_df.loc[joints_df.UniqueName == row.UniqueName, 'X'].astype(float).values[0]:
                zle_dirn = 4
            else:
                zle_dirn = 5
                
            list_new_joints.append(new_joint)
            new_element = real_joint + constant_eleID
            joints_df.loc[index, 'UniqueName'] = new_joint
            joints_df.loc[index, 'X'] = joints_df[joints_df.UniqueName == str(real_joint)]['X'].tolist()[0]
            joints_df.loc[index, 'Y'] = joints_df[joints_df.UniqueName == str(real_joint)]['Y'].tolist()[0]
            joints_df.loc[index, 'Z'] = joints_df[joints_df.UniqueName == str(real_joint)]['Z'].tolist()[0]
            dict_of_hinges[real_joint] = (new_joint, new_element, zle_dirn)
            dict_of_hinges_1['N'+str(real_joint)] = (real_joint, new_joint, new_element)

    
    joints_df = joints_df.astype({'UniqueName': int, 'X': float, 'Y': float, 'Z': float})
    return joints_df.copy(), dict_of_hinges, dict_of_hinges_1, list_new_joints

# EXTRACT NODAL LOADS FROM ETABS
def get_pt_loads(model=None):
    if model is None:
        model = get_model_from_etabs(True)
    
    joints_df, dict_of_hinges, dict_of_hinges_1, list_new_joints = get_joints(model)
    
    # Initialize a dataframe to store the point loads
    pts_loads_df = pd.DataFrame(columns=PT_LOADS_DATA_COLS)
    
    # Iterate through the joints to get the loads from etabs if any
    for index, row in joints_df.iterrows():
        try:
            pt_loads_df = pd.DataFrame.from_dict({col:val for (col,val) in zip(PT_LOADS_DATA_COLS, model.PointObj.GetLoadForce(str(row.UniqueName))[1:-1])})
        except:
            continue
        pts_loads_df = pts_loads_df.append(pt_loads_df, ignore_index=True)
    
    pts_loads_df = pts_loads_df.astype({'UniqueName' : int, })
    
    # filter out only the dead load
    pts_loads_df = pts_loads_df[pts_loads_df.LoadPattern == 'Dead'].copy()
    
    return pts_loads_df.copy()

# EXTRACT FRAME CONNECTIVITY FROM ETABS
def get_frames(dict_of_hinges_1, model=None):
    if model is None:
        model = get_model_from_etabs(True)
    
    # Extract all frame labels from etabs
    frame_label_data = model.FrameObj.GetLabelNameList()
    frame_labels_df = pd.DataFrame.from_dict({col:val for (col,val) in zip(['UniqueName', 'Label', 'Story'], frame_label_data[1:-1])})
    
    # get all frame objects from etabs
    frame_data = model.FrameObj.GetAllFrames()
    frames_df = pd.DataFrame.from_dict({col:val for (col,val) in zip(FRAME_DATA_COLS, frame_data [1:-1])})
    frames_df['Label'] = frames_df['UniqueName'].replace(frame_labels_df.set_index('UniqueName')['Label'])
    
    # Dictionary to get NL properties for the zero length element
    dict_of_hinges_2 = {}
    
    # update joint Names by iterating through each frames and chenging the names of both I & J nodes if required
    for index, row in frames_df.iterrows():
        # check if point I has been renmaed
        if row.PointI in dict_of_hinges_1.keys():
            dict_of_hinges_2[dict_of_hinges_1[row.PointI][2]]        = frames_df.loc[index, 'Prop']
            # replace the node with new joint
            frames_df.loc[index, 'PointI'] = dict_of_hinges_1[row.PointI][1]
            
        # check if point J has been renamed 
        if row.PointJ in dict_of_hinges_1.keys():
            dict_of_hinges_2[dict_of_hinges_1[row.PointJ][2]]        = frames_df.loc[index, 'Prop']
            # replace the node with new joint
            frames_df.loc[index, 'PointJ'] = dict_of_hinges_1[row.PointJ][1]
    
    frames_df = frames_df.astype({'UniqueName': int, 'PointI' : int, 'PointJ' : int})
    return frames_df.copy(), dict_of_hinges_2

# EXTRACT NODAL MASSES FROM ETABS
def get_nodal_masses(model=None):
    if model is None:
        model = get_model_from_etabs(True)
    
    # extract the assembled joint masses from etabs using the get_dbtable method
    mass_df = get_dbtable('Assembled Joint Masses', model)
    mass_df = mass_df.astype({'PointElm': int  , 'UX' : float, 'UY' : float, 'UZ' : float, 'RX' : float, 
                              'RY'      : float, 'RZ' : float, 'X'  : float, 'Y'  : float, 'Z'  : float})
    return mass_df.copy()

# EXTRACT FRAME SECTION PROPERTIES FROM ETABS
def get_frame_props(dict_of_hinges_1, model=None):
    if model is None:
        model = get_model_from_etabs(True)
    
    frames_df, dict_of_hinges_2 = get_frames(dict_of_hinges_1, model)
    
    # Initialize a dataframe to store the frame properties
    frame_props_df = pd.DataFrame(columns=FRAME_PROP_COLS_2)
    
    # iterate trough each fame to extract the frame properties if it does not already exists
    for index, row in frames_df.iterrows():
        
        # if the property exists then continue to next
        if row.Prop in frame_props_df.index:
            continue
        
        # if the property does not exist, extract from etabs and add to the dataframe using append
        frame_prop_df = pd.DataFrame.from_dict({row.Prop:{col:val for (col,val) in zip(FRAME_PROP_COLS_2, model.PropFrame.GetSectProps(row.Prop)[:-1])}}, orient='index')
        frame_props_df = frame_props_df.append(frame_prop_df)
        
    return frame_props_df.copy()

# EXTRACT FRAME SECTION PROPERTIES FROM ETBAS
def get_frame_props_from_db_table(model=None):
    
    FLOAT_COLS = ['Area', 'As2', 'As3', 'J', 'I22', 'I33', 'S22Pos', 'S33Pos', 'Z22', 'Z33', 'R22', 'R33', 'I3Mod']
    
    if model is None:
        model = get_model_from_etabs()
        
    # extract the frame section properties from etabs using the get_dbtable method
    frame_props_df = get_dbtable('Frame Section Property Definitions - Summary', model)[FRAME_PROP_COLS]
    
    # update the properties as per modifiers defined in ETABS
    frame_props_df['I33'] = frame_props_df['I33'].astype(float) * frame_props_df ['I3Mod'].astype(float)
    frame_props_df.set_index('Name', inplace=True)
    frame_props_df = frame_props_df.astype({col:'float' for col in FLOAT_COLS})
    return frame_props_df.copy()

# GET JOINTS WHERE REACTION NEEDS TO BE RECORDED AND WHERE DISPLACEMENT NEEDS TO BE RECORDED
def get_node_dicts(joints_df):
    
    # joints not on the lowest level are diaplcement nodes
    disp_joints_df = joints_df[joints_df.Z != joints_df.Z.min()].copy()
    
    # all joints at the lowest level are reaction nodes
    rxn_joints_df = joints_df[joints_df.Z == joints_df.Z.min()].copy()
    
    dict_of_disp_nodes = disp_joints_df[['UniqueName','X','Y','Z']].set_index('UniqueName').T.to_dict()
    dict_of_rxn_nodes = rxn_joints_df [['UniqueName','X','Y','Z']].set_index('UniqueName').T.to_dict()
    
    return dict_of_disp_nodes, dict_of_rxn_nodes

# EXTRACT MODAL ANALYSIS RESULTS FROM ETABS
def get_modal_results_from_etabs(model):
    
    # extract the Modal Participating Mass Ratio table from etabs using the get_dbtable method
    df = get_dbtable('Modal Participating Mass Ratios', model)
    etabs_periods = [round(n, 3) for n in df.Period.astype(float).tolist()[:4]]
    return etabs_periods

# MAIN FUNCTION TO OBTAIN ALL REQUIRED DATA FROM ETABS TO CREATE A OPENSEES MODEL
def get_etabs_data(model=None, units=None):
    
    if model is None:
        model = get_model_from_etabs()
        model.SetPresentUnits(units)
    
    # call different methods written above to extract and process data from ETABS
    joints_df, dict_of_hinges, dict_of_hinges_1, list_new_joints = get_joints(model)
    dict_of_disp_nodes, dict_of_rxn_nodes = get_node_dicts(joints_df.copy())
    pt_loads_df = get_pt_loads(model)
    frames_df, dict_of_hinges_2 = get_frames(dict_of_hinges_1, model)
    mass_df = get_nodal_masses(model)
    frame_props_df = get_frame_props_from_db_table(model)
    etabs_periods = get_modal_results_from_etabs(model)
    
    return joints_df, pt_loads_df, frames_df, mass_df, frame_props_df, dict_of_hinges, dict_of_hinges_2, list_new_joints, dict_of_disp_nodes, dict_of_rxn_nodes, etabs_periods
