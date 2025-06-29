import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import subprocess
import sys
from threading import Thread, Lock
from queue import Queue, Empty
import os
import shutil
import re
import queue
import threading
from typing import Optional, Tuple, Dict, List, Pattern
import keyword
from pathlib import Path
import json
import platform

class SimplePythonIDE:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("-7的全新Python IDE")
        self.current_folder = None
        self.current_file_path = None
        self.line_number_bar = None
        self.theme_mode = "light"
        self.highlight_patterns = [
            (r'\b(%s)\b' % '|'.join(keyword.kwlist), 'keyword'),
            (r'\b(True|False|None)\b', 'constant'),
            (r'#[^\n]*', 'comment'),
            (r'"[^"]*"', 'string'),
            (r"'[^']*'", 'string'),
            (r'\b\d+\b', 'number'),
        ]
        self.tag_config = {
            'keyword': {'foreground': 'purple'},
            'constant': {'foreground': 'orange'},
            'comment': {'foreground': 'green'},
            'string': {'foreground': 'red'},
            'number': {'foreground': 'blue'},
            'error': {'background': 'red', 'foreground': 'white'},
        }
        self.autocomplete_words = list(keyword.kwlist) + dir(__builtins__)
        self.error_mapping = self._load_error_translations()
        self.process = None
        self.output_queue = Queue()
        self.progress_lock = Lock()
        self.packager = PackageHelper(self)
        self.compile_window = None
        self.pkg_mgr_window = None
        self.fullscreen = False
        self.style = ttk.Style()
        self._setup_ui()
        self._init_highlight_tags()
        self._apply_theme()
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.minsize(800, 600)  # 设置最小窗口尺寸

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        return "break"

    def exit_fullscreen(self, event=None):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)
        return "break"

    def _load_error_translations(self):
        err_file = "error_translations.json"
        def_mapping = {
            "SyntaxError": "语法错误",
            "NameError": "名称错误（变量未定义）",
            "TypeError": "类型错误",
            "ValueError": "值错误",
            "IndexError": "索引错误（超出范围）",
            "KeyError": "键错误（字典键不存在）",
            "AttributeError": "属性错误（对象没有该属性）",
            "ImportError": "导入错误（模块未找到）",
            "ModuleNotFoundError": "模块未找到错误",
            "FileNotFoundError": "文件未找到错误",
            "PermissionError": "权限错误",
            "ZeroDivisionError": "除零错误",
            "IndentationError": "缩进错误",
            "TabError": "制表符错误",
            "UnboundLocalError": "局部变量未绑定错误",
            "RuntimeError": "运行时错误",
            "RecursionError": "递归错误（递归深度过大）"
        }
        try:
            if os.path.exists(err_file):
                with open(err_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(err_file, 'w', encoding='utf-8') as f:
                    json.dump(def_mapping, f, ensure_ascii=False, indent=2)
                return def_mapping
        except Exception as e:
            print(f"加载错误翻译失败: {str(e)}")
            return def_mapping

    def _setup_ui(self):
        self._create_menu()
        
        # 主布局框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 垂直分割窗 (顶部编辑器 + 底部工具)
        self.main_paned = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 顶部框架 (包含文件树和编辑器)
        self.top_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.top_frame, weight=3)  # 编辑器区域权重更大
        
        # 水平分割窗 (左侧文件树 + 右侧编辑器)
        self.top_paned = ttk.PanedWindow(self.top_frame, orient=tk.HORIZONTAL)
        self.top_paned.pack(fill=tk.BOTH, expand=True)
        
        # 文件树区域
        self.file_tree_frame = ttk.LabelFrame(self.top_paned, text="文件资源管理器", width=200)
        self.top_paned.add(self.file_tree_frame, weight=1)
        self._create_file_tree()
        
        # 编辑器区域
        self.editor_frame = ttk.Frame(self.top_paned)
        self.top_paned.add(self.editor_frame, weight=5)  # 编辑器区域权重更大
        self._create_code_editor()
        
        # 按钮区域
        self.button_frame = ttk.Frame(self.top_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        self._create_button_frame()
        
        # 工具区域
        self.tool_frame = ttk.LabelFrame(self.main_paned, text="工具面板")
        self.main_paned.add(self.tool_frame, weight=1)  # 工具区域权重较小
        self._create_tool_notebook()
        
        # 绑定编辑器事件
        self.code_editor.bind('<KeyRelease>', self._highlight_code)
        self.code_editor.bind('<KeyPress>', self._autocomplete_handler)
        self.code_editor.bind('<KeyRelease>', self._update_line_numbers)
        self.code_editor.bind('<MouseWheel>', self._update_line_numbers)
        self.code_editor.bind('<Button-1>', self._update_line_numbers)
        self.code_editor.bind('<Configure>', self._update_line_numbers)

    def _create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="打开文件", command=self.open_file)
        self.file_menu.add_command(label="打开文件夹", command=self.open_folder)
        self.file_menu.add_command(label="保存", command=self.save_file)
        self.file_menu.add_command(label="另存为", command=self.save_file_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="退出", command=self.root.quit)
        self.menu_bar.add_cascade(label="文件", menu=self.file_menu)
        self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.theme_menu.add_command(label="浅色主题", command=lambda: self.switch_theme("light"))
        self.theme_menu.add_command(label="深色主题", command=lambda: self.switch_theme("dark"))
        self.menu_bar.add_cascade(label="主题", menu=self.theme_menu)
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.tools_menu.add_command(label="库管理器", command=lambda: self.tool_notebook.select(0))
        self.tools_menu.add_command(label="编译选项", command=lambda: self.tool_notebook.select(1))
        self.menu_bar.add_cascade(label="工具", menu=self.tools_menu)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_command(label="全屏 (F11)", command=self.toggle_fullscreen)
        self.view_menu.add_command(label="退出全屏 (Esc)", command=self.exit_fullscreen)
        self.menu_bar.add_cascade(label="视图", menu=self.view_menu)

    def _create_tool_notebook(self):
        self.tool_notebook = ttk.Notebook(self.tool_frame)
        self.tool_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._create_pkg_manager_tab()
        self._create_compile_tab()

    def _create_pkg_manager_tab(self):
        pkg_frame = ttk.Frame(self.tool_notebook)
        self.tool_notebook.add(pkg_frame, text="库管理器")
        
        # 系统信息
        info_frame = ttk.LabelFrame(pkg_frame, text="系统信息")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(info_frame, text=f"Python版本: {platform.python_version()}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"工作目录: {os.getcwd()}").pack(anchor=tk.W)
        
        # 镜像源
        mirror_frame = ttk.LabelFrame(pkg_frame, text="镜像源")
        mirror_frame.pack(fill=tk.X, padx=5, pady=5)
        self.mirror_var = tk.StringVar()
        mirrors = [
            ("官方源", "https://pypi.org/simple/"),
            ("阿里云", "https://mirrors.aliyun.com/pypi/simple/"),
            ("清华大学", "https://pypi.tuna.tsinghua.edu.cn/simple/"),
            ("中科大", "https://pypi.mirrors.ustc.edu.cn/simple/"),
            ("华为云", "https://mirrors.huaweicloud.com/repository/pypi/simple/")
        ]
        for name, url in mirrors:
            ttk.Radiobutton(mirror_frame, text=name, variable=self.mirror_var, value=url).pack(anchor=tk.W)
        self.mirror_var.set(mirrors[0][1])
        
        # 包管理
        pkg_frame_inner = ttk.LabelFrame(pkg_frame, text="包管理")
        pkg_frame_inner.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(pkg_frame_inner, text="包名 (多个用空格分隔):").pack(anchor=tk.W)
        self.pkg_entry = ttk.Entry(pkg_frame_inner)
        self.pkg_entry.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(pkg_frame_inner)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="检测pip更新", command=self.check_pip_update).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="更新pip", command=self.update_pip).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="安装", command=self.install_pkgs).pack(side=tk.LEFT, padx=2)
        
        # 输出区域
        output_frame = ttk.LabelFrame(pkg_frame, text="输出")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text = scrolledtext.ScrolledText(output_frame, height=8)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text.config(state=tk.DISABLED)

    def _create_compile_tab(self):
        compile_frame = ttk.Frame(self.tool_notebook)
        self.tool_notebook.add(compile_frame, text="编译选项")
        
        # 编译选项
        options_frame = ttk.LabelFrame(compile_frame, text="编译选项")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(options_frame, text="选择编译方式:").pack(anchor=tk.W)
        
        btn_frame = ttk.Frame(options_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        run_btn = ttk.Button(
            btn_frame, 
            text="直接运行", 
            command=lambda: self.run_code(do_compile=False),
            width=12
        )
        run_btn.pack(side=tk.LEFT, padx=5)
        
        exe_btn = ttk.Button(
            btn_frame, 
            text="编译为EXE", 
            command=lambda: self.packager.package("exe"),
            width=12
        )
        exe_btn.pack(side=tk.LEFT, padx=5)
        
        other_btn = ttk.Button(
            btn_frame, 
            text="其他格式(开发中)", 
            state=tk.DISABLED,
            width=12
        )
        other_btn.pack(side=tk.LEFT, padx=5)
        
        # 打包进度
        progress_frame = ttk.LabelFrame(compile_frame, text="打包进度")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        self.stage_label = ttk.Label(
            progress_frame, 
            text="当前阶段：未开始"
        )
        self.stage_label.pack(anchor=tk.W, padx=10)
        
        # 日志输出
        log_frame = ttk.LabelFrame(progress_frame, text="日志输出")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            height=6
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state='disabled')

    def check_pip_update(self):
        self._run_cmd([sys.executable, "-m", "pip", "list", "--outdated"], "检测更新")

    def install_pkgs(self):
        pkgs = self.pkg_entry.get().strip()
        if not pkgs:
            messagebox.showerror("错误", "请输入包名")
            return
        mirror = self.mirror_var.get()
        self._run_cmd([sys.executable, "-m", "pip", "install", *pkgs.split(), "-i", mirror], "安装")

    def update_pip(self):
        mirror = self.mirror_var.get()
        self._run_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-i", mirror], "更新pip")

    def _run_cmd(self, cmd, action):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"{action}中...\n")
        self.output_text.config(state=tk.DISABLED)
        threading.Thread(target=self._exec_cmd, args=(cmd, action), daemon=True).start()

    def _exec_cmd(self, cmd, action):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8"
            )
            for line in proc.stdout:
                self.root.after(0, self._append_output, line)
            proc.wait()
            if proc.returncode == 0:
                self.root.after(0, self._append_output, f"\n{action}成功!\n")
            else:
                self.root.after(0, self._append_output, f"\n{action}失败! 错误码: {proc.returncode}\n")
        except Exception as e:
            self.root.after(0, self._append_output, f"\n错误: {str(e)}\n")

    def _append_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def switch_theme(self, theme):
        self.theme_mode = theme
        self._apply_theme()

    def _apply_theme(self):
        bg_color = "#f0f0f0" if self.theme_mode == "light" else "#2d2d2d"
        fg_color = "#000000" if self.theme_mode == "light" else "#e0e0e0"
        editor_bg = "#ffffff" if self.theme_mode == "light" else "#1e1e1e"
        self.root.configure(bg=bg_color)
        self.code_editor.configure(bg=editor_bg, fg=fg_color, insertbackground=fg_color)
        self.line_number_bar.configure(bg="#e0e0e0" if self.theme_mode == "light" else "#3d3d3d", 
                                     fg="#666666" if self.theme_mode == "light" else "#a0a0a0")
        self.output_text.configure(bg=editor_bg, fg=fg_color)
        self.log_area.configure(bg=editor_bg, fg=fg_color)
        
        # 修复Treeview样式问题
        self.style.configure("Treeview", 
                            background="#ffffff" if self.theme_mode == "light" else "#252526",
                            foreground="#000000" if self.theme_mode == "light" else "#d4d4d4")
        self.style.map("Treeview", 
                      background=[('selected', '#347083')],
                      foreground=[('selected', 'white')])
        
        # 配置其他组件样式
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("TButton", background="#e1e1e1" if self.theme_mode == "light" else "#3c3c3c", 
                       foreground=fg_color)
        self.style.configure("TLabelFrame", background=bg_color, foreground=fg_color)
        self.style.configure("TNotebook", background=bg_color)
        self.style.configure("TNotebook.Tab", background="#d9d9d9" if self.theme_mode == "light" else "#2d2d2d", 
                       foreground=fg_color)
        self.style.map("TNotebook.Tab", background=[("selected", bg_color)])
        self.style.configure("Vertical.TScrollbar", background=bg_color, troughcolor=bg_color)
        self.style.configure("Horizontal.TScrollbar", background=bg_color, troughcolor=bg_color)
        
        self.tag_config = {
            'keyword': {'foreground': '#9b59b6' if self.theme_mode == "light" else '#bb86fc'},
            'constant': {'foreground': '#e67e22' if self.theme_mode == "light" else '#ffb74d'},
            'comment': {'foreground': '#27ae60' if self.theme_mode == "light" else '#66bb6a'},
            'string': {'foreground': '#e74c3c' if self.theme_mode == "light" else '#f44336'},
            'number': {'foreground': '#3498db' if self.theme_mode == "light" else '#29b6f6'},
            'error': {'background': 'red', 'foreground': 'white'},
        }
        self._init_highlight_tags()
        self._highlight_code()

    def _create_file_tree(self):
        self.tree = ttk.Treeview(self.file_tree_frame, show='tree')
        ysb = ttk.Scrollbar(self.file_tree_frame, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self.file_tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tree.heading('#0', text='目录结构', anchor='w')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.bind('<<TreeviewOpen>>', self._update_tree_children)
        self.tree.bind('<Double-1>', self._open_tree_file)

    def _create_code_editor(self):
        # 创建行号栏和编辑器框架
        editor_container = ttk.Frame(self.editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        # 行号栏
        self.line_number_bar = tk.Text(
            editor_container, 
            width=4, 
            height=1,
            font=("Consolas", 11),
            padx=4,
            takefocus=0,
            border=0,
            highlightthickness=0,
            state="disabled"
        )
        self.line_number_bar.pack(side=tk.LEFT, fill=tk.Y)
        
        # 编辑器
        self.code_editor = scrolledtext.ScrolledText(
            editor_container, 
            wrap=tk.NONE,
            font=("Consolas", 11),
            padx=5,
            pady=5
        )
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        vsb = ttk.Scrollbar(editor_container, orient="vertical", command=self.code_editor.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_editor.configure(yscrollcommand=vsb.set)
        
        # 水平滚动条
        hsb = ttk.Scrollbar(self.editor_frame, orient="horizontal", command=self.code_editor.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.code_editor.configure(xscrollcommand=hsb.set)
        
        # 设置滚动同步
        self.code_editor.configure(yscrollcommand=lambda f, l: self._on_scroll(f, l))
        self.line_number_bar.configure(yscrollcommand=lambda f, l: self.code_editor.yview_moveto(f))

    def _on_scroll(self, first, last):
        self.line_number_bar.yview_moveto(first)
        self._update_line_numbers()

    def _update_line_numbers(self, event=None):
        if not hasattr(self, 'code_editor'):
            return
        line_count = int(self.code_editor.index('end-1c').split('.')[0])
        line_numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        if self.line_number_bar:
            self.line_number_bar.config(state="normal")
            self.line_number_bar.delete("1.0", tk.END)
            self.line_number_bar.insert("1.0", line_numbers)
            self.line_number_bar.config(state="disabled")

    def _create_button_frame(self):
        # 按钮区域
        run_button = ttk.Button(
            self.button_frame, 
            text="运行 (F5)", 
            command=self.run_code,
            width=12
        )
        run_button.pack(side=tk.LEFT, padx=5)
        
        compile_button = ttk.Button(
            self.button_frame, 
            text="编译选项", 
            command=lambda: self.tool_notebook.select(1),
            width=12
        )
        compile_button.pack(side=tk.LEFT, padx=5)
        
        save_button = ttk.Button(
            self.button_frame, 
            text="保存", 
            command=self.save_file,
            width=8
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        open_button = ttk.Button(
            self.button_frame, 
            text="打开", 
            command=self.open_file,
            width=8
        )
        open_button.pack(side=tk.LEFT, padx=5)
        
        # 添加全屏按钮
        fullscreen_button = ttk.Button(
            self.button_frame, 
            text="全屏", 
            command=self.toggle_fullscreen,
            width=8
        )
        fullscreen_button.pack(side=tk.RIGHT, padx=5)

    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        self.current_folder = folder_path
        self.tree.delete(*self.tree.get_children())
        root_node = self.tree.insert('', 'end', text=folder_path, open=True)
        self._load_tree(root_node, folder_path)

    def _load_tree(self, parent, path):
        try:
            for p in Path(path).iterdir():
                if p.name.startswith('.'):
                    continue
                node = self.tree.insert(parent, 'end', text=p.name)
                if p.is_dir():
                    self.tree.insert(node, 'end')
        except Exception as e:
            messagebox.showerror("错误", f"无法加载目录: {str(e)}")

    def _update_tree_children(self, event):
        node = self.tree.focus()
        path = self._get_node_path(node)
        self.tree.delete(*self.tree.get_children(node))
        self._load_tree(node, path)

    def _open_tree_file(self, event):
        node = self.tree.focus()
        path = self._get_node_path(node)
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.code_editor.delete('1.0', tk.END)
                    self.code_editor.insert('1.0', f.read())
                    self.current_file_path = path
                self._update_line_numbers()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")

    def _get_node_path(self, node):
        path = []
        while node:
            path.append(self.tree.item(node)['text'])
            node = self.tree.parent(node)
        return os.path.join(*reversed(path))

    def _init_highlight_tags(self):
        for tag, style in self.tag_config.items():
            self.code_editor.tag_configure(tag, **style)

    def _highlight_code(self, event=None):
        code = self.code_editor.get("1.0", "end-1c")
        self.code_editor.mark_set("range_start", "1.0")
        for tag in self.tag_config.keys():
            self.code_editor.tag_remove(tag, "1.0", tk.END)
        for pattern, tag in self.highlight_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                start = f"1.0 + {match.start()}c"
                end = f"1.0 + {match.end()}c"
                self.code_editor.tag_add(tag, start, end)

    def _autocomplete_handler(self, event):
        if event.keysym in ['Return', 'Escape']:
            self.autocomplete_list.place_forget()
            return
        line = self.code_editor.get("insert linestart", "insert")
        last_word = re.findall(r'\w+$', line)
        if last_word:
            prefix = last_word[0]
            matches = [w for w in self.autocomplete_words if w.startswith(prefix)]
            if matches:
                x, y = self.code_editor.bbox("insert")
                if x and y:
                    self.autocomplete_list.place(x=x, y=y+20)
                    self.autocomplete_list.delete(0, tk.END)
                    for m in sorted(matches):
                        self.autocomplete_list.insert(tk.END, m)
                    self.autocomplete_list.bind('<<ListboxSelect>>', self._insert_completion)
            else:
                self.autocomplete_list.place_forget()
        else:
            self.autocomplete_list.place_forget()

    def _insert_completion(self, event):
        selected = self.autocomplete_list.get(tk.ACTIVE)
        line = self.code_editor.get("insert linestart", "insert")
        last_word = re.findall(r'\w+$', line)
        if last_word:
            word_len = len(last_word[0])
            self.code_editor.delete(f"insert - {word_len}c", "insert")
        self.code_editor.insert("insert", selected)
        self.autocomplete_list.place_forget()

    def run_code(self, do_compile=False):
        if not messagebox.askyesno("警告", "运行未知代码可能有风险，是否继续？"):
            return
        if not self.save_file_if_needed():
            return
        self.code_editor.tag_remove('error', '1.0', tk.END)
        try:
            code = self.code_editor.get('1.0', tk.END)
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            self._handle_syntax_error(e)
            return
        try:
            if os.name == 'nt':
                process = subprocess.Popen(
                    f'start cmd /k python "{self.current_file_path}"', 
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                Thread(target=self._monitor_process_output, args=(process,), daemon=True).start()
            elif os.name == 'posix':
                process = subprocess.Popen(
                    f'x-terminal-emulator -e bash -c "python \\"{self.current_file_path}\\"; read -p \'按回车键继续...\'"',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                Thread(target=self._monitor_process_output, args=(process,), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"执行失败: {str(e)}")

    def _handle_syntax_error(self, e):
        error_type = self.error_mapping.get(type(e).__name__, type(e).__name__)
        message = f"{error_type} 在第 {e.lineno} 行\n\n{e.text.strip()}\n{' ' * (e.offset - 1)}^\n\n{e.msg}"
        messagebox.showerror("语法错误", message)
        if e.lineno:
            start = f"{e.lineno}.0"
            end = f"{e.lineno}.end"
            self.code_editor.tag_add('error', start, end)
            self.code_editor.see(start)

    def _monitor_process_output(self, process):
        output = []
        try:
            for line in iter(process.stdout.readline, ''):
                output.append(line)
                if any(error_type in line for error_type in self.error_mapping):
                    process.wait()
                    self._show_error_dialog(''.join(output))
                    break
        except Exception as e:
            print(f"监控输出时出错: {e}")
        finally:
            process.stdout.close()

    def _show_error_dialog(self, error_output):
        error_type = None
        line_number = None
        error_pattern = re.compile(r'(\w+Error): (.*?)(?:\n|$)')
        line_pattern = re.compile(r'line (\d+)')
        error_match = error_pattern.search(error_output)
        line_match = line_pattern.search(error_output)
        if error_match:
            error_type = error_match.group(1)
            error_msg = error_match.group(2)
            translated_type = self.error_mapping.get(error_type, error_type)
            if line_match:
                line_number = int(line_match.group(1))
                message = f"{translated_type} 在第 {line_number} 行\n\n{error_msg}"
                self.root.after(0, lambda: self._highlight_error_line(line_number))
            else:
                message = f"{translated_type}\n\n{error_msg}"
            self.root.after(0, lambda: messagebox.showerror("运行错误", message))

    def _highlight_error_line(self, line_number):
        self.code_editor.tag_remove('error', '1.0', tk.END)
        start = f"{line_number}.0"
        end = f"{line_number}.end"
        self.code_editor.tag_add('error', start, end)
        self.code_editor.see(start)

    def save_file_if_needed(self):
        if self.current_file_path and os.path.exists(self.current_file_path):
            return self._save_to_file(self.current_file_path)
        else:
            return self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[
                ("Python Files", "*.py"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            return self._save_to_file(file_path)
        return False

    def save_file(self):
        if self.current_file_path:
            return self._save_to_file(self.current_file_path)
        else:
            return self.save_file_as()

    def _save_to_file(self, file_path):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.code_editor.get("1.0", tk.END))
            self.current_file_path = file_path
            return True
        except OSError as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            return False

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Python Files", "*.py"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.code_editor.delete("1.0", tk.END)
                    self.code_editor.insert("1.0", f.read())
                    self.current_file_path = file_path
                self._update_line_numbers()
            except Exception as e:
                messagebox.showerror("错误", f"打开失败: {str(e)}")


class PackageHelper:
    def __init__(self, ide):
        self.ide = ide
        self.source_file = ""
        self.output_dir = ""
        self.progress_window = None
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.stage_regex = [
            (re.compile(r'Analyzing\s.+', re.I), '分析依赖', 'analyzing'),
            (re.compile(r'collecting\s.+', re.I), '收集文件', 'collecting'),
            (re.compile(r'generating\s.+', re.I), '生成中间文件', 'generating'),
            (re.compile(r'writing\s.+', re.I), '写入数据', 'writing'),
            (re.compile(r'building\s.+', re.I), '构建可执行文件', 'building'),
            (re.compile(r'completed\s.+', re.I), '完成打包', 'completed'),
            (re.compile(r'(\d+)/(\d+)\s+steps'), '步骤', 'dynamic')
        ]
        self.stage_weights = {
            'analyzing': 15,
            'collecting': 25,
            'generating': 15,
            'writing': 20,
            'building': 20,
            'completed': 5
        }
        self.completed_stages_progress = 0
        self.current_stage = None
        self.current_step_progress = 0

    def package(self, output_format):
        if not self.ide.save_file_if_needed():
            return
        self.output_dir = filedialog.askdirectory(title="选择保存路径")
        if not self.output_dir:
            messagebox.showerror("错误", "必须选择保存路径")
            return
        self.clean_intermediate = messagebox.askyesno(
            "清除中间文件",
            "打包完成后是否清除build和spec文件夹？"
        )
        self.source_file = self.ide.current_file_path
        self.ide.progress_bar['value'] = 0
        self.ide.stage_label.config(text="当前阶段：初始化")
        self.ide.log_area.config(state='normal')
        self.ide.log_area.delete(1.0, tk.END)
        self.ide.log_area.config(state='disabled')
        threading.Thread(
            target=self._package, 
            args=(output_format,), 
            daemon=True
        ).start()
        self.ide.root.after(100, self.update_progress)

    def update_progress(self):
        while not self.log_queue.empty():
            log = self.log_queue.get_nowait()
            self.ide.log_area.config(state='normal')
            self.ide.log_area.insert(tk.END, log + "\n")
            self.ide.log_area.config(state='disabled')
            self.ide.log_area.see(tk.END)
        while not self.progress_queue.empty():
            progress, stage = self.progress_queue.get_nowait()
            self.ide.progress_bar['value'] = min(progress, 100)
            self.ide.stage_label.config(text=f"当前阶段：{stage}")
        self.ide.root.after(100, self.update_progress)

    def _package(self, output_format):
        if output_format == "exe":
            self.package_to_exe()
        else:
            self.log_queue.put("不支持的打包格式")
            messagebox.showinfo("错误", "选择的格式不支持")

    def package_to_exe(self):
        if not self._check_pyinstaller():
            return
        try:
            process = subprocess.Popen(
                ["pyinstaller", "--onefile",
                 "--distpath", self.output_dir,
                 "--workpath", os.path.join(self.output_dir, "build"),
                 "--specpath", os.path.join(self.output_dir, "spec"),
                 "--clean", self.source_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8"
            )
            self._process_pyinstaller_output(process)
            if process.returncode == 0:
                self._handle_success()
            else:
                messagebox.showerror("失败", f"错误代码：{process.returncode}")
        except Exception as e:
            self.log_queue.put(f"打包异常：{str(e)}")
            messagebox.showerror("错误", str(e))

    def _check_pyinstaller(self):
        try:
            subprocess.run(
                ["pyinstaller", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            self.log_queue.put(f"错误：{str(e)}")
            messagebox.showerror("错误", "请先安装pyinstaller\npip install pyinstaller")
            return False

    def _process_pyinstaller_output(self, process):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.log_queue.put(output.strip())
                self._update_progress_from_output(output)

    def _update_progress_from_output(self, output):
        for regex, display_name, stage_key in self.stage_regex:
            match = regex.search(output)
            if match:
                if stage_key == 'dynamic' and self.current_stage:
                    self._update_dynamic_progress(match, display_name)
                else:
                    self._update_stage_progress(stage_key, display_name)
                break

    def _update_dynamic_progress(self, match, display_name):
        current = int(match.group(1))
        total = int(match.group(2))
        stage_weight = self.stage_weights.get(self.current_stage, 0)
        self.current_step_progress = (current / total) * stage_weight
        total_progress = self.completed_stages_progress + self.current_step_progress
        self.progress_queue.put((
            total_progress,
            f"{display_name} ({current}/{total})"
        ))

    def _update_stage_progress(self, stage_key, display_name):
        if self.current_stage:
            self.completed_stages_progress += self.stage_weights.get(self.current_stage, 0)
        self.current_stage = stage_key
        self.current_step_progress = 0
        self.progress_queue.put((
            self.completed_stages_progress,
            display_name
        ))

    def _handle_success(self):
        if self.current_stage:
            self.completed_stages_progress += self.stage_weights.get(self.current_stage, 0)
        self.progress_queue.put((100, "完成"))
        if self.clean_intermediate:
            self._clean_intermediate_files()
        messagebox.showinfo("成功", f"文件已生成到：\n{self.output_dir}")

    def _clean_intermediate_files(self):
        build_path = os.path.join(self.output_dir, "build")
        spec_path = os.path.join(self.output_dir, "spec")
        try:
            if os.path.exists(build_path):
                shutil.rmtree(build_path)
            if os.path.exists(spec_path):
                shutil.rmtree(spec_path)
            self.log_queue.put("已清除中间文件")
        except Exception as e:
            self.log_queue.put(f"删除中间文件失败：{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.geometry("1000x700")
        ide = SimplePythonIDE(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"应用程序崩溃: {str(e)}")
        raise