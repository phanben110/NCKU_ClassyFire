# #App path
# app_path = r"C:\Users\user\Documents\TMIC\MSDIAL.v5.5.241113-net48\MSDIAL.exe"

# #Save project file
# project_file_path = r"C:\Users\user\Desktop\自動化檔案\data\projects"

# #Select Input folder paths
# folder_analysis_path = r"C:\Users\user\Documents\1209_pos_testUR"
# #C:\Users\user\Documents\1209_NEG_testUR
# #C:\Users\user\Documents\1209_pos_testUR
# #C:\Users\user\Documents\1211_POS_testBL

# #Select input folder (Input of MS-DIAL: Only name of folder)
# folders_to_select = ["POOL_POS1209_LIU_54_01_2081.d","QC_40PPB_4_95_01_2091.d","UR2_POS1209_WEI_38_01_2086.d","POOL_POS1209_WEI_42_01_2090.d"]

# #Step 6: Set parameters
# ionization = "Soft ionization"  #Opts: "Soft ionization", "Hard ionization"
# separation = "Chromatography" #Opts: "Chromatography", "Direct infusion" 
# collision = "CID/HCD" #Opts: "CID/HCD", "ECD", "HotECD", "EIEIO", "EID", "OAD"
# data_ms1 = "Centroid data" #Opts: "Profile data", "Centroid data"
# data_type_msms = "Centroid data" #Opts: "Profile data", "Centroid data"
# ion = "Positive ion mode" #Opts: "Positive ion mode", "Negative ion mode"
# target_omics = "Metabolomics" #Opts: "Metabolomics", "Lipidomics", "Proteomics"

# #Choose libary path
# library_path = r"C:\Users\user\Desktop\自動化檔案\Database"
# #Save output
# result_path = r"C:\Users\user\Desktop\自動化檔案\data"

import json

# Load config from JSON file
with open("msdial_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Assign config values to variables
app_path = config["app_path"]
project_file_path = config["project_file_path"]
folder_analysis_path = config["folder_analysis_path"]
folders_to_select = config["folders_to_select"]

ionization = config["ionization"]
separation = config["separation"]
collision = config["collision"]
data_ms1 = config["data_ms1"]
data_type_msms = config["data_type_msms"]
ion = config["ion"]
target_omics = config["target_omics"]

library_path = config["library_path"]
result_path = config["result_path"]

# Optional: print to check values
print("App Path:", app_path)
print("Selected Folders:", folders_to_select)
