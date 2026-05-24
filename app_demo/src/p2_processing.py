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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import pandas as pd
from app_demo.src.title import title_app


app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if app_root not in sys.path:
    sys.path.insert(0, app_root)

import configs
from copy_results_to_final import copy_folder_results_to_final, copy_file_to_final

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename='runtime.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_access(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{current_time} - Processing - {message}")
    print(f"{current_time} - Processing - {message}")


# ─── Folder helpers ─────────────────────────────────────────────────────────────
def clean_result_folders():
    config = Config()
    for folder in [config.SOURCE_FOLDER, config.GROUPING_FOLDER,
                   config.FINAL_RESULT_FOLDER, config.CONVERT_RESULT_FOLDER,
                   config.METABOANALYST_FOLDER]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
    print("Folders cleaned.")


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


def check_clean_result_files():
    config = Config()
    source_folder = config.SOURCE_FOLDER
    expected_count = _get_expected_task1_count()

    if not os.path.exists(source_folder):
        return False, []

    files = _collect_clean_result_files(source_folder)
    if expected_count > 0:
        if len(files) < expected_count:
            return False, files
        time.sleep(10)
        files = _collect_clean_result_files(source_folder)
        if len(files) < expected_count:
            return False, files

    return len(files) > 0, files


def run_main_script():
    try:
        log_access("Starting MS-DIAL msdial_new.py script execution")
        subprocess.run(["python", "msdial_new.py"], check=True, text=True)
        return True
    except Exception as e:
        log_access(f"Error running msdial_new.py: {str(e)}")
        return False


# ─── Shared progress event types ───────────────────────────────────────────────
#
#  Every worker pushes dicts onto a thread-safe queue.Queue.
#  The main Streamlit thread drains the queue and updates UI.
#
#  Event shapes:
#    {'type': 'log',      'file_idx': i, 'msg': str}
#    {'type': 'step_start','file_idx': i, 'step': 1-4}
#    {'type': 'step_prog', 'file_idx': i, 'step': 1-4, 'done': int, 'total': int, 'msg': str}
#    {'type': 'step_done', 'file_idx': i, 'step': 1-4}
#    {'type': 'step_fail', 'file_idx': i, 'step': 1-4, 'error': str}
#    {'type': 'file_done', 'file_idx': i}
#    {'type': 'file_fail', 'file_idx': i, 'step': int, 'error': str}


STEP_NAMES = {
    1: "Classification",
    2: "Merging",
    3: "ID Conversion",
    4: "Aggregation",
}


def _worker_process_file(file_idx: int, fname: str, config: Config,
                         event_queue: queue.Queue):
    """
    Worker function — runs in a ThreadPoolExecutor thread.
    Processes one file through all 4 pipeline steps.
    Communicates progress exclusively via event_queue (thread-safe).
    Never touches Streamlit directly.
    """
    def push(event: dict):
        event['file_idx'] = file_idx
        event_queue.put(event)

    push({'type': 'log', 'msg': f"── Starting file: {fname} ──"})

    # ── Build per-file isolated directories ────────────────────────────────────
    file_stem = Path(fname).stem
    base = Path(config.SOURCE_FOLDER).parent

    per_file_src = base / f"_src_{file_idx}_{file_stem}"
    per_file_out = base / f"_out_{file_idx}_{file_stem}"

    for d in [per_file_src, per_file_out]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    shutil.copy2(Path(config.SOURCE_FOLDER) / fname, per_file_src / fname)

    # ── Configure pipeline for this file ───────────────────────────────────────
    pipeline = ChemicalAnalysisPipeline(Config())
    pipeline.config.SOURCE_FOLDER         = str(per_file_src)
    pipeline.config.GROUPING_FOLDER       = str(per_file_out / "grouping")
    pipeline.config.FINAL_RESULT_FOLDER   = str(per_file_out / "final_result")
    pipeline.config.CONVERT_RESULT_FOLDER = str(per_file_out / "convert_result")
    pipeline.config.METABOANALYST_FOLDER  = str(per_file_out / "metaboanalyst")

    step_folder_map = {
        1: (f'Task2_Step1_{file_stem}_Grouping',     Path(pipeline.config.GROUPING_FOLDER)),
        2: (f'Task2_Step2_{file_stem}_Final',         Path(pipeline.config.FINAL_RESULT_FOLDER)),
        3: (f'Task2_Step3_{file_stem}_Converted',     Path(pipeline.config.CONVERT_RESULT_FOLDER)),
        4: (f'Task2_Step4_{file_stem}_Metaboanalyst', Path(pipeline.config.METABOANALYST_FOLDER)),
    }

    # ── Run steps 1-4 sequentially for this file ───────────────────────────────
    for step in range(1, 5):
        push({'type': 'step_start', 'step': step})
        push({'type': 'log', 'msg': f"[{fname}] Step {step}/4 — {STEP_NAMES[step]}"})

        def make_callback(s):
            def progress_callback(done, total, message=None):
                push({'type': 'step_prog', 'step': s,
                      'done': done, 'total': total,
                      'msg': message or f"{done}/{total}"})
            return progress_callback

        try:
            pipeline.run_step(step, progress_callback=make_callback(step))
        except Exception as e:
            push({'type': 'step_fail', 'step': step, 'error': str(e)})
            push({'type': 'file_fail', 'step': step, 'error': str(e),
                  'msg': f"[{fname}] ❌ failed at step {step}: {e}"})
            push({'type': 'log', 'msg': f"[{fname}] ERROR step {step}: {e}"})
            # Clean up temp dirs
            try:
                shutil.rmtree(per_file_src)
                shutil.rmtree(per_file_out)
            except Exception:
                pass
            return  # stop processing this file

        # Copy results to final folder
        try:
            prefix, folder = step_folder_map[step]
            copy_result = copy_folder_results_to_final(prefix, folder, overwrite=True)
            push({'type': 'log',
                  'msg': f"[{fname}] Step {step} → copied {copy_result['copied_count']} file(s)"})
        except Exception as e:
            push({'type': 'log', 'msg': f"[{fname}] WARN copy step {step}: {e}"})

        push({'type': 'step_done', 'step': step})

    # ── Cleanup ────────────────────────────────────────────────────────────────
    try:
        shutil.rmtree(per_file_src)
    except Exception:
        pass

    push({'type': 'file_done', 'msg': f"[{fname}] ✅ all 4 steps complete"})
    push({'type': 'log', 'msg': f"[{fname}] ✅ completed successfully"})


# ─── Thread-safe log capture ────────────────────────────────────────────────────
class LogCapture:
    def __init__(self):
        self._lock = threading.Lock()
        self.logs: list[str] = []

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        with self._lock:
            self.logs.append(entry)
            if len(self.logs) > 200:
                self.logs = self.logs[-200:]

    def snapshot(self, n=80) -> list[str]:
        with self._lock:
            return list(self.logs[-n:])


# ─── Time helpers ───────────────────────────────────────────────────────────────
def format_duration(seconds: float) -> str:
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def eta_from_done(done, total, elapsed) -> str:
    if total <= 0 or done <= 0 or done >= total or elapsed < 1 or done < 2:
        return "estimating…"
    remaining = (elapsed / done) * (total - done)
    return f"{format_duration(remaining)} remaining"


# ─── CSS injection ──────────────────────────────────────────────────────────────
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;500;700&display=swap');

    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

    /* Start button */
    .stButton > button {
        width: 100%; height: 80px; font-size: 22px; font-weight: 700;
        letter-spacing: 0.04em;
        background: linear-gradient(135deg, #1d4ed8, #2563eb, #3b82f6);
        color: #fff; border: none; border-radius: 12px;
        box-shadow: 0 4px 14px rgba(37,99,235,0.35);
        transition: all 0.25s ease; font-family: 'IBM Plex Mono', monospace;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1e40af, #1d4ed8, #2563eb);
        box-shadow: 0 6px 20px rgba(37,99,235,0.45);
        transform: translateY(-2px);
    }

    /* Progress bars */
    .stProgress > div > div { background: linear-gradient(90deg,#3b82f6,#60a5fa); border-radius:4px; }
    .stProgress > div { border-radius:4px; box-shadow:none; background:#e2e8f0; }

    /* Log box */
    .custom-log-box {
        max-height: 260px; overflow-y: auto; overflow-x: auto;
        padding: 12px 16px; background: #f8fafc; border: 1px solid #cbd5e1;
        border-radius: 10px; color: #374151; font-size: 12px;
        font-family: 'IBM Plex Mono', monospace; white-space: pre-wrap; line-height: 1.55;
    }
    .custom-log-box pre { margin:0; font-family:inherit; white-space:pre-wrap; }

    /* File queue metrics */
    .fq-metric {
        text-align:center; padding:10px 4px 8px; border-radius:10px;
        font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:600;
        letter-spacing:0.06em; text-transform:uppercase; margin-bottom:6px; line-height:1.3;
    }
    .fq-metric span { font-size:26px; font-weight:700; display:block; line-height:1.1; }
    .fq-done   { background:#f0fdf4; color:#16a34a; border:1px solid #86efac; }
    .fq-active { background:#eff6ff; color:#2563eb; border:1px solid #93c5fd; }
    .fq-left   { background:#fffbeb; color:#d97706; border:1px solid #fcd34d; }
    .fq-failed { background:#fef2f2; color:#dc2626; border:1px solid #fca5a5; }

    /* Per-file progress card */
    .fcard {
        border:1px solid #e2e8f0; border-radius:10px; padding:8px 12px;
        margin-bottom:6px; background:#fff; font-size:12px;
    }
    .fcard-active { border-color:#93c5fd; background:#eff6ff; }
    .fcard-done   { border-color:#86efac; background:#f0fdf4; opacity:0.75; }
    .fcard-failed { border-color:#fca5a5; background:#fef2f2; }
    .fcard-wait   { opacity:0.55; }
    .fcard-title  { font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:11.5px;
                    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:4px; }
    .fcard-steps  { display:flex; gap:4px; flex-wrap:wrap; }
    .fstep {
        font-size:10px; padding:1px 6px; border-radius:4px; font-family:'IBM Plex Mono',monospace;
        font-weight:600; border:1px solid transparent;
    }
    .fstep-done    { background:#dcfce7; color:#15803d; border-color:#86efac; }
    .fstep-active  { background:#dbeafe; color:#1d4ed8; border-color:#93c5fd; }
    .fstep-waiting { background:#f1f5f9; color:#94a3b8; border-color:#e2e8f0; }
    .fstep-failed  { background:#fee2e2; color:#b91c1c; border-color:#fca5a5; }

    /* Scroll list */
    .fq-scroll { max-height:420px; overflow-y:auto; }

    h3 { font-family:'Sora',sans-serif!important; font-weight:700!important; letter-spacing:-0.02em; }
    </style>
    """, unsafe_allow_html=True)


# ─── File queue panel renderer ──────────────────────────────────────────────────
def render_file_queue_panel(file_states: dict, all_files: list):
    """
    file_states[fname] = {
        'status': 'waiting' | 'active' | 'done' | 'failed',
        'steps': {1: 'waiting'|'active'|'done'|'failed', ...},
        'step_prog': {1: (done, total), ...}
    }
    """
    total      = len(all_files)
    done_count = sum(1 for s in file_states.values() if s['status'] == 'done')
    active_count = sum(1 for s in file_states.values() if s['status'] == 'active')
    fail_count = sum(1 for s in file_states.values() if s['status'] == 'failed')
    remaining  = total - done_count - active_count - fail_count

    # ── Metric row ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='fq-metric fq-done'>✅ Done<br><span>{done_count}</span></div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='fq-metric fq-active'>🔄 Active<br><span>{active_count}</span></div>",
                    unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='fq-metric fq-left'>⏳ Queue<br><span>{remaining}</span></div>",
                    unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='fq-metric fq-failed'>❌ Failed<br><span>{fail_count}</span></div>",
                    unsafe_allow_html=True)

    # ── Per-file cards ──
    cards_html = "<div class='fq-scroll'>"
    for fname in all_files:
        state  = file_states.get(fname, {'status': 'waiting', 'steps': {}, 'step_prog': {}})
        status = state['status']

        cls_map = {'active': 'fcard-active', 'done': 'fcard-done',
                   'failed': 'fcard-failed', 'waiting': 'fcard-wait'}
        icon_map = {'active': '🔄', 'done': '✅', 'failed': '❌', 'waiting': '⏳'}

        card_cls = cls_map.get(status, 'fcard-wait')
        icon     = icon_map.get(status, '⏳')

        steps_html = ""
        for s in range(1, 5):
            s_status = state['steps'].get(s, 'waiting')
            s_cls = {
                'done': 'fstep-done', 'active': 'fstep-active',
                'failed': 'fstep-failed', 'waiting': 'fstep-waiting',
            }.get(s_status, 'fstep-waiting')

            label = STEP_NAMES.get(s, f"S{s}")
            prog = state['step_prog'].get(s)
            prog_txt = f" {prog[0]}/{prog[1]}" if prog and s_status == 'active' else ""
            steps_html += f"<span class='fstep {s_cls}'>{label}{prog_txt}</span>"

        short_name = html.escape(fname[:40] + ("…" if len(fname) > 40 else ""))
        cards_html += (
            f"<div class='fcard {card_cls}'>"
            f"<div class='fcard-title'>{icon} {short_name}</div>"
            f"<div class='fcard-steps'>{steps_html}</div>"
            f"</div>"
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)


# ─── Sidebar info ───────────────────────────────────────────────────────────────
def display_pipeline_info():
    st.sidebar.markdown("### 🔬 Pipeline Tasks")
    st.sidebar.markdown("""
**Task 1: MS-DIAL Processing**
- Run msdial_new.py, produce .txt files in clean_result

**Task 2: Parallel Classification**
- Each Task 1 file processed independently
- Files run **in parallel** (configurable workers)
- 4 steps per file: Classification → Merge → ID Conversion → Aggregation
""")


# ─── Main app ───────────────────────────────────────────────────────────────────
def main():
    title_app("ClassyFire - Chemical Analysis Pipeline")
    display_pipeline_info()
    inject_custom_css()

    # ── Session state ──
    defaults = {
        'process_running':   False,
        'task1_completed':   False,
        'main_process':      False,
        'log_capture':       LogCapture(),
        'task1_files':       [],
        'file_states':       {},   # fname → state dict (see render_file_queue_panel)
        'event_queue':       None,
        'executor':          None,
        'futures':           {},
        'pipeline_done':     False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Worker count slider (shown only when idle) ──
    if not st.session_state.process_running:
        st.markdown("#### ⚙️ Parallel workers")
        max_workers = st.slider(
            "Number of files to process simultaneously",
            min_value=1, max_value=8, value=3,
            help="Higher = faster overall, but uses more CPU/RAM and API quota."
        )

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            if st.button("🚀 Start Pipeline", type="primary"):
                clean_result_folders()
                st.session_state.process_running = True
                st.session_state.task1_completed = False
                st.session_state.pipeline_done   = False
                st.session_state.task1_files     = []
                st.session_state.file_states     = {}
                st.session_state.event_queue     = queue.Queue()
                st.session_state.futures         = {}
                st.session_state.log_capture     = LogCapture()
                st.session_state._max_workers    = max_workers
                st.session_state.main_process    = run_main_script()
                st.session_state.log_capture.add_log("Pipeline started")
                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    #  PROCESSING UI
    # ══════════════════════════════════════════════════════════════════════════
    if not st.session_state.process_running:
        return

    st.markdown("### Processing Status")

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        status_text      = st.empty()
        overall_label    = st.empty()
        overall_bar      = st.progress(0)
        eta_text         = st.empty()
        st.markdown("#### Recent Activity")
        recent_log_ph    = st.empty()

    with col_right:
        max_w_display    = st.session_state.get('_max_workers', 3)
        st.markdown(f"#### 📂 File Queue  *({max_w_display} workers)*")
        file_panel_ph    = st.empty()

    start_time     = time.time()
    max_wait       = 3600 * 5
    event_queue    = st.session_state.event_queue

    # ── helpers ──
    def refresh_panel():
        with file_panel_ph.container():
            if st.session_state.task1_files:
                render_file_queue_panel(
                    st.session_state.file_states,
                    st.session_state.task1_files,
                )
            else:
                st.info("Waiting for Task 1 to produce files…")

    def refresh_log():
        logs = st.session_state.log_capture.snapshot(80)
        body = html.escape("\n".join(logs)) if logs else "No activity yet."
        recent_log_ph.markdown(
            f"<div class='custom-log-box'><pre>{body}</pre></div>",
            unsafe_allow_html=True,
        )

    def refresh_overall():
        all_files  = st.session_state.task1_files
        n          = len(all_files)
        states     = st.session_state.file_states
        done_count = sum(1 for s in states.values() if s["status"] == "done")
        fail_count = sum(1 for s in states.values() if s["status"] == "failed")
        finished   = done_count + fail_count
        elapsed    = time.time() - start_time

        # Granular progress: each file has 4 steps, each step reports item-level progress
        total_units = n * 4
        done_units  = 0.0
        for state in states.values():
            for s in range(1, 5):
                s_status = state["steps"].get(s, "waiting")
                if s_status == "done":
                    done_units += 1.0
                elif s_status == "active":
                    prog = state["step_prog"].get(s)
                    if prog and prog[1] > 0:
                        done_units += prog[0] / prog[1]

        ratio = done_units / total_units if total_units > 0 else 0.0
        pct   = int(ratio * 100)

        if ratio > 0.005 and elapsed > 3:
            remaining = elapsed * (1.0 - ratio) / ratio
            eta = f"{format_duration(remaining)} remaining"
        else:
            eta = "estimating…"

        overall_label.text(
            f"Files completed: {finished}/{n}  ({done_count} ✅  {fail_count} ❌)  —  {pct}%"
        )
        overall_bar.progress(pct)
        eta_text.text(f"⏳ {eta}")

    def drain_events():
        """Process all pending events from worker threads. Called by main thread only."""
        states = st.session_state.file_states
        log    = st.session_state.log_capture
        files  = st.session_state.task1_files

        while True:
            try:
                ev = event_queue.get_nowait()
            except queue.Empty:
                break

            fi   = ev.get('file_idx')
            fname = files[fi] if (fi is not None and fi < len(files)) else None

            etype = ev['type']

            if etype == 'log':
                log.add_log(ev.get('msg', ''))

            elif etype == 'step_start' and fname:
                step = ev['step']
                states[fname]['status'] = 'active'
                states[fname]['steps'][step] = 'active'

            elif etype == 'step_prog' and fname:
                step = ev['step']
                states[fname]['step_prog'][step] = (ev['done'], ev['total'])

            elif etype == 'step_done' and fname:
                step = ev['step']
                states[fname]['steps'][step] = 'done'
                states[fname]['step_prog'].pop(step, None)

            elif etype == 'step_fail' and fname:
                step = ev['step']
                states[fname]['steps'][step] = 'failed'

            elif etype == 'file_done' and fname:
                states[fname]['status'] = 'done'
                log.add_log(ev.get('msg', f'{fname} done'))

            elif etype == 'file_fail' and fname:
                states[fname]['status'] = 'failed'
                log.add_log(ev.get('msg', f'{fname} failed'))

    # ══════════════════════════════════════════════════════════════════════════
    #  MAIN POLLING LOOP
    # ══════════════════════════════════════════════════════════════════════════
    while st.session_state.process_running:

        if time.time() - start_time > max_wait:
            st.error("Timeout — stopping pipeline")
            st.session_state.process_running = False
            break

        # ── Task 1: wait for MS-DIAL output files ──────────────────────────
        if not st.session_state.task1_completed:
            status_text.info("⏳ Task 1: MS-DIAL running…")
            overall_label.text("Waiting for Task 1 output files…")
            overall_bar.progress(0)
            refresh_panel()
            refresh_log()

            has_files, files = check_clean_result_files()
            if not has_files:
                time.sleep(2)
                continue

            # Task 1 done
            st.session_state.task1_completed = True
            st.session_state.task1_files     = files
            st.session_state.file_states     = {
                f: {'status': 'waiting', 'steps': {s: 'waiting' for s in range(1, 5)}, 'step_prog': {}}
                for f in files
            }

            # Copy raw Task-1 files to final folder
            config   = Config()
            dst_root = Path(configs.final_result_path)
            dst_root.mkdir(parents=True, exist_ok=True)
            for fname in files:
                src = Path(config.SOURCE_FOLDER) / fname
                try:
                    copy_file_to_final(src, dst_root, 'Task1_CleanResult', overwrite=True)
                    st.session_state.log_capture.add_log(f"Copied Task1 file: {fname}")
                except Exception as e:
                    st.session_state.log_capture.add_log(f"WARN copy {fname}: {e}")

            st.session_state.log_capture.add_log(
                f"Task 1 done — {len(files)} file(s). Launching {st.session_state._max_workers} parallel worker(s)."
            )
            status_text.success(
                f"✅ Task 1 done — {len(files)} file(s). Starting parallel Task 2…"
            )

            # ── Launch ThreadPoolExecutor ──────────────────────────────────
            config = Config()
            executor = ThreadPoolExecutor(max_workers=st.session_state._max_workers)
            futures  = {}
            for idx, fname in enumerate(files):
                fut = executor.submit(
                    _worker_process_file,
                    idx, fname, config, event_queue
                )
                futures[fut] = fname

            st.session_state.executor = executor
            st.session_state.futures  = futures
            refresh_panel()
            refresh_log()
            time.sleep(1)
            continue

        # ── Task 2: drain events, update UI, check completion ──────────────
        drain_events()
        refresh_overall()
        refresh_panel()
        refresh_log()

        futures = st.session_state.futures
        if futures:
            # Check if all futures are done
            all_done = all(f.done() for f in futures)

            if not all_done:
                status_text.info(
                    f"🔄 Task 2 running — {st.session_state._max_workers} parallel worker(s)…"
                )
                time.sleep(1)
                continue

            # All workers finished — one final drain
            drain_events()
            refresh_overall()
            refresh_panel()
            refresh_log()

            # Shutdown executor
            try:
                st.session_state.executor.shutdown(wait=False)
            except Exception:
                pass

            states     = st.session_state.file_states
            fail_count = sum(1 for s in states.values() if s['status'] == 'failed')
            done_count = sum(1 for s in states.values() if s['status'] == 'done')

            st.session_state.process_running = False
            overall_bar.progress(100)

            if fail_count == 0:
                status_text.success(
                    f"✅ Pipeline complete — {done_count} file(s) processed successfully."
                )
            else:
                status_text.warning(
                    f"⚠️ Pipeline finished — {done_count} succeeded, {fail_count} failed."
                )

            dst = str(Path(getattr(configs, 'final_result_path', 'output')).resolve())
            st.info(f"📁 Results saved to: **{dst}**")
            break

        time.sleep(1)


if __name__ == "__main__":
    main()