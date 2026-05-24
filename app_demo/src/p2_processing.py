import streamlit as st
import os
import time
import shutil
import subprocess
import html
from datetime import datetime
import logging
from pathlib import Path
from app_demo.src.core import ChemicalAnalysisPipeline, Config
import queue
import sys
from app_demo.src.title import title_app


app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if app_root not in sys.path:
    sys.path.insert(0, app_root)

from copy_results_to_final import copy_results_to_final, copy_folder_results_to_final

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
        config.SOURCE_FOLDER,
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
    print("Clear")

# def check_clean_result_files():
#     """Check if files exist in data/clean_result folder"""
#     source_folder = "data/clean_result"
#     if not os.path.exists(source_folder):
#         return False, []
    
#     excel_files = [f for f in os.listdir(source_folder) if f.endswith('.xlsx')]
#     return len(excel_files) > 0, excel_files
def check_clean_result_files():
    """Check if files exist in data/clean_result folder"""
    config = Config()
    source_folder = config.SOURCE_FOLDER
    
    log_access("Waiting 5 seconds before checking clean_result files...")
    print("⏳ Waiting 5 seconds before checking files...")
    time.sleep(5)  # Delay 5 giây

    if not os.path.exists(source_folder):
        log_access(f"Folder not found: {source_folder}")
        print(f"❌ Folder not found: {source_folder}")
        return False, []
    
    #excel_files = [f for f in os.listdir(source_folder) if f.endswith('.xlsx')]
    excel_files = [
    f for f in os.listdir(source_folder)
    if f.lower().endswith(('.xlsx', '.csv','.txt'))
    ]
    file_count = len(excel_files)

    log_access(f"Detected {file_count} Excel file(s) in {source_folder}")
    print(f"📂 Detected {file_count} Excel file(s) in '{source_folder}'")

    return file_count > 0, excel_files


# def run_main_script():
#     """Run the main.py script using subprocess"""
#     try:
#         log_access("Starting MS-DIAL main.py script execution")
#         process = subprocess.Popen(
#             #["python", "main.py"], #main.py #msdial_new.py
#             ["python", "msdial_new.py"], #main.py #msdial_new.py
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             bufsize=1,
#             universal_newlines=True
#         )
#         print("code " , process)
#         return process
#     except Exception as e:
#         log_access(f"Error starting main.py: {str(e)}")
#         return None



def run_main_script():
    """Run the main.py script using subprocess"""
    try:
        log_access("Starting MS-DIAL main.py script execution")
        subprocess.run(
            #["python", "main.py"],
            ["python","msdial_new.py"],
            check=True,         # nếu main.py trả về lỗi (exit code != 0) sẽ raise Exception
            text=True
        )
        return True  # Chạy xong thì trả về True
    except subprocess.CalledProcessError as e:
        log_access(f"main.py exited with error code {e.returncode}")
        print(f"main.py exited with error code {e.returncode}")
        return False
    except Exception as e:
        log_access(f"Error starting main.py: {str(e)}")
        print(f"Error starting main.py: {str(e)}")
        return False


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


def format_duration(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def estimate_time_remaining(start_time, percent):
    if percent <= 0 or percent >= 100:
        return "Estimating..."
    elapsed = time.time() - start_time
    estimated_total = elapsed / (percent / 100.0)
    remaining = max(estimated_total - elapsed, 0)
    return f"{format_duration(remaining)} remaining"


def update_overall_progress(overall_text, overall_progress_bar, eta_text, step_index, total_steps, ratio, description, start_time):
    ratio = min(max(ratio, 0.0), 1.0)
    percent = int(((step_index - 1) + ratio) / total_steps * 100)
    overall_progress_bar.progress(percent)
    overall_text.text(f"Overall progress: {step_index}/{total_steps} — {description} ({percent}%)")
    eta_text.text(f"⏳ {estimate_time_remaining(start_time, percent)}")
    return percent


def update_recent_activity(placeholder, log_capture, max_entries=80):
    logs = log_capture.logs[-max_entries:]
    if not logs:
        content = "<div class='custom-log-box'>No recent activity yet.</div>"
    else:
        escaped_logs = html.escape("\n".join(logs))
        content = f"<div class='custom-log-box'><pre>{escaped_logs}</pre></div>"
    placeholder.markdown(content, unsafe_allow_html=True)


def run_pipeline_step(step_number, pipeline, status_text, step_text, log_capture, step_progress_bar, overall_text, overall_progress_bar, overall_eta_text, overall_step_index, total_steps, start_time):
    step_names = {
        1: "Classification Processing",
        2: "Data Merging",
        3: "Identifier Conversion",
        4: "Final Aggregation"
    }

    step_name = step_names.get(step_number, f"Step {step_number}")
    status_text.text(f"Task 2 — Step {step_number}/4")
    step_text.text(step_name)
    log_capture.add_log(f"Starting Task 2, Step {step_number}: {step_name}")

    current_progress = {'done': 0, 'total': 0}

    def progress_callback(done, total, message=None):
        current_progress['done'] = done
        current_progress['total'] = total
        percent = int(done / total * 100) if total else 0
        step_progress_bar.progress(percent)
        label = message or f"{done}/{total}"
        step_text.text(f"{step_name} — {label}")
        update_overall_progress(overall_text, overall_progress_bar, overall_eta_text, overall_step_index, total_steps, done / total if total else 0.0, step_name, start_time)

    try:
        pipeline.run_step(step_number, progress_callback=progress_callback)
        log_capture.add_log(f"Task 2, Step {step_number} completed successfully")
        status_text.success(f"Task 2 — Step {step_number}/4 completed")
        if current_progress['total']:
            step_progress_bar.progress(100)
            step_text.text(f"{step_name} — Completed {current_progress['done']}/{current_progress['total']}")
        else:
            step_progress_bar.progress(100)
            step_text.text(f"{step_name} — Completed")
        update_overall_progress(overall_text, overall_progress_bar, overall_eta_text, overall_step_index, total_steps, 1.0, step_name, start_time)
        return True
    except Exception as e:
        log_capture.add_log(f"ERROR in Task 2, Step {step_number}: {str(e)}")
        status_text.error(f"Error in Task 2, Step {step_number}: {str(e)}")
        step_text.text(f"{step_name} — failed")
        return False


def rerun_app():
    """Handle Streamlit rerun for compatibility"""
    st.rerun()

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
        .custom-log-box {
            max-height: 340px;
            overflow-y: auto;
            overflow-x: auto;
            padding: 14px;
            background: #f7fafc;
            border: 1px solid #d9e2ec;
            border-radius: 14px;
            color: #4b5563;
            font-size: 14px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            white-space: pre-wrap;
            line-height: 1.45;
        }
        .custom-log-box pre {
            margin: 0;
            font-family: inherit;
            white-space: pre-wrap;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'process_running' not in st.session_state:
        st.session_state.process_running = False
    if 'task1_completed' not in st.session_state:
        st.session_state.task1_completed = False
    if 'main_process' not in st.session_state:
        st.session_state.main_process = False
    if 'log_capture' not in st.session_state:
        st.session_state.log_capture = LogCapture()

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
                st.session_state.log_capture.add_log("Pipeline started - cleaned result folders")
                rerun_app()

    # Process running
    if st.session_state.process_running:
        st.markdown("### Processing Status")
        status_container = st.container()
        progress_container = st.container()
        activity_container = st.container()
        
        with status_container:
            status_text = st.empty()
            step_text = st.empty()
        
        with progress_container:
            st.markdown("#### Overall Progress")
            overall_text = st.empty()
            overall_progress_bar = st.progress(0)
            st.markdown("#### Current Step Progress")
            step_progress_text = st.empty()
            step_progress_bar = st.progress(0)
            eta_text = st.empty()
        
        with activity_container:
            st.markdown("#### Recent activity")
            st.markdown("_Live log output from pipeline processing. Scroll to review more events._")
            recent_log_placeholder = st.empty()
        
        max_wait_time = 3600*5  # 1 hour maximum wait time
        start_time = time.time()
        
        while st.session_state.process_running:
            current_time = time.time()
            
            # Check timeout
            if current_time - start_time > max_wait_time:
                st.error("Process timeout - stopping pipeline")
                st.session_state.log_capture.add_log("ERROR: Process timeout - stopping pipeline")
                start_time = time.time()
                # if st.session_state.main_process:
                #     st.session_state.main_process.terminate()
                st.session_state.process_running = False
                break
            
            # Task 1: MS-DIAL Processing
            has_files, files = check_clean_result_files()
            if not st.session_state.task1_completed:
                update_overall_progress(overall_text, overall_progress_bar, eta_text, 1, 5, 0.0, "MS-DIAL processing", start_time)
                step_progress_text.text("MS-DIAL progress — 0/1")
                step_progress_bar.progress(0)

                if st.session_state.main_process:
                    poll_result = st.session_state.main_process
                    if has_files:
                        log_msg = "Task 1: MS-DIAL main script completed successfully"
                        log_access(log_msg)
                        st.session_state.log_capture.add_log(log_msg)
                        st.session_state.main_process = None
                    # else:
                    #     log_msg = f"Task 1: MS-DIAL main script failed with return code: {poll_result}"
                    #     log_access(log_msg)
                    #     st.session_state.log_capture.add_log(f"ERROR: {log_msg}")
                    #     st.error(f"Task 1 failed with error code: {poll_result}")
                    #     st.session_state.process_running = False
                    #     break
                
                # has_files, files = check_clean_result_files()
                if has_files:
                    st.session_state.task1_completed = True
                    log_msg = f"Task 1 completed: Files detected in clean_result folder: {len(files)} files"
                    log_access(log_msg)
                    st.session_state.log_capture.add_log(log_msg)
                    status_text.success("✅ Task 1 completed! Copying Task 1 results to final_result_path...")
                    try:
                        config = Config()
                        copy_result = copy_folder_results_to_final(
                            'Task1_CleanResult',
                            Path(config.SOURCE_FOLDER),
                            overwrite=True
                        )
                        status_text.info(f"Copied {copy_result['copied_count']} files to: {copy_result['dst_root']}")
                        st.session_state.log_capture.add_log(f"Copied results after Task 1 to {copy_result['dst_root']}")
                    except Exception as e:
                        st.warning(f"⚠️ Copy after Task 1 failed: {e}")
                        st.session_state.log_capture.add_log(f"ERROR: Copy after Task 1 failed: {e}")
                    status_text.success("✅ Task 1 completed! Copying Task 1 results to final_result_path...")
                    step_text.info("Task 1 complete")
                    step_progress_text.text("MS-DIAL completed — 1/1")
                    step_progress_bar.progress(100)
                    update_overall_progress(overall_text, overall_progress_bar, eta_text, 1, 5, 1.0, "MS-DIAL complete", start_time)
                    print("[CMD] Task 1 completed. Copying Task 1 results...")
                    st.session_state.log_capture.add_log("Task 1 completed: Results copied and Task 2 starting")
                    update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
                    time.sleep(2)  # Brief pause to show Task 1 completion
                else:
                    status_text.text("Task 1: Running MS-DIAL - Processing data files...")
                    step_text.text("Task 1 in progress")
                    step_progress_text.text("MS-DIAL running — 0/1")
                    print("[CMD] Task 1: Running MS-DIAL - processing data files...")
                    step_progress_bar.progress(0)
                    time.sleep(2)
                    update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
                    continue
            
            # Task 2: Chemical Structure Classification
            if st.session_state.task1_completed:
                pipeline = ChemicalAnalysisPipeline(Config())
                step_names = {
                    1: "Classification Processing",
                    2: "Data Merging",
                    3: "Identifier Conversion",
                    4: "Final Aggregation"
                }
                for step in range(1, 5):
                    step_name = step_names.get(step, f"Step {step}")
                    status_text.info(f"Task 2 — Step {step}/4")
                    step_text.text(step_name)
                    step_progress_text.text(f"{step_name} — waiting to start")
                    step_progress_bar.progress(0)
                    update_overall_progress(overall_text, overall_progress_bar, eta_text, step + 1, 5, 0.0, step_name, start_time)
                    success = run_pipeline_step(
                        step,
                        pipeline,
                        status_text,
                        step_text,
                        st.session_state.log_capture,
                        step_progress_bar,
                        overall_text,
                        overall_progress_bar,
                        eta_text,
                        step + 1,
                        5,
                        start_time
                    )
                    
                    if not success:
                        st.error(f"Task 2 stopped at step {step}")
                        st.session_state.process_running = False
                        break

                    try:
                        config = Config()
                        step_map = {
                            1: ('Task2_Step1_Grouping', Path(config.GROUPING_FOLDER)),
                            2: ('Task2_Step2_Final', Path(config.FINAL_RESULT_FOLDER)),
                            3: ('Task2_Step3_Converted', Path(config.CONVERT_RESULT_FOLDER)),
                            4: ('Task2_Step4_MetaboanalystPubchem', Path(config.METABOANALYST_FOLDER)),
                        }
                        prefix, folder = step_map.get(step, (f'Task2_Step{step}', Path(config.METABOANALYST_FOLDER)))
                        copy_result = copy_folder_results_to_final(prefix, folder, overwrite=True)
                        status_text.info(f"Copied {copy_result['copied_count']} files to: {copy_result['dst_root']}")
                        st.session_state.log_capture.add_log(f"Copied results after Task 2 step {step} to {copy_result['dst_root']}")
                    except Exception as e:
                        st.warning(f"⚠️ Copy after Task 2 step {step} failed: {e}")
                        st.session_state.log_capture.add_log(f"ERROR: Copy after Task 2 step {step} failed: {e}")
                    
                    update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
                    time.sleep(1)
                
                if st.session_state.process_running:
                    st.session_state.process_running = False
                    status_text.success("✅ Pipeline completed! Task 1 and Task 2 finished successfully.")
                    step_text.success("All steps completed")
                    overall_progress_bar.progress(100)
                    step_progress_bar.progress(100)
                    eta_text.text("✅ Completed")
                    st.session_state.log_capture.add_log("Pipeline completed successfully")

                    # New message for Step 3
                    st.markdown(
                        "<div style='text-align:center; padding:15px; background-color:#D4EDDA; color:#155724; border-radius:8px; font-size:18px;'>"
                        "🎉 Done! Please go to <b>Step 3</b> to view your results."
                        "</div>",
                        unsafe_allow_html=True
                    )
                    break

            
            update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
            
            time.sleep(2)
        
        # if not st.session_state.process_running:
        #     rerun_app()

if __name__ == "__main__":
    main()