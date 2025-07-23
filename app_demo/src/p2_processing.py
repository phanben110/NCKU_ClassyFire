import streamlit as st
import os
import time
import shutil
import subprocess
from datetime import datetime
import logging
from app_demo.src.core import ChemicalAnalysisPipeline, Config
import queue
import io
import sys
from app_demo.src.title import title_app

# Configure logging
logging.basicConfig(
    filename='runtime.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_access(message):
    """Log access information"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{current_time} - Processing - {message}")
    print(f"{current_time} - Processing - {message}")

def clean_result_folders():
    """Clean all result folders to start fresh"""
    config = Config()
    folders_to_clean = [
        "data/clean_result",
        config.GROUPING_FOLDER,
        config.FINAL_RESULT_FOLDER,
        config.CONVERT_RESULT_FOLDER,
        config.METABOANALYST_FOLDER
    ]
    
    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            log_access(f"Cleaned {folder} folder")
        os.makedirs(folder, exist_ok=True)
        log_access(f"Created new {folder} folder")

def check_clean_result_files():
    """Check if files exist in data/clean_result folder"""
    source_folder = "data/clean_result"
    if not os.path.exists(source_folder):
        return False, []
    
    excel_files = [f for f in os.listdir(source_folder) if f.endswith('.xlsx')]
    return len(excel_files) > 0, excel_files

def run_main_script():
    """Run the main.py script using subprocess"""
    try:
        log_access("Starting MS-DIAL main.py script execution")
        process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        return process
    except Exception as e:
        log_access(f"Error starting main.py: {str(e)}")
        return None

class LogCapture:
    def __init__(self):
        self.log_queue = queue.Queue()
        self.logs = []
        
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        self.log_queue.put(log_entry)
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

def run_pipeline_step(step_number, pipeline, status_text, log_capture, progress_bar):
    step_names = {
        1: "Classification Processing",
        2: "Data Merging",
        3: "Identifier Conversion",
        4: "Final Aggregation"
    }
    
    try:
        step_name = step_names.get(step_number, f"Step {step_number}")
        status_text.text(f"Running Task 2, Step {step_number}: {step_name}...")
        log_capture.add_log(f"Starting Task 2, Step {step_number}: {step_name}")
        
        stdout_buffer = io.StringIO()
        sys.stdout = stdout_buffer
        
        try:
            pipeline.run_step(step_number)
            log_capture.add_log(f"Task 2, Step {step_number} completed successfully")
            status_text.text(f"Task 2, Step {step_number}: {step_name} completed!")
            progress_bar.progress(min(100, int(50 + step_number * 12.5)))  # 50% + 12.5% per step
            return True
        finally:
            sys.stdout = sys.__stdout__
            stdout_content = stdout_buffer.getvalue()
            if stdout_content.strip():
                for line in stdout_content.strip().split('\n'):
                    log_capture.add_log(f"STDOUT: {line}")
                    
    except Exception as e:
        log_capture.add_log(f"ERROR in Task 2, Step {step_number}: {str(e)}")
        status_text.error(f"Error in Task 2, Step {step_number}: {str(e)}")
        return False

def rerun_app():
    """Handle Streamlit rerun for compatibility"""
    st.experimental_rerun()

def display_pipeline_info():
    """Display information about the pipeline steps"""
    st.sidebar.markdown("### 🔬 Pipeline Tasks")
    st.sidebar.markdown("""
    **Task 1: MS-DIAL Processing**
    - Run MS-DIAL application (main.py)
    - Process input data files
    - Clean and prepare data
    - Generate initial results in clean_result folder
    
    **Task 2: Chemical Structure Classification**
    
    **Step 1: Classification Processing**
    - Process input data files
    - Apply chemical classification
    - Generate classification results
    
    **Step 2: Data Merging**
    - Merge classification results with original data
    - Combine experimental data with classifications
    - Preserve data integrity
    
    **Step 3: Identifier Conversion**
    - Convert chemical identifiers to multiple formats
    - Use CTS API for conversions
    - Add HMDB, KEGG, PubChem CID, ChEBI IDs
    
    **Step 4: Final Aggregation**
    - Aggregate all processed data
    - Create final analysis-ready dataset
    - Output MetaboAnalyst compatible format
    
    *Steps run automatically in sequence: 1 → 2 → 3 → 4*
    """)

def main():
    title_app("ClassyFire - Chemical Analysis Pipeline")
    display_pipeline_info()
    
    # Custom CSS for larger Start Pipeline button and styled progress bar without shadow
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            height: 80px;
            font-size: 26px;
            font-weight: bold;
            background: linear-gradient(45deg, #1e90ff, #00b7eb);
            color: white;
            border: none;
            border-radius: 15px;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(45deg, #00b7eb, #1e90ff);
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        }
        .stButton > button:active {
            transform: translateY(0);
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        }
        .stProgress > div > div {
            background: linear-gradient(90deg, #1e90ff, #00b7eb);
            border-radius: 5px;
        }
        .stProgress > div {
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            box-shadow: none;  /* Removed shadow */
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'process_running' not in st.session_state:
        st.session_state.process_running = False
    if 'task1_completed' not in st.session_state:
        st.session_state.task1_completed = False
    if 'main_process' not in st.session_state:
        st.session_state.main_process = None
    if 'log_capture' not in st.session_state:
        st.session_state.log_capture = LogCapture()
    if 'log_counter' not in st.session_state:
        st.session_state.log_counter = 0
    if 'show_logs' not in st.session_state:
        st.session_state.show_logs = False
    if 'progress_bar' not in st.session_state:
        st.session_state.progress_bar = None

    # Start button
    if not st.session_state.process_running:
        col1, col2, col3 = st.columns([1, 3, 1])  # Wider center column for larger button
        with col2:
            if st.button("🚀 Start Pipeline", type="primary"):
                clean_result_folders()
                st.session_state.process_running = True
                st.session_state.task1_completed = False
                st.session_state.main_process = run_main_script()
                st.session_state.log_capture = LogCapture()
                st.session_state.log_counter = 0
                st.session_state.log_capture.add_log("Pipeline started - cleaned result folders")
                rerun_app()

    # Log visibility toggle
    st.session_state.show_logs = st.checkbox("Show Logs", value=st.session_state.show_logs)

    # Process running
    if st.session_state.process_running:
        st.markdown("### Processing Status")
        status_container = st.container()
        progress_container = st.container()
        log_container = st.container()
        
        with status_container:
            status_text = st.empty()
        
        with progress_container:
            st.markdown("#### Progress")
            if st.session_state.progress_bar is None:
                st.session_state.progress_bar = st.progress(0)
            progress_bar = st.session_state.progress_bar
        
        with log_container:
            if st.session_state.show_logs:
                st.markdown("### Real-time Logs")
                log_placeholder = st.empty()
        
        max_wait_time = 3600  # 1 hour maximum wait time
        start_time = time.time()
        
        while st.session_state.process_running:
            current_time = time.time()
            
            # Check timeout
            if current_time - start_time > max_wait_time:
                st.error("Process timeout - stopping pipeline")
                st.session_state.log_capture.add_log("ERROR: Process timeout - stopping pipeline")
                if st.session_state.main_process:
                    st.session_state.main_process.terminate()
                st.session_state.process_running = False
                break
            
            # Task 1: MS-DIAL Processing
            if not st.session_state.task1_completed:
                if st.session_state.main_process:
                    poll_result = st.session_state.main_process.poll()
                    if poll_result is not None:
                        if poll_result == 0:
                            log_msg = "Task 1: MS-DIAL main script completed successfully"
                            log_access(log_msg)
                            st.session_state.log_capture.add_log(log_msg)
                        else:
                            log_msg = f"Task 1: MS-DIAL main script failed with return code: {poll_result}"
                            log_access(log_msg)
                            st.session_state.log_capture.add_log(f"ERROR: {log_msg}")
                            st.error(f"Task 1 failed with error code: {poll_result}")
                            st.session_state.process_running = False
                            break
                        
                        st.session_state.main_process = None
                
                has_files, files = check_clean_result_files()
                if has_files:
                    st.session_state.task1_completed = True
                    log_msg = f"Task 1 completed: Files detected in clean_result folder: {len(files)} files"
                    log_access(log_msg)
                    st.session_state.log_capture.add_log(log_msg)
                    status_text.success("✅ Task 1 completed! Starting Task 2: Chemical Structure Classification")
                    progress_bar.progress(50)  # Task 1 = 50%
                    st.session_state.log_capture.add_log("Starting Task 2: Chemical Structure Classification")
                    time.sleep(2)  # Brief pause to show Task 1 completion
                else:
                    status_text.text("Task 1: Running MS-DIAL - Processing data files...")
                    progress_bar.progress(25)  # Partial progress for Task 1
                    time.sleep(2)
                    # Update log display if enabled
                    if st.session_state.show_logs:
                        current_logs = st.session_state.log_capture.logs
                        st.session_state.log_counter += 1
                        log_placeholder.text_area(
                            "Logs:",
                            value="\n".join(current_logs[-20:]),
                            height=300,  # Larger height
                            disabled=True,
                            key=f"log_{st.session_state.log_counter}"
                        )
                    continue
            
            # Task 2: Chemical Structure Classification
            if st.session_state.task1_completed:
                pipeline = ChemicalAnalysisPipeline(Config())
                for step in range(1, 5):
                    success = run_pipeline_step(
                        step, pipeline, status_text, st.session_state.log_capture, progress_bar
                    )
                    
                    # Update log display if enabled
                    if st.session_state.show_logs:
                        current_logs = st.session_state.log_capture.logs
                        st.session_state.log_counter += 1
                        log_placeholder.text_area(
                            "Logs:",
                            value="\n".join(current_logs[-20:]),
                            height=300,  # Larger height
                            disabled=True,
                            key=f"log_{st.session_state.log_counter}"
                        )
                    
                    if not success:
                        st.error(f"Task 2 stopped at step {step}")
                        st.session_state.process_running = False
                        break
                    
                    time.sleep(1)
                
                if st.session_state.process_running:
                    st.session_state.process_running = False
                    status_text.success("✅ Pipeline completed! Task 1 and Task 2 finished successfully.")
                    progress_bar.progress(100)  # Full completion
                    st.session_state.log_capture.add_log("Pipeline completed successfully")
                    break
            
            # Update log display if enabled
            if st.session_state.show_logs:
                current_logs = st.session_state.log_capture.logs
                st.session_state.log_counter += 1
                log_placeholder.text_area(
                    "Logs:",
                    value="\n".join(current_logs[-20:]),
                    height=300,  # Larger height
                    disabled=True,
                    key=f"log_{st.session_state.log_counter}"
                )
            
            time.sleep(2)
        
        # if not st.session_state.process_running:
        #     rerun_app()

if __name__ == "__main__":
    main()