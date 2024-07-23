import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import win32com.client
import psutil
import json
import os

CONFIG_FILE = "network_configs.json"

class IPChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IP 地址修改器")
        self.root.geometry("400x450")

        # 自动获取IP选项
        self.auto_ip_var = tk.BooleanVar(value=False)
        self.auto_ip_check = tk.Checkbutton(root, text="自动获取IP", variable=self.auto_ip_var, command=self.toggle_auto_ip)
        self.auto_ip_check.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

        # 网络适配器选项
        self.adapter_label = tk.Label(root, text="网络适配器：")
        self.adapter_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.adapter_var = tk.StringVar()
        self.adapter_menu = ttk.Combobox(root, textvariable=self.adapter_var, values=self.get_network_adapters())
        self.adapter_menu.grid(row=1, column=1, padx=10, pady=5)
        self.adapter_var.set("以太网" if "以太网" in self.adapter_menu['values'] else self.adapter_menu['values'][0])

        # IP 地址设置
        self.ip_label = tk.Label(root, text="IP 地址：")
        self.ip_label.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.ip_entry = tk.Entry(root)
        self.ip_entry.grid(row=2, column=1, padx=10, pady=5)

        self.subnet_label = tk.Label(root, text="子网掩码：")
        self.subnet_label.grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        self.subnet_entry = tk.Entry(root)
        self.subnet_entry.grid(row=3, column=1, padx=10, pady=5)

        self.gateway_label = tk.Label(root, text="默认网关：")
        self.gateway_label.grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        self.gateway_entry = tk.Entry(root)
        self.gateway_entry.grid(row=4, column=1, padx=10, pady=5)

        self.dns_label = tk.Label(root, text="DNS 服务器 1：")
        self.dns_label.grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        self.dns_entry1 = tk.Entry(root)
        self.dns_entry1.grid(row=5, column=1, padx=10, pady=5)

        self.dns_label2 = tk.Label(root, text="DNS 服务器 2：")
        self.dns_label2.grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)
        self.dns_entry2 = tk.Entry(root)
        self.dns_entry2.grid(row=6, column=1, padx=10, pady=5)

        # 配置选项
        self.config_var = tk.StringVar()
        self.config_menu = ttk.Combobox(root, textvariable=self.config_var, values=self.load_config_names())
        self.config_menu.grid(row=7, column=0, padx=10, pady=5)
        self.config_menu.bind("<<ComboboxSelected>>", self.load_config)

        self.save_button = tk.Button(root, text="保存配置", command=self.save_config)
        self.save_button.grid(row=7, column=1, padx=10, pady=5)

        self.new_config_button = tk.Button(root, text="新建配置", command=self.new_config)
        self.new_config_button.grid(row=8, column=0, padx=10, pady=5)

        self.delete_config_button = tk.Button(root, text="删除配置", command=self.delete_config)
        self.delete_config_button.grid(row=8, column=1, padx=10, pady=5)

        # 按钮
        self.apply_button = tk.Button(root, text="应用", command=self.apply_changes)
        self.apply_button.grid(row=9, column=0, padx=10, pady=5)

        self.refresh_button = tk.Button(root, text="刷新设备", command=self.refresh_adapters)
        self.refresh_button.grid(row=9, column=1, padx=10, pady=5)

        if self.config_menu['values']:
            self.config_var.set(self.config_menu['values'][0])
            self.load_config()

    def get_network_adapters(self):
        adapters = []
        for adapter in psutil.net_if_addrs().keys():
            adapters.append(adapter)
        return adapters

    def toggle_auto_ip(self):
        if self.auto_ip_var.get():
            self.ip_entry.config(state=tk.DISABLED)
            self.subnet_entry.config(state=tk.DISABLED)
            self.gateway_entry.config(state=tk.DISABLED)
        else:
            self.ip_entry.config(state=tk.NORMAL)
            self.subnet_entry.config(state=tk.NORMAL)
            self.gateway_entry.config(state=tk.NORMAL)

    def apply_changes(self):
        adapter_name = self.adapter_var.get()
        ip_address = self.ip_entry.get()
        subnet_mask = self.subnet_entry.get()
        gateway = self.gateway_entry.get()
        dns_servers = [self.dns_entry1.get(), self.dns_entry2.get()]
        dns_servers = [dns for dns in dns_servers if dns]  # Remove empty strings

        if not adapter_name:
            messagebox.showerror("错误", "请选择网络适配器")
            return

        if not self.auto_ip_var.get():
            if not ip_address or not subnet_mask or not gateway or not dns_servers:
                messagebox.showerror("错误", "请填写所有字段")
                return

        try:
            wmi = win32com.client.GetObject("winmgmts:root\cimv2")
            adapters = wmi.ExecQuery(f"SELECT * FROM Win32_NetworkAdapterConfiguration WHERE Description='{adapter_name}'")
            for adapter in adapters:
                if adapter.IPEnabled:
                    if self.auto_ip_var.get():
                        adapter.EnableDHCP()
                    else:
                        adapter.EnableStatic(IPAddress=[ip_address], SubnetMask=[subnet_mask])
                        adapter.SetGateways(DefaultIPGateway=[gateway])
                    adapter.SetDNSServerSearchOrder(DNSServerSearchOrder=dns_servers)
            messagebox.showinfo("成功", "IP 地址修改成功")
        except Exception as e:
            messagebox.showerror("错误", f"IP 地址修改失败: {e}")

    def refresh_adapters(self):
        self.adapter_menu['values'] = self.get_network_adapters()
        self.adapter_var.set("以太网" if "以太网" in self.adapter_menu['values'] else self.adapter_menu['values'][0])

    def save_config(self):
        config_name = self.config_var.get()
        config_data = {
            'adapter': self.adapter_var.get(),
            'auto_ip': self.auto_ip_var.get(),
            'ip': self.ip_entry.get(),
            'subnet': self.subnet_entry.get(),
            'gateway': self.gateway_entry.get(),
            'dns1': self.dns_entry1.get(),
            'dns2': self.dns_entry2.get()
        }

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                configs = json.load(file)
        else:
            configs = {}

        configs[config_name] = config_data

        with open(CONFIG_FILE, 'w') as file:
            json.dump(configs, file, indent=4, ensure_ascii=False)

        self.config_menu['values'] = self.load_config_names()
        messagebox.showinfo("成功", f"{config_name} 已保存")

    def load_config_names(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                configs = json.load(file)
            return list(configs.keys())
        return []

    def load_config(self, *args):
        config_name = self.config_var.get()

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                configs = json.load(file)
            
            config_data = configs.get(config_name, {})
            if config_data:
                self.adapter_var.set(config_data.get('adapter', ''))
                self.auto_ip_var.set(config_data.get('auto_ip', False))
                self.toggle_auto_ip()
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, config_data.get('ip', ''))
                self.subnet_entry.delete(0, tk.END)
                self.subnet_entry.insert(0, config_data.get('subnet', ''))
                self.gateway_entry.delete(0, tk.END)
                self.gateway_entry.insert(0, config_data.get('gateway', ''))
                self.dns_entry1.delete(0, tk.END)
                self.dns_entry1.insert(0, config_data.get('dns1', ''))
                self.dns_entry2.delete(0, tk.END)
                self.dns_entry2.insert(0, config_data.get('dns2', ''))

    def new_config(self):
        new_config_name = simpledialog.askstring("新建配置", "请输入新配置的名称：")
        if new_config_name:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as file:
                    configs = json.load(file)
                if new_config_name in configs:
                    messagebox.showerror("错误", "配置名称已存在")
                    return
            else:
                configs = {}

            configs[new_config_name] = {
                'adapter': '',
                'auto_ip': False,
                'ip': '',
                'subnet': '',
                'gateway': '',
                'dns1': '',
                'dns2': ''
            }

            with open(CONFIG_FILE, 'w') as file:
                json.dump(configs, file, indent=4, ensure_ascii=False)

            self.config_menu['values'] = self.load_config_names()
            self.config_var.set(new_config_name)
            self.load_config()

    def delete_config(self):
        config_name = self.config_var.get()
        if not config_name:
            messagebox.showerror("错误", "请选择要删除的配置")
            return

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                configs = json.load(file)

            if config_name in configs:
                del configs[config_name]

                with open(CONFIG_FILE, 'w') as file:
                    json.dump(configs, file, indent=4, ensure_ascii=False)

                self.config_menu['values'] = self.load_config_names()
                if self.config_menu['values']:
                    self.config_var.set(self.config_menu['values'][0])
                    self.load_config()
                else:
                    self.config_var.set('')
                    self.adapter_var.set('')
                    self.auto_ip_var.set(False)
                    self.ip_entry.delete(0, tk.END)
                    self.subnet_entry.delete(0, tk.END)
                    self.gateway_entry.delete(0, tk.END)
                    self.dns_entry1.delete(0, tk.END)
                    self.dns_entry2.delete(0, tk.END)

                messagebox.showinfo("成功", f"{config_name} 已删除")
            else:
                messagebox.showerror("错误", "配置名称不存在")

if __name__ == "__main__":
    root = tk.Tk()
    app = IPChangerApp(root)
    root.mainloop()