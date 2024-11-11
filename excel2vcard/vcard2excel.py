import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

def vcard_to_excel(vcf_file_path, excel_file_path):
    # 读取VCF文件，明确指定使用UTF-8编码
    with open(vcf_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 分割vCard条目
    vcard_entries = content.split('END:VCARD\n')

    # 初始化一个列表来存储联系人信息
    contacts = []

    # 遍历每个vCard条目
    for entry in vcard_entries:
        if entry:
            # 提取姓名
            name_start = entry.find('FN:')
            if name_start != -1:
                name_end = entry.find('\n', name_start)
                name = entry[name_start + 3:name_end].strip()

            # 提取电话号码
            tel_start = entry.find('TEL;')
            if tel_start != -1:
                tel_end = entry.find('\n', tel_start)
                tel = entry[tel_start + entry[tel_start:].find(':') + 1:tel_end].strip()

            # 将联系人信息添加到列表
            contacts.append({'Name': name, 'Phone': tel})

    # 创建DataFrame
    df = pd.DataFrame(contacts)

    # 写入Excel文件
    df.to_excel(excel_file_path, index=False)

def select_file_and_directory():
    # 创建一个Tkinter窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 选择VCF文件
    vcf_file_path = filedialog.askopenfilename(
        title="Select VCF File",
        filetypes=[("VCF Files", "*.vcf"), ("All Files", "*.*")]
    )

    if not vcf_file_path:
        messagebox.showinfo("Info", "No file selected. Exiting.")
        return

    # 选择保存Excel文件的目录
    excel_directory = filedialog.askdirectory(
        title="Select Directory to Save Excel File"
    )

    if not excel_directory:
        messagebox.showinfo("Info", "No directory selected. Exiting.")
        return

    # 设置Excel文件名
    excel_file_path = f"{excel_directory}/contacts.xlsx"

    # 调用转换函数
    vcard_to_excel(vcf_file_path, excel_file_path)
    messagebox.showinfo("Success", f"Excel file saved at {excel_file_path}")

# 运行主函数
if __name__ == "__main__":
    select_file_and_directory()
