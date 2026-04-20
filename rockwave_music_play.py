#!/usr/bin/env python3
"""
jzmp3.com 音乐下载器 - 简洁版
使用 Playwright 实现全自动搜索和下载
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import os
import json
import time
import re
import urllib.parse
import platform

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


COLORS = {
    'bg_main': '#c9b896',
    'bg_panel': '#b8a580',
    'bg_input': '#e8dcc8',
    'wood_dark': '#3d2e1c',
    'wood_medium': '#5c4a30',
    'wood_light': '#8b7355',
    'brass': '#6b5344',
    'brass_shiny': '#7d6550',
    'text': '#2d2010',
    'text_light': '#5c4a30',
    'green_led': '#806030',
    'red_led': '#603010',
    'shadow': '#a89070',
}

FONTS = {
    'title': ('Georgia', 18, 'bold'),
    'heading': ('Georgia', 12, 'bold'),
    'body': ('Courier New', 11),
    'mono': ('Courier New', 10),
    'small': ('Courier New', 9),
    'led': ('Courier New', 9, 'bold'),
}


class ROCKWAVEMP3AutoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("♪ RockWave 音乐播放器")
        self.root.geometry("900x700")
        self.root.minsize(850, 650)
        self.root.configure(bg=COLORS['bg_main'])

        self.download_dir = "/Users/apple/Music/mp3"
        os.makedirs(self.download_dir, exist_ok=True)

        self.downloaded_file = os.path.join(self.download_dir, "downloaded.json")
        self.downloaded = self.load_downloaded()

        self.current_songs = []
        self.current_query = ""
        self.current_page = 1
        self.total_pages = 1
        self.play_process = None
        self.playing = False
        self.duration = 0
        self.file_list = []
        self.playback_start_time = None
        
        # 不使用锁，改用简单的状态标记
        self._stopping = False

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        self._force_stop_playback()
        self.root.destroy()

    def load_downloaded(self):
        try:
            if os.path.exists(self.downloaded_file):
                with open(self.downloaded_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_downloaded(self):
        with open(self.downloaded_file, 'w') as f:
            json.dump(self.downloaded, f, indent=2, ensure_ascii=False)

    def create_widgets(self):
        # 使用 Grid 布局来精确控制
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        main_container = tk.Frame(self.root, bg=COLORS['bg_main'])
        main_container.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        # 配置主容器的行列权重
        main_container.grid_rowconfigure(0, weight=0)  # header
        main_container.grid_rowconfigure(1, weight=0)  # search
        main_container.grid_rowconfigure(2, weight=2)  # results (更多空间)
        main_container.grid_rowconfigure(3, weight=1)  # downloaded (较少空间)
        main_container.grid_rowconfigure(4, weight=0)  # footer
        main_container.grid_columnconfigure(0, weight=1)

        self.create_header(main_container, row=0)
        self.create_search_section(main_container, row=1)
        self.create_results_section(main_container, row=2)
        self.create_downloaded_section(main_container, row=3)
        self.create_footer(main_container, row=4)

    def create_header(self, parent, row):
        header = tk.Frame(parent, bg=COLORS['wood_dark'], padx=3, pady=3)
        header.grid(row=row, column=0, sticky='ew', pady=(0, 10))

        inner = tk.Frame(header, bg=COLORS['wood_medium'], padx=15, pady=8)
        inner.pack(fill=tk.X)

        tk.Label(inner, text="♪ RockWave 音乐下载器",
                 bg=COLORS['wood_medium'],
                 fg=COLORS['bg_input'],
                 font=('Georgia', 14, 'bold')).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="▷ 就绪")
        tk.Label(inner, textvariable=self.status_var,
                 bg=COLORS['wood_medium'],
                 fg=COLORS['wood_light'],
                 font=FONTS['small']).pack(side=tk.RIGHT)

    def create_search_section(self, parent, row):
        frame = tk.Frame(parent, bg=COLORS['bg_panel'], padx=8, pady=6)
        frame.grid(row=row, column=0, sticky='ew', pady=(0, 5))

        tk.Label(frame, text="关键词:",
                 bg=COLORS['bg_panel'],
                 fg=COLORS['text'],
                 font=FONTS['body']).pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(frame,
                              textvariable=self.search_var,
                              font=FONTS['body'],
                              bg=COLORS['bg_input'],
                              fg=COLORS['text'],
                              insertbackground=COLORS['text'],
                              bd=2,
                              relief=tk.SUNKEN)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        self.search_entry.bind('<Return>', lambda e: self.auto_search())

        self.search_btn = tk.Button(frame,
                                 text="[ 搜索 ]",
                                 font=FONTS['body'],
                                 bg=COLORS['wood_dark'],
                                 fg=COLORS['wood_light'],
                                 relief=tk.RAISED,
                                 bd=2,
                                 padx=8,
                                 pady=2,
                                 command=self.auto_search)
        self.search_btn.pack(side=tk.LEFT)

    def create_results_section(self, parent, row):
        frame = tk.Frame(parent, bg=COLORS['wood_dark'], padx=2, pady=2)
        frame.grid(row=row, column=0, sticky='nsew', pady=(0, 5))

        inner = tk.Frame(frame, bg=COLORS['bg_panel'], padx=8, pady=6)
        inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(inner, text="┌─ 搜索结果 | 双击下载 ─┐",
                 bg=COLORS['bg_panel'],
                 fg=COLORS['wood_dark'],
                 font=FONTS['mono']).pack(anchor=tk.W, pady=(0, 5))

        listbox_frame = tk.Frame(inner, bg=COLORS['wood_dark'], bd=2, relief=tk.SUNKEN)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.songs_listbox = tk.Listbox(listbox_frame,
                                   font=FONTS['mono'],
                                   bg=COLORS['bg_input'],
                                   fg=COLORS['text'],
                                   selectbackground=COLORS['wood_light'],
                                   relief=tk.FLAT,
                                   bd=0,
                                   highlightthickness=0,
                                   height=8)
        self.songs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.songs_listbox.bind('<Double-Button-1>', lambda e: self.download_selected())

        scrollbar = tk.Scrollbar(listbox_frame, command=self.songs_listbox.yview)
        self.songs_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 分页按钮
        btn_frame = tk.Frame(inner, bg=COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        self.download_btn = tk.Button(btn_frame, text="[ 下载所选 ]",
                                font=FONTS['body'], bg=COLORS['wood_dark'],
                                fg=COLORS['wood_light'], padx=8, pady=2,
                                command=self.download_selected)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.prev_btn = tk.Button(btn_frame, text="[ 上一页 ]",
                font=FONTS['body'], bg=COLORS['wood_dark'],
                fg=COLORS['wood_light'], padx=8, pady=2,
                command=self.prev_page)
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.page_label = tk.Label(btn_frame, text="第 1/1 页",
                font=FONTS['mono'], bg=COLORS['bg_panel'], fg=COLORS['brass'])
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(btn_frame, text="[ 下一页 ]",
                font=FONTS['body'], bg=COLORS['wood_dark'],
                fg=COLORS['wood_light'], padx=8, pady=2,
                command=self.next_page)
        self.next_btn.pack(side=tk.LEFT)

        self.progress_var = tk.StringVar(value="")
        tk.Label(btn_frame, textvariable=self.progress_var,
                 font=FONTS['small'], bg=COLORS['bg_panel'],
                 fg=COLORS['brass']).pack(side=tk.RIGHT)

    def create_downloaded_section(self, parent, row):
        frame = tk.Frame(parent, bg=COLORS['wood_dark'], padx=2, pady=2)
        frame.grid(row=row, column=0, sticky='nsew', pady=(0, 5))

        inner = tk.Frame(frame, bg=COLORS['bg_panel'], padx=8, pady=6)
        inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(inner, text="┌─ 已下载歌曲 ─┐",
                 bg=COLORS['bg_panel'],
                 fg=COLORS['wood_dark'],
                 font=FONTS['mono']).pack(anchor=tk.W, pady=(0, 5))

        # 水平分割：左侧歌曲列表，右侧歌词
        pane = tk.PanedWindow(inner, bg=COLORS['bg_panel'], orient=tk.HORIZONTAL, sashwidth=4)
        pane.pack(fill=tk.BOTH, expand=True)

        # 左侧：歌曲列表
        left_frame = tk.Frame(pane, bg=COLORS['wood_dark'])
        pane.add(left_frame, minsize=200)

        listbox_frame = tk.Frame(left_frame, bg=COLORS['wood_dark'], bd=1, relief=tk.SUNKEN)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.downloaded_listbox = tk.Listbox(listbox_frame,
                                     font=FONTS['mono'],
                                     bg=COLORS['bg_input'],
                                     fg=COLORS['text'],
                                     selectbackground=COLORS['wood_light'],
                                     relief=tk.FLAT,
                                     bd=0,
                                     highlightthickness=0,
                                     exportselection=False)
        self.downloaded_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.downloaded_listbox.bind('<<ListboxSelect>>', self.on_downloaded_select)
        self.downloaded_listbox.bind('<Double-Button-1>', self.on_downloaded_double_click)

        scrollbar = tk.Scrollbar(listbox_frame, command=self.downloaded_listbox.yview)
        self.downloaded_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧：歌词
        right_frame = tk.Frame(pane, bg=COLORS['wood_dark'])
        pane.add(right_frame, minsize=150)

        tk.Label(right_frame, text="♪ 歌词",
               bg=COLORS['wood_dark'], fg=COLORS['wood_light'],
               font=FONTS['small']).pack(anchor=tk.W, padx=3, pady=2)

        lyrics_frame = tk.Frame(right_frame, bg=COLORS['wood_dark'], bd=1, relief=tk.SUNKEN)
        lyrics_frame.pack(fill=tk.BOTH, expand=True)

        self.local_lyrics_listbox = tk.Listbox(lyrics_frame,
                                   font=FONTS['mono'],
                                   bg=COLORS['bg_input'],
                                   fg=COLORS['text'],
                                   relief=tk.FLAT,
                                   bd=0,
                                   highlightthickness=0,
                                   exportselection=False)
        self.local_lyrics_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lyrics_scroll = tk.Scrollbar(lyrics_frame, command=self.local_lyrics_listbox.yview)
        self.local_lyrics_listbox.configure(yscrollcommand=lyrics_scroll.set)
        lyrics_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部按钮
        btn_frame = tk.Frame(inner, bg=COLORS['bg_panel'])
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(btn_frame, text="[ 刷新 ]",
                font=FONTS['body'], bg=COLORS['wood_dark'],
                fg=COLORS['wood_light'], padx=6, pady=2,
                command=self.refresh_downloaded_list).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(btn_frame, text="[ 打开目录 ]",
                font=FONTS['body'], bg=COLORS['wood_dark'],
                fg=COLORS['wood_light'], padx=6, pady=2,
                command=self.open_download_directory).pack(side=tk.LEFT, padx=(0, 10))

        self.local_play_btn = tk.Button(btn_frame,
                text="[ ▶ 播放 ]",
                font=FONTS['body'], bg=COLORS['wood_dark'],
                fg=COLORS['wood_light'], padx=8, pady=2,
                command=self.play_or_stop)
        self.local_play_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.local_play_btn.configure(state='disabled')

        self.time_label = tk.Label(btn_frame,
                text="00:00 / 00:00",
                font=FONTS['mono'], bg=COLORS['bg_panel'], fg=COLORS['brass'])
        self.time_label.pack(side=tk.LEFT, padx=(5, 0))

    def create_footer(self, parent, row):
        frame = tk.Frame(parent, bg=COLORS['wood_dark'], padx=3, pady=3)
        frame.grid(row=row, column=0, sticky='ew')

        inner = tk.Frame(frame, bg=COLORS['wood_medium'], padx=10, pady=4)
        inner.pack(fill=tk.X)

        tk.Label(inner, text=f"下载目录: {self.download_dir}",
               bg=COLORS['wood_medium'], fg=COLORS['wood_light'],
               font=FONTS['small']).pack(side=tk.LEFT)

        tk.Button(inner, text="[ 更改目录 ]",
                font=FONTS['small'], bg=COLORS['wood_dark'],
                fg=COLORS['wood_light'], padx=6, pady=1,
                command=self.browse_directory).pack(side=tk.RIGHT)

    # ==================== 搜索功能 ====================
    
    def auto_search(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("提示", "请输入搜索关键词")
            return

        if not PLAYWRIGHT_AVAILABLE:
            messagebox.showerror("错误", "请先安装 playwright")
            return

        self.current_query = query
        self.current_page = 1

        self.status_var.set(f"▷ 正在搜索: {query}...")
        self.search_btn.configure(state='disabled')
        self.songs_listbox.delete(0, tk.END)
        self.songs_listbox.insert(tk.END, "  ▌ 正在搜索...")

        threading.Thread(target=self._search_thread, args=(query, 1), daemon=True).start()

    def _search_thread(self, query, page_num):
        browser = None
        try:
            print(f"DEBUG: 开始搜索 '{query}', 页码 {page_num}")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                page = browser.new_page()
                page.set_default_timeout(30000)  # 30秒超时

                encoded_query = urllib.parse.quote(query)
                if page_num == 1:
                    search_url = f"https://jzmp3.com/so/{encoded_query}"
                else:
                    search_url = f"https://jzmp3.com/so/{encoded_query}/{page_num}/"

                print(f"DEBUG: 访问 URL: {search_url}")
                
                response = page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
                print(f"DEBUG: 页面响应状态: {response.status if response else 'None'}")
                
                # 等待页面加载
                time.sleep(3)
                
                # 尝试等待搜索结果出现
                try:
                    page.wait_for_selector('.result-info', timeout=5000)
                except:
                    print("DEBUG: 等待 .result-info 超时，继续解析")

                items = page.query_selector_all('.result-info')
                print(f"DEBUG: 找到 {len(items)} 个搜索结果")
                
                songs = []

                for item in items:
                    title_el = item.query_selector('.result-title')
                    artist_el = item.query_selector('.result-artist')
                    album_el = item.query_selector('.result-album')

                    title = title_el.inner_text().strip() if title_el else ""
                    artist = artist_el.inner_text().strip() if artist_el else ""
                    album = album_el.inner_text().strip() if album_el else ""

                    if title:
                        songs.append({'title': title, 'artist': artist, 'album': album})

                total_pages = 1
                try:
                    total_el = page.query_selector('#total-pages')
                    if total_el:
                        total_text = total_el.inner_text()
                        if total_text.isdigit():
                            total_pages = int(total_text)
                except:
                    pass
                if total_pages < 1:
                    total_pages = 1

                print(f"DEBUG: 搜索完成，共 {len(songs)} 首歌曲")
                browser.close()
                browser = None
                self.root.after(0, lambda: self._search_complete(songs, query, total_pages))

        except Exception as err:
            error_msg = str(err)
            print(f"DEBUG: 搜索错误: {error_msg}")
            if browser:
                try:
                    browser.close()
                except:
                    pass
            self.root.after(0, lambda: self._search_error(error_msg))

    def _search_complete(self, songs, query, total_pages=1):
        self.current_songs = songs
        self.total_pages = total_pages
        self.songs_listbox.delete(0, tk.END)

        if not songs:
            self.songs_listbox.insert(tk.END, "  ✘ 未找到歌曲")
            self.status_var.set(f"✘ 未找到: {query}")
        else:
            for i, song in enumerate(songs):
                display = f"  ♪ [{i+1:02d}] {song['title']} - {song['artist']}"
                self.songs_listbox.insert(tk.END, display)
            self.status_var.set(f"✓ 找到 {len(songs)} 首")

        self.search_btn.configure(state='normal')
        self.update_page_buttons()

    def update_page_buttons(self):
        self.page_label.configure(text=f"第 {self.current_page}/{self.total_pages} 页")
        self.prev_btn.configure(state='normal' if self.current_page > 1 else 'disabled')
        self.next_btn.configure(state='normal' if self.current_page < self.total_pages else 'disabled')

    def prev_page(self):
        if self.current_page > 1 and self.current_query:
            self.current_page -= 1
            self.search_btn.configure(state='disabled')
            self.songs_listbox.delete(0, tk.END)
            self.songs_listbox.insert(tk.END, "  ▌ 加载中...")
            threading.Thread(target=self._search_thread, args=(self.current_query, self.current_page), daemon=True).start()

    def next_page(self):
        if self.current_page < self.total_pages and self.current_query:
            self.current_page += 1
            self.search_btn.configure(state='disabled')
            self.songs_listbox.delete(0, tk.END)
            self.songs_listbox.insert(tk.END, "  ▌ 加载中...")
            threading.Thread(target=self._search_thread, args=(self.current_query, self.current_page), daemon=True).start()

    def _search_error(self, error):
        self.songs_listbox.delete(0, tk.END)
        self.songs_listbox.insert(tk.END, f"  ✘ 搜索出错: {error}")
        self.status_var.set("✘ 搜索失败")
        self.search_btn.configure(state='normal')

    # ==================== 下载功能 ====================

    def download_selected(self):
        selection = self.songs_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一首歌曲")
            return

        index = selection[0]
        if index >= len(self.current_songs):
            return

        song = self.current_songs[index]
        self.auto_download_song(song)

    def auto_download_song(self, song):
        title = song['title']
        artist = song['artist']

        if not PLAYWRIGHT_AVAILABLE:
            messagebox.showerror("错误", "playwright 未安装")
            return

        self.status_var.set(f"▷ 正在获取: {title}")
        self.progress_var.set("▷ 打开播放页...")
        self.download_btn.configure(state='disabled')

        threading.Thread(target=self._download_thread, args=(song,), daemon=True).start()

    def _download_thread(self, song):
        title = song['title']
        artist = song['artist']

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                self.root.after(0, lambda: self.progress_var.set("▷ 搜索..."))

                encoded_query = urllib.parse.quote(f"{title} {artist}")
                page.goto(f"https://jzmp3.com/so/{encoded_query}", timeout=20000)
                time.sleep(2)

                self.root.after(0, lambda: self.progress_var.set("▷ 进入播放页..."))

                play_icons = page.query_selector_all('.play-icon')
                if play_icons:
                    play_icons[0].click()
                    time.sleep(2)

                self.root.after(0, lambda: self.progress_var.set("▷ 提取链接..."))

                html = page.content()

                # 提取音频链接
                audio_patterns = [
                    r'src=["\'](https?://[^\s"\']+\.(?:aac|mp3|flac|wav))["\']',
                    r'(?:src|url)["\']?\s*[:=]\s*["\'](https?://[^\s"\']+\.(?:aac|mp3|flac|wav))["\']',
                    r'https?://[^\s"\']+\.(?:aac|mp3|flac|wav)(?:\?[^\s"\']*)?',
                ]

                audio_urls = []
                for pattern in audio_patterns:
                    matches = re.findall(pattern, html, re.I)
                    if matches:
                        audio_urls.extend(matches)

                audio_url = None
                preferred_domains = ['kuwo', 'lv-sycdn', 'cdn', 'yinyue', 'music', 'audio']
                for url in audio_urls:
                    if any(domain in url.lower() for domain in preferred_domains):
                        audio_url = url
                        break
                if not audio_url and audio_urls:
                    audio_url = audio_urls[0]

                # 提取歌词 - 从播放页面获取
                self.root.after(0, lambda: self.progress_var.set("▷ 提取歌词..."))
                print(f"DEBUG: 开始提取歌词...")
                
                lyrics = []
                lrc_filename = None
                
                # 格式1: data-time="秒数">歌词内容 (网站的主要格式)
                lyric_matches = re.findall(r'class="lyric-line"\s+data-time="(\d+)"[^>]*>([^<]+)<', html)
                print(f"DEBUG: 找到 {len(lyric_matches)} 行歌词")
                
                for time_sec, text in lyric_matches:
                    if text.strip():
                        lyrics.append((float(time_sec), text.strip()))

                # 格式2: [mm:ss.xx] 传统 LRC 格式 (备用)
                if not lyrics:
                    lrc_lines = re.findall(r'\[(\d{2}):(\d{2})\.(\d{2,3})\]([^\[\n]*)', html)
                    print(f"DEBUG: LRC格式找到 {len(lrc_lines)} 行歌词")
                    for mins, sec, ms, text in lrc_lines:
                        if text.strip():
                            time_seconds = int(mins) * 60 + int(sec) + int(ms) / (1000 if len(ms) == 3 else 100)
                            lyrics.append((time_seconds, text.strip()))

                # 保存歌词文件
                if lyrics:
                    lrc_filename = f"{artist} - {title}.lrc" if artist else f"{title}.lrc"
                    lrc_filename = "".join(c for c in lrc_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                    lrc_filepath = os.path.join(self.download_dir, lrc_filename)
                    lrc_content = '\n'.join([f"[{int(l[0]//60):02d}:{l[0]%60:05.2f}]{l[1]}" for l in lyrics])
                    with open(lrc_filepath, 'w', encoding='utf-8') as f:
                        f.write(lrc_content)
                    print(f"DEBUG: 歌词已保存: {lrc_filename}, 共 {len(lyrics)} 行")
                else:
                    print("DEBUG: 未找到歌词内容")

                browser.close()

                if not audio_url:
                    self.root.after(0, lambda: self._download_error("未找到音频链接"))
                    return

                self.root.after(0, lambda: self.progress_var.set(f"▷ 下载中..."))

                ext = 'mp3'
                if '.aac' in audio_url:
                    ext = 'aac'
                elif '.flac' in audio_url:
                    ext = 'flac'
                elif '.wav' in audio_url:
                    ext = 'wav'

                filename = f"{artist} - {title}.{ext}" if artist else f"{title}.{ext}"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                filepath = os.path.join(self.download_dir, filename)

                result = subprocess.run(
                    ['curl', '-L', '-o', filepath, '--connect-timeout', '10',
                     '--max-time', '120', audio_url],
                    capture_output=True, text=True, timeout=130
                )

                if result.returncode == 0 and os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    if file_size > 1000:
                        self.root.after(0, lambda: self._download_success(
                            filename, file_size, title, artist, audio_url, lrc_filename))
                    else:
                        self.root.after(0, lambda: self._download_error("文件太小"))
                else:
                    self.root.after(0, lambda: self._download_error("下载失败"))

        except Exception as e:
            self.root.after(0, lambda: self._download_error(str(e)))

    def _download_success(self, filename, file_size, title, artist, url, lrc_filename=None):
        self.status_var.set(f"✓ 下载成功: {filename}")
        self.progress_var.set("")

        self.downloaded[filename] = {
            'url': url,
            'title': title,
            'artist': artist,
            'size': file_size,
            'timestamp': time.time()
        }
        self.save_downloaded()
        self.refresh_downloaded_list()
        self.download_btn.configure(state='normal')

        lrc_info = f"\n歌词: {lrc_filename}" if lrc_filename else ""
        messagebox.showinfo("下载成功", f"✓ 下载完成!\n\n{filename}\n大小: {file_size/1024/1024:.2f} MB{lrc_info}")

    def _download_error(self, error):
        self.status_var.set(f"✘ 下载失败: {error}")
        self.progress_var.set("")
        self.download_btn.configure(state='normal')
        messagebox.showerror("下载失败", str(error))

    # ==================== 播放功能 ====================

    def refresh_downloaded_list(self):
        self.downloaded_listbox.delete(0, tk.END)
        self.file_list = []

        try:
            if os.path.exists(self.download_dir):
                for filename in sorted(os.listdir(self.download_dir)):
                    if filename.endswith(('.mp3', '.aac', '.flac', '.wav')):
                        filepath = os.path.join(self.download_dir, filename)
                        size_mb = os.path.getsize(filepath) / 1024 / 1024
                        self.file_list.append(filename)
                        self.downloaded_listbox.insert(tk.END, f"  ♪ {filename} ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"刷新列表失败: {e}")

        if not self.file_list:
            self.downloaded_listbox.insert(tk.END, "  ○ 暂无下载记录")

    def on_downloaded_select(self, event):
        selection = self.downloaded_listbox.curselection()
        if not selection:
            self.local_play_btn.configure(text="[ ▶ 播放 ]", state='disabled')
            self.time_label.configure(text="00:00 / 00:00")
            self.selected_local_file = None
            self.local_lyrics_listbox.delete(0, tk.END)
            return

        index = selection[0]
        if 0 <= index < len(self.file_list):
            filename = self.file_list[index]
            self.selected_local_file = os.path.join(self.download_dir, filename)
            
            if self.playing:
                self.local_play_btn.configure(text="[ ■ 停止 ]", state='normal')
            else:
                self.local_play_btn.configure(text="[ ▶ 播放 ]", state='normal')
        else:
            self.local_play_btn.configure(text="[ ▶ 播放 ]", state='disabled')
            self.time_label.configure(text="00:00 / 00:00")
            self.selected_local_file = None
            return

        self.load_lyrics(filename)

    def load_lyrics(self, filename):
        """加载并显示歌词"""
        base_name = os.path.splitext(filename)[0]
        lrc_filename = base_name + '.lrc'
        lrc_filepath = os.path.join(self.download_dir, lrc_filename)
        
        self.local_lyrics_listbox.delete(0, tk.END)
        
        if os.path.exists(lrc_filepath):
            try:
                with open(lrc_filepath, 'r', encoding='utf-8') as f:
                    lrc_content = f.read()
                for line in lrc_content.split('\n'):
                    match = re.match(r'\[\d+:\d+\.\d+\](.+)', line)
                    if match:
                        text = match.group(1).strip()
                        if text:
                            self.local_lyrics_listbox.insert(tk.END, f"  {text}")
                    elif line.strip() and not line.startswith('['):
                        self.local_lyrics_listbox.insert(tk.END, line.strip())
            except Exception as e:
                print(f"加载歌词失败: {e}")
                self.local_lyrics_listbox.insert(tk.END, "  ○ 歌词加载失败")
        else:
            self.local_lyrics_listbox.insert(tk.END, "  ○ 未找到歌词文件")

    def on_downloaded_double_click(self, event):
        if hasattr(self, '_last_double_click') and time.time() - self._last_double_click < 0.5:
            return
        self._last_double_click = time.time()
        
        self.on_downloaded_select(event)
        if hasattr(self, 'selected_local_file') and self.selected_local_file:
            self.play_or_stop()

    def play_or_stop(self):
        """播放或停止 - 简化版本，避免死锁"""
        if self.playing:
            # 停止播放 - 不使用锁
            self._force_stop_playback()
            self.local_play_btn.configure(text="[ ▶ 播放 ]", state='normal')
            self.time_label.configure(text="00:00 / 00:00")
            self.status_var.set("▷ 已停止")
            return

        # 开始播放
        if not hasattr(self, 'selected_local_file') or not self.selected_local_file:
            return

        if not os.path.exists(self.selected_local_file):
            messagebox.showerror("错误", "文件不存在")
            return

        self.local_play_btn.configure(text="[ ■ 停止 ]", state='normal')
        self.playing = True
        self.playback_start_time = time.time()
        
        # 根据系统和格式选择播放命令
        if platform.system() == 'Darwin':
            # macOS: ffplay 支持更多格式（包括 M4A/AAC）
            if subprocess.run(['which', 'ffplay'], capture_output=True).returncode == 0:
                cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', self.selected_local_file]
            else:
                cmd = ['afplay', self.selected_local_file]
        elif platform.system() == 'Linux':
            cmd = None
            for player in ['mpg123', 'ffplay', 'aplay']:
                if subprocess.run(['which', player], capture_output=True).returncode == 0:
                    if player == 'ffplay':
                        cmd = ['ffplay', '-nodisp', '-autoexit', self.selected_local_file]
                    elif player == 'mpg123':
                        cmd = ['mpg123', '-q', self.selected_local_file]
                    else:
                        cmd = ['aplay', self.selected_local_file]
                    break
            if not cmd:
                messagebox.showerror("错误", "未找到音频播放器")
                self.playing = False
                return
        else:
            cmd = ['start', '', self.selected_local_file]

        try:
            self.play_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.status_var.set("▷ 正在播放...")
            threading.Thread(target=self._get_duration, daemon=True).start()
            threading.Thread(target=self._wait_playback_end, daemon=True).start()
        except Exception as e:
            self.playing = False
            self.play_process = None
            messagebox.showerror("播放失败", str(e))

    def _force_stop_playback(self):
        """强制停止播放 - 不使用锁"""
        self.playing = False
        if self.play_process:
            try:
                self.play_process.terminate()
                try:
                    self.play_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.play_process.kill()
                    self.play_process.wait(timeout=1)
            except:
                pass
            finally:
                self.play_process = None
        self.playback_start_time = None

    def _wait_playback_end(self):
        """等待播放结束的线程"""
        if self.play_process:
            self.play_process.wait()
        # 播放结束后更新UI
        if self.playing:  # 只有非手动停止才更新
            self.playing = False
            self.play_process = None
            self.playback_start_time = None
            self.root.after(0, self._on_playback_end)

    def _on_playback_end(self):
        self.local_play_btn.configure(text="[ ▶ 播放 ]", state='normal')
        self.time_label.configure(text="00:00 / 00:00")
        self.status_var.set("▷ 播放完成")

    def _get_duration(self):
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', self.selected_local_file],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                self.duration = float(result.stdout.strip())
                tot_min = int(self.duration // 60)
                tot_sec = int(self.duration % 60)
                self.root.after(0, lambda: self.time_label.configure(text=f"00:00 / {tot_min:02d}:{tot_sec:02d}"))
                self.root.after(500, self.update_time_label)
        except:
            self.duration = 0

    def update_time_label(self):
        if not self.playing or not self.play_process:
            return
        
        if self.play_process.poll() is not None:
            return
            
        elapsed = time.time() - self.playback_start_time if self.playback_start_time else 0
        cur_min = int(elapsed // 60)
        cur_sec = int(elapsed % 60)
        tot_min = int(self.duration // 60)
        tot_sec = int(self.duration % 60)
        self.time_label.configure(text=f"{cur_min:02d}:{cur_sec:02d} / {tot_min:02d}:{tot_sec:02d}")
        if self.playing:
            self.root.after(500, self.update_time_label)

    # ==================== 其他功能 ====================

    def open_download_directory(self):
        try:
            subprocess.run(['open', self.download_dir])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {str(e)}")

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.download_dir)
        if directory:
            self.download_dir = directory
            self.downloaded_file = os.path.join(self.download_dir, "downloaded.json")
            self.downloaded = self.load_downloaded()
            self.refresh_downloaded_list()


def main():
    root = tk.Tk()
    app = ROCKWAVEMP3AutoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
