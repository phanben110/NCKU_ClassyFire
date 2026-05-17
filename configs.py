import json

# Load config from JSON file
with open("msdial_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Assign config values to variables
import json
import os

# Uses absolute path to ensure it reads the correct file in the same directory
config_path = os.path.join(os.path.dirname(__file__), "msdial_config.json")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Using .get() prevents KeyError by returning None or a default value if missing
app_path = config.get("app_path")
project_file_path = config.get("project_file_path")
folder_analysis_path = config.get("folder_analysis_path")
raw_files_to_select = config.get("raw_files_to_select", [])
folders_to_select = config.get("folders_to_select", [])

ionization = config.get("ionization")
separation = config.get("separation")
collision = config.get("collision")
data_ms1 = config.get("data_ms1")
data_type_msms = config.get("data_type_msms")
ion = config.get("ion")
target_omics = config.get("target_omics")

load_parameter_path = config.get("load_parameter_path")
library_path = config.get("library_path")

accu_mass_ms1 = config.get("accu_mass_ms1")
accu_mass_ms2 = config.get("accu_mass_ms2")

result_path = config.get("result_path") 
final_result_path = config.get("final_result_path")
