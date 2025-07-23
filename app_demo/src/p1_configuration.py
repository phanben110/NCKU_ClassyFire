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
    filename='runtime.log',  # Tên file log
    level=logging.INFO,     # Mức độ logging
    format='%(asctime)s - %(message)s',  # Định dạng log
    datefmt='%Y-%m-%d %H:%M:%S'  # Định dạng thời gian
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
    
import streamlit as st
import pandas as pd
import json
import os
import logging
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    filename='runtime.log',  # Tên file log
    level=logging.INFO,     # Mức độ logging
    format='%(asctime)s - %(message)s',  # Định dạng log
    datefmt='%Y-%m-%d %H:%M:%S'  # Định dạng thời gian
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

import streamlit as st
import pandas as pd
import json
import os
import logging
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    filename='runtime.log',  # Tên file log
    level=logging.INFO,     # Mức độ logging
    format='%(asctime)s - %(message)s',  # Định dạng log
    datefmt='%Y-%m-%d %H:%M:%S'  # Định dạng thời gian
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
    "app_path": r"C:\Users\user\Documents\TMIC\MSDIAL.v5.5.241113-net48\MSDIAL.exe",
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
    "result_path": r"C:\Users\user\Desktop\自動化檔案\data"
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
        st.success("Configuration saved successfully!")
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False

def show_configuration_page():
    """Display the configuration page"""
    title_app("ClassyFire - MS-DIAL Configuration Setup")

    # Custom CSS for beautiful buttons and styling
    st.markdown("""
    <style>
    /* Main container width */
    .main .block-container {
        max-width: 800%;
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
    
    /* Primary button (Save) */
    div[data-testid="column"]:nth-child(1) .stButton > button {
        background: linear-gradient(45deg, #11998e 0%, #38ef7d 100%);
        box-shadow: 0 4px 15px 0 rgba(17, 153, 142, 0.3);
    }
    
    div[data-testid="column"]:nth-child(1) .stButton > button:hover {
        box-shadow: 0 6px 20px 0 rgba(17, 153, 142, 0.4);
    }
    
    /* Reset button */
    div[data-testid="column"]:nth-child(2) .stButton > button {
        background: linear-gradient(45deg, #ff9a9e 0%, #fecfef 100%);
        box-shadow: 0 4px 15px 0 rgba(255, 154, 158, 0.3);
    }
    
    div[data-testid="column"]:nth-child(2) .stButton > button:hover {
        box-shadow: 0 6px 20px 0 rgba(255, 154, 158, 0.4);
    }
    
    /* Preview button */
    div[data-testid="column"]:nth-child(3) .stButton > button {
        background: linear-gradient(45deg, #a8edea 0%, #fed6e3 100%);
        box-shadow: 0 4px 15px 0 rgba(168, 237, 234, 0.3);
        color: #333 !important;
    }
    
    div[data-testid="column"]:nth-child(3) .stButton > button:hover {
        box-shadow: 0 6px 20px 0 rgba(168, 237, 234, 0.4);
    }
    
    /* Form styling */
    .stForm {
        border: 2px solid #e0e6ed;
        border-radius: 15px;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .main-header {
        color: #000000; /* Màu đen */
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
        margin-top: 0;
        text-align: left; /* Không căn giữa */
    }


    
    /* Section dividers */
    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 2px;
        margin: 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    # Load existing configuration
    current_config = load_config()
    
    with st.form("config_form"):
        st.markdown("### Application Paths")
        
        app_path = st.text_input(
            "MS-DIAL Application Path",
            value=current_config["app_path"],
            help="Path to the MS-DIAL executable file"
        )
        
        project_file_path = st.text_input(
            "Project File Path",
            value=current_config["project_file_path"],
            help="Directory for MS-DIAL project files"
        )
        
        folder_analysis_path = st.text_input(
            "Analysis Folder Path",
            value=current_config["folder_analysis_path"],
            help="Path to the folder containing data files to analyze"
        )
        
        library_path = st.text_input(
            "Library Path",
            value=current_config["library_path"],
            help="Path to the spectral library database"
        )
        
        result_path = st.text_input(
            "Result Output Path",
            value=current_config["result_path"],
            help="Directory where analysis results will be saved"
        )
        
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("### Folder Selection")
        
        folders_to_select = st.multiselect(
            "Select folders to analyze",
            options=[
                "POOL_POS1209_LIU_54_01_2081.d",
                "QC_40PPB_4_95_01_2091.d", 
                "UR2_POS1209_WEI_38_01_2086.d",
                "POOL_POS1209_WEI_42_01_2090.d"
            ],
            default=current_config["folders_to_select"],
            help="Choose which data folders to include in the analysis"
        )
        
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("### MS-DIAL Parameters")
        
        col3, col4 = st.columns(2)
        
        with col3:
            ionization = st.selectbox(
                "Ionization",
                options=["Soft ionization", "Hard ionization"],
                index=0 if current_config["ionization"] == "Soft ionization" else 1,
                help="Type of ionization method used"
            )
            
            separation = st.selectbox(
                "Separation",
                options=["Chromatography", "Direct infusion"],
                index=0 if current_config["separation"] == "Chromatography" else 1,
                help="Sample separation method"
            )
            
            collision = st.selectbox(
                "Collision",
                options=["CID/HCD", "ECD", "HotECD", "EIEIO", "EID", "OAD"],
                index=["CID/HCD", "ECD", "HotECD", "EIEIO", "EID", "OAD"].index(current_config["collision"]),
                help="Collision-induced dissociation method"
            )
            
            target_omics = st.selectbox(
                "Target Omics",
                options=["Metabolomics", "Lipidomics", "Proteomics"],
                index=["Metabolomics", "Lipidomics", "Proteomics"].index(current_config["target_omics"]),
                help="Type of omics analysis to perform"
            )
        
        with col4:
            data_ms1 = st.selectbox(
                "MS1 Data Type",
                options=["Profile data", "Centroid data"],
                index=0 if current_config["data_ms1"] == "Profile data" else 1,
                help="Data format for MS1 spectra"
            )
            
            data_type_msms = st.selectbox(
                "MS/MS Data Type", 
                options=["Profile data", "Centroid data"],
                index=0 if current_config["data_type_msms"] == "Profile data" else 1,
                help="Data format for MS/MS spectra"
            )
            
            ion = st.selectbox(
                "Ion Mode",
                options=["Positive ion mode", "Negative ion mode"],
                index=0 if current_config["ion"] == "Positive ion mode" else 1,
                help="Ion detection mode"
            )
        
        # Form submission buttons with beautiful styling
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
        
        with col_btn1:
            submitted = st.form_submit_button(
                "Save Configuration", 
                use_container_width=True
            )
        
        with col_btn2:
            reset_button = st.form_submit_button(
                "Reset Default",
                use_container_width=True
            )
            
        with col_btn3:
            preview_button = st.form_submit_button(
                "Preview Config",
                use_container_width=True
            )
        
        if submitted:
            config_data = {
                'app_path': app_path,
                'project_file_path': project_file_path,
                'folder_analysis_path': folder_analysis_path,
                'folders_to_select': folders_to_select,
                'library_path': library_path,
                'result_path': result_path,
                'ionization': ionization,
                'separation': separation,
                'collision': collision,
                'data_ms1': data_ms1,
                'data_type_msms': data_type_msms,
                'ion': ion,
                'target_omics': target_omics
            }
            save_config(config_data)
        
        if reset_button:
            save_config(DEFAULT_CONFIG)
            st.experimental_rerun()  # Fixed: Use st.experimental_rerun() instead of st.rerun()
            
        if preview_button:
            st.info("Current configuration is shown below in the preview section.")
    
    
    # Beautiful configuration preview
    with st.expander("👁️ Current Configuration Preview", expanded=False):
        st.markdown("### Configuration Details")
        
        # Display config in a more organized way
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Paths:**")
            st.code(f"App: {current_config['app_path']}")
            st.code(f"Project: {current_config['project_file_path']}")
            st.code(f"Analysis: {current_config['folder_analysis_path']}")
            
            st.markdown("**Selected Folders:**")
            for folder in current_config['folders_to_select']:
                st.write(f"• {folder}")
        
        with col2:
            st.markdown("**MS Parameters:**")
            st.write(f"**Ionization:** {current_config['ionization']}")
            st.write(f"**Separation:** {current_config['separation']}")
            st.write(f"**Collision:** {current_config['collision']}")
            st.write(f"**Target Omics:** {current_config['target_omics']}")
            st.write(f"**MS1 Data:** {current_config['data_ms1']}")
            st.write(f"**MS/MS Data:** {current_config['data_type_msms']}")
            st.write(f"**Ion Mode:** {current_config['ion']}")
        
        # JSON view option
        if st.checkbox("Show raw JSON", key="show_json"):
            st.json(current_config)

# Usage in main app:
# if page == "Configuration":
#     show_configuration_page()