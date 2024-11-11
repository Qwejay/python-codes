import pandas as pd
import vobject
import os
import logging
import tkinter as tk
from tkinter import filedialog

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_input(excel_file, output_dir):
    if not os.path.isfile(excel_file):
        raise FileNotFoundError(f"Excel文件 {excel_file} 不存在")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def excel_to_vcard(excel_file, output_dir):
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file)
    except Exception as e:
        logging.error(f"读取Excel文件时出错: {e}")
        return
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    vcards = []
    
    # 遍历每一行数据
    for index, row in df.iterrows():
        try:
            # 检查数据类型
            if not isinstance(row['姓'], str):
                if pd.isna(row['姓']):
                    row['姓'] = ''
                else:
                    row['姓'] = str(row['姓'])
            if not isinstance(row['名'], str):
                if pd.isna(row['名']):
                    row['名'] = ''
                else:
                    row['名'] = str(row['名'])
            if not isinstance(row['手机'], str):
                if pd.isna(row['手机']):
                    row['手机'] = ''
                else:
                    row['手机'] = str(row['手机'])
            
            # 创建一个新的vCard
            vcard = vobject.vCard()
            
            # 添加姓名
            vcard.add('n')
            vcard.n.value = vobject.vcard.Name(family=row['姓'], given=row['名'])
            
            # 添加显示名称
            vcard.add('fn')
            vcard.fn.value = f"{row['姓']} {row['名']}"
            
            # 添加电话号码
            if pd.notna(row['手机']):
                vcard.add('tel')
                vcard.tel.value = row['手机']
                vcard.tel.type_param = 'CELL'
            
            vcards.append(vcard)
        except Exception as e:
            logging.error(f"处理行 {index + 1} 时出错: {e}")
    
    # 保存所有vCard到单个文件
    output_file = os.path.join(output_dir, "contacts.vcf")
    with open(output_file, 'w', encoding='utf-8') as f:
        for vcard in vcards:
            f.write(vcard.serialize())
    
    logging.info(f"转换完成，vCard文件保存在 {output_file}")

def select_files():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    excel_file = filedialog.askopenfilename(title="选择Excel文件", filetypes=[("Excel files", "*.xlsx *.xls")])
    if not excel_file:
        logging.error("未选择Excel文件")
        return
    
    output_dir = filedialog.askdirectory(title="选择输出目录")
    if not output_dir:
        logging.error("未选择输出目录")
        return
    
    try:
        validate_input(excel_file, output_dir)
        excel_to_vcard(excel_file, output_dir)
    except Exception as e:
        logging.error(f"程序出错: {e}")

if __name__ == "__main__":
    select_files()