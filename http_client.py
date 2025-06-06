import mimetypes
import tkinter as tk
from pathlib import Path
from tkinter import ttk, scrolledtext, simpledialog
import json
import requests
import threading
import time
import os


class HttpClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Postwoman')
        self.geometry('1000x600')
        self.save_file = Path('requests.json')
        self.requests = {}
        self.create_widgets()
        self.load_requests()

    def create_widgets(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        side = ttk.Frame(container)
        side.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.req_list = tk.Listbox(side, height=15)
        self.req_list.pack(fill=tk.BOTH, expand=True)
        self.req_list.bind('<<ListboxSelect>>', self.on_select_request)
        ttk.Button(side, text='New', command=self.new_request).pack(fill=tk.X, pady=2)
        ttk.Button(side, text='Save', command=self.save_current_request).pack(fill=tk.X)

        main = ttk.Frame(container)
        main.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        top = ttk.Frame(main)
        top.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(top, text='Method:').pack(side=tk.LEFT)
        self.method_var = tk.StringVar(value='GET')
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        ttk.Combobox(top, textvariable=self.method_var, values=methods, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(top, text='URL:').pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(top, width=60)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        header_frame = ttk.LabelFrame(main, text='Headers')
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        self.headers_text = scrolledtext.ScrolledText(header_frame, height=4)
        self.headers_text.pack(fill=tk.X)

        body_frame = ttk.LabelFrame(main, text='Body')
        body_frame.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        body_top = ttk.Frame(body_frame)
        body_top.pack(fill=tk.X)
        ttk.Label(body_top, text='Type:').pack(side=tk.LEFT)
        self.body_type = tk.StringVar(value='raw')
        ttk.Combobox(body_top, textvariable=self.body_type,
                     values=['raw', 'json', 'form-urlencoded', 'form-data']).pack(side=tk.LEFT)
        self.body_text = scrolledtext.ScrolledText(body_frame, height=10)
        self.body_text.pack(fill=tk.BOTH, expand=True)
        parallel_frame = ttk.Frame(main)
        parallel_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(parallel_frame, text='Parallel:').pack(side=tk.LEFT)
        self.parallel_var = tk.IntVar(value=1)
        ttk.Spinbox(parallel_frame, from_=1, to=100, textvariable=self.parallel_var, width=5).pack(side=tk.LEFT)
        ttk.Button(parallel_frame, text='Send', command=self.send).pack(side=tk.LEFT, padx=5)

        response_frame = ttk.LabelFrame(main, text='Response')
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

    def parse_body(self):
        btype = self.body_type.get()
        text = self.body_text.get('1.0', tk.END).strip()
        data = None
        json_data = None
        files = None
        if btype == 'json':
            try:
                import json
                json_data = json.loads(text) if text else None
            except Exception:
                json_data = None
        elif btype == 'form-urlencoded':
            data = dict(line.split('=', 1) for line in text.splitlines() if '=' in line)
        elif btype == 'form-data':
            data = {}
            files = {}
            for line in text.splitlines():
                if '=' in line:
                    k, v = line.split('=', 1)
                    if v.startswith('@') and os.path.isfile(v[1:]):
                        files[k] = open(v[1:], 'rb')
                    else:
                        data[k] = v
        else:
            data = text if text else None
        return data, json_data, files

    def load_requests(self):
        if self.save_file.exists():
            try:
                self.requests = json.loads(self.save_file.read_text())
            except Exception:
                self.requests = {}
        for name in self.requests:
            self.req_list.insert(tk.END, name)

    def save_requests_file(self):
        self.save_file.write_text(json.dumps(self.requests, indent=2))

    def new_request(self):
        self.method_var.set('GET')
        self.url_entry.delete(0, tk.END)
        self.headers_text.delete('1.0', tk.END)
        self.body_type.set('raw')
        self.body_text.delete('1.0', tk.END)
        self.parallel_var.set(1)

    def save_current_request(self):
        name = simpledialog.askstring('Save request', 'Name:')
        if not name:
            return
        self.requests[name] = {
            'method': self.method_var.get(),
            'url': self.url_entry.get(),
            'headers': self.headers_text.get('1.0', tk.END),
            'body_type': self.body_type.get(),
            'body_text': self.body_text.get('1.0', tk.END),
            'parallel': self.parallel_var.get(),
        }
        self.save_requests_file()
        if name not in self.req_list.get(0, tk.END):
            self.req_list.insert(tk.END, name)

    def on_select_request(self, event):
        if not self.req_list.curselection():
            return
        name = self.req_list.get(self.req_list.curselection()[0])
        req = self.requests.get(name)
        if not req:
            return
        self.method_var.set(req.get('method', 'GET'))
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, req.get('url', ''))
        self.headers_text.delete('1.0', tk.END)
        self.headers_text.insert(tk.END, req.get('headers', ''))
        self.body_type.set(req.get('body_type', 'raw'))
        self.body_text.delete('1.0', tk.END)
        self.body_text.insert(tk.END, req.get('body_text', ''))
        self.parallel_var.set(req.get('parallel', 1))

    def send_request(self, method, url, headers, data, json_data, files, out_list):
        start = time.time()
        try:
            resp = requests.request(method=method, url=url, headers=headers,
                                    data=data, json=json_data, files=files)
            elapsed = time.time() - start
            out_list.append(f'Status: {resp.status_code} Time: {elapsed:.2f}s\n{resp.text}\n')
        except Exception as e:
            elapsed = time.time() - start
            out_list.append(f'Error: {e} Time: {elapsed:.2f}s\n')

    def send(self):
        method = self.method_var.get()
        url = self.url_entry.get()
        headers = self.parse_headers()
        data, json_data, files = self.parse_body()

        if files:
            key, file_obj = next(iter(files.items()))
            file_bytes = file_obj.read()
            file_name = Path(file_obj.name).name
            mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            file_template = {key: (file_name, file_bytes, mime_type)}
            file_obj.close()

        parallel = self.parallel_var.get()
        outputs = []
        threads = []
        for _ in range(parallel):
            t = threading.Thread(target=self.send_request,
                                 args=(
                                     method,
                                     url,
                                     headers,
                                     data,
                                     json_data,
                                     file_template.copy() if files else None,
                                     outputs))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        if files:
            for f in files.values():
                f.close()
        self.response_text.delete('1.0', tk.END)
        self.response_text.insert(tk.END, '\n'.join(outputs))


if __name__ == '__main__':
    HttpClient().mainloop()
