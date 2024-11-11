import os
import sys
import datetime
import exifread
import piexif
import pillow_heif
import ttkbootstrap as ttk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='rename_tool.log')

DATE_FORMAT = "%Y%m%d_%H%M%S"
stop_requested = False
renaming_in_progress = False

COMMON_DATE_FORMATS = [
    "%Y%m%d_%H%M%S",    # 20230729_141530
    "%Y-%m-%d %H:%M:%S",  # 2023-07-29 14:15:30
    "%d-%m-%Y %H:%M:%S",  # 29-07-2023 14:15:30
    "%Y%m%d",            # 20230729
    "%H%M%S",            # 141530
    "%Y-%m-%d",          # 2023-07-29
    "%d-%m-%Y"           # 29-07-2023
]

def get_exif_date(file_path):
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f)
            if 'EXIF DateTimeOriginal' in tags:
                date_str = str(tags['EXIF DateTimeOriginal'])
                return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logging.error(f"读取EXIF数据失败: {file_path}, 错误: {e}")
    return None

def get_heic_date(file_path):
    try:
        heif_file = pillow_heif.read_heif(file_path)
        exif_dict = piexif.load(heif_file.info['exif'])
        if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logging.error(f"读取HEIC数据失败: {file_path}, 错误: {e}")
    return None

def get_file_modification_date(file_path):
    try:
        modification_time = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(modification_time)
    except Exception as e:
        logging.error(f"获取文件修改日期失败: {file_path}, 错误: {e}")
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
    global stop_requested, renaming_in_progress
    
    if renaming_in_progress:
        messagebox.showwarning("重命名进行中", "重命名操作已在进行中，请稍后再试。")
        return

    renaming_in_progress = True
    start_button.config(state=ttk.DISABLED)
    stop_button.config(state=ttk.NORMAL)

    processed_files = set()
    total_files = files_listbox.size()
    for i in range(total_files):
        if stop_requested:
            stop_requested = False
            messagebox.showinfo("重命名停止", "重命名操作已停止。")
            break
        file_path = files_listbox.get(i).strip('"')
        if file_path not in processed_files:
            renamed = rename_photo(file_path, files_listbox, progress_var, total_files, i)
            if renamed:
                processed_files.add(file_path)
                files_listbox.delete(i)
                files_listbox.insert(ttk.END, f'"{file_path}" 重命名为 "{renamed}"')
            if auto_scroll_var.get():
                files_listbox.see(ttk.END)
    messagebox.showinfo("重命名完成", f"成功重命名 {len(processed_files)} 个文件。")

    renaming_in_progress = False
    start_button.config(state=ttk.NORMAL)
    stop_button.config(state=ttk.DISABLED)

def rename_photo(file_path, files_listbox, progress_var, total_files, current_index):
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
                logging.info(f'重命名成功: "{file_path}" 重命名为 "{new_file_path}"')
                progress_var.set((current_index + 1) * 100 / total_files)
                return new_file_path
            except Exception as e:
                logging.error(f"重命名失败: {file_path}, 错误: {e}")
    progress_var.set((current_index + 1) * 100 / total_files)
    return False

def on_drop(event, files_listbox):
    paths = re.findall(r'(?<=\{)[^{}]*(?=\})|[^{}\s]+', event.data)
    for path in paths:
        path = path.strip().strip('{}')
        if path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic')) and path not in files_listbox.get(0, ttk.END):
            files_listbox.insert(ttk.END, path)

def open_file(event):
    selected_index = files_listbox.curselection()
    if selected_index:
        file_path = files_listbox.get(selected_index[0]).strip('"')
        try:
            if os.name == 'nt':  # Windows
                os.system(f'start "" "{file_path}"')
            elif os.name == 'posix':  # macOS or Linux
                if sys.platform == 'darwin':  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
            logging.info(f"文件打开命令已执行: {file_path}")
        except Exception as e:
            logging.error(f"无法打开文件: {file_path}, 错误: {e}")
            messagebox.showerror("打开文件错误", f"无法打开文件: {file_path}\n错误: {e}")

def remove_file(event):
    selected_indices = files_listbox.curselection()
    for index in selected_indices[::-1]:
        files_listbox.delete(index)

def stop_renaming():
    global stop_requested
    stop_requested = True

def open_settings():
    settings_window = ttk.Toplevel(root)
    settings_window.title("设置")

    ttk.Label(settings_window, text="日期格式:").grid(row=0, column=0, padx=10, pady=10)
    date_format_var = ttk.StringVar(value=DATE_FORMAT)
    date_format_combobox = ttk.Combobox(settings_window, textvariable=date_format_var, values=COMMON_DATE_FORMATS)
    date_format_combobox.grid(row=0, column=1, padx=10, pady=10)

    # 日期格式说明
    formats_explanation = (
        "常用日期格式示例:\n"
        "%Y%m%d_%H%M%S -> 20230729_141530\n"
        "%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n"
        "%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n"
        "%Y%m%d -> 20230729\n"
        "%H%M%S -> 141530\n"
        "%Y-%m-%d -> 2023-07-29\n"
        "%d-%m-%Y -> 29-07-2023"
    )
    ttk.Label(settings_window, text=formats_explanation).grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    save_button = ttk.Button(settings_window, text="保存设置", command=lambda: save_settings(date_format_var.get()))
    save_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

def save_settings(date_format):
    global DATE_FORMAT
    DATE_FORMAT = date_format
    messagebox.showinfo("设置", "设置已保存")

def select_files(files_listbox):
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.jpg *.jpeg *.tiff *.bmp *.gif *.heic")])
    for file_path in file_paths:
        if file_path not in files_listbox.get(0, ttk.END):
            files_listbox.insert(ttk.END, file_path)

root = TkinterDnD.Tk()
root.title("照片重命名工具")
root.geometry("800x600")

style = ttk.Style('litera')  # 使用ttkbootstrap主题

# 在创建主窗口之后再创建变量
auto_scroll_var = ttk.BooleanVar()

main_frame = ttk.Frame(root)
main_frame.pack(fill=ttk.BOTH, expand=True)

label_description = ttk.Label(main_frame, text="将文件拖拽至此处添加至重命名列表，双击打开文件，右键移除文件")
label_description.pack(fill=ttk.X, padx=10, pady=10)

files_listbox = ttk.tk.Listbox(main_frame, width=100, height=15)
files_listbox.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
files_listbox.drop_target_register(DND_FILES)
files_listbox.dnd_bind('<<Drop>>', lambda e: on_drop(e, files_listbox))
files_listbox.bind('<Double-1>', open_file)
files_listbox.bind('<Button-3>', remove_file)

progress_var = ttk.DoubleVar()
progress = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
progress.pack(fill=ttk.X, padx=10, pady=10)

button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=ttk.X, padx=10, pady=10)

start_button = ttk.Button(button_frame, text="开始重命名", command=lambda: Thread(target=rename_photos, args=(files_listbox, progress_var)).start())
start_button.pack(side=ttk.LEFT, padx=5)
start_button.config(state=ttk.NORMAL)

stop_button = ttk.Button(button_frame, text="停止重命名", command=stop_renaming)
stop_button.pack(side=ttk.LEFT, padx=5)
stop_button.config(state=ttk.DISABLED)

settings_button = ttk.Button(button_frame, text="设置", command=open_settings)
settings_button.pack(side=ttk.LEFT, padx=5)

clear_button = ttk.Button(button_frame, text="清空列表", command=lambda: files_listbox.delete(0, ttk.END))
clear_button.pack(side=ttk.LEFT, padx=5)

select_files_button = ttk.Button(button_frame, text="添加文件", command=lambda: select_files(files_listbox))
select_files_button.pack(side=ttk.LEFT, padx=5)

auto_scroll_checkbox = ttk.Checkbutton(button_frame, text="自动滚动", variable=auto_scroll_var)
auto_scroll_checkbox.pack(side=ttk.LEFT, padx=5)

root.mainloop()
