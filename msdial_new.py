from pywinauto.keyboard import send_keys
from pywinauto.application import Application
import pyperclip 
from pywinauto import mouse
import time
import win32gui
import win32con
import pyautogui
from pywinauto import Desktop
import os
import shutil
import datetime
import configs

# Close all windows
pyautogui.hotkey('win', 'd')

# Open MS-DIAL
app = Application(backend="uia").start(configs.app_path)

# Connect app
main_window = app.window(title="MSDIAL")  
main_window.wait("ready", timeout=10)  # waitting open process
main_window.set_focus()  # focus window

hwnd_update = win32gui.FindWindow(None, "Update notification")
if hwnd_update != 0:
    print("A new MS-DIAL is available!")
    update = main_window.child_window(title="No", auto_id="7", control_type="Button")
    update.click()
time.sleep(2)

main_window.set_focus()  # focus window
# Click "New project"
new_project_btn = main_window.child_window(title="New project", control_type="Text")
new_project_btn.click_input()
time.sleep(1)

# Edit Project file path
input_box = main_window.descendants(control_type="Edit")[1]
input_box.set_text(configs.project_file_path)
time.sleep(2)

# Click "Next"
next_path = main_window.child_window(title="Next", control_type = "Text")  # Tìm ô nhập liệu
next_path.click_input()
time.sleep(1)

## Choose analysis folders
# Click Browse
browse_button = main_window.child_window(title="Browse", control_type="Button")
browse_button.click_input()
time.sleep(1)

#Adjust two windows
# Get handle two window
hwnd_setting = win32gui.FindWindow(None, "Setting project parameters")
hwnd_folder = win32gui.FindWindow(None, "Import analysis files")  # Thay bằng tên thực tế
# Get window dimentions
left, top, right, bottom = win32gui.GetWindowRect(hwnd_setting)
new_left = (right - left) // 2 +  left
width = right - left
height = bottom - top
# Change dimentions
win32gui.SetWindowPos(hwnd_folder, None, new_left, top, width, height, win32con.SWP_NOZORDER)

# Change folder path having analysis folders
trys = main_window.child_window(title="All locations", control_type="SplitButton")
trys.click_input()
# Paste folder_analysis_path
folder_analysis_path = configs.folder_analysis_path
pyperclip.copy(folder_analysis_path)
send_keys("^v")
send_keys("{ENTER}")
time.sleep(1)

# Sort list display
#Get list folder displayed on screen
import_window = main_window.child_window(title="Items View", control_type="List")
list_items = import_window.descendants(control_type="ListItem")
folder_names = [item.window_text() for item in list_items]

# Compare time
folder_path_1 = folder_analysis_path +  rf"\{folder_names[0]}"
folder_path_n = folder_analysis_path +  rf"\{folder_names[-1]}"

time1 = datetime.datetime.fromtimestamp(os.stat(folder_path_1).st_mtime)
time2 = datetime.datetime.fromtimestamp(os.stat(folder_path_n).st_mtime)

#Make screen display the new ones
if time1 < time2:
    day_motifiled = main_window.child_window(title="Date modified", auto_id="System.DateModified", control_type="SplitButton")
    day_motifiled.click_input()
time.sleep(1)

# Lấy tọa độ trung tâm của vùng cuộn
rect = import_window.rectangle()
center_x = rect.left + (rect.width() // 2)
center_y = rect.top + (rect.height() // 2)

# Cuộn lên trên (số bước cuộn có thể điều chỉnh)
mouse.scroll(coords=(center_x, center_y), wheel_dist=1000)

# Select analysis folders
folders_to_select = configs.folders_to_select

pyautogui.keyDown('ctrl')
for i in range(len(folders_to_select)-1):
    #Detect folders
    try:
        folder = main_window.child_window(title=folders_to_select[i], control_type="ListItem")
        folder_rect = folder.rectangle()
    except:
        print(f"Error: Can not find {folders_to_select[i]}")
        raise SystemExit

    x = (folder_rect.right - folder_rect.left) // 2 + folder_rect.left
    y = (folder_rect.top - folder_rect.bottom) // 2 + folder_rect.bottom

    pyautogui.click(x, y)
try:
    folder = main_window.child_window(title=folders_to_select[-1], control_type="ListItem")
    folder_rect = folder.rectangle()
except:
    print(f"Error: Can not find {folders_to_select[-1]}")
    raise SystemExit

start_x = (folder_rect.right - folder_rect.left) // 2 + folder_rect.left
start_y = (folder_rect.top - folder_rect.bottom) // 2 + folder_rect.bottom

# Setting zone
center_x = new_left - 30 
center_y = (top - bottom) // 2 +  bottom
end_x, end_y = center_x, center_y  # Target

#Add analyis folders
pyautogui.moveTo(start_x, start_y)
pyautogui.mouseDown()
pyautogui.moveTo(end_x, end_y, duration=0.2)
pyautogui.mouseUp()
pyautogui.keyUp('ctrl')

# Close Import analysis files window
folder_window = main_window.child_window(title="Import analysis files", control_type="Window")
folder_window.close()

# Click "Next"
next_path = main_window.child_window(title="Next", control_type = "Text")  # Tìm ô nhập liệu
next_path.click_input()

#Step 6: 
## Set parameter
# Ionization group
ionization_group = main_window.child_window(title="Ionization type", control_type="Group")
ionization = configs.ionization
if ionization == "Hard ionization":
    hard_ionization = ionization_group.child_window(auto_id="RadioButton_EI", control_type="RadioButton")
    hard_ionization.click()  
elif ionization == "Soft ionization":
    soft_ionization = ionization_group.child_window(auto_id="RadioButton_ESI", control_type="RadioButton")
    soft_ionization.click()

# Separation type
separation_group = main_window.child_window(title="Separation type", control_type="Group")
separation = configs.separation
if separation == "Chromatography":
    chromatography = separation_group.child_window(auto_id="RadioButton_Separation_GCorLC", control_type="RadioButton")
    chromatography.click()
elif separation == "Direct infusion":
    direct_infusion = separation_group.child_window(auto_id="RadioButton_Infusion", control_type="RadioButton")
    direct_infusion.click() 

#Collision
collision_group = main_window.child_window(title="Collision type", control_type="Group")
collision = configs.collision
if collision == "CID/HCD":
    CID_HCD = collision_group.child_window(title="CID/HCD", control_type="RadioButton")
    CID_HCD.click()
elif collision == "ECD":
    ECD = collision_group.child_window(title="ECD", control_type="RadioButton")
    ECD.click()
elif collision == "HotECD":
    ECD = collision_group.child_window(title="HotECD", control_type="RadioButton")
    ECD.click()
elif collision == "EIEIO":
    ECD = collision_group.child_window(title="EIEIO", control_type="RadioButton")
    ECD.click()
elif collision == "EID":
    ECD = collision_group.child_window(title="EID", control_type="RadioButton")
    ECD.click()
elif collision == "OAD":
    ECD = collision_group.child_window(title="OAD", control_type="RadioButton")
    ECD.click()

#Data type (MS1)
data_type_ms1 = main_window.child_window(title='Data type (MS1)', control_type="Group")
data_ms1 = configs.data_ms1
if data_ms1 == "Profile data":
    profile_data = data_type_ms1.child_window(auto_id="RadioButton_ProfileMode", control_type="RadioButton")
    profile_data.click_input()
elif data_ms1 == "Centroid data":
    centroid_data = data_type_ms1.child_window(auto_id="RadioButton_CentroidMode", control_type="RadioButton")
    centroid_data.click_input()

#Data type (MS/MS)
data_type_msms = main_window.child_window(title='Data type (MS/MS)',control_type="Group")
data_msms = configs.data_type_msms
if data_msms == "Profile data":
    profile_data = data_type_msms.child_window(title="Profile data", auto_id="RadioButton_ProfileModeMS2", control_type="RadioButton")
    profile_data.click() 
elif data_msms == "Centroid data":
    centroid_data = data_type_msms.child_window(title="Centroid data", auto_id="RadioButton_CentroidModeMS2", control_type="RadioButton")
    centroid_data.click() 

# Ion mode
ion_mode = main_window.child_window(title="Ion mode", auto_id="GroupBox_IonMode", control_type="Group")
ion = configs.ion
if ion == "Positive ion mode":
    positive = ion_mode.child_window(title="Positive ion mode", auto_id="RadioButton_PositiveMode", control_type="RadioButton")
    positive.click() 
elif ion == "Negative ion mode":
    nagative = ion_mode.child_window(title="Negative ion mode", auto_id="RadioButton_NegativeMode", control_type="RadioButton")
    nagative.click()

#Targe omics
target_omics = configs.target_omics
if target_omics == "Metabolomics":
    Metabolomics = main_window.child_window(title="Metabolomics", auto_id="RadioButton_Metabolomics", control_type="RadioButton")
    Metabolomics.click()
elif target_omics == "Lipidomics":
    Lipidomics = main_window.child_window(title="Lipidomics", auto_id="RadioButton_Lipidomics", control_type="RadioButton")
    Lipidomics.click()
elif target_omics == "Proteomics":
    Proteomics = main_window.child_window(title="Proteomics", auto_id="RadioButton_Proteomics", control_type="RadioButton")
    Proteomics.click()

# Click "Next"
next_path = main_window.child_window(title="Next", control_type = "Text")  # Tìm ô nhập liệu
next_path.click_input()
time.sleep(2)

# List parameters
# Identification parameters
identification = main_window.child_window(title="CompMs.App.Msdial.ViewModel.Setting.IdentifySettingViewModel", control_type="ListItem")
identification.click_input()

#Add library
data_setting_button = main_window.child_window(title="M-3,1L-1,1 -1,3 1,3 1,1 3,1 3,-1 1,-1 1,-3 -1,-3 -1,-1 -3,-1z", control_type="Button",found_index=0)
data_setting_button.click_input()

#Edit library_path
library_path = configs.library_path
if ion == "Positive ion mode":
    file_library = library_path + r'\Pos_bank_唯礽.msp'
elif ion == "Negative ion mode":
    file_library = library_path + r'\Neg_bank_唯礽.msp'
database_path_edit = main_window.descendants(control_type="Edit")[0]
database_path_edit.set_text(file_library)

#Run process
run = main_window.child_window(title="Run", control_type = "Text")  # Tìm ô nhập liệu
run.click_input()

#Wating for loading library
time.sleep(30)

#Detech window:
#ERROR window: Error parsing file
#Data window: Analysis sucessful
window_title = "Dataset: " + folder_analysis_path
analysis_window = 0
error_window = 0

while analysis_window == 0 and analysis_window == 0:
    time.sleep(10)
    error_window = win32gui.FindWindow(None, "Unexpected exception occured.")
    if error_window != 0:
        print(f"Error: Error parsing file")
        raise SystemExit
    analysis_window = win32gui.FindWindow(None, window_title)

# Detect Data window
app = Desktop(backend="uia")  # Sử dụng backend "uia" cho giao diện người dùng
result_window = app.window(title=window_title)

# Click Export option
export = result_window.child_window(title="Export", control_type="TabItem")
export.click_input()

# Click Peak list result
list_result = export.child_window(title="Peak list result", control_type="Button")
list_result.click()

# Difine result_window
list_result_window = result_window.child_window(title="Peak list export", control_type="Window")
# Save the result path
result_path = configs.result_path
input_box = list_result_window.descendants(control_type="Edit")[0]
input_box.set_text(result_path)

# Add results
add_all = list_result_window.child_window(title="Add all >>", control_type="Button")
add_all.click()

# Export results
export_results = list_result_window.child_window(title="Export", control_type="Button")
export_results.click()

# Copy file
dest_dir = r"C:\Users\user\Desktop\自動化檔案\data\clean_result"
os.makedirs(dest_dir, exist_ok=True)

for file_name in os.listdir(result_path):
    source_file = os.path.join(result_path, file_name)
    dest_file = os.path.join(dest_dir, file_name)

    if os.path.isfile(source_file):
        shutil.copy2(source_file, dest_file) 

# Show the main Classify
classify_window = win32gui.FindWindow(None, "ClassyFire - Google Chrome")
win32gui.ShowWindow(classify_window, win32con.SW_RESTORE)