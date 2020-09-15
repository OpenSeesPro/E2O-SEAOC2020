from PyCSI import getSapModelFromEtabs
import pandas as pd, numpy as np

def set_load_cases_selected_for_display(loadCaseList, SapModel = getSapModelFromEtabs(True)):
    return SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay(loadCaseList)

def set_load_combo_selected_for_display(loadComboList, SapModel = getSapModelFromEtabs(True)):
    return SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay(loadComboList)

def set_load_patterns_selected_for_display(loadPatternList, SapModel = getSapModelFromEtabs(True)):
    return SapModel.DatabaseTables.SetLoadPatternsSelectedForDisplay(loadPatternList)

def deselect_all_load_cases_and_combos_for_output(SapModel = getSapModelFromEtabs(True)):
    return [bool(~set_load_cases_selected_for_display('', SapModel)[-1]), 
            bool(~set_load_combo_selected_for_display('', SapModel)[-1]),]

def get_database_table_for_all_load_cases_and_combos(table_title, SapModel):

    # # connect to ETABS model
    # SapModel = getSapModelFromEtabs(True)
    # SapModel.SetPresentUnits(4)
    
    # get lists of all load cases and combinations
    try:
        listOfLoadCases     = [i for i in list(SapModel.LoadCases.GetNameList()[-2]) if '~' not in i]
    except:
        listOfLoadCases     = []
        
    try:
        listOfLoadCombos    = list(SapModel.RespCombo.GetNameList()[-2])
    except:
        listOfLoadCombos    = []
    
    # select all laod cases and combinations for output
    SapModel.DatabaseTables.SetLoadCombinationsSelectedForDisplay   (listOfLoadCombos)
    SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay          (listOfLoadCases)
    
    # get table from API
    ret     = SapModel.DatabaseTables.GetTableForDisplayArray(table_title, '', '')
    
    # develop DataFrame
    headers = list(ret[2])
    data    = np.array(ret[4])
    data    = data.reshape(len(data)//len(headers), len(headers))
    df      = pd.DataFrame(data)
    
    cols_dict = dict(zip(df.columns.tolist(), headers))
    df.rename(cols_dict, axis = 'columns', inplace = True)
    
    return df.copy()

# # CONNECT TO ETABS #
# SapModel            = getSapModelFromEtabs(True)
# SapModel.SetPresentUnits(3)
# mass_df = get_database_table_for_all_load_cases_and_combos('Diaphragm Center of Mass Displacements', SapModel)