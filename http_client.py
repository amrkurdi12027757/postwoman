import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import requests
import threading
import time
import os

class HttpClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Postwoman')
        self.geometry('800x600')
        self.create_widgets()

    def create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text='Method:').pack(side=tk.LEFT)
        self.method_var = tk.StringVar(value='GET')
        methods = ['GET','POST','PUT','DELETE','PATCH','HEAD','OPTIONS']
        ttk.Combobox(top, textvariable=self.method_var, values=methods, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(top, text='URL:').pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(top, width=60)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        header_frame = ttk.LabelFrame(self, text='Headers')
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        self.headers_text = scrolledtext.ScrolledText(header_frame, height=4)
        self.headers_text.pack(fill=tk.X)

        body_frame = ttk.LabelFrame(self, text='Body')
        body_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        body_top = ttk.Frame(body_frame)
        body_top.pack(fill=tk.X)
        ttk.Label(body_top, text='Type:').pack(side=tk.LEFT)
        self.body_type = tk.StringVar(value='raw')
        body_type_cb = ttk.Combobox(body_top, textvariable=self.body_type,
                                    values=['raw','json','form-urlencoded','form-data'])
        body_type_cb.pack(side=tk.LEFT)
        body_type_cb.bind('<<ComboboxSelected>>', self.update_body_ui)
        self.body_area = ttk.Frame(body_frame)
        self.body_area.pack(fill=tk.BOTH, expand=True)
        self.body_text = scrolledtext.ScrolledText(self.body_area, height=10)
        self.body_text.pack(fill=tk.BOTH, expand=True)
        self.form_rows = []
        self.update_body_ui()
        parallel_frame = ttk.Frame(self)
        parallel_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parallel_frame, text='Parallel:').pack(side=tk.LEFT)
        self.parallel_var = tk.IntVar(value=1)
        ttk.Spinbox(parallel_frame, from_=1, to=100, textvariable=self.parallel_var, width=5).pack(side=tk.LEFT)
        ttk.Button(parallel_frame, text='Send', command=self.send).pack(side=tk.LEFT, padx=5)

        response_frame = ttk.LabelFrame(self, text='Response')
        response_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        self.response_text = scrolledtext.ScrolledText(response_frame, height=15)
        self.response_text.pack(fill=tk.BOTH, expand=True)

    def parse_headers(self):
        headers = {}
        for line in self.headers_text.get('1.0', tk.END).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip()] = v.strip()
        return headers

    def update_body_ui(self, *args):
        for child in self.body_area.winfo_children():
            child.destroy()
        self.form_rows.clear()
        btype = self.body_type.get()
        if btype == 'form-data':
            add_btn = ttk.Button(self.body_area, text='Add field', command=self.add_form_row)
            add_btn.pack(anchor='w', pady=2)
            self.form_container = ttk.Frame(self.body_area)
            self.form_container.pack(fill=tk.BOTH, expand=True)
            self.add_form_row()
        else:
            self.body_text = scrolledtext.ScrolledText(self.body_area, height=10)
            self.body_text.pack(fill=tk.BOTH, expand=True)

    def add_form_row(self):
        row = ttk.Frame(self.form_container)
        key = ttk.Entry(row, width=15)
        value = ttk.Entry(row, width=30)
        file_var = tk.StringVar()

        def choose_file():
            path = tk.filedialog.askopenfilename()
            if path:
                file_var.set(path)
                value.delete(0, tk.END)
                value.insert(0, path)

        ttk.Button(row, text='File...', command=choose_file).pack(side=tk.RIGHT)
        value.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        key.pack(side=tk.LEFT, padx=2)
        row.pack(fill=tk.X, pady=2)
        self.form_rows.append((key, value, file_var))
    def parse_body(self):
        btype = self.body_type.get()
        data = None
        json_data = None
        files = None
        if btype == 'json':
            text = self.body_text.get('1.0', tk.END).strip()
            try:
                import json
                json_data = json.loads(text) if text else None
            except Exception:
                json_data = None
        elif btype == 'form-urlencoded':
            text = self.body_text.get('1.0', tk.END).strip()
            data = dict(line.split('=',1) for line in text.splitlines() if '=' in line)
        elif btype == 'form-data':
            data = {}
            files = {}
            for key, value, file_var in self.form_rows:
                k = key.get().strip()
                v = value.get()
                path = file_var.get()
                if not k:
                    continue
                if path:
                    if os.path.isfile(path):
                        files[k] = path
                else:
                    data[k] = v
        else:
            text = self.body_text.get('1.0', tk.END).strip()
            data = text if text else None
        return data, json_data, files
    def send_request(self, method, url, headers, data, json_data, files, out_list):
        start = time.time()
        files_data = None
        if files:
            files_data = {k: open(p, 'rb') for k, p in files.items() if os.path.isfile(p)}
        try:
            resp = requests.request(method=method, url=url, headers=headers,
                                   data=data, json=json_data, files=files_data)
            elapsed = time.time() - start
            out_list.append(f'Status: {resp.status_code} Time: {elapsed:.2f}s\n{resp.text[:200]}\n')
        except Exception as e:
            elapsed = time.time() - start
            out_list.append(f'Error: {e} Time: {elapsed:.2f}s\n')
        finally:
            if files_data:
                for f in files_data.values():
                    f.close()

    def send(self):
        method = self.method_var.get()
        url = self.url_entry.get()
        headers = self.parse_headers()
        data, json_data, files = self.parse_body()
        parallel = self.parallel_var.get()
        outputs = []
        threads = []
        for _ in range(parallel):
            t = threading.Thread(target=self.send_request,
                                 args=(method, url, headers, data, json_data, files, outputs))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.response_text.delete('1.0', tk.END)
        self.response_text.insert(tk.END, '\n'.join(outputs))
if __name__ == '__main__':
    HttpClient().mainloop()
