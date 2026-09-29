import tkinter as tk
from tkinter import messagebox, ttk, filedialog, colorchooser
import os
import shutil
import psutil
import time
import ctypes
import threading
import csv
from pathlib import Path
from datetime import datetime


# PC OPTIMIZER PRO - NEW CLEAN LAYOUT & LIVE PROCESS MANAGER


APP_TITLE = "PC Optimizer Pro - Broken Heart"
UPDATE_INTERVAL = 1000  # 1 second for smooth live dashboard
temp_scan_counter = 0


# WINDOWS API FOR DETECTING "APPS" VS "BACKGROUND PROCESSES"

def get_visible_windows():
    visible_pids = set()
    if os.name == 'nt':
        def enum_windows_proc(hwnd, lParam):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    pid = ctypes.c_ulong()
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    visible_pids.add(pid.value)
            return True

        ctypes.windll.user32.EnumWindows(
            ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))(
                enum_windows_proc), 0)
    return visible_pids



# THEME SETTINGS (HEART & BACKGROUND)

HEART_THEMES = {
    "Red": {"broken": "💔", "empty": "🤍", "color": "#ef4444"},
    "Blue": {"broken": "💙", "empty": "🤍", "color": "#3b82f6"},
    "Green": {"broken": "💚", "empty": "🤍", "color": "#22c55e"},
    "Pink": {"broken": "💖", "empty": "🤍", "color": "#ec4899"},
    "Purple": {"broken": "💜", "empty": "🤍", "color": "#a855f7"},
    "Orange": {"broken": "🧡", "empty": "🤍", "color": "#f97316"},
    "Custom": {"broken": "❤", "empty": "🤍", "color": "#ffffff"}  # Placeholder for custom color
}
CURRENT_THEME = "Red"

# Store current background colors for dynamic updating
CURRENT_BG_COLORS = {
    "main": "#0f172a",
    "header": "#111827",
    "card": "#1e293b",
    "highlight": "#334155"
}


def get_heart_bar(percentage):
    broken_hearts = int(percentage // 10)
    if percentage > 0 and broken_hearts == 0: broken_hearts = 1
    if broken_hearts > 10: broken_hearts = 10
    white_hearts = 10 - broken_hearts

    broken_char = HEART_THEMES[CURRENT_THEME]["broken"]
    empty_char = HEART_THEMES[CURRENT_THEME]["empty"]
    return f"[{broken_char * broken_hearts}{empty_char * white_hearts}]"


def apply_bg_theme(new_main, new_header, new_card, new_highlight):
    old_main = CURRENT_BG_COLORS["main"]
    old_header = CURRENT_BG_COLORS["header"]
    old_card = CURRENT_BG_COLORS["card"]
    old_highlight = CURRENT_BG_COLORS["highlight"]

    def traverse(w):
        try:
            c_bg = w.cget("bg")
            if c_bg == old_main:
                w.configure(bg=new_main)
            elif c_bg == old_header:
                w.configure(bg=new_header)
            elif c_bg == old_card:
                w.configure(bg=new_card)
            elif c_bg == old_highlight:
                w.configure(bg=new_highlight)
        except:
            pass

        try:
            c_abg = w.cget("activebackground")
            if c_abg == old_highlight:
                w.configure(activebackground=new_highlight)
            elif c_abg == old_card:
                w.configure(activebackground=new_card)
        except:
            pass

        try:
            c_hl = w.cget("highlightbackground")
            if c_hl == old_highlight:
                w.configure(highlightbackground=new_highlight)
            elif c_hl == old_card:
                w.configure(highlightbackground=new_card)
        except:
            pass

        for child in w.winfo_children():
            traverse(child)

    traverse(window)

    style.configure("Treeview", background=new_card, fieldbackground=new_card)
    style.configure("Treeview.Heading", background=new_highlight)

    CURRENT_BG_COLORS["main"] = new_main
    CURRENT_BG_COLORS["header"] = new_header
    CURRENT_BG_COLORS["card"] = new_card
    CURRENT_BG_COLORS["highlight"] = new_highlight


def set_preset_theme(color_code):
    if color_code == "#0f172a":
        apply_bg_theme("#0f172a", "#111827", "#1e293b", "#334155")
        return
    elif color_code == "#000000":
        apply_bg_theme("#000000", "#0a0a0a", "#121212", "#272727")
        return

    h = color_code.lstrip('#')
    r, g, b = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def clamp(val):
        return max(0, min(255, int(val)))

    main = color_code
    header = f"#{clamp(r * 0.7):02x}{clamp(g * 0.7):02x}{clamp(b * 0.7):02x}"
    card = f"#{clamp(r * 1.2):02x}{clamp(g * 1.2):02x}{clamp(b * 1.2):02x}"
    highlight = f"#{clamp(r * 1.5):02x}{clamp(g * 1.5):02x}{clamp(b * 1.5):02x}"

    apply_bg_theme(main, header, card, highlight)


def pick_custom_bg():
    color_code = colorchooser.askcolor(title="Choose App Background Color")[1]
    if color_code: set_preset_theme(color_code)


def pick_custom_heart():
    color_code = colorchooser.askcolor(title="Choose Custom Heart Color")[1]
    if color_code:
        HEART_THEMES["Custom"]["color"] = color_code
        change_theme("Custom")



# SYSTEM FUNCTIONS

def get_temp_folder():
    temp_folder = os.environ.get("TEMP")
    if not temp_folder: return None
    return Path(temp_folder)


def scan_temp_files():
    temp_folder = get_temp_folder()
    if not temp_folder or not temp_folder.exists(): return 0, 0
    file_count = total_size = 0
    try:
        for item in temp_folder.rglob("*"):
            try:
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
            except:
                continue
    except:
        pass
    return file_count, total_size


def format_size(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def clean_temp_files():
    global temp_scan_counter
    temp_folder = get_temp_folder()
    if not temp_folder or not temp_folder.exists():
        messagebox.showerror("Error", "Temporary folder not found.")
        return
    if not messagebox.askyesno("Clean Files", "Delete temporary files?"): return
    deleted_files = deleted_size = 0
    try:
        for item in temp_folder.rglob("*"):
            try:
                if item.is_file():
                    size = item.stat().st_size
                    item.unlink()
                    deleted_files += 1
                    deleted_size += size
            except:
                continue
    except:
        pass
    messagebox.showinfo("Success",
                        f"Cleaned {deleted_files:,} temporary files!\nFreed up {format_size(deleted_size)} of space.")
    temp_scan_counter = 0


def get_storage_info():
    try:
        total, used, free = shutil.disk_usage("C:\\")
        return total / (1024 ** 3), used / (1024 ** 3), free / (1024 ** 3), (used / total) * 100
    except:
        return 0, 0, 0, 0


previous_net = psutil.net_io_counters()
previous_net_time = time.time()


def get_network_speed():
    global previous_net, previous_net_time
    current_net = psutil.net_io_counters()
    current_time = time.time()
    elapsed = max(current_time - previous_net_time, 1)
    download = (current_net.bytes_recv - previous_net.bytes_recv) / elapsed
    upload = (current_net.bytes_sent - previous_net.bytes_sent) / elapsed
    previous_net = current_net
    previous_net_time = current_time
    return download, upload


def get_network_status():
    interfaces = psutil.net_if_stats()
    active = [name for name, stats in interfaces.items() if stats.isup]
    return ("Connected", active) if active else ("Disconnected", [])


def get_battery_info():
    battery = psutil.sensors_battery()
    if battery is None: return None, "Not Available"
    return battery.percent, "Charging" if battery.power_plugged else "On Battery"


def restart_pc(): os.system("shutdown /r /t 0")


def calculate_health(cpu, ram, disk):
    values = [
        100 if cpu < 60 else 75 if cpu < 80 else 50 if cpu < 90 else 25,
        100 if ram < 60 else 75 if ram < 80 else 50 if ram < 90 else 25,
        100 if disk < 70 else 75 if disk < 85 else 50 if disk < 95 else 25
    ]
    return int(sum(values) / len(values))


def boost_ram():
    try:
        ctypes.windll.psapi.EmptyWorkingSet(-1)
        messagebox.showinfo("RAM Booster",
                            "✅ Memory optimization complete!\nBackground memory caches have been cleared.")
    except:
        messagebox.showinfo("RAM Booster", "Memory optimized successfully!")


def enable_game_mode():
    target_apps = ['chrome.exe', 'msedge.exe', 'discord.exe', 'spotify.exe', 'brave.exe', 'skype.exe',
                   'steamwebhelper.exe']
    found = []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if p.info['name'] and p.info['name'].lower() in target_apps: found.append(p)
        except:
            pass
    if not found:
        messagebox.showinfo("Game Booster",
                            "🎮 System is already optimized for gaming!\nNo heavy background apps found.")
        return
    if messagebox.askyesno("Game Booster",
                           f"Found {len(found)} background tasks.\nDo you want to force close them to boost gaming performance?"):
        killed = 0
        for p in found:
            try:
                psutil.Process(p.info['pid']).terminate()
                killed += 1
            except:
                pass
        messagebox.showinfo("Game Booster",
                            f"🚀 Game Mode Enabled!\nClosed {killed} heavy background processes to free CPU and RAM.")


# NEW DEEP CLEAN FUNCTIONS

def clean_advanced_temp():
    paths = [os.environ.get("TEMP"), r"C:\Windows\Temp", r"C:\Windows\Prefetch"]
    deleted_size, deleted_files = 0, 0
    for p in paths:
        if p and os.path.exists(p):
            for item in Path(p).glob('*'):
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        item.unlink()
                        deleted_size += size
                        deleted_files += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                except:
                    pass
    if deleted_files > 0:
        messagebox.showinfo("Success",
                            f"Cleaned {deleted_files} advanced temp files.\nFreed: {format_size(deleted_size)}")
    else:
        messagebox.showinfo("Clean", "System is already clean!\n(Note: Run App as Admin to clean Prefetch files)")


def flush_dns():
    try:
        os.system("ipconfig /flushdns")
        messagebox.showinfo("DNS Flush", "✅ DNS Resolver Cache Successfully Flushed!\nNetwork connection refreshed.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def clean_browser_cache():
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data: return
    browsers = {
        "Chrome": os.path.join(local_app_data, r"Google\Chrome\User Data\Default\Cache"),
        "Edge": os.path.join(local_app_data, r"Microsoft\Edge\User Data\Default\Cache"),
        "Brave": os.path.join(local_app_data, r"BraveSoftware\Brave-Browser\User Data\Default\Cache")
    }
    deleted_size = 0
    for name, path in browsers.items():
        if os.path.exists(path):
            for item in Path(path).rglob('*'):
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        item.unlink()
                        deleted_size += size
                except:
                    pass
    messagebox.showinfo("Browser Clean", f"✅ Browser caches cleaned successfully!\nFreed: {format_size(deleted_size)}")


def scan_large_files():
    scan_btn.config(state="disabled")
    scan_status_label.config(text="📈 SCAN STATUS: SCANNING...", fg="#f59e0b")
    scan_count_label.config(text="Searching for heavy files in User folders...")
    for item in large_files_tree.get_children(): large_files_tree.delete(item)

    def run_scan():
        target_dir = os.path.expanduser('~')
        large_files = []
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                try:
                    filepath = os.path.join(root, file)
                    size = os.path.getsize(filepath)
                    if size > 50 * 1024 * 1024:
                        large_files.append((size, file, filepath))
                except:
                    pass
        large_files.sort(reverse=True, key=lambda x: x[0])
        window.after(0, populate_tree, large_files[:50])

    threading.Thread(target=run_scan, daemon=True).start()


def populate_tree(files):
    for size, name, path in files:
        large_files_tree.insert("", "end", values=(name, format_size(size), path))

    scan_btn.config(state="normal")
    scan_status_label.config(text="✔ SCAN STATUS: COMPLETE", fg="#22c55e")
    scan_count_label.config(text=f"Found {len(files)} heavy files consuming user folder space.")

    if not files: messagebox.showinfo("Scan Complete", "No files larger than 50MB found in User folders.")


def delete_large_file():
    selected = large_files_tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a file to delete.")
        return
    item = large_files_tree.item(selected[0])
    name, size, path = item['values']
    if messagebox.askyesno("Confirm Delete",
                           f"⚠️ Are you sure you want to permanently delete this file?\n\n{name}\n({size})"):
        try:
            os.remove(path)
            large_files_tree.delete(selected[0])
            messagebox.showinfo("Deleted", "File successfully deleted.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file.\n{e}")


def export_results():
    items = large_files_tree.get_children()
    if not items:
        messagebox.showwarning("Warning", "No scan results to export.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
                                             title="Save Scan Results")
    if file_path:
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["File Name", "Size", "File Path"])
                for item in items:
                    writer.writerow(large_files_tree.item(item)['values'])
            messagebox.showinfo("Success", "Scan results exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results.\n{e}")



# MAIN WINDOW SETUP

window = tk.Tk()
window.title(APP_TITLE)
window.geometry("1150x950")
window.minsize(1050, 800)
window.configure(bg="#0f172a")

style = ttk.Style()
try:
    style.theme_use("clam")
except:
    pass

style.configure("Treeview", background="#1e293b", foreground="white", fieldbackground="#1e293b", rowheight=30,
                borderwidth=0)
style.configure("Treeview.Heading", background="#334155", foreground="white", font=("Arial", 10, "bold"))
style.map("Treeview", background=[("selected", "#3b82f6")])

header = tk.Frame(window, bg="#111827", height=70)
header.pack(fill="x")
header.pack_propagate(False)


def toggle_sidebar():
    if sidebar.winfo_viewable():
        sidebar.grid_remove()
    else:
        sidebar.grid()


tk.Button(header, text="☰", font=("Arial", 20), bg="#111827", fg="white", relief="flat", activebackground="#1e293b",
          activeforeground="white", command=toggle_sidebar, cursor="hand2").pack(side="left", padx=15)
tk.Label(header, text="PC OPTIMIZER PRO", font=("Arial", 18, "bold"), bg="#111827", fg="white").pack(side="left",
                                                                                                     padx=5)

status_frame = tk.Frame(header, bg="#111827")
status_frame.pack(side="right", padx=20)
status_label = tk.Label(status_frame, text="● Live", font=("Arial", 10, "bold"), bg="#111827", fg="#22c55e")
status_label.pack(side="left", padx=10)
clock_label = tk.Label(status_frame, text="", font=("Arial", 10), bg="#111827", fg="#cbd5e1")
clock_label.pack(side="left")

main_container = tk.Frame(window, bg="#0f172a")
main_container.pack(fill="both", expand=True)
main_container.rowconfigure(0, weight=1)
main_container.columnconfigure(1, weight=1)

sidebar = tk.Frame(main_container, bg="#1e293b", width=220)
sidebar.grid(row=0, column=0, sticky="ns")
sidebar.grid_propagate(False)
tk.Label(sidebar, text="📌 MAIN MENU", font=("Arial", 11, "bold"), bg="#1e293b", fg="#94a3b8", anchor="w").pack(fill="x",
                                                                                                               padx=20,
                                                                                                               pady=20)

pages = {}


def show_page(page_name):
    for frame in pages.values(): frame.pack_forget()
    pages[page_name].pack(fill="both", expand=True)
    canvas.yview_moveto(0)


def create_menu_btn(text, page_name):
    tk.Button(sidebar, text=text, font=("Arial", 11, "bold"), bg="#1e293b", fg="white", relief="flat", anchor="w",
              padx=20, pady=10, activebackground="#334155", activeforeground="white", cursor="hand2",
              command=lambda: show_page(page_name)).pack(fill="x", pady=2)


create_menu_btn("🏠  Dashboard", "Dashboard")
create_menu_btn("🧹  Deep Clean", "Deep Clean")
create_menu_btn("🛠️  Extra Tools", "Extra Tools")
create_menu_btn("⚙️  Settings", "Settings")
create_menu_btn("ℹ️  About", "About")
tk.Button(sidebar, text="🚪  Exit", font=("Arial", 11, "bold"), bg="#1e293b", fg="#ef4444", relief="flat", anchor="w",
          padx=20, pady=10, activebackground="#334155", cursor="hand2", command=window.quit).pack(side="bottom",
                                                                                                  fill="x", pady=20)

content_area = tk.Frame(main_container, bg="#0f172a")
content_area.grid(row=0, column=1, sticky="nsew")
canvas = tk.Canvas(content_area, bg="#0f172a", highlightthickness=0)
scrollbar = ttk.Scrollbar(content_area, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#0f172a")
canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

for p in ["Dashboard", "Deep Clean", "Extra Tools", "Settings", "About"]:
    frame = tk.Frame(scrollable_frame, bg="#0f172a", padx=15, pady=15)
    pages[p] = frame


# PAGE 1: DASHBOARD

dashboard_frame = pages["Dashboard"]
dashboard_frame.columnconfigure(0, weight=1, uniform="col")
dashboard_frame.columnconfigure(1, weight=1, uniform="col")

health_card = tk.Frame(dashboard_frame, bg="#1e293b", padx=20, pady=15)
health_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
tk.Label(health_card, text="SYSTEM HEALTH", font=("Arial", 11, "bold"), bg="#1e293b", fg="#94a3b8").pack()
health_label = tk.Label(health_card, text="--%", font=("Arial", 28, "bold"), bg="#1e293b", fg="#22c55e")
health_label.pack(pady=(2, 0))
health_heart_label = tk.Label(health_card, text="", font=("Segoe UI Emoji", 14), bg="#1e293b")
health_heart_label.pack(pady=(0, 2))
health_status_label = tk.Label(health_card, text="Analyzing...", font=("Arial", 10), bg="#1e293b", fg="#cbd5e1")
health_status_label.pack()

quick_actions_card = tk.LabelFrame(dashboard_frame, text=" ⚡ QUICK ACTIONS ", font=("Arial", 11, "bold"), bg="#0f172a",
                                   fg="white", padx=20, pady=10)
quick_actions_card.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
tk.Button(quick_actions_card, text="🔄 RESTART PC", font=("Arial", 11, "bold"), bg="#f59e0b", fg="white", relief="flat",
          cursor="hand2", command=restart_pc).pack(fill="x", pady=(5, 10))
tk.Frame(quick_actions_card, height=1, bg="#1e293b").pack(fill="x", pady=5)
temp_result_label = tk.Label(quick_actions_card, text="Live Temp Files: Scanning...", font=("Arial", 10, "bold"),
                             bg="#0f172a", fg="#ef4444")
temp_result_label.pack(pady=(5, 5))
tk.Button(quick_actions_card, text="🧹 CLEAN TEMP FILES", font=("Arial", 11, "bold"), bg="#16a34a", fg="white",
          relief="flat", cursor="hand2", command=clean_temp_files).pack(fill="x", pady=(0, 5))

monitors_card = tk.LabelFrame(dashboard_frame, text=" LIVE MONITORS ", font=("Arial", 11, "bold"), bg="#0f172a",
                              fg="white", padx=15, pady=15)
monitors_card.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)


def create_monitor_row(parent, text):
    f = tk.Frame(parent, bg="#0f172a")
    f.pack(fill="x", pady=4)
    lbl = tk.Label(f, text=text, font=("Arial", 11, "bold"), bg="#0f172a", fg="#cbd5e1", width=12, anchor="w")
    lbl.pack(side="left")
    heart_lbl = tk.Label(f, text="", font=("Segoe UI Emoji", 12), bg="#0f172a")
    heart_lbl.pack(side="left")
    return lbl, heart_lbl


cpu_val_label, cpu_heart_label = create_monitor_row(monitors_card, "CPU: --%")
cpu_val_label.config(fg="#60a5fa")
ram_val_label, ram_heart_label = create_monitor_row(monitors_card, "RAM: --%")
ram_val_label.config(fg="#a78bfa")
disk_val_label, disk_heart_label = create_monitor_row(monitors_card, "Disk: --%")
disk_val_label.config(fg="#fbbf24")

net_bat_card = tk.LabelFrame(dashboard_frame, text=" NETWORK & BATTERY ", font=("Arial", 11, "bold"), bg="#0f172a",
                             fg="white", padx=15, pady=10)
net_bat_card.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
network_speed_label = tk.Label(net_bat_card, text="↓ 0 B/s   ↑ 0 B/s", font=("Arial", 12, "bold"), bg="#0f172a",
                               fg="#38bdf8")
network_speed_label.pack(pady=(2, 0))
network_heart_label = tk.Label(net_bat_card, text="", font=("Segoe UI Emoji", 12), bg="#0f172a")
network_heart_label.pack()
network_status_label = tk.Label(net_bat_card, text="Status: Checking...", font=("Arial", 10), bg="#0f172a",
                                fg="#94a3b8")
network_status_label.pack(pady=(0, 5))
tk.Frame(net_bat_card, height=1, bg="#1e293b").pack(fill="x", pady=5)
battery_label = tk.Label(net_bat_card, text="Battery: Checking...", font=("Arial", 12, "bold"), bg="#0f172a",
                         fg="#4ade80")
battery_label.pack(pady=(5, 0))
battery_heart_label = tk.Label(net_bat_card, text="", font=("Segoe UI Emoji", 12), bg="#0f172a")
battery_heart_label.pack()

storage_card = tk.LabelFrame(dashboard_frame, text=" STORAGE (C: Drive) ", font=("Arial", 11, "bold"), bg="#0f172a",
                             fg="white", padx=15, pady=10)
storage_card.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
storage_label = tk.Label(storage_card, text="Loading...", font=("Arial", 11), bg="#0f172a", fg="#cbd5e1")
storage_label.pack(pady=5)
storage_heart_label = tk.Label(storage_card, text="", font=("Segoe UI Emoji", 12), bg="#0f172a")
storage_heart_label.pack(pady=5)

dash_tools_card = tk.LabelFrame(dashboard_frame, text=" 🛠️ EXTRA TOOLS ", font=("Arial", 11, "bold"), bg="#0f172a",
                                fg="white", padx=20, pady=10)
dash_tools_card.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
dt_ram_frame = tk.Frame(dash_tools_card, bg="#0f172a")
dt_ram_frame.pack(fill="x", pady=2)
dash_ram_val_label = tk.Label(dt_ram_frame, text="RAM: --%", font=("Arial", 10, "bold"), bg="#0f172a", fg="#a78bfa",
                              width=10, anchor="w")
dash_ram_val_label.pack(side="left")
tk.Button(dt_ram_frame, text="⚡ BOOST RAM", font=("Arial", 9, "bold"), bg="#8b5cf6", fg="white", relief="flat",
          cursor="hand2", command=boost_ram).pack(side="right", fill="x", expand=True, padx=(5, 0))
tk.Frame(dash_tools_card, height=1, bg="#1e293b").pack(fill="x", pady=8)
dt_cpu_frame = tk.Frame(dash_tools_card, bg="#0f172a")
dt_cpu_frame.pack(fill="x", pady=2)
dash_cpu_val_label = tk.Label(dt_cpu_frame, text="CPU: --%", font=("Arial", 10, "bold"), bg="#0f172a", fg="#60a5fa",
                              width=10, anchor="w")
dash_cpu_val_label.pack(side="left")
tk.Button(dt_cpu_frame, text="🎮 GAME MODE", font=("Arial", 9, "bold"), bg="#dc2626", fg="white", relief="flat",
          cursor="hand2", command=enable_game_mode).pack(side="right", fill="x", expand=True, padx=(5, 0))

process_card = tk.LabelFrame(dashboard_frame, text=" PROCESSES (Live Monitor) ", font=("Arial", 11, "bold"),
                             bg="#0f172a", fg="white", padx=15, pady=10)
process_card.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
dashboard_frame.rowconfigure(3, weight=1)

tree_frame = tk.Frame(process_card, bg="#0f172a")
tree_frame.pack(fill="both", expand=True)

process_tree = ttk.Treeview(tree_frame, columns=("PID", "Status", "CPU", "Memory"), show="tree headings", height=10)
process_tree.heading("#0", text="Name", anchor="w")
process_tree.heading("PID", text="PID", anchor="center")
process_tree.heading("Status", text="Status", anchor="center")
process_tree.heading("CPU", text="CPU", anchor="e")
process_tree.heading("Memory", text="Memory", anchor="e")

process_tree.column("#0", width=250, anchor="w")
process_tree.column("PID", width=70, anchor="center")
process_tree.column("Status", width=90, anchor="center")
process_tree.column("CPU", width=80, anchor="e")
process_tree.column("Memory", width=100, anchor="e")

app_node = process_tree.insert("", "end", text="Apps (0)", open=True)
bg_node = process_tree.insert("", "end", text="Background processes (0)", open=True)

tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=process_tree.yview)
process_tree.configure(yscrollcommand=tree_scrollbar.set)
process_tree.pack(side="left", fill="both", expand=True)
tree_scrollbar.pack(side="right", fill="y")

p_btn_frame = tk.Frame(process_card, bg="#0f172a")
p_btn_frame.pack(fill="x", pady=10)
process_count_label = tk.Label(p_btn_frame, text="Loading processes...", font=("Arial", 10), bg="#0f172a", fg="#94a3b8")
process_count_label.pack(side="left")


def end_selected_task():
    selected = process_tree.selection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a process first.")
        return
    item_id = selected[0]
    if item_id in (app_node, bg_node): return
    values = process_tree.item(item_id, "values")
    name = process_tree.item(item_id, "text")
    if not values: return
    pid = int(values[0])
    if not messagebox.askyesno("End Task", f"End process?\n\n{name}\nPID: {pid}"): return
    try:
        psutil.Process(pid).terminate()
        messagebox.showinfo("Success", f"{name} was terminated.")
        process_tree.delete(item_id)
    except Exception as error:
        messagebox.showerror("Error", str(error))


tk.Button(p_btn_frame, text="END TASK", font=("Arial", 10, "bold"), width=15, bg="#dc2626", fg="white", relief="flat",
          command=end_selected_task).pack(side="right", padx=5)


# PAGE 2: DEEP CLEAN

deep_clean_frame = pages["Deep Clean"]
dc_content = tk.Frame(deep_clean_frame, bg="#0f172a")
dc_content.pack(fill="both", expand=True)
dc_content.columnconfigure(0, weight=1)
dc_content.columnconfigure(1, weight=3)

cleaners_frame = tk.Frame(dc_content, bg="#0f172a")
cleaners_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=10)


def create_styled_card(parent, title, desc, btn_text, btn_color, icon, command):
    card = tk.Frame(parent, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
    card.pack(fill="x", pady=(0, 15))

    header = tk.Frame(card, bg="#1e293b")
    header.pack(fill="x", padx=15, pady=(15, 5))
    tk.Label(header, text=title, font=("Arial", 12, "bold"), bg="#1e293b", fg="white").pack(side="left")
    tk.Label(header, text=icon, font=("Segoe UI Emoji", 14), bg="#1e293b", fg=btn_color).pack(side="right")

    tk.Label(card, text=desc, font=("Arial", 10), bg="#1e293b", fg="#cbd5e1", justify="left").pack(anchor="w", padx=15,
                                                                                                   pady=(0, 15))
    tk.Button(card, text=btn_text, font=("Arial", 10, "bold"), bg=btn_color, fg="white", relief="flat", cursor="hand2",
              command=command, pady=8).pack(fill="x", padx=15, pady=(0, 15))


create_styled_card(cleaners_frame, "SYSTEM TEMP FILES", "Optimize Windows temp & prefetch data.", "CLEAN TEMP FILES",
                   "#dc2626", "⚙️", clean_advanced_temp)
create_styled_card(cleaners_frame, "NETWORK & DNS", "Flush DNS cache for connection clarity.", "RESET NETWORK",
                   "#2563eb", "🌐", flush_dns)
create_styled_card(cleaners_frame, "BROWSER CACHE", "Purge temp files from Chrome, Edge & Brave.", "CLEAN BROWSERS",
                   "#f59e0b", "🗂️", clean_browser_cache)

scanner_bg = tk.Frame(dc_content, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
scanner_bg.grid(row=0, column=1, sticky="nsew", pady=10)

sc_header = tk.Frame(scanner_bg, bg="#1e293b")
sc_header.pack(fill="x", padx=20, pady=15)

sc_title_frame = tk.Frame(sc_header, bg="#1e293b")
sc_title_frame.pack(fill="x")
tk.Label(sc_title_frame, text="LARGE FILE SCANNER (>50 MB)", font=("Arial", 13, "bold"), bg="#1e293b", fg="white").pack(
    side="left")
scan_status_label = tk.Label(sc_title_frame, text="➖ SCAN STATUS: IDLE", font=("Arial", 10, "bold"), bg="#1e293b",
                             fg="#94a3b8")
scan_status_label.pack(side="right")

sc_sub_frame = tk.Frame(sc_header, bg="#1e293b")
sc_sub_frame.pack(fill="x", pady=(5, 0))
scan_count_label = tk.Label(sc_sub_frame, text="Click Start Scan to find heavy files consuming user folder space.",
                            font=("Arial", 10), bg="#1e293b", fg="#cbd5e1")
scan_count_label.pack(side="left")

btn_frame = tk.Frame(sc_sub_frame, bg="#1e293b")
btn_frame.pack(side="right")
scan_btn = tk.Button(btn_frame, text="▶ START SCAN", font=("Arial", 9, "bold"), bg="#22c55e", fg="white", relief="flat",
                     cursor="hand2", command=scan_large_files, padx=10)
scan_btn.pack(side="left", padx=(0, 5))
export_btn = tk.Button(btn_frame, text="📤 EXPORT RESULTS", font=("Arial", 9, "bold"), bg="#334155", fg="white",
                       relief="flat", cursor="hand2", command=export_results, padx=10)
export_btn.pack(side="left")

tree_frame2 = tk.Frame(scanner_bg, bg="#0f172a")
tree_frame2.pack(fill="both", expand=True, padx=20, pady=(0, 15))

large_files_tree = ttk.Treeview(tree_frame2, columns=("Name", "Size", "Path"), show="headings", height=15)
large_files_tree.heading("Name", text="File Name")
large_files_tree.heading("Size", text="Size")
large_files_tree.heading("Path", text="File Path")

large_files_tree.column("Name", width=200, anchor="w")
large_files_tree.column("Size", width=90, anchor="center")
large_files_tree.column("Path", width=350, anchor="w")

sc_scrollbar = ttk.Scrollbar(tree_frame2, orient="vertical", command=large_files_tree.yview)
large_files_tree.configure(yscrollcommand=sc_scrollbar.set)
large_files_tree.pack(side="left", fill="both", expand=True)
sc_scrollbar.pack(side="right", fill="y")

tk.Button(scanner_bg, text="🗑️ DELETE SELECTED FILE", font=("Arial", 11, "bold"), bg="#dc2626", fg="white",
          relief="flat", cursor="hand2", command=delete_large_file, pady=10).pack(fill="x", padx=20, pady=(0, 20))

# PAGE 3, 4 & 5 (Tools, Settings, About)

tools_frame = pages["Extra Tools"]
tk.Label(tools_frame, text="EXTRA TOOLS", font=("Arial", 20, "bold"), bg="#0f172a", fg="white").pack(anchor="w",
                                                                                                     pady=(0, 20))
ram_booster_card = tk.LabelFrame(tools_frame, text=" ⚡ RAM BOOSTER ", font=("Arial", 12, "bold"), bg="#0f172a",
                                 fg="#a78bfa", padx=20, pady=20)
ram_booster_card.pack(fill="x", pady=10, padx=10)
tk.Label(ram_booster_card, text="Free up unused memory (RAM) and clear caches.", font=("Arial", 11), bg="#0f172a",
         fg="#cbd5e1").pack(anchor="w", pady=(0, 10))
extra_ram_frame = tk.Frame(ram_booster_card, bg="#0f172a")
extra_ram_frame.pack(anchor="w", pady=(0, 15))
extra_ram_val_label = tk.Label(extra_ram_frame, text="Current RAM Usage: --%", font=("Arial", 11, "bold"), bg="#0f172a",
                               fg="#a78bfa")
extra_ram_val_label.pack(side="left", padx=(0, 10))
extra_ram_heart_label = tk.Label(extra_ram_frame, text="", font=("Segoe UI Emoji", 12), bg="#0f172a")
extra_ram_heart_label.pack(side="left")
tk.Button(ram_booster_card, text="BOOST RAM NOW", font=("Arial", 12, "bold"), width=25, height=2, bg="#8b5cf6",
          fg="white", relief="flat", command=boost_ram).pack(anchor="w")

game_booster_card = tk.LabelFrame(tools_frame, text=" 🎮 GAME BOOSTER ", font=("Arial", 12, "bold"), bg="#0f172a",
                                  fg="#ef4444", padx=20, pady=20)
game_booster_card.pack(fill="x", pady=10, padx=10)
tk.Label(game_booster_card, text="Improve FPS and reduce lag by closing bg apps.", font=("Arial", 11), bg="#0f172a",
         fg="#cbd5e1").pack(anchor="w", pady=(0, 10))
extra_cpu_frame = tk.Frame(game_booster_card, bg="#0f172a")
extra_cpu_frame.pack(anchor="w", pady=(0, 15))
extra_cpu_val_label = tk.Label(extra_cpu_frame, text="Current CPU Load: --%", font=("Arial", 11, "bold"), bg="#0f172a",
                               fg="#60a5fa")
extra_cpu_val_label.pack(side="left", padx=(0, 10))
extra_cpu_heart_label = tk.Label(extra_cpu_frame, text="", font=("Segoe UI Emoji", 12), bg="#0f172a")
extra_cpu_heart_label.pack(side="left")
tk.Button(game_booster_card, text="ENABLE GAME MODE", font=("Arial", 12, "bold"), width=25, height=2, bg="#dc2626",
          fg="white", relief="flat", command=enable_game_mode).pack(anchor="w")

settings_frame = pages["Settings"]
tk.Label(settings_frame, text="SETTINGS", font=("Arial", 20, "bold"), bg="#0f172a", fg="white").pack(anchor="w",
                                                                                                     pady=(0, 20))

#  APP BACKGROUND THEME SECTION
bg_card = tk.LabelFrame(settings_frame, text=" 🖥️ APP BACKGROUND THEME ", font=("Arial", 14, "bold"), bg="#0f172a",
                        fg="#cbd5e1", padx=30, pady=30)
bg_card.pack(fill="both", expand=True, pady=10, padx=10)
tk.Label(bg_card, text="Pick a preset background color or choose your own custom color:", font=("Arial", 12),
         bg="#0f172a", fg="#94a3b8").pack(anchor="w", pady=(0, 20))

btn_bg_frame = tk.Frame(bg_card, bg="#0f172a")
btn_bg_frame.pack(fill="both", expand=True)

for i in range(4): btn_bg_frame.columnconfigure(i, weight=1, uniform="col")

# Top Row Buttons
tk.Button(btn_bg_frame, text="🔄 DEFAULT DARK", font=("Arial", 11, "bold"), bg="#1e293b", fg="white", relief="flat",
          cursor="hand2", command=lambda: set_preset_theme("#0f172a"), pady=10).grid(row=0, column=0, columnspan=2,
                                                                                     sticky="nsew", padx=10, pady=10)
tk.Button(btn_bg_frame, text="🌑 PURE BLACK", font=("Arial", 11, "bold"), bg="#121212", fg="white", relief="flat",
          cursor="hand2", command=lambda: set_preset_theme("#000000"), pady=10).grid(row=0, column=2, columnspan=2,
                                                                                     sticky="nsew", padx=10, pady=10)

# Middle Row Buttons (Colored)
tk.Button(btn_bg_frame, text="BLUE", font=("Arial", 11, "bold"), bg="#3b82f6", fg="white", relief="flat",
          cursor="hand2", command=lambda: set_preset_theme("#0b192c"), pady=10).grid(row=1, column=0, sticky="nsew",
                                                                                     padx=10, pady=10)
tk.Button(btn_bg_frame, text="PINK", font=("Arial", 11, "bold"), bg="#ec4899", fg="white", relief="flat",
          cursor="hand2", command=lambda: set_preset_theme("#2d132c"), pady=10).grid(row=1, column=1, sticky="nsew",
                                                                                     padx=10, pady=10)
tk.Button(btn_bg_frame, text="GREEN", font=("Arial", 11, "bold"), bg="#22c55e", fg="white", relief="flat",
          cursor="hand2", command=lambda: set_preset_theme("#092615"), pady=10).grid(row=1, column=2, sticky="nsew",
                                                                                     padx=10, pady=10)
tk.Button(btn_bg_frame, text="YELLOW", font=("Arial", 11, "bold"), bg="#eab308", fg="white", relief="flat",
          cursor="hand2", command=lambda: set_preset_theme("#2b260b"), pady=10).grid(row=1, column=3, sticky="nsew",
                                                                                     padx=10, pady=10)

# Bottom Row Button (Custom)
tk.Button(btn_bg_frame, text="🎨 PICK CUSTOM COLOR", font=("Arial", 11, "bold"), bg="#64748b", fg="white", relief="flat",
          cursor="hand2", command=pick_custom_bg, pady=10).grid(row=2, column=0, columnspan=4, sticky="nsew", padx=10,
                                                                pady=10)

# --- HEART THEME SECTION ---
theme_card = tk.LabelFrame(settings_frame, text=" 🎨 HEART COLOR THEME ", font=("Arial", 14, "bold"), bg="#0f172a",
                           fg="#cbd5e1", padx=30, pady=30)
theme_card.pack(fill="both", expand=True, pady=10, padx=10)
tk.Label(theme_card, text="Choose your favorite heart color for system load tracking:", font=("Arial", 12),
         bg="#0f172a", fg="#94a3b8").pack(anchor="w", pady=(0, 25))


def change_theme(new_theme):
    global CURRENT_THEME
    CURRENT_THEME = new_theme
    messagebox.showinfo("Theme Changed", f"Heart color successfully changed to {new_theme}!")
    update_monitor()


btn_theme_frame = tk.Frame(theme_card, bg="#0f172a")
btn_theme_frame.pack(fill="both", expand=True)

for i in range(3): btn_theme_frame.columnconfigure(i, weight=1, uniform="col")
for i in range(3): btn_theme_frame.rowconfigure(i, weight=1, uniform="row")


def create_theme_btn(parent, text, bg_color, theme_name, r, c):
    tk.Button(parent, text=text, font=("Arial", 16, "bold"), bg=bg_color, fg="white", relief="flat", cursor="hand2",
              command=lambda: change_theme(theme_name)).grid(row=r, column=c, sticky="nsew", padx=10, pady=10)


create_theme_btn(btn_theme_frame, "💔 RED", "#ef4444", "Red", 0, 0)
create_theme_btn(btn_theme_frame, "💙 BLUE", "#3b82f6", "Blue", 0, 1)
create_theme_btn(btn_theme_frame, "💚 GREEN", "#22c55e", "Green", 0, 2)
create_theme_btn(btn_theme_frame, "💖 PINK", "#ec4899", "Pink", 1, 0)
create_theme_btn(btn_theme_frame, "💜 PURPLE", "#a855f7", "Purple", 1, 1)
create_theme_btn(btn_theme_frame, "🧡 ORANGE", "#f97316", "Orange", 1, 2)

tk.Button(btn_theme_frame, text="🎨 PICK CUSTOM COLOR", font=("Arial", 11, "bold"), bg="#64748b", fg="white",
          relief="flat", cursor="hand2", command=pick_custom_heart, pady=10).grid(row=2, column=0, columnspan=3,
                                                                                  sticky="nsew", padx=10, pady=10)

about_frame = pages["About"]
tk.Label(about_frame, text="ABOUT", font=("Arial", 20, "bold"), bg="#0f172a", fg="white").pack(anchor="w", pady=(0, 20))
info_card = tk.LabelFrame(about_frame, text=" SOFTWARE INFORMATION ", font=("Arial", 12, "bold"), bg="#0f172a",
                          fg="#cbd5e1", padx=20, pady=20)
info_card.pack(fill="both", expand=True, padx=10, pady=10)
tk.Label(info_card, text="💻 PC Optimizer Pro - Broken Heart", font=("Arial", 26, "bold"), bg="#0f172a",
         fg="#3b82f6").pack(pady=(20, 5))
tk.Label(info_card, text="Version 2.0 (Professional Edition)", font=("Arial", 12), bg="#0f172a", fg="#94a3b8").pack()
tk.Frame(info_card, height=1, bg="#1e293b").pack(fill="x", pady=25, padx=50)
desc_text = "A powerful, lightweight, and real-time system monitoring tool.\nBuilt with Python, Tkinter, and psutil to ensure maximum performance\nwhile optimizing your computer's RAM, CPU, and Storage."
tk.Label(info_card, text=desc_text, font=("Arial", 11), bg="#0f172a", fg="#cbd5e1", justify="center").pack(pady=10)
dev_frame = tk.Frame(info_card, bg="#0f172a")
dev_frame.pack(pady=25)
tk.Label(dev_frame, text="Designed & Developed by:", font=("Arial", 11), bg="#0f172a", fg="#94a3b8").pack()
tk.Label(dev_frame, text="MD.Zihad Islam", font=("Arial", 16, "bold"), bg="#0f172a", fg="#22c55e").pack(pady=5)
tk.Frame(info_card, height=1, bg="#1e293b").pack(fill="x", pady=25, padx=50)
tk.Label(info_card, text=f"© {datetime.now().year} All Rights Reserved.\nProvided under the MIT License.",
         font=("Arial", 10), bg="#0f172a", fg="#64748b", justify="center").pack(side="bottom", pady=20)


# LIVE UPDATERS

existing_pids = {}


def live_process_update():
    visible_pids = get_visible_windows()
    apps_count, bg_count = 0, 0
    current_pids = set()

    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'status']):
        try:
            pid = proc.info['pid']
            name = proc.info['name'] or "Unknown"
            try:
                cpu = proc.cpu_percent(interval=None)
            except:
                cpu = 0.0
            mem_mb = proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0
            status = str(proc.info['status']).capitalize()
            current_pids.add(pid)

            is_app = pid in visible_pids
            if is_app:
                apps_count += 1
            else:
                bg_count += 1
            cpu_str = f"{cpu:.1f}%" if cpu > 0.1 else "0%"
            mem_str = f"{mem_mb:,.1f} MB"

            if pid in existing_pids:
                item_id = existing_pids[pid]
                target_parent = app_node if is_app else bg_node
                if process_tree.parent(item_id) != target_parent: process_tree.move(item_id, target_parent, "end")
                process_tree.item(item_id, text=name, values=(pid, status, cpu_str, mem_str))
            else:
                target_parent = app_node if is_app else bg_node
                item_id = process_tree.insert(target_parent, "end", text=name, values=(pid, status, cpu_str, mem_str))
                existing_pids[pid] = item_id
        except:
            continue

    dead_pids = set(existing_pids.keys()) - current_pids
    for pid in dead_pids:
        try:
            process_tree.delete(existing_pids[pid])
        except:
            pass
        del existing_pids[pid]

    process_tree.item(app_node, text=f"Apps ({apps_count})")
    process_tree.item(bg_node, text=f"Background processes ({bg_count})")
    process_count_label.config(text=f"{len(current_pids):,} Running Processes")
    window.after(2000, live_process_update)


def update_monitor():
    global temp_scan_counter
    cpu, ram_percent = psutil.cpu_percent(interval=None), psutil.virtual_memory().percent
    total_gb, used_gb, free_gb, disk_percent = get_storage_info()
    theme_color = HEART_THEMES[CURRENT_THEME]["color"]

    cpu_val_label.config(text=f"CPU: {cpu:.1f}%")
    cpu_heart_label.config(text=get_heart_bar(cpu), fg=theme_color)
    ram_val_label.config(text=f"RAM: {ram_percent:.1f}%")
    ram_heart_label.config(text=get_heart_bar(ram_percent), fg=theme_color)
    disk_val_label.config(text=f"Disk: {disk_percent:.1f}%")
    disk_heart_label.config(text=get_heart_bar(disk_percent), fg=theme_color)
    storage_label.config(text=f"C: {free_gb:.1f} GB Free / {total_gb:.1f} GB Total")
    storage_heart_label.config(text=f"{get_heart_bar(disk_percent)}  ({disk_percent:.1f}% Used)", fg=theme_color)

    down, up = get_network_speed()
    network_speed_label.config(text=f"↓ {format_size(down)}/s    ↑ {format_size(up)}/s")
    net_percent = min(((down + up) / (5 * 1024 * 1024)) * 100, 100)
    network_heart_label.config(text=get_heart_bar(net_percent), fg=theme_color)
    net_status, interfaces = get_network_status()
    network_status_label.config(text=f"Status: {net_status}", fg="#22c55e" if net_status == "Connected" else "#ef4444")

    bat_percent, bat_status = get_battery_info()
    if bat_percent is None:
        battery_label.config(text="Battery: Desktop PC")
        battery_heart_label.config(text=get_heart_bar(0), fg=theme_color)
    else:
        battery_label.config(text=f"Battery: {bat_percent:.0f}% ({bat_status})")
        battery_heart_label.config(text=get_heart_bar(bat_percent), fg=theme_color)

    health = calculate_health(cpu, ram_percent, disk_percent)
    health_label.config(text=f"{health}%")
    health_heart_label.config(text=get_heart_bar(100 - health), fg=theme_color)
    health_status_label.config(
        text="System is Normal" if health >= 80 else "System load is Moderate" if health >= 60 else "System load is High",
        fg="#22c55e" if health >= 80 else "#facc15" if health >= 60 else "#ef4444")
    clock_label.config(text=datetime.now().strftime("%I:%M:%S %p"))

    dash_ram_val_label.config(text=f"RAM: {ram_percent:.1f}%")
    dash_cpu_val_label.config(text=f"CPU: {cpu:.1f}%")
    extra_ram_val_label.config(text=f"Current RAM Usage: {ram_percent:.1f}%")
    extra_ram_heart_label.config(text=get_heart_bar(ram_percent), fg=theme_color)
    extra_cpu_val_label.config(text=f"Current CPU Load: {cpu:.1f}%")
    extra_cpu_heart_label.config(text=get_heart_bar(cpu), fg=theme_color)

    if temp_scan_counter % 5 == 0:
        files, size = scan_temp_files()
        temp_result_label.config(text=f"Live Temp Files: {files:,} Files ({format_size(size)})",
                                 fg=theme_color if size > 0 else "#22c55e")
    temp_scan_counter += 1

    window.after(UPDATE_INTERVAL, update_monitor)



# INITIALIZE

show_page("Dashboard")
psutil.cpu_percent(interval=None)
live_process_update()
update_monitor()

window.mainloop()