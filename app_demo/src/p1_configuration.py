import streamlit as st
import pandas as pd
import json
import os
import logging
import warnings
from datetime import datetime
from app_demo.src.title import title_app

warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    filename='runtime.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Function to log access information
def log_access(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{current_time} - P1. Upload     - {message}")
    print(f"{current_time} - P1. Upload     - {message}")

# Function to upload and display Excel data
def upload_data(file_names=None, sample_count=None):
    log_access("upload data")
    show_configuration_page() 

# Configuration file path
CONFIG_FILE = "msdial_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "app_path": r"C:\Users\user\Downloads\MSDIAL.v5.5.250627-net48\MSDIAL.exe",
    "project_file_path": r"C:\Users\user\Desktop\自動化檔案\data\projects",
    "folder_analysis_path": r"C:\Users\user\Documents\1209_pos_testUR",
    "folders_to_select": [
        "POOL_POS1209_LIU_54_01_2081.d",
        "QC_40PPB_4_95_01_2091.d", 
        "UR2_POS1209_WEI_38_01_2086.d",
        "POOL_POS1209_WEI_42_01_2090.d"
    ],
    "ionization": "Soft ionization",
    "separation": "Chromatography",
    "collision": "CID/HCD", 
    "data_ms1": "Centroid data",
    "data_type_msms": "Centroid data",
    "ion": "Positive ion mode",
    "target_omics": "Metabolomics",
    "library_path": r"C:\Users\user\Desktop\自動化檔案\Database",
    "result_path": r"C:\Users\user\Desktop\自動化檔案\data\NCKU_ClassyFire\data\clean_result"
}

def load_config():
    """Load configuration from JSON file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to handle missing keys
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
        else:
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False

def scan_folder_for_d_files(folder_path):
    """Scan folder for directories with .d extension"""

    if not folder_path:
        return []

    # ✅ Remove leading/trailing quotes safely
    folder_path_fix = folder_path.strip().strip('"').strip("'")

    try:
        if not os.path.exists(folder_path_fix):
            return []

        d_folders = []
        for item in os.listdir(folder_path_fix):
            item_path = os.path.join(folder_path_fix, item)
            print(item_path)
            # Check if it's a directory and ends with .d
            if os.path.isdir(item_path) and item.lower().endswith('.d'):
                d_folders.append(item)
                print(f"Found .d folder: {item_path}")

        return sorted(d_folders)
    except Exception as e:
        st.warning(f"Error scanning folder: {e}")
        return []


def validate_raw_file_names(base_path, raw_file_names):
    """
    Validate if raw file names exist in the base path
    
    Args:
        base_path: Base directory path to check
        raw_file_names: List of raw file names (e.g., ["name_1", "name_2", "name_3"])
    
    Returns:
        tuple: (bool, list, str) - (is_valid, valid_folders, error_message)
    """
    if not raw_file_names:
        return False, [], "⚠️ No raw file names provided"
    
    valid_folders = []
    missing_folders = []
    
    for name in raw_file_names:
        name = name.strip()
        if not name:
            continue
            
        folder_name = name 
        base_path_fix = base_path[1:-1] if (base_path.startswith('"') and base_path.endswith('"')) else base_path
        folder_path = os.path.join(base_path_fix, f"{folder_name}.raw")
        print(folder_path)
        print(os.path.exists(folder_path))
        
        if os.path.exists(folder_path):
            valid_folders.append(folder_name)
        else:
            missing_folders.append(folder_name)
    
    if missing_folders:
        error_msg = f"❌ The following folders were not found:\n" + "\n".join([f"  • {f}" for f in missing_folders])
        return False, valid_folders, error_msg
    
    if not valid_folders:
        return False, [], "⚠️ No valid folders found"
    
    return True, valid_folders, f"✅ All {len(valid_folders)} folders found successfully"


def show_configuration_page():
    """Display the configuration page"""
    title_app("ClassyFire - MS-DIAL Configuration Setup")

    # Custom CSS for beautiful buttons and styling
    st.markdown("""
    <style>
    /* Main container width */
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Custom button styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(102, 126, 234, 0.4);
    }
    
    /* Section styling */
    .section-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #e0e6ed;
    }
    
    .section-header {
        color: #2c3e50;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    /* Section dividers */
    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 2px;
        margin: 2rem 0;
    }
    
    /* Info box styling */
    .folder-info {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #2196f3;
    }
    
    /* Success box */
    .success-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #4caf50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Load existing configuration
    current_config = load_config()
    
    # Initialize session state
    if 'app_path' not in st.session_state:
        st.session_state.app_path = current_config["app_path"]
    if 'project_file_path' not in st.session_state:
        st.session_state.project_file_path = current_config["project_file_path"]
    if 'folder_analysis_path' not in st.session_state:
        st.session_state.folder_analysis_path = current_config["folder_analysis_path"]
    if 'library_path' not in st.session_state:
        st.session_state.library_path = current_config["library_path"]
    if 'result_path' not in st.session_state:
        st.session_state.result_path = current_config["result_path"]
    if 'folders_to_select' not in st.session_state:
        st.session_state.folders_to_select = current_config.get("folders_to_select", [])
    if 'validation_message' not in st.session_state:
        st.session_state.validation_message = None
    if 'validation_type' not in st.session_state:
        st.session_state.validation_type = None
    if 'ionization' not in st.session_state:
        st.session_state.ionization = current_config["ionization"]
    if 'separation' not in st.session_state:
        st.session_state.separation = current_config["separation"]
    if 'collision' not in st.session_state:
        st.session_state.collision = current_config["collision"]
    if 'data_ms1' not in st.session_state:
        st.session_state.data_ms1 = current_config["data_ms1"]
    if 'data_type_msms' not in st.session_state:
        st.session_state.data_type_msms = current_config["data_type_msms"]
    if 'ion' not in st.session_state:
        st.session_state.ion = current_config["ion"]
    if 'target_omics' not in st.session_state:
        st.session_state.target_omics = current_config["target_omics"]

    # ==================== SECTION 1: APPLICATION PATHS ====================
    # st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📁 Application Paths</div>', unsafe_allow_html=True)
    
    app_path = st.text_input(
        "MS-DIAL Application Path",
        value=st.session_state.app_path,
        help="Path to the MS-DIAL executable file",
        key="input_app_path"
    )
    st.session_state.app_path = app_path
    
    project_file_path = st.text_input(
        "Project File Path",
        value=st.session_state.project_file_path,
        help="Directory for MS-DIAL project files",
        key="input_project_path"
    )
    st.session_state.project_file_path = project_file_path
    
    folder_analysis_path = st.text_input(
        "Analysis Folder Path",
        value=st.session_state.folder_analysis_path,
        help="Path to the folder containing data files to analyze",
        key="input_analysis_path"
    )
    st.session_state.folder_analysis_path = folder_analysis_path
    
    library_path = st.text_input(
        "Library Path",
        value=st.session_state.library_path,
        help="Path to the spectral library database",
        key="input_library_path"
    )
    st.session_state.library_path = library_path
    
    result_path = st.text_input(
        "Result Output Path",
        value=st.session_state.result_path,
        help="Directory where analysis results will be saved",
        key="input_result_path"
    )
    st.session_state.result_path = result_path
    
    st.markdown('</div>', unsafe_allow_html=True)

    # ==================== SECTION 2: FOLDER SELECTION ====================
    # st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    # st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📂 Folder Selection</div>', unsafe_allow_html=True)

    # Dropdown để chọn mode
    selection_mode = st.selectbox(
        "Selection Method",
        options=["Select from Folder", "Enter Raw File Names"],
        index=0 if not current_config.get("use_raw_file", False) else 1,
        help="Choose how you want to select folders for analysis",
        key="selection_mode"
    )

    # st.markdown("---")
    
    raw_file = False

    if selection_mode == "Enter Raw File Names":
        # Raw file input mode
        raw_file = True
        raw_file_input = st.text_area(
            "Folder Names",
            value=current_config.get("raw_file_input", ""),
            placeholder='Example: 50MeOH_QC_ur-4_wei_20251216, 50MeOH_QC_ur-4_wei_20251216_20251217223054',
            help='Enter folder names separated by commas. The .d extension will be added automatically if not present.',
            height=100,
            key="raw_file_input"
        )
        
        load_button = st.button("🔍 Load & Validate", type="primary", use_container_width=True, key="btn_load_validate")

        
        # Process when button clicked
        if load_button:
            if raw_file_input.strip():
                raw_file_list = [name.strip() for name in raw_file_input.split(',') if name.strip()]
                
                if raw_file_list:
                    is_valid, folders_to_select, message = validate_raw_file_names(
                        st.session_state.folder_analysis_path, 
                        raw_file_list
                    )
                    
                    st.session_state.folders_to_select = folders_to_select
                    st.session_state.validation_message = message
                    
                    if is_valid:
                        st.session_state.validation_type = 'success'
                    elif folders_to_select:
                        st.session_state.validation_type = 'warning'
                    else:
                        st.session_state.validation_type = 'error'
                else:
                    st.session_state.validation_message = "⚠️ Please enter at least one folder name"
                    st.session_state.validation_type = 'warning'
                    st.session_state.folders_to_select = []
            else:
                st.session_state.validation_message = "⚠️ Please enter folder names"
                st.session_state.validation_type = 'warning'
                st.session_state.folders_to_select = []
        
        # Display validation results
        if st.session_state.validation_message:
            if st.session_state.validation_type == 'success':
                st.success(st.session_state.validation_message)
            elif st.session_state.validation_type == 'warning':
                st.warning(st.session_state.validation_message)
            elif st.session_state.validation_type == 'error':
                st.error(st.session_state.validation_message)
            
            # Show validated folders
            if st.session_state.folders_to_select:
                with st.expander("📂 Validated Folders", expanded=True):
                    for idx, folder in enumerate(st.session_state.folders_to_select, 1):
                        st.markdown(f"`{idx}.` **{folder}**")
                    st.markdown(f"**Total: {len(st.session_state.folders_to_select)} folders**")

    else:


        scan_button = st.button("🔍 Scan Folders", type="primary", use_container_width=True, key="btn_scan")

        
        # Scan for folders when button clicked or if already scanned
        if scan_button or 'available_folders' in st.session_state:
            if scan_button:
                available_folders = scan_folder_for_d_files(st.session_state.folder_analysis_path)
                st.session_state.available_folders = available_folders
            else:
                available_folders = st.session_state.get('available_folders', [])
            
            if available_folders:
                st.markdown(f'<div class="folder-info">📁 Found {len(available_folders)} .d folders in: <code>{st.session_state.folder_analysis_path}</code></div>', 
                        unsafe_allow_html=True)
                
                # Filter current selection to only include folders that still exist
                current_selection = [folder for folder in st.session_state.folders_to_select 
                                if folder in available_folders]
                
                folders_to_select = st.multiselect(
                    "Select folders to analyze",
                    options=available_folders,
                    default=current_selection,
                    help="Choose which data folders to include in the analysis.",
                    key="multiselect_folders"
                )
                
                # Update session state
                st.session_state.folders_to_select = folders_to_select
                
                # Show folder count info
                if folders_to_select:
                    st.success(f"✅ Selected {len(folders_to_select)} out of {len(available_folders)} available folders")
                    
                    with st.expander("📂 Selected Folders", expanded=False):
                        for idx, folder in enumerate(folders_to_select, 1):
                            st.markdown(f"`{idx}.` **{folder}**")
                else:
                    st.warning("⚠️ No folders selected for analysis")
            else:
                st.warning(f"⚠️ No .d folders found in: {st.session_state.folder_analysis_path}")
                st.info("💡 Please check if the Analysis Folder Path is correct and contains .d directories")
                st.session_state.folders_to_select = []
        # else:
        #     st.info("💡 Click 'Scan Folders' to detect available .d folders")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # ==================== SECTION 3: MS-DIAL PARAMETERS ====================
    #st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    # st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚙️ MS-DIAL Parameters</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        ionization = st.selectbox(
            "Ionization",
            options=["Soft ionization", "Hard ionization"],
            index=0 if st.session_state.ionization == "Soft ionization" else 1,
            help="Type of ionization method used",
            key="select_ionization"
        )
        st.session_state.ionization = ionization
        
        separation = st.selectbox(
            "Separation",
            options=["Chromatography", "Direct infusion"],
            index=0 if st.session_state.separation == "Chromatography" else 1,
            help="Sample separation method",
            key="select_separation"
        )
        st.session_state.separation = separation
        
        collision = st.selectbox(
            "Collision",
            options=["CID/HCD", "ECD", "HotECD", "EIEIO", "EID", "OAD"],
            index=["CID/HCD", "ECD", "HotECD", "EIEIO", "EID", "OAD"].index(st.session_state.collision),
            help="Collision-induced dissociation method",
            key="select_collision"
        )
        st.session_state.collision = collision
        
        target_omics = st.selectbox(
            "Target Omics",
            options=["Metabolomics", "Lipidomics", "Proteomics"],
            index=["Metabolomics", "Lipidomics", "Proteomics"].index(st.session_state.target_omics),
            help="Type of omics analysis to perform",
            key="select_target_omics"
        )
        st.session_state.target_omics = target_omics
    
    with col4:
        data_ms1 = st.selectbox(
            "MS1 Data Type",
            options=["Profile data", "Centroid data"],
            index=0 if st.session_state.data_ms1 == "Profile data" else 1,
            help="Data format for MS1 spectra",
            key="select_data_ms1"
        )
        st.session_state.data_ms1 = data_ms1
        
        data_type_msms = st.selectbox(
            "MS/MS Data Type", 
            options=["Profile data", "Centroid data"],
            index=0 if st.session_state.data_type_msms == "Profile data" else 1,
            help="Data format for MS/MS spectra",
            key="select_data_type_msms"
        )
        st.session_state.data_type_msms = data_type_msms
        
        ion = st.selectbox(
            "Ion Mode",
            options=["Positive ion mode", "Negative ion mode"],
            index=0 if st.session_state.ion == "Positive ion mode" else 1,
            help="Ion detection mode",
            key="select_ion"
        )
        st.session_state.ion = ion
    
    st.markdown('</div>', unsafe_allow_html=True)

    # ==================== ACTION BUTTONS ====================
    #st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    
    folders_to_select = st.session_state.folders_to_select
    
    if raw_file:
        raw_file_list = st.session_state.folders_to_select
        folders_to_select = [] 
        
    else: 
        raw_file_list = []
    
    with col_btn1:
        if st.button("💾 Save Configuration", type="primary", use_container_width=True, key="btn_save"):
            # Validate required fields
            required_fields = {
                'app_path': st.session_state.app_path,
                'project_file_path': st.session_state.project_file_path,
                'folder_analysis_path': st.session_state.folder_analysis_path,
                'library_path': st.session_state.library_path,
                'result_path': st.session_state.result_path,
                'ionization': st.session_state.ionization,
                'separation': st.session_state.separation,
                'collision': st.session_state.collision,
                'data_ms1': st.session_state.data_ms1,
                'data_type_msms': st.session_state.data_type_msms,
                'ion': st.session_state.ion,
                'target_omics': st.session_state.target_omics,
            }
            
            # Check for empty fields
            empty_fields = []
            for field_name, field_value in required_fields.items():
                if not field_value or (isinstance(field_value, str) and field_value.strip() == ""):
                    empty_fields.append(field_name)
            
            # Check folders/files selection
            if selection_mode == "Select from Available Folders":
                if not st.session_state.folders_to_select:
                    empty_fields.append('folders_to_select')
            else:  # Enter Raw File Names
                if not raw_file_list and raw_file == True:
                    empty_fields.append('raw_files_to_select')
            
            # If there are empty fields, show error
            if empty_fields :
                st.error(f"❌ Please fill in all required fields! Missing: {', '.join(empty_fields)}")
            else:
                # All fields are filled, proceed to save
                config_data = {
                    'app_path': st.session_state.app_path,
                    'project_file_path': st.session_state.project_file_path,
                    'folder_analysis_path': st.session_state.folder_analysis_path,
                    'folders_to_select': folders_to_select,
                    'raw_files_to_select': raw_file_list,
                    'library_path': st.session_state.library_path,
                    'result_path': st.session_state.result_path,
                    'ionization': st.session_state.ionization,
                    'separation': st.session_state.separation,
                    'collision': st.session_state.collision,
                    'data_ms1': st.session_state.data_ms1,
                    'data_type_msms': st.session_state.data_type_msms,
                    'ion': st.session_state.ion,
                    'target_omics': st.session_state.target_omics,
                    'use_raw_file': selection_mode == "Enter Raw File Names"
                }
                
                if save_config(config_data):
                    st.success("✅ Configuration saved successfully!")
                    st.balloons()

    
    with col_btn2:
        if st.button("🔄 Reset to Default", use_container_width=True, key="btn_reset"):
            if save_config(DEFAULT_CONFIG):
                st.success("✅ Reset to default configuration!")
                # Update all session state
                for key, value in DEFAULT_CONFIG.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.rerun()
        
    with col_btn3:
        preview_button = st.button("👁️ Preview Config", use_container_width=True, key="btn_preview")

    # ==================== CONFIGURATION PREVIEW ====================
    with st.expander("👁️ Current Configuration Preview", expanded=preview_button):
        st.markdown("### Configuration Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Paths:**")
            st.code(f"App: {st.session_state.app_path}", language="text")
            st.code(f"Project: {st.session_state.project_file_path}", language="text")
            st.code(f"Analysis: {st.session_state.folder_analysis_path}", language="text")
            st.code(f"Library: {st.session_state.library_path}", language="text")
            st.code(f"Result: {st.session_state.result_path}", language="text")
            
            st.markdown("**Selected Folders:**")
            if st.session_state.folders_to_select:
                for idx, folder in enumerate(st.session_state.folders_to_select, 1):
                    st.write(f"`{idx}.` {folder}")
                st.info(f"Total: **{len(st.session_state.folders_to_select)}** folders")
            else:
                st.write("• No folders selected")
        
        with col2:
            st.markdown("**MS Parameters:**")
            st.write(f"**Ionization:** {st.session_state.ionization}")
            st.write(f"**Separation:** {st.session_state.separation}")
            st.write(f"**Collision:** {st.session_state.collision}")
            st.write(f"**Target Omics:** {st.session_state.target_omics}")
            st.write(f"**MS1 Data:** {st.session_state.data_ms1}")
            st.write(f"**MS/MS Data:** {st.session_state.data_type_msms}")
            st.write(f"**Ion Mode:** {st.session_state.ion}")
        
        # JSON view option
        if st.checkbox("Show raw JSON", key="show_json"):
            preview_config = {
                'app_path': st.session_state.app_path,
                'project_file_path': st.session_state.project_file_path,
                'folder_analysis_path': st.session_state.folder_analysis_path,
                'folders_to_select': folders_to_select,
                'raw_files_to_select': raw_file_list,
                'library_path': st.session_state.library_path,
                'result_path': st.session_state.result_path,
                'ionization': st.session_state.ionization,
                'separation': st.session_state.separation,
                'collision': st.session_state.collision,
                'data_ms1': st.session_state.data_ms1,
                'data_type_msms': st.session_state.data_type_msms,
                'ion': st.session_state.ion,
                'target_omics': st.session_state.target_omics
            }
            st.json(preview_config)