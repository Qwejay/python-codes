import os
import datetime
import exifread
import piexif
import pillow_heif
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread
import logging
import re

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

DATE_FORMAT = "%Y%m%d_%H%M%S"
INCLUDE_TIMESTAMP = True
stop_requested = False

def get_exif_date(file_path):
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f)
            if 'EXIF DateTimeOriginal' in tags:
                date_str = str(tags['EXIF DateTimeOriginal'])
                return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logging.error(f"读取EXIF数据失败: {e}")
    return None

def get_heic_date(file_path):
    try:
        heif_file = pillow_heif.read_heif(file_path)
        exif_dict = piexif.load(heif_file.info['exif'])
        if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logging.error(f"读取HEIC数据失败: {e}")
    return None

def get_file_modification_date(file_path):
    try:
        modification_time = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(modification_time)
    except Exception as e:
        logging.error(f"获取文件修改日期失败: {e}")
    return None

def generate_unique_filename(directory, base_name, ext, original_filename):
    new_filename = f"{base_name}{ext}"
    new_file_path = os.path.join(directory, new_filename)
    if new_file_path.lower() == original_filename.lower():
        return new_file_path
    counter = 1
    while os.path.exists(new_file_path):
        new_filename = f"{base_name}_{counter}{ext}"
        new_file_path = os.path.join(directory, new_filename)
        counter += 1
    return new_file_path

def rename_photos(files_listbox, progress_var):
    total_files = files_listbox.size()
    for i in range(total_files):
        file_path = files_listbox.get(i).strip('"')
        rename_photo(file_path, files_listbox, progress_var, total_files)
    messagebox.showinfo("重命名完成", f"成功重命名 {total_files} 个文件。")

def rename_photo(file_path, files_listbox, progress_var, total_files):
    filename = os.path.basename(file_path)
    date_time = get_heic_date(file_path) if filename.lower().endswith('.heic') else get_exif_date(file_path)
    if not date_time:
        date_time = get_file_modification_date(file_path)
    if date_time:
        base_name = date_time.strftime(DATE_FORMAT)
        ext = os.path.splitext(filename)[1]
        directory = os.path.dirname(file_path)
        new_file_path = generate_unique_filename(directory, base_name, ext, file_path)
        if new_file_path != file_path:
            try:
                os.rename(file_path, new_file_path)
                files_listbox.insert(tk.END, f'"{file_path}" 重命名为 "{new_file_path}"')
            except Exception as e:
                logging.error(f"重命名失败: {file_path}, 错误: {e}")
    progress_var.set(progress_var.get() + 100 / total_files)

def on_drop(event, files_listbox):
    paths = re.findall(r'(?<=\{)[^{}]*(?=\})|[^{}\s]+', event.data)
    for path in paths:
        path = path.strip().strip('{}')
        if path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic')) and path not in files_listbox.get(0, tk.END):
            files_listbox.insert(tk.END, path)

def open_file(event, files_listbox):
    selected_index = files_listbox.curselection()
    if selected_index:
        file_path = files_listbox.get(selected_index[0]).strip('"')
        os.startfile(file_path)

def remove_file(event, files_listbox):
    selected_indices = files_listbox.curselection()
    for index in selected_indices[::-1]:
        files_listbox.delete(index)

def stop_renaming():
    global stop_requested
    stop_requested = True

def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("设置")

    tk.Label(settings_window, text="日期格式:").grid(row=0, column=0, padx=10, pady=10)
    date_format_var = tk.StringVar(value=DATE_FORMAT)
    date_format_entry = tk.Entry(settings_window, textvariable=date_format_var)
    date_format_entry.grid(row=0, column=1, padx=10, pady=10)

    include_timestamp_var = tk.BooleanVar(value=INCLUDE_TIMESTAMP)
    include_timestamp_checkbox = tk.Checkbutton(settings_window, text="包括时间戳", variable=include_timestamp_var)
    include_timestamp_checkbox.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    save_button = tk.Button(settings_window, text="保存设置", command=lambda: save_settings(date_format_var.get(), include_timestamp_var.get()))
    save_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

def save_settings(date_format, include_timestamp):
    global DATE_FORMAT, INCLUDE_TIMESTAMP
    DATE_FORMAT = date_format
    INCLUDE_TIMESTAMP = include_timestamp
    messagebox.showinfo("设置", "设置已保存")

root = TkinterDnD.Tk()
root.title("照片重命名工具")
root.geometry("800x600")

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

label_description = ttk.Label(main_frame, text="将文件拖拽至此处以添加至重命名列表，双击打开文件，右键移除文件")
label_description.pack(fill=tk.X, padx=10, pady=10)

files_listbox = tk.Listbox(main_frame, width=100, height=15)
files_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
files_listbox.drop_target_register(DND_FILES)
files_listbox.dnd_bind('<<Drop>>', lambda e: on_drop(e, files_listbox))
files_listbox.bind('<Double-1>', lambda e: open_file(e, files_listbox))
files_listbox.bind('<Button-3>', lambda e: remove_file(e, files_listbox))

progress_var = tk.DoubleVar()
progress = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
progress.pack(fill=tk.X, padx=10, pady=10)

button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=tk.X, padx=10, pady=10)

start_button = ttk.Button(button_frame, text="开始重命名", command=lambda: Thread(target=rename_photos, args=(files_listbox, progress_var)).start())
start_button.pack(side=tk.LEFT, padx=5)

stop_button = ttk.Button(button_frame, text="停止重命名", command=stop_renaming)
stop_button.pack(side=tk.LEFT, padx=5)

settings_button = ttk.Button(button_frame, text="设置", command=open_settings)
settings_button.pack(side=tk.LEFT, padx=5)

clear_button = ttk.Button(button_frame, text="清空列表", command=lambda: files_listbox.delete(0, tk.END))
clear_button.pack(side=tk.LEFT, padx=5)

root.mainloop()
