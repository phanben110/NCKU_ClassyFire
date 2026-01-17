import streamlit as st
import os
import logging
import requests
import numpy as np
import pandas as pd
import io
import json
import warnings
from app_demo.src.title import title_app
import zipfile
from datetime import datetime

warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    filename='runtime.log',  # Tên file log
    level=logging.INFO,         # Mức độ logging
    format='%(asctime)s - %(message)s',  # Định dạng log
    datefmt='%Y-%m-%d %H:%M:%S'  # Định dạng thời gian
)

# Function to log access information
def log_access(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{current_time} - P3. Download   - {message}")
    print(f"{current_time} - P3. Download   - {message}")


# def download_result(file_names=None, sample_count=None):
#     log_access("Download result")
#     title_app("ClassyFire - Download Results")
def download_result(file_names=None, sample_count=None):
    log_access("Download result")
    title_app("ClassyFire - Download Results")

    folder_path = "data/metaboanalyst_pubchem"

    if not os.path.exists(folder_path):
        st.warning("📂 The folder 'data/metaboanalyst_pubchem' does not exist.")
        return

    csv_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".csv")]

    if not csv_files:
        st.warning(
            "⚠️ No CSV file found.\n\n"
            "➡️ Please go back to **Step 1** to check your settings, "
            "then **Step 2** to run the process."
        )
        return

    # Pick most recent file
    csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
    file_path = os.path.join(folder_path, csv_files[0])

    try:
        df = pd.read_csv(file_path)

        st.markdown(
            f"<h2 style='text-align:center; color:#2E86C1;'>📄 Showing File: {csv_files[0]}</h2>",
            unsafe_allow_html=True
        )

        # Center the table
        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            st.dataframe(df, use_container_width=True, height=500)

            # Download button
            csv_bytes = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_bytes,
                file_name=csv_files[0],
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error reading CSV file: {e}")

