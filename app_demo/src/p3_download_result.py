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


def download_result(file_names=None, sample_count=None):
    log_access("Download result")
    title_app("ClassyFire - Download Results")