import streamlit as st
from streamlit_option_menu import option_menu
import re
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from app_demo.src.p1_configuration import *
from app_demo.src.p2_processing import *
from app_demo.src.p3_download_result import *
from app_demo.src.footer import settingFooter
import warnings
import logging
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

# Create an option menu for the main menu in the sidebar
st.set_page_config(page_title="ClassyFire", page_icon="app_demo/image/Icon_chemitry.png", layout="wide")
#st.set_page_config(page_title="Semi-quantitative", page_icon="app_demo/image/Icon_chemitry.png", layout="wide",  theme={"primaryColor": "#4CAF50"})
st.sidebar.image("app_demo/image/logo_NCKU.jpeg", use_column_width=True)

with st.sidebar:
    selected = option_menu("Main Menu", ["1. Configuration", "2. Processing", "3. Download Result"],
                           icons=["gear-fill", "cpu-fill", "cloud-arrow-down-fill" ], menu_icon="bars", default_index=0)
# Based on the selected option, you can display different content in your web application
# page for select icon https://icons.getbootstrap.com/

# st.sidebar.image("app_demo/image/Picture1.png", use_column_width=True)

# settingFooter()







if selected == "1. Configuration":
    upload_data()   
elif selected == "2. Processing":
    main()
elif selected == "3. Download Result":
    download_result()

