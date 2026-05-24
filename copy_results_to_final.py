import json
import os
import shutil
import time
import errno
from pathlib import Path


def load_config(config_path: Path) -> dict:
    with config_path.open('r', encoding='utf-8') as f:
        return json.load(f)


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def make_unique_target(target: Path) -> Path:
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = target.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def safe_copy(src: Path, dst: Path, max_retries: int = 5, delay: float = 0.5):
    """Copy a file with retries on file-in-use / permission errors (e.g. Windows WinError 32).

    Retries with exponential backoff when the OS reports the file is in use.
    """
    src_path = Path(src)
    dst_path = Path(dst)
    for attempt in range(max_retries):
        try:
            shutil.copy2(src_path, dst_path)
            return
        except PermissionError as e:
            winerr = getattr(e, 'winerror', None)
            errnum = getattr(e, 'errno', None)
            if winerr == 32 or errnum in (errno.EACCES, errno.EPERM):
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))
                    continue
            raise
        except OSError as e:
            if getattr(e, 'winerror', None) == 32 or getattr(e, 'errno', None) == errno.EACCES:
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))
                    continue
            raise


def copy_file_to_final(src_file: Path, dst_folder: Path, prefix: str, overwrite: bool = True):
    if not src_file.exists() or not src_file.is_file():
        return None

    dst_name = f"{prefix}_{src_file.name}"
    dst_path = dst_folder / dst_name
    ensure_dir(dst_path.parent)

    if dst_path.exists() and not overwrite:
        dst_path = make_unique_target(dst_path)

    safe_copy(src_file, dst_path)
    return str(dst_path)


def copy_folder_to_final(src_folder: Path, dst_folder: Path, prefix: str, overwrite: bool = True):
    if not src_folder.exists() or not src_folder.is_dir():
        print(f"Skipping missing folder: {src_folder}")
        return []

    copied_files = []
    for item in sorted(src_folder.iterdir()):
        if item.is_file():
            copied = copy_file_to_final(item, dst_folder, prefix, overwrite=overwrite)
            if copied:
                copied_files.append(copied)
        elif item.is_dir():
            for sub_item in sorted(item.rglob('*')):
                if sub_item.is_file():
                    rel_path = sub_item.relative_to(src_folder)
                    dst_name = f"{prefix}_{rel_path.as_posix().replace('/', '_')}"
                    dst_path = dst_folder / dst_name
                    ensure_dir(dst_path.parent)
                    if dst_path.exists() and not overwrite:
                        dst_path = make_unique_target(dst_path)
                    safe_copy(sub_item, dst_path)
                    copied_files.append(str(dst_path))
    if copied_files:
        print(f"Copied {len(copied_files)} files from {src_folder} to {dst_folder}")
    return copied_files


def copy_results_to_final(config_path: Path = None, source_map: list = None, overwrite: bool = True):
    root = Path(__file__).resolve().parent
    config_path = Path(config_path) if config_path else root / 'msdial_config.json'

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = load_config(config_path)
    final_result_path = config.get('final_result_path')

    if not final_result_path:
        raise ValueError('final_result_path is missing in msdial_config.json')

    dst_root = Path(final_result_path)
    ensure_dir(dst_root)

    if source_map is None:
        source_map = [
            ('Task1_CleanResult', root / 'data' / 'clean_result'),
            ('Task2_Step1_Grouping', root / 'data' / 'grouping_result'),
            ('Task2_Step2_Final', root / 'data' / 'final_result'),
            ('Task2_Step3_Converted', root / 'data' / 'convert_result'),
            ('Task2_Step4_MetaboanalystPubchem', root / 'data' / 'metaboanalyst_pubchem'),
        ]

    copied_files = []
    for prefix, src_folder in source_map:
        copied_files.extend(copy_folder_to_final(src_folder, dst_root, prefix, overwrite=overwrite))

    if not copied_files:
        print('No result files were copied. Check the source directories and config path.')
    else:
        print(f'Total files copied: {len(copied_files)}')

    return {
        'dst_root': str(dst_root),
        'copied_count': len(copied_files),
        'files': copied_files,
    }


def copy_folder_results_to_final(prefix: str, src_folder: Path, overwrite: bool = True, config_path: Path = None):
    root = Path(__file__).resolve().parent
    config_path = Path(config_path) if config_path else root / 'msdial_config.json'

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = load_config(config_path)
    final_result_path = config.get('final_result_path')

    if not final_result_path:
        raise ValueError('final_result_path is missing in msdial_config.json')

    dst_root = Path(final_result_path)
    ensure_dir(dst_root)

    copied_files = copy_folder_to_final(src_folder, dst_root, prefix, overwrite=overwrite)
    if not copied_files:
        print(f'No files copied from {src_folder}')
    return {
        'dst_root': str(dst_root),
        'copied_count': len(copied_files),
        'files': copied_files,
    }


def main():
    root = Path(__file__).resolve().parent
    config_path = root / 'msdial_config.json'

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = load_config(config_path)
    final_result_path = config.get('final_result_path')

    if not final_result_path:
        raise ValueError('final_result_path is missing in msdial_config.json')

    dst_root = Path(final_result_path)
    ensure_dir(dst_root)

    source_map = [
        ('Task1_Grouping', root / 'data' / 'grouping_result'),
        ('Task2_Step1_Final', root / 'data' / 'final_result'),
        ('Task2_Step2_Converted', root / 'data' / 'convert_result'),
        ('Task2_Step3_MetaboanalystPubchem', root / 'data' / 'metaboanalyst_pubchem'),
        ('Task2_Step4_MetaboanalystResult', root / 'data' / 'metaboanalyst_result'),
    ]

    total_copied = 0
    for prefix, src_folder in source_map:
        total_copied += copy_results(src_folder, dst_root, prefix)

    if total_copied == 0:
        print('No result files were copied. Check the source directories and config path.')
    else:
        print(f'Total files copied: {total_copied}')


if __name__ == '__main__':
    main()
