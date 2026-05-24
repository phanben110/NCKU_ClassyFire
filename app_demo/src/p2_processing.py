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
import pandas as pd
from app_demo.src.title import title_app


app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if app_root not in sys.path:
    sys.path.insert(0, app_root)

import configs
from copy_results_to_final import copy_results_to_final, copy_folder_results_to_final, copy_file_to_final

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


def _get_expected_task1_count():
    try:
        return len(configs.raw_files_to_select or [])
    except Exception:
        return 0


def _collect_clean_result_files(source_folder):
    if not os.path.exists(source_folder):
        return []
    return sorted([
        f for f in os.listdir(source_folder)
        if f.lower().endswith(('.xlsx', '.csv', '.txt'))
    ])


def _read_clean_result_file(path: Path):
    if path.suffix.lower() == '.xlsx':
        return pd.read_excel(path, dtype=str)
    return pd.read_csv(path, sep=None, engine='python', dtype=str)


def check_clean_result_files():
    """Check if files exist in data/clean_result folder."""
    config = Config()
    source_folder = config.SOURCE_FOLDER
    expected_count = _get_expected_task1_count()

    if not os.path.exists(source_folder):
        log_access(f"Folder not found: {source_folder}")
        print(f"❌ Folder not found: {source_folder}")
        return False, []

    files = _collect_clean_result_files(source_folder)
    file_count = len(files)
    log_access(f"Detected {file_count} Task 1 output file(s) in {source_folder}")
    print(f"📂 Detected {file_count} Task 1 output file(s) in '{source_folder}'")

    if expected_count > 0:
        if file_count < expected_count:
            return False, files

        log_access(f"Expected {expected_count} files for Task 1. Waiting 10 seconds for file writes to complete...")
        print("⏳ Expected files found. Waiting 10 seconds to ensure all files are written...")
        time.sleep(10)

        files = _collect_clean_result_files(source_folder)
        file_count = len(files)
        log_access(f"Rechecked Task 1 output files after wait: {file_count} files present")
        print(f"📂 After waiting, {file_count} files are present in '{source_folder}'")

        if file_count < expected_count:
            return False, files

    return file_count > 0, files


def run_main_script():
    """Run the main.py script using subprocess"""
    try:
        log_access("Starting MS-DIAL main.py script execution")
        subprocess.run(
            ["python", "main.py"],
            check=True,
            text=True
        )
        return True
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


def estimate_time_remaining_by_average(done, total, elapsed_time):
    if total <= 0 or done <= 0 or done >= total or elapsed_time is None:
        return "Estimating..."
    if elapsed_time < 1.0 or done < 2:
        return "Estimating..."
    avg_time_per_item = elapsed_time / done
    remaining_seconds = avg_time_per_item * (total - done)
    result = f"{format_duration(remaining_seconds)} remaining"
    print(f"[ETA] {done}/{total} | elapsed={elapsed_time:.1f}s | avg={avg_time_per_item:.2f}s/item | remaining={remaining_seconds:.1f}s → {result}")
    return result


def update_overall_progress(overall_text, overall_progress_bar, eta_text, step_index, total_steps, ratio, description, start_time, eta_text_str=None):
    ratio = min(max(ratio, 0.0), 1.0)
    percent = int(((step_index - 1) + ratio) / total_steps * 100)
    overall_progress_bar.progress(percent)
    overall_text.text(f"Overall progress: {step_index}/{total_steps} — {description} ({percent}%)")
    if eta_text_str:
        eta_text.text(f"⏳ {eta_text_str}")
    else:
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
    first_callback_time = None

    def progress_callback(done, total, message=None):
        nonlocal first_callback_time
        current_progress['done'] = done
        current_progress['total'] = total
        percent = int(done / total * 100) if total else 0
        step_progress_bar.progress(percent)
        label = message or f"{done}/{total}"
        step_text.text(f"{step_name} — {label}")

        if first_callback_time is None:
            first_callback_time = time.time()
        elapsed = time.time() - first_callback_time
        eta_str = estimate_time_remaining_by_average(done, total, elapsed)
        update_overall_progress(
            overall_text, overall_progress_bar, overall_eta_text,
            overall_step_index, total_steps,
            done / total if total else 0.0,
            step_name, start_time, eta_text_str=eta_str
        )

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
    st.rerun()


def display_pipeline_info():
    st.sidebar.markdown("### 🔬 Pipeline Tasks")
    st.sidebar.markdown("""
    **Task 1: MS-DIAL Processing**
    - Run MS-DIAL application (main.py)
    - Process input data files
    - Clean and prepare data
    - Generate multiple .txt files in clean_result folder
    
    **Task 2: Chemical Structure Classification**
    
    Each Task 1 output file is processed independently through 4 steps:
    
    **Step 1: Classification Processing**
    **Step 2: Data Merging**
    **Step 3: Identifier Conversion**
    **Step 4: Final Aggregation**
    
    *Each file goes through all 4 steps before the next file starts.*
    """)


# ─────────────────────────────────────────────
#  UI helper: render the file-status dashboard
# ─────────────────────────────────────────────
def render_file_queue_panel(
    files: list,
    current_idx: int,       # 0-based index of the file being processed right now
    done_indices: set,      # set of 0-based indices already finished
    failed_indices: set,    # set of 0-based indices that failed
):
    """
    Render a compact, styled card panel that shows every file's status:
      ✅  done  |  🔄  active  |  ⏳  waiting  |  ❌  failed
    """
    total = len(files)
    done_count = len(done_indices)
    remaining = total - done_count - (1 if current_idx < total else 0)

    # Header metrics row
    col_done, col_active, col_left = st.columns(3)
    with col_done:
        st.markdown(
            f"<div class='fq-metric fq-done'>✅ Done<br><span>{done_count}</span></div>",
            unsafe_allow_html=True,
        )
    with col_active:
        active_name = files[current_idx] if current_idx < total else "—"
        st.markdown(
            f"<div class='fq-metric fq-active'>🔄 Active<br>"
            f"<span>{current_idx + 1 if current_idx < total else total}</span>"
            # f"<small> / {total}</small></div>",
            unsafe_allow_html=True,
        )
    with col_left:
        st.markdown(
            f"<div class='fq-metric fq-left'>⏳ Remaining<br><span>{max(remaining, 0)}</span></div>",
            unsafe_allow_html=True,
        )

    # Current file highlight
    if current_idx < total:
        st.markdown(
            f"<div class='fq-current-file'>"
            f"<span class='fq-label'>Currently processing:</span> "
            f"<span class='fq-filename'>{files[current_idx]}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # File list scroll box
    rows_html = ""
    for i, fname in enumerate(files):
        if i in failed_indices:
            icon, cls = "❌", "fq-row-failed"
        elif i in done_indices:
            icon, cls = "✅", "fq-row-done"
        elif i == current_idx:
            icon, cls = "🔄", "fq-row-active"
        else:
            icon, cls = "⏳", "fq-row-waiting"

        rows_html += (
            f"<div class='fq-row {cls}'>"
            f"<span class='fq-icon'>{icon}</span>"
            f"<span class='fq-num'>#{i+1:02d}</span>"
            f"<span class='fq-fname'>{html.escape(fname)}</span>"
            f"</div>"
        )

    st.markdown(
        f"<div class='fq-scroll-box'>{rows_html}</div>",
        unsafe_allow_html=True,
    )


def inject_custom_css():
    st.markdown("""
    <style>
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sora', sans-serif;
    }

    /* ── Start button ── */
    .stButton > button {
        width: 100%;
        height: 80px;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 0.04em;
        background: linear-gradient(135deg, #1d4ed8, #2563eb, #3b82f6);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        transition: all 0.25s ease;
        font-family: 'IBM Plex Mono', monospace;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1e40af, #1d4ed8, #2563eb);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45);
        transform: translateY(-2px);
    }

    /* ── Progress bars ── */
    .stProgress > div > div {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        border-radius: 4px;
    }
    .stProgress > div {
        border-radius: 4px;
        box-shadow: none;
        background: #e2e8f0;
    }

    /* ── Log box ── */
    .custom-log-box {
        max-height: 280px;
        overflow-y: auto;
        overflow-x: auto;
        padding: 12px 16px;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        color: #374151;
        font-size: 12.5px;
        font-family: 'IBM Plex Mono', monospace;
        white-space: pre-wrap;
        line-height: 1.55;
    }
    .custom-log-box pre { margin: 0; font-family: inherit; white-space: pre-wrap; }

    /* ── File queue metrics ── */
    .fq-metric {
        text-align: center;
        padding: 10px 4px 8px;
        border-radius: 10px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 6px;
        line-height: 1.3;
    }
    .fq-metric span { font-size: 28px; font-weight: 700; display: block; line-height: 1.1; }
    .fq-metric small { font-size: 14px; opacity: 0.7; }
    .fq-done  { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }
    .fq-active{ background: #eff6ff; color: #2563eb; border: 1px solid #93c5fd; }
    .fq-left  { background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; }

    /* ── Current file banner ── */
    .fq-current-file {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 8px 0 10px;
        font-size: 13.5px;
    }
    .fq-label  { color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }
    .fq-filename { color: #1e3a5f; font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; margin-left: 6px; }

    /* ── File scroll list ── */
    .fq-scroll-box {
        max-height: 220px;
        overflow-y: auto;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        background: #f8fafc;
        padding: 6px 4px;
    }
    .fq-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 12.5px;
        font-family: 'IBM Plex Mono', monospace;
        margin-bottom: 2px;
        transition: background 0.15s;
    }
    .fq-icon { font-size: 13px; flex-shrink: 0; }
    .fq-num  { color: #94a3b8; font-size: 11px; flex-shrink: 0; min-width: 28px; }
    .fq-fname { color: #334155; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

    .fq-row-done    { background: #f0fdf4; }
    .fq-row-done .fq-fname    { color: #86efac; }
    .fq-row-active  { background: #eff6ff; border: 1px solid #bfdbfe; }
    .fq-row-active .fq-fname  { color: #2563eb; font-weight: 600; }
    .fq-row-waiting { background: #ffffff; }
    .fq-row-waiting .fq-fname { color: #64748b; }
    .fq-row-failed  { background: #fef2f2; }
    .fq-row-failed .fq-fname  { color: #ef4444; }

    /* ── Section headers ── */
    h3 { font-family: 'Sora', sans-serif !important; font-weight: 700 !important; letter-spacing: -0.02em; }
    </style>
    """, unsafe_allow_html=True)


def main():
    title_app("ClassyFire - Chemical Analysis Pipeline")
    display_pipeline_info()
    inject_custom_css()

    # ── Session state init ──
    for key, default in [
        ('process_running', False),
        ('task1_completed', False),
        ('main_process', False),
        ('log_capture', LogCapture()),
        ('task1_files', []),           # list of filenames found after Task 1
        ('current_file_idx', 0),       # index of file currently being processed
        ('done_file_indices', set()),
        ('failed_file_indices', set()),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Start button ──
    if not st.session_state.process_running:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            if st.button("🚀 Start Pipeline", type="primary"):
                clean_result_folders()
                st.session_state.process_running = True
                st.session_state.task1_completed = False
                st.session_state.task1_files = []
                st.session_state.current_file_idx = 0
                st.session_state.done_file_indices = set()
                st.session_state.failed_file_indices = set()
                st.session_state.main_process = run_main_script()
                st.session_state.log_capture = LogCapture()
                st.session_state.log_capture.add_log("Pipeline started — cleaned result folders")
                rerun_app()

    # ── Main processing UI ──
    if st.session_state.process_running:
        st.markdown("### Processing Status")

        # Layout: left = progress/log | right = file queue
        col_left, col_right = st.columns([3, 2], gap="large")

        with col_left:
            status_text        = st.empty()
            step_text          = st.empty()

            st.markdown("#### Overall Progress")
            overall_text       = st.empty()
            overall_progress   = st.progress(0)

            st.markdown("#### Current Step")
            step_progress_text = st.empty()
            step_progress_bar  = st.progress(0)
            eta_text           = st.empty()

            st.markdown("#### Recent Activity")
            st.markdown(
                "_Live log — scroll to review events._",
                unsafe_allow_html=True,
            )
            recent_log_placeholder = st.empty()

        with col_right:
            st.markdown("#### 📂 File Queue")
            file_queue_placeholder = st.empty()

        # ── Timing ──
        start_time   = time.time()
        max_wait     = 3600 * 5

        # ── Helper: refresh file-queue panel ──
        def _refresh_file_panel():
            with file_queue_placeholder.container():
                if st.session_state.task1_files:
                    render_file_queue_panel(
                        st.session_state.task1_files,
                        st.session_state.current_file_idx,
                        st.session_state.done_file_indices,
                        st.session_state.failed_file_indices,
                    )
                else:
                    st.info("Waiting for Task 1 to produce files…")

        # ════════════════════════════════════════════════════════════
        #  MAIN LOOP
        # ════════════════════════════════════════════════════════════
        while st.session_state.process_running:

            # ── Timeout guard ──
            if time.time() - start_time > max_wait:
                st.error("Process timeout — stopping pipeline")
                st.session_state.log_capture.add_log("ERROR: Process timeout")
                st.session_state.process_running = False
                break

            # ────────────────────────────────────────────────────────
            #  TASK 1 — wait for MS-DIAL to produce .txt files
            # ────────────────────────────────────────────────────────
            if not st.session_state.task1_completed:
                has_files, files = check_clean_result_files()

                # Update overall bar (task1 = slot 1 of N)
                total_t1_slots = 1
                update_overall_progress(
                    overall_text, overall_progress, eta_text,
                    1, 1 + 1,   # rough placeholder; will be recalculated per file
                    0.0, "MS-DIAL processing", start_time
                )
                step_progress_text.text("MS-DIAL progress — waiting…")
                step_progress_bar.progress(0)
                _refresh_file_panel()

                if has_files:
                    st.session_state.task1_completed = True
                    st.session_state.task1_files = files          # store list
                    st.session_state.current_file_idx = 0
                    st.session_state.done_file_indices = set()
                    st.session_state.failed_file_indices = set()

                    log_msg = f"Task 1 completed — {len(files)} file(s) detected in clean_result"
                    log_access(log_msg)
                    st.session_state.log_capture.add_log(log_msg)
                    status_text.success(f"✅ Task 1 done — {len(files)} file(s) ready for Task 2")

                    # Copy each raw Task-1 file to final folder as-is
                    config = Config()
                    dst_root = Path(configs.final_result_path)
                    dst_root.mkdir(parents=True, exist_ok=True)
                    for fname in files:
                        src = Path(config.SOURCE_FOLDER) / fname
                        try:
                            copied = copy_file_to_final(src, dst_root, 'Task1_CleanResult', overwrite=True)
                            if copied:
                                st.session_state.log_capture.add_log(f"Copied Task1 file: {fname}")
                        except Exception as e:
                            st.session_state.log_capture.add_log(f"WARN: copy failed for {fname}: {e}")

                    step_progress_text.text(f"MS-DIAL completed — {len(files)} file(s)")
                    step_progress_bar.progress(100)
                    _refresh_file_panel()
                    update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
                    time.sleep(2)
                else:
                    status_text.text("Task 1: Running MS-DIAL — processing data files…")
                    step_text.text("Task 1 in progress")
                    step_progress_text.text("MS-DIAL running — 0/1")
                    step_progress_bar.progress(0)
                    update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
                    time.sleep(2)
                    continue

            # ────────────────────────────────────────────────────────
            #  TASK 2 — process each Task-1 output file individually
            # ────────────────────────────────────────────────────────
            if st.session_state.task1_completed:
                config     = Config()
                all_files  = st.session_state.task1_files
                n_files    = len(all_files)

                # Total "slots" for overall bar: 1 (Task1) + 4 steps × n_files
                total_slots = 1 + 4 * n_files

                all_ok = True

                for file_idx, fname in enumerate(all_files):
                    st.session_state.current_file_idx = file_idx
                    _refresh_file_panel()

                    file_path = Path(config.SOURCE_FOLDER) / fname
                    log_access(f"Task 2: starting file {file_idx+1}/{n_files}: {fname}")
                    st.session_state.log_capture.add_log(
                        f"── File {file_idx+1}/{n_files}: {fname} ──"
                    )

                    # Build a temporary per-file source folder
                    # so the pipeline reads exactly one file
                    per_file_src = Path(config.SOURCE_FOLDER).parent / f"_single_file_src_{file_idx}"
                    if per_file_src.exists():
                        shutil.rmtree(per_file_src)
                    per_file_src.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, per_file_src / fname)

                    # Build a per-file output root (keeps outputs separate)
                    file_stem = Path(fname).stem
                    per_file_out = Path(config.METABOANALYST_FOLDER).parent / f"output_{file_stem}"
                    per_file_out.mkdir(parents=True, exist_ok=True)

                    # Instantiate a fresh pipeline for this file
                    pipeline = ChemicalAnalysisPipeline(Config())
                    pipeline.config.SOURCE_FOLDER      = str(per_file_src)
                    pipeline.config.GROUPING_FOLDER    = str(per_file_out / "grouping")
                    pipeline.config.FINAL_RESULT_FOLDER= str(per_file_out / "final_result")
                    pipeline.config.CONVERT_RESULT_FOLDER = str(per_file_out / "convert_result")
                    pipeline.config.METABOANALYST_FOLDER  = str(per_file_out / "metaboanalyst")

                    step_names = {
                        1: "Classification Processing",
                        2: "Data Merging",
                        3: "Identifier Conversion",
                        4: "Final Aggregation",
                    }

                    file_ok = True
                    for step in range(1, 5):
                        # overall slot = 1 (Task1 done) + steps done before this file + (step-1)
                        overall_slot = 1 + file_idx * 4 + step
                        step_name = step_names[step]

                        status_text.info(
                            f"File {file_idx+1}/{n_files}: {fname}  |  Step {step}/4 — {step_name}"
                        )
                        step_progress_text.text(f"{step_name} — starting…")
                        step_progress_bar.progress(0)
                        update_overall_progress(
                            overall_text, overall_progress, eta_text,
                            overall_slot, total_slots,
                            0.0, f"[{file_idx+1}/{n_files}] {step_name}", start_time
                        )
                        _refresh_file_panel()

                        success = run_pipeline_step(
                            step, pipeline,
                            status_text, step_text,
                            st.session_state.log_capture,
                            step_progress_bar,
                            overall_text, overall_progress, eta_text,
                            overall_slot, total_slots, start_time
                        )

                        if not success:
                            st.error(f"❌ File '{fname}' failed at step {step}")
                            st.session_state.failed_file_indices.add(file_idx)
                            file_ok = False
                            all_ok  = False
                            break

                        # Copy step results to final folder
                        try:
                            step_folder_map = {
                                1: (f'Task2_Step1_{file_stem}_Grouping',     Path(pipeline.config.GROUPING_FOLDER)),
                                2: (f'Task2_Step2_{file_stem}_Final',         Path(pipeline.config.FINAL_RESULT_FOLDER)),
                                3: (f'Task2_Step3_{file_stem}_Converted',     Path(pipeline.config.CONVERT_RESULT_FOLDER)),
                                4: (f'Task2_Step4_{file_stem}_Metaboanalyst', Path(pipeline.config.METABOANALYST_FOLDER)),
                            }
                            prefix, folder = step_folder_map[step]
                            copy_result = copy_folder_results_to_final(prefix, folder, overwrite=True)
                            st.session_state.log_capture.add_log(
                                f"Copied {copy_result['copied_count']} file(s) → {copy_result['dst_root']}"
                            )
                        except Exception as e:
                            st.warning(f"⚠️ Copy after step {step} for '{fname}' failed: {e}")
                            st.session_state.log_capture.add_log(
                                f"ERROR: copy after step {step} for {fname}: {e}"
                            )

                        update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
                        time.sleep(0.5)

                    # Clean up temp source dir
                    try:
                        shutil.rmtree(per_file_src)
                    except Exception:
                        pass

                    if file_ok:
                        st.session_state.done_file_indices.add(file_idx)
                        st.session_state.log_capture.add_log(
                            f"✅ File {file_idx+1}/{n_files} complete: {fname}"
                        )
                    _refresh_file_panel()
                    update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
                    time.sleep(1)

                # ── All files done ──
                st.session_state.process_running = False
                if all_ok:
                    status_text.success("✅ Pipeline completed! All files processed successfully.")
                else:
                    n_fail = len(st.session_state.failed_file_indices)
                    status_text.warning(f"⚠️ Pipeline finished with {n_fail} failed file(s).")

                step_text.success("All steps completed")
                overall_progress.progress(100)
                step_progress_bar.progress(100)
                eta_text.text("✅ Completed")
                st.session_state.log_capture.add_log("Pipeline finished")
                _refresh_file_panel()

                dst_root_display = getattr(configs, 'final_result_path', 'the output folder')
                st.info(f"📁 Results have been saved to: **{dst_root_display}**")
                break

            update_recent_activity(recent_log_placeholder, st.session_state.log_capture)
            time.sleep(2)


if __name__ == "__main__":
    main()