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
        This script is a utility script to perform tasks supporting scraping data
        from ETABS as well as creating model in OpenSees and running analysis.

'''

import comtypes.client
import sys
import time
import pandas as pd
import numpy as np

def get_model_from_etabs():
    try:
        # attach to a running instance of ETABS
        etabs = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
    except (OSError, comtypes.COMError):
        print("No running instance of the program found or failed to attach.")
        sys.exit(-1)
    return etabs.SapModel

def set_load_cases_selected_for_display(loadCaseList, model = get_model_from_etabs()):
    return model.DatabaseTables.SetLoadCasesSelectedForDisplay(loadCaseList)

def set_load_combo_selected_for_display(loadComboList, model = get_model_from_etabs()):
    return model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(loadComboList)

def set_load_patterns_selected_for_display(loadPatternList, model = get_model_from_etabs()):
    return model.DatabaseTables.SetLoadPatternsSelectedForDisplay(loadPatternList)

def deselect_all_load_cases_and_combos_for_output(model = get_model_from_etabs()):
    return [bool(~set_load_cases_selected_for_display('', model)[-1]), 
            bool(~set_load_combo_selected_for_display('', model)[-1]),]

def get_database_table_for_all_load_cases_and_combos(table_title, model=None):
    # connect to ETABS model
    if model is None:
        model = get_model_from_etabs(True)
    
    # set units to kip, in (default for OpenSees)
    model.SetPresentUnits(3)
    
    # get lists of all load cases and combinations
    try:
        listOfLoadCases = [i for i in list(model.LoadCases.GetNameList()[-2]) if '~' not in i]
    except:
        listOfLoadCases = []
        
    try:
        listOfLoadCombos = list(model.RespCombo.GetNameList()[-2])
    except:
        listOfLoadCombos = []
    
    # select all laod cases and combinations for output
    model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(listOfLoadCombos)
    model.DatabaseTables.SetLoadCasesSelectedForDisplay(listOfLoadCases)
    
    # get table from API
    ret = model.DatabaseTables.GetTableForDisplayArray(table_title, '', '')
    
    # develop DataFrame
    headers = list(ret[2])
    data = np.array(ret[4])
    data = data.reshape(len(data)//len(headers), len(headers))
    df = pd.DataFrame(data)
    
    cols_dict = dict(zip(df.columns.tolist(), headers))
    df.rename(cols_dict, axis = 'columns', inplace = True)
    
    return df.copy()

def start_time():
    print('Started at: ' + time.strftime('%a, %d %b %Y %H:%M:%S PST', time.localtime()))
    return time.time()

def end_time(start_time, final=True):
    end_time    = time.time()
    (mins, secs)= divmod(round(end_time - start_time, 0), 60)
    print(f'\nTime Elapsed: {mins} minute(s) {secs} second(s).\n')
    if final:
        print('Finished at: ' + time.strftime('%a, %d %b %Y %H:%M:%S PST', time.localtime()))
    return