# -*- coding: utf-8 -*-
"""
Created on Sun Aug  2 16:40:54 2020

@author: asinghania
"""

import os, numpy as np, pandas as pd

COLS        = ['FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']
COL_DICT    = {i:col for i, col in zip(range(6), COLS)}



def post_process(analysis, initialOrTangent, dir_):
    if 'rayleigh' in analysis:
        fpath       = os.path.join(os.getcwd(), dir_, 'ele_frc_20279_' + initialOrTangent + '.out')
        fpath2      = os.path.join(os.getcwd(), dir_, 'ele_def_20279_' + initialOrTangent + '.out')
    else:
        fpath       = os.path.join(os.getcwd(), dir_, 'ele_frc_20279.out')
        fpath2      = os.path.join(os.getcwd(), dir_, 'ele_def_20279.out')
        
    df          = pd.DataFrame([s.split() for s in open(fpath, 'r').readlines()])
    df['RY']    = pd.DataFrame([s.split() for s in open(fpath2, 'r').readlines()])[0]
    df          = df.astype(float).rename(columns=COL_DICT)
    
    ax          = df.plot(x='RY', y='MY', grid=True, figsize=(15,5))
    ax.set_axisbelow(True)
    
    df.to_excel(os.path.join(os.getcwd(), dir_, 'hinge_hyst-' + analysis + '-' + initialOrTangent + '.xlsx'))
    return df.copy()

def base_shear(analysis, dir_, dict_of_rxn_nodes, initialOrTangent):
    df_shear_x      = pd.DataFrame(columns = [])
    df_shear_x['t'] = np.arange(0,50.01,0.01)
    df_shear_y      = df_shear_x.copy()
    
    for rxn_node in dict_of_rxn_nodes:
        fpath           = os.path.join(os.getcwd(), dir_, 'node_' + str(rxn_node) + '_rxn_' + initialOrTangent + '.out')
        df              = pd.DataFrame([s.split() for s in open(fpath, 'r').readlines()])
        df              = df.astype(float).rename(columns=COL_DICT)
        
        df_shear_x['X - '+ str(rxn_node)]    = df.FX
        df_shear_y['Y - '+ str(rxn_node)]    = df.FY
        
    df_shear_x['Vx'] = df_shear_x.sum(axis = 1)
    df_shear_y['Vy'] = df_shear_y.sum(axis = 1)
    
    df_shear_x.to_excel(os.path.join(os.getcwd(), dir_, 'base shear x-' + analysis + '-' + initialOrTangent + '.xlsx'))
    df_shear_y.to_excel(os.path.join(os.getcwd(), dir_, 'base shear y-' + analysis + '-' + initialOrTangent + '.xlsx'))
    
    return
        