import os
import datetime
import exifread
import piexif
import pillow_heif
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def get_exif_date(file_path):
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f)
            if 'EXIF DateTimeOriginal' in tags:
                date_str = str(tags['EXIF DateTimeOriginal'])
                return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logging.error(f"读取 {file_path} 的 EXIF 数据时出错: {e}")
    return None

def get_heic_date(file_path):
    try:
        heif_file = pillow_heif.read_heif(file_path)
        exif_dict = piexif.load(heif_file.info['exif'])
        if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logging.error(f"读取 {file_path} 的 HEIC 数据时出错: {e}")
    return None

def get_file_modification_date(file_path):
    try:
        modification_time = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(modification_time)
    except Exception as e:
        logging.error(f"读取 {file_path} 的修改日期时出错: {e}")
    return None

def rename_photo(file_path, files_listbox, progress_var, total_files):
    filename = os.path.basename(file_path)
    date_time = get_heic_date(file_path) if filename.lower().endswith('.heic') else get_exif_date(file_path)
    if not date_time:
        date_time = get_file_modification_date(file_path)
    if date_time:
        new_filename = date_time.strftime('%Y%m%d_%H%M%S') + os.path.splitext(filename)[1]
        new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
        os.rename(file_path, new_file_path)
        files_listbox.insert(tk.END, f'{filename} -> {new_filename}')
        print(f'重命名: {filename} -> {new_filename}')
    else:
        logging.warning(f'未找到 {filename} 的日期')
    progress_var.set(progress_var.get() + 100 / total_files)

def on_drop(event, files_listbox):
    paths = event.data.split()
    for path in paths:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path) and file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic')):
                        if file_path not in files_listbox.get(0, tk.END):
                            files_listbox.insert(tk.END, file_path)
        elif os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic')):
            if path not in files_listbox.get(0, tk.END):
                files_listbox.insert(tk.END, path)

def start_renaming(files_listbox, progress_var):
    original_files = list(files_listbox.get(0, tk.END))  # 保存原始文件路径
    files_listbox.delete(0, tk.END)  # 清空列表
    progress_var.set(0)
    total_files = len(original_files)
    for file_path in original_files:
        rename_photo(file_path, files_listbox, progress_var, total_files)
    files_listbox.insert(tk.END, "重命名完成。")

def open_file(event, files_listbox):
    selected = files_listbox.get(files_listbox.curselection())
    if " -> " in selected:
        original_name, new_name = selected.split(" -> ")
        directory = os.path.dirname(original_name)
        new_file_path = os.path.join(directory, new_name)
        os.startfile(new_file_path)
    else:
        os.startfile(selected)

def remove_file(event, files_listbox):
    selected_indices = files_listbox.curselection()
    for index in selected_indices[::-1]:  # 从后往前删除，避免索引错乱
        files_listbox.delete(index)

def clear_list(files_listbox):
    files_listbox.delete(0, tk.END)

# 创建主窗口
root = TkinterDnD.Tk()
root.title("照片重命名")

# 创建并放置部件
ttk.Label(root, text="拖动文件夹或文件即可添加进重命名列表，双击打开文件，右键清除该文件").grid(row=0, column=0, padx=10, pady=10)
files_listbox = tk.Listbox(root, width=50)
files_listbox.grid(row=1, column=0, padx=10, pady=10)
files_listbox.drop_target_register(DND_FILES)
files_listbox.dnd_bind('<<Drop>>', lambda e: on_drop(e, files_listbox))
files_listbox.bind('<Double-Button-1>', lambda e: open_file(e, files_listbox))
files_listbox.bind('<Button-3>', lambda e: remove_file(e, files_listbox))  # 绑定右键点击事件

progress_var = tk.DoubleVar()
progress = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

ttk.Button(root, text="开始重命名", command=lambda: Thread(target=start_renaming, args=(files_listbox, progress_var)).start()).grid(row=3, column=0, padx=10, pady=10)
ttk.Button(root, text="清空列表", command=lambda: clear_list(files_listbox)).grid(row=4, column=0, padx=10, pady=10)

# 运行应用程序
root.mainloop()