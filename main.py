import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import subprocess
import sys
from threading import Thread
import os
import shutil
import re
import queue
import threading
import keyword
from pathlib import Path
import json
import platform
import webbrowser

class SimplePythonIDE:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("-7的全新Python IDE")
        self.cf = None
        self.cfp = None
        self.lnb = None
        self.hp = [
            (r'\b(%s)\b' % '|'.join(keyword.kwlist), 'kw'),
            (r'\b(True|False|None)\b', 'con'),
            (r'\b\d+\b', 'num'),
            (r'#[^\n]*', 'com'),
            (r'"(?:[^"\\]|\\.)*"', 'str'),
            (r"'(?:[^'\\]|\\.)*'", 'str'),
        ]
        self.tc = {
            'kw': {'foreground': '#800080'},
            'con': {'foreground': '#FFA500'},
            'com': {'foreground': '#008000'},
            'str': {'foreground': '#FF0000'},
            'num': {'foreground': '#0000FF'},
            'err': {'background': '#FF0000', 'foreground': '#FFFFFF'},
        }
        self.acw = list(keyword.kwlist) + dir(__builtins__)
        self.em = self._le()
        self.p = None
        self.oq = queue.Queue()
        self.pl = threading.Lock()
        self.ph = PackageHelper(self)
        self.cw = None
        self.pmw = None
        self.style = ttk.Style()
        self._su()
        self._iht()
        self.root.bind("<F5>", lambda e: self.rc())
        self.root.minsize(800, 600)
        self.tp_visible = False
        self.hc_timer = None
        self.acl = None
        self.work_dir = None
        self.scroll_lock = False

    def _le(self):
        ef = "error_translations.json"
        dm = {
            "SyntaxError": "语法错误: 代码不符合Python语法规则",
            "NameError": "名称错误: 使用了未定义的变量或函数",
            "TypeError": "类型错误: 操作或函数应用于不适当类型的对象",
            "ValueError": "值错误: 传入无效值",
            "IndexError": "索引错误: 序列下标超出范围",
            "KeyError": "键错误: 字典中不存在该键",
            "AttributeError": "属性错误: 对象没有该属性",
            "ImportError": "导入错误: 导入模块/对象失败",
            "ModuleNotFoundError": "模块未找到: 无法找到指定模块",
            "FileNotFoundError": "文件未找到: 找不到指定文件或目录",
            "PermissionError": "权限错误: 没有足够权限执行该操作",
            "ZeroDivisionError": "除零错误: 除数不能为零",
            "IndentationError": "缩进错误: 缩进不正确",
            "TabError": "制表符错误: 制表符和空格混用",
            "UnboundLocalError": "局部变量未绑定: 在赋值前引用了局部变量",
            "RuntimeError": "运行时错误: 一般运行时错误",
            "RecursionError": "递归错误: 超出最大递归深度",
            "KeyboardInterrupt": "键盘中断: 用户中断执行(Ctrl+C)",
            "MemoryError": "内存错误: 内存不足",
            "OverflowError": "溢出错误: 数值运算超出最大限制",
            "NotImplementedError": "未实现错误: 功能尚未实现",
            "AssertionError": "断言错误: 断言语句失败",
            "StopIteration": "迭代停止: 迭代器没有更多值",
            "GeneratorExit": "生成器退出: 生成器被关闭",
            "SystemError": "系统错误: 解释器内部错误",
            "OSError": "操作系统错误: 系统相关错误",
            "Warning": "警告: 非致命警告"
        }
        try:
            if os.path.exists(ef):
                with open(ef, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(ef, 'w', encoding='utf-8') as f:
                    json.dump(dm, f, ensure_ascii=False, indent=2)
                return dm
        except Exception:
            return dm

    def _su(self):
        self._cm()
        self.mf = ttk.Frame(self.root)
        self.mf.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.mp = ttk.PanedWindow(self.mf, orient=tk.VERTICAL)
        self.mp.pack(fill=tk.BOTH, expand=True)
        self.tf = ttk.Frame(self.mp)
        self.mp.add(self.tf, weight=3)
        self.tp = ttk.PanedWindow(self.tf, orient=tk.HORIZONTAL)
        self.tp.pack(fill=tk.BOTH, expand=True)
        self.ftf = ttk.LabelFrame(self.tp, text="文件资源管理器", width=200)
        self.tp.add(self.ftf, weight=1)
        self._cf()
        self.efr = ttk.Frame(self.tp)
        self.tp.add(self.efr, weight=5)
        self._cce()
        self.tfr = ttk.LabelFrame(self.mp, text="工具面板")
        self.tfr.pack_forget()
        self.root.bind('<KeyRelease>', self._hc_d)
        self.root.bind('<KeyPress>', self._ah)
        self.root.bind('<KeyRelease>', self._uln)
        self.root.bind('<MouseWheel>', self._uln)
        self.root.bind('<Button-1>', self._uln)
        self.root.bind('<Configure>', self._uln)

    def _cm(self):
        self.mb = tk.Menu(self.root)
        self.root.config(menu=self.mb)
        self.fm = tk.Menu(self.mb, tearoff=0)
        self.fm.add_command(label="打开文件", command=self.of)
        self.fm.add_command(label="打开文件夹", command=self.ofd)
        self.fm.add_command(label="保存", command=self.sf)
        self.fm.add_command(label="另存为", command=self.sfa)
        self.fm.add_command(label="设置工作目录", command=self.set_work_dir)
        self.fm.add_separator()
        self.fm.add_command(label="退出", command=self.root.quit)
        self.mb.add_cascade(label="文件", menu=self.fm)
        self.em = tk.Menu(self.mb, tearoff=0)
        self.em.add_command(label="撤销", command=self.undo, accelerator="Ctrl+Z")
        self.em.add_command(label="重做", command=self.redo, accelerator="Ctrl+Y")
        self.em.add_separator()
        self.em.add_command(label="剪切", command=self.cut, accelerator="Ctrl+X")
        self.em.add_command(label="复制", command=self.copy, accelerator="Ctrl+C")
        self.em.add_command(label="粘贴", command=self.paste, accelerator="Ctrl+V")
        self.em.add_separator()
        self.em.add_command(label="全选", command=self.select_all, accelerator="Ctrl+A")
        self.em.add_command(label="查找", command=self.find_text, accelerator="Ctrl+F")
        self.mb.add_cascade(label="编辑", menu=self.em)
        self.rm = tk.Menu(self.mb, tearoff=0)
        self.rm.add_command(label="运行 (F5)", command=self.rc)
        self.mb.add_cascade(label="运行", menu=self.rm)
        self.tm = tk.Menu(self.mb, tearoff=0)
        self.tm.add_command(label="库管理器", command=lambda: self.tt(0))
        self.tm.add_command(label="编译选项", command=lambda: self.tt(1))
        self.mb.add_cascade(label="工具", menu=self.tm)
        self.hm = tk.Menu(self.mb, tearoff=0)
        self.hm.add_command(label="打开官网", command=lambda: webbrowser.open("https://github.com/fuzhiyin-7/IDE"))
        self.mb.add_cascade(label="帮助", menu=self.hm)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-x>", lambda e: self.cut())
        self.root.bind("<Control-c>", lambda e: self.copy())
        self.root.bind("<Control-v>", lambda e: self.paste())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<Control-f>", lambda e: self.find_text())

    def set_work_dir(self):
        wd = filedialog.askdirectory()
        if wd:
            self.work_dir = wd
            messagebox.showinfo("工作目录设置", f"工作目录已设置为:\n{wd}")

    def tt(self, idx):
        if not self.tp_visible:
            self.mp.add(self.tfr, weight=1)
            self.tp_visible = True
        self.tn.select(idx)

    def tc_hide(self):
        if self.tp_visible:
            self.mp.forget(self.tfr)
            self.tp_visible = False

    def _ctn(self):
        top_frame = ttk.Frame(self.tfr)
        top_frame.pack(fill=tk.X, pady=5)
        ttk.Button(top_frame, text="×", command=self.tc_hide, width=2).pack(side=tk.RIGHT, padx=5)
        self.tn = ttk.Notebook(self.tfr)
        self.tn.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._cpmt()
        self._cct()

    def _cpmt(self):
        pmf = ttk.Frame(self.tn)
        self.tn.add(pmf, text="库管理器")
        ifr = ttk.LabelFrame(pmf, text="系统信息")
        ifr.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(ifr, text=f"Python版本: {platform.python_version()}").pack(anchor=tk.W)
        ttk.Label(ifr, text=f"工作目录: {os.getcwd()}").pack(anchor=tk.W)
        mf = ttk.LabelFrame(pmf, text="镜像源")
        mf.pack(fill=tk.X, padx=5, pady=5)
        self.mv = tk.StringVar()
        ms = [("官方源","https://pypi.org/simple/"),("阿里云","https://mirrors.aliyun.com/pypi/simple/"),
              ("清华大学","https://pypi.tuna.tsinghua.edu.cn/simple/"),("中科大","https://pypi.mirrors.ustc.edu.cn/simple/"),
              ("华为云","https://mirrors.huaweicloud.com/repository/pypi/simple/")]
        for n, u in ms:
            ttk.Radiobutton(mf, text=n, variable=self.mv, value=u).pack(anchor=tk.W)
        self.mv.set(ms[0][1])
        pfi = ttk.LabelFrame(pmf, text="包管理")
        pfi.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(pfi, text="包名 (多个用空格分隔):").pack(anchor=tk.W)
        self.pe = ttk.Entry(pfi)
        self.pe.pack(fill=tk.X, padx=5, pady=5)
        bf = ttk.Frame(pfi)
        bf.pack(fill=tk.X, pady=5)
        ttk.Button(bf, text="检测pip更新", command=self.cpu).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="更新pip", command=self.up).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text="安装", command=self.ip).pack(side=tk.LEFT, padx=2)
        ofr = ttk.LabelFrame(pmf, text="输出")
        ofr.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ofb = ttk.Frame(ofr)
        ofb.pack(fill=tk.X, pady=2)
        ttk.Button(ofb, text="清空输出", command=self._cot).pack(side=tk.LEFT, padx=5)
        self.ot = scrolledtext.ScrolledText(ofr, height=8)
        self.ot.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ot.config(state=tk.DISABLED)

    def _cot(self):
        self.ot.config(state=tk.NORMAL)
        self.ot.delete(1.0, tk.END)
        self.ot.config(state=tk.DISABLED)

    def _cct(self):
        cf = ttk.Frame(self.tn)
        self.tn.add(cf, text="编译选项")
        ofr = ttk.LabelFrame(cf, text="编译选项")
        ofr.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(ofr, text="选择编译方式:").pack(anchor=tk.W)
        bf = ttk.Frame(ofr)
        bf.pack(fill=tk.X, pady=5)
        ttk.Button(bf, text="直接运行", command=lambda: self.rc(), width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="编译为EXE", command=lambda: self.ph.p("exe"), width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="其他格式", state=tk.DISABLED, width=12).pack(side=tk.LEFT, padx=5)
        pfr = ttk.LabelFrame(cf, text="打包进度")
        pfr.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.pb = ttk.Progressbar(pfr, orient=tk.HORIZONTAL, mode='determinate', maximum=100)
        self.pb.pack(fill=tk.X, padx=10, pady=5)
        self.sl = ttk.Label(pfr, text="当前阶段：未开始")
        self.sl.pack(anchor=tk.W, padx=10)
        lfr = ttk.LabelFrame(pfr, text="日志输出")
        lfr.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        lfb = ttk.Frame(lfr)
        lfb.pack(fill=tk.X, pady=2)
        ttk.Button(lfb, text="清空输出", command=self._cll).pack(side=tk.LEFT, padx=5)
        self.la = scrolledtext.ScrolledText(lfr, wrap=tk.WORD, height=6)
        self.la.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.la.config(state='disabled')

    def _cll(self):
        self.la.config(state='normal')
        self.la.delete(1.0, tk.END)
        self.la.config(state='disabled')

    def cpu(self):
        self._rc([sys.executable, "-m", "pip", "list", "--outdated"], "检测更新")

    def ip(self):
        p = self.pe.get().strip()
        if not p:
            messagebox.showerror("错误", "请输入包名")
            return
        m = self.mv.get()
        self._rc([sys.executable, "-m", "pip", "install", *p.split(), "-i", m], "安装")

    def up(self):
        m = self.mv.get()
        self._rc([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-i", m], "更新pip")

    def _rc(self, c, a):
        self.ot.config(state=tk.NORMAL)
        self.ot.delete(1.0, tk.END)
        self.ot.insert(tk.END, f"{a}中...\n")
        self.ot.config(state=tk.DISABLED)
        threading.Thread(target=self._ec, args=(c, a), daemon=True).start()

    def _ec(self, c, a):
        try:
            p = subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8")
            for l in p.stdout:
                self.root.after(0, self._ao, l)
            p.wait()
            if p.returncode == 0:
                self.root.after(0, self._ao, f"\n{a}成功!\n")
            else:
                self.root.after(0, self._ao, f"\n{a}失败! 错误码: {p.returncode}\n")
        except Exception as e:
            self.root.after(0, self._ao, f"\n错误: {str(e)}\n")

    def _ao(self, t):
        self.ot.config(state=tk.NORMAL)
        self.ot.insert(tk.END, t)
        self.ot.see(tk.END)
        self.ot.config(state=tk.DISABLED)

    def _cf(self):
        self.tr = ttk.Treeview(self.ftf, show='tree')
        ysb = ttk.Scrollbar(self.ftf, orient='vertical', command=self.tr.yview)
        xsb = ttk.Scrollbar(self.ftf, orient='horizontal', command=self.tr.xview)
        self.tr.configure(yscroll=ysb.set, xscroll=xsb.set)
        self.tr.heading('#0', text='目录结构', anchor='w')
        self.tr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tr.bind('<<TreeviewOpen>>', self._utc)
        self.tr.bind('<Double-1>', self._otf)

    def _cce(self):
        ec = ttk.Frame(self.efr)
        ec.pack(fill=tk.BOTH, expand=True)
        self.lnb = tk.Text(ec, width=4, height=1, font=("Consolas", 11), padx=4, takefocus=0, border=0, highlightthickness=0, state="disabled")
        self.lnb.pack(side=tk.LEFT, fill=tk.Y)
        self.ce = tk.Text(ec, wrap=tk.NONE, font=("Consolas", 11), padx=5, pady=5, undo=True)
        vsb = ttk.Scrollbar(ec, orient="vertical", command=self._sync_scroll)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(ec, orient="horizontal", command=self.ce.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.ce.configure(yscrollcommand=self._update_scroll)
        self.ce.configure(xscrollcommand=hsb.set)
        self.ce.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lnb.configure(yscrollcommand=lambda *args: vsb.set(*args))
        self.ce.bind('<KeyRelease>', self._uln)
        self.ce.bind('<KeyPress>', self._ah)
        self.ce.bind('<MouseWheel>', self._uln)
        self.ce.bind('<Button-1>', self._uln)
        self.ce.bind('<Configure>', self._uln)
        self.ce.bind('<KeyRelease>', self._hc_d)
        self.ce.insert(tk.END, "欢迎使用Python IDE！\n\n功能说明：\n1. 支持Python代码编辑和运行\n2. 支持文件资源管理器\n3. 支持库管理和编译选项\n\n请从文件开始使用...")

    def _update_scroll(self, *args):
        if not self.scroll_lock:
            self.scroll_lock = True
            self.lnb.yview_moveto(args[0])
            self.scroll_lock = False
        return True

    def _sync_scroll(self, *args):
        if not self.scroll_lock:
            self.scroll_lock = True
            self.ce.yview(*args)
            self.lnb.yview(*args)
            self.scroll_lock = False
        self._uln()

    def _uln(self, e=None):
        if not self.ce.winfo_exists():
            return
        lc = int(self.ce.index('end-1c').split('.')[0])
        lns = "\n".join(str(i) for i in range(1, lc + 1))
        self.lnb.config(state="normal")
        self.lnb.delete("1.0", tk.END)
        self.lnb.insert("1.0", lns)
        self.lnb.config(state="disabled")
        self._hc_d()

    def ofd(self):
        fp = filedialog.askdirectory()
        if not fp:
            return
        self.cf = fp
        self.tr.delete(*self.tr.get_children())
        rn = self.tr.insert('', 'end', text=fp, open=True)
        self._lt(rn, fp)

    def _lt(self, p, pt):
        try:
            for pth in Path(pt).iterdir():
                if pth.name.startswith('.'):
                    continue
                n = self.tr.insert(p, 'end', text=pth.name)
                if pth.is_dir():
                    self.tr.insert(n, 'end')
        except Exception as e:
            messagebox.showerror("错误", f"无法加载目录: {str(e)}")

    def _utc(self, e):
        n = self.tr.focus()
        pt = self._gnp(n)
        self.tr.delete(*self.tr.get_children(n))
        self._lt(n, pt)

    def _otf(self, e):
        n = self.tr.focus()
        pt = self._gnp(n)
        if os.path.isfile(pt):
            try:
                with open(pt, 'r', encoding='utf-8') as f:
                    self.ce.delete('1.0', tk.END)
                    self.ce.insert('1.0', f.read())
                    self.cfp = pt
                self._uln()
                self._hc_d()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")

    def _gnp(self, n):
        p = []
        while n:
            p.append(self.tr.item(n)['text'])
            n = self.tr.parent(n)
        return os.path.join(*reversed(p))

    def _iht(self):
        for t, s in self.tc.items():
            self.ce.tag_configure(t, **s)

    def _hc_d(self, e=None):
        if self.hc_timer:
            self.root.after_cancel(self.hc_timer)
        self.hc_timer = self.root.after(300, self._hc)

    def _hc(self):
        if not self.ce.winfo_exists():
            return
        self.ce.mark_set("range_start", "1.0")
        for t in self.tc.keys():
            self.ce.tag_remove(t, "1.0", tk.END)
        c = self.ce.get("1.0", "end-1c")
        for p, t in self.hp:
            flags = re.MULTILINE | re.DOTALL if t == 'str' else re.MULTILINE
            ms = re.finditer(p, c, flags)
            for m in ms:
                s = f"1.0 + {m.start()}c"
                e = f"1.0 + {m.end()}c"
                self.ce.tag_add(t, s, e)

    def _ah(self, e):
        if e.keysym in ['Return', 'Escape']:
            if self.acl and self.acl.winfo_exists():
                self.acl.destroy()
            return
        if e.keysym == 'Tab' and self.acl and self.acl.winfo_exists():
            self._ic(None)
            return "break"
        ln = self.ce.get("insert linestart", "insert")
        lw = re.findall(r'\w+$', ln)
        if lw:
            px = lw[0]
            ms = [w for w in self.acw if w.startswith(px)]
            if ms:
                x, y = self.ce.bbox("insert")
                if x is None or y is None:
                    return
                if self.acl and self.acl.winfo_exists():
                    self.acl.destroy()
                self.acl = tk.Listbox(self.ce, height=min(10, len(ms)))
                self.acl.place(x=x, y=y+20)
                for m in sorted(ms)[:20]:
                    self.acl.insert(tk.END, m)
                self.acl.bind('<<ListboxSelect>>', self._ic)
                self.acl.bind('<Return>', self._ic)
                self.acl.focus_set()
                self.acl.selection_set(0)
            else:
                if self.acl and self.acl.winfo_exists():
                    self.acl.destroy()
        else:
            if self.acl and self.acl.winfo_exists():
                self.acl.destroy()

    def _ic(self, e):
        if not self.acl or not self.acl.winfo_exists():
            return
        if not self.acl.curselection():
            return
        s = self.acl.get(self.acl.curselection()[0])
        ln = self.ce.get("insert linestart", "insert")
        lw = re.findall(r'\w+$', ln)
        if lw:
            wl = len(lw[0])
            self.ce.delete(f"insert - {wl}c", "insert")
        self.ce.insert("insert", s)
        self.acl.destroy()

    def rc(self, dc=False):
        if not self.sfi():
            return
        self.ce.tag_remove('err', '1.0', tk.END)
        try:
            c = self.ce.get('1.0', tk.END)
            compile(c, '<string>', 'exec')
        except SyntaxError as e:
            self._hse(e)
            return
        try:
            wd = self.work_dir if self.work_dir else os.path.dirname(self.cfp)
            if not wd:
                wd = os.getcwd()
            if platform.system() == "Windows":
                subprocess.Popen(f'start cmd /k "cd /d "{wd}" && python "{self.cfp}"', shell=True)
            else:
                subprocess.Popen(['x-terminal-emulator', '-e', f'bash -c \'cd "{wd}" && python3 "{self.cfp}"\''])
        except Exception as e:
            messagebox.showerror("执行失败", f"无法启动终端: {str(e)}")

    def _hse(self, e):
        et = self.em.get(type(e).__name__, type(e).__name__)
        m = f"{et} 在第 {e.lineno} 行\n\n{e.text.strip()}\n{' ' * (e.offset - 1)}^\n\n{e.msg}"
        messagebox.showerror("语法错误", m)
        if e.lineno:
            s = f"{e.lineno}.0"
            e = f"{e.lineno}.end"
            self.ce.tag_add('err', s, e)
            self.ce.see(s)

    def sfi(self):
        if self.cfp and os.path.exists(self.cfp):
            return self._stf(self.cfp)
        else:
            return self.sfa()

    def sfa(self):
        fp = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if fp:
            return self._stf(fp)
        return False

    def sf(self):
        if self.cfp:
            return self._stf(self.cfp)
        else:
            return self.sfa()

    def _stf(self, fp):
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.ce.get("1.0", tk.END))
            self.cfp = fp
            return True
        except OSError as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            return False

    def of(self):
        fp = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if fp:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    self.ce.delete("1.0", tk.END)
                    self.ce.insert("1.0", f.read())
                    self.cfp = fp
                self._uln()
                self._hc_d()
            except Exception as e:
                messagebox.showerror("错误", f"打开失败: {str(e)}")

    def undo(self):
        try:
            self.ce.edit_undo()
        except:
            pass

    def redo(self):
        try:
            self.ce.edit_redo()
        except:
            pass

    def cut(self):
        self.ce.event_generate("<<Cut>>")

    def copy(self):
        self.ce.event_generate("<<Copy>>")

    def paste(self):
        self.ce.event_generate("<<Paste>>")

    def select_all(self):
        self.ce.tag_add(tk.SEL, "1.0", tk.END)
        self.ce.mark_set(tk.INSERT, "1.0")
        self.ce.see(tk.INSERT)
        return "break"

    def find_text(self):
        self.find_window = tk.Toplevel(self.root)
        self.find_window.title("查找")
        self.find_window.geometry("400x150")
        self.find_window.resizable(False, False)
        self.find_window.transient(self.root)
        self.find_window.grab_set()
        tk.Label(self.find_window, text="查找内容:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        self.find_entry = tk.Entry(self.find_window, width=40)
        self.find_entry.pack(padx=10, pady=5)
        frame = tk.Frame(self.find_window)
        frame.pack(pady=10)
        tk.Button(frame, text="查找下一个", command=self.find_next, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="取消", command=self.find_window.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def find_next(self):
        search_str = self.find_entry.get()
        if not search_str:
            return
        start_pos = self.ce.index(tk.INSERT)
        pos = self.ce.search(search_str, start_pos, nocase=1, stopindex=tk.END)
        if pos:
            end_pos = f"{pos}+{len(search_str)}c"
            self.ce.tag_remove(tk.SEL, "1.0", tk.END)
            self.ce.tag_add(tk.SEL, pos, end_pos)
            self.ce.mark_set(tk.INSERT, end_pos)
            self.ce.see(tk.INSERT)
            self.ce.focus_set()
        else:
            if start_pos != "1.0":
                pos = self.ce.search(search_str, "1.0", nocase=1, stopindex=tk.END)
                if pos:
                    end_pos = f"{pos}+{len(search_str)}c"
                    self.ce.tag_remove(tk.SEL, "1.0", tk.END)
                    self.ce.tag_add(tk.SEL, pos, end_pos)
                    self.ce.mark_set(tk.INSERT, end_pos)
                    self.ce.see(tk.INSERT)
                    self.ce.focus_set()
                else:
                    messagebox.showinfo("查找", "找不到匹配项")
            else:
                messagebox.showinfo("查找", "找不到匹配项")

class PackageHelper:
    def __init__(self, ide):
        self.ide = ide
        self.sf = ""
        self.od = ""
        self.lq = queue.Queue()
        self.pq = queue.Queue()
        self.sr = [
            (re.compile(r'Analyzing\s.+', re.I), '分析依赖', 'a'),
            (re.compile(r'collecting\s.+', re.I), '收集文件', 'c'),
            (re.compile(r'generating\s.+', re.I), '生成中间文件', 'g'),
            (re.compile(r'writing\s.+', re.I), '写入数据', 'w'),
            (re.compile(r'building\s.+', re.I), '构建可执行文件', 'b'),
            (re.compile(r'completed\s.+', re.I), '完成打包', 'd'),
            (re.compile(r'(\d+)/(\d+)\s+steps'), '步骤', 'dy')
        ]
        self.sw = {'a':15, 'c':25, 'g':15, 'w':20, 'b':20, 'd':5}
        self.csp = 0
        self.cs = None
        self.cspg = 0

    def p(self, of):
        if not self.ide.sfi():
            return
        self.od = filedialog.askdirectory(title="选择保存路径")
        if not self.od:
            messagebox.showerror("错误", "必须选择保存路径")
            return
        self.ci = messagebox.askyesno("清除中间文件", "打包完成后是否清除build和spec文件夹？")
        self.sf = self.ide.cfp
        self.ide.pb['value'] = 0
        self.ide.sl.config(text="当前阶段：初始化")
        self.ide.la.config(state='normal')
        self.ide.la.delete(1.0, tk.END)
        self.ide.la.config(state='disabled')
        threading.Thread(target=self._p, args=(of,), daemon=True).start()
        self.ide.root.after(100, self.up)

    def up(self):
        while not self.lq.empty():
            l = self.lq.get_nowait()
            self.ide.la.config(state='normal')
            self.ide.la.insert(tk.END, l + "\n")
            self.ide.la.config(state='disabled')
            self.ide.la.see(tk.END)
        while not self.pq.empty():
            p, s = self.pq.get_nowait()
            self.ide.pb['value'] = min(p, 100)
            self.ide.sl.config(text=f"当前阶段：{s}")
        self.ide.root.after(100, self.up)

    def _p(self, of):
        if of == "exe":
            self.pte()
        else:
            self.lq.put("不支持的打包格式")
            messagebox.showinfo("错误", "选择的格式不支持")

    def pte(self):
        if not self._cp():
            return
        try:
            p = subprocess.Popen(["pyinstaller", "--onefile", "--distpath", self.od, "--workpath", os.path.join(self.od, "build"), "--specpath", os.path.join(self.od, "spec"), "--clean", self.sf], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8")
            self._ppo(p)
            if p.returncode == 0:
                self._hs()
            else:
                messagebox.showerror("失败", f"错误代码：{p.returncode}")
        except Exception as e:
            self.lq.put(f"打包异常：{str(e)}")
            messagebox.showerror("错误", str(e))

    def _cp(self):
        try:
            subprocess.run(["pyinstaller", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            self.lq.put(f"错误：{str(e)}")
            messagebox.showerror("错误", "请先安装pyinstaller\npip install pyinstaller")
            return False

    def _ppo(self, p):
        while True:
            o = p.stdout.readline()
            if o == '' and p.poll() is not None:
                break
            if o:
                self.lq.put(o.strip())
                self._upfo(o)
        if p.returncode == 0:
            self._hs()

    def _upfo(self, o):
        for r, dn, sk in self.sr:
            m = r.search(o)
            if m:
                if sk == 'dy' and self.cs:
                    self._udp(m, dn)
                else:
                    self._usp(sk, dn)
                break

    def _udp(self, m, dn):
        cur = int(m.group(1))
        tot = int(m.group(2))
        sw = self.sw.get(self.cs, 0)
        self.cspg = (cur / tot) * sw
        tp = self.csp + self.cspg
        self.pq.put((tp, f"{dn} ({cur}/{tot})"))

    def _usp(self, sk, dn):
        if self.cs:
            self.csp += self.sw.get(self.cs, 0)
        self.cs = sk
        self.cspg = 0
        self.pq.put((self.csp, dn))

    def _hs(self):
        if self.cs:
            self.csp += self.sw.get(self.cs, 0)
        self.pq.put((100, "完成"))
        if self.ci:
            self._cif()
        messagebox.showinfo("成功", f"文件已生成到：\n{self.od}")

    def _cif(self):
        bp = os.path.join(self.od, "build")
        sp = os.path.join(self.od, "spec")
        try:
            if os.path.exists(bp):
                shutil.rmtree(bp)
            if os.path.exists(sp):
                shutil.rmtree(sp)
            self.lq.put("已清除中间文件")
        except Exception as e:
            self.lq.put(f"删除中间文件失败：{str(e)}")

if __name__ == "__main__":
    r = tk.Tk()
    try:
        r.geometry("1000x700")
        ide = SimplePythonIDE(r)
        ide._ctn()
        r.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"应用程序崩溃: {str(e)}")
        raise