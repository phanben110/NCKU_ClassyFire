import time
import shutil
import os

# Đường dẫn file nguồn và thư mục đích
source_file = os.path.join('data', 'test', 'Pool_ur-5_liu_20251226.txt')
#source_file = os.path.join('data', 'test', 'Task1_CleanResult_104-2_bp-12_liu_20260107.txt')
destination_dir = os.path.join('data', 'clean_result')

# Tạo thư mục đích nếu chưa tồn tại
os.makedirs(destination_dir, exist_ok=True)

# Delay 3 giây
print("Đang đợi 3 giây trước khi sao chép...")
time.sleep(5)

# Sao chép file
destination_file = os.path.join(destination_dir, os.path.basename(source_file))
shutil.copy(source_file, destination_file)

print(f"Đã sao chép {source_file} đến {destination_file}")
