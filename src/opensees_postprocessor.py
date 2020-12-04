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
        This script is used to post-process the data generated through analyses
        in OpenSees.

'''

import os
import numpy as np 
import pandas as pd

COLS = ['FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']
COL_DICT = {i:col for i, col in zip(range(6), COLS)}

def post_process(initialOrTangent, dir_):
    fpath = os.path.join(dir_, f'ele_frc_20279_{initialOrTangent}.out')
    fpath2 = os.path.join(dir_, f'ele_def_20279_{initialOrTangent}.out')
        
    df = pd.DataFrame([s.split() for s in open(fpath, 'r').readlines()])
    df['RY'] = pd.DataFrame([s.split() for s in open(fpath2, 'r').readlines()])[0]
    df = df.astype(float).rename(columns=COL_DICT)
    
    ax = df.plot(x='RY', y='MY', grid=True, figsize=(15,5))
    ax.set_axisbelow(True)
    
    df.to_excel(os.path.join(dir_, f'hinge_hyst-{initialOrTangent}.xlsx'))
    return df.copy()

def base_shear(dir_, dict_of_rxn_nodes, initialOrTangent):
    df_shear_x = pd.DataFrame(columns = [])
    df_shear_x['t'] = np.arange(0,50.01,0.01)
    df_shear_y = df_shear_x.copy()
    
    for rxn_node in dict_of_rxn_nodes:
        fpath = os.path.join(dir_, 'node_' + str(rxn_node) + '_rxn_' + initialOrTangent + '.out')
        df = pd.DataFrame([s.split() for s in open(fpath, 'r').readlines()])
        df = df.astype(float).rename(columns=COL_DICT)
        
        df_shear_x[f'X - {rxn_node}'] = df.FX
        df_shear_y[f'Y - {rxn_node}'] = df.FY
        
    df_shear_x['Vx'] = df_shear_x.sum(axis = 1)
    df_shear_y['Vy'] = df_shear_y.sum(axis = 1)
    
    df_shear_x.to_excel(os.path.join(dir_, f'base shear x-{initialOrTangent}.xlsx'))
    df_shear_y.to_excel(os.path.join(dir_, f'base shear y-{initialOrTangent}.xlsx'))
    
    return
        