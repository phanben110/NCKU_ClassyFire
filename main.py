import time
import shutil
import os

# Đường dẫn file nguồn và thư mục đích
source_file = 'data/test/sample.xlsx'
destination_dir = 'data/clean_result'

# Tạo thư mục đích nếu chưa tồn tại
os.makedirs(destination_dir, exist_ok=True)

# Delay 3 giây
print("Đang đợi 3 giây trước khi sao chép...")
time.sleep(5)

# Sao chép file
destination_file = os.path.join(destination_dir, os.path.basename(source_file))
shutil.copy(source_file, destination_file)

print(f"Đã sao chép {source_file} đến {destination_file}")
