from pathlib import Path
import csv
import re
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- DEFAULT SETTINGS ---

DEFAULT_MIDI_NOTES = {
    "kick:hit": 36,
    "kick_sub:hit": 35,
    "snare:hit": 38, "snare_top:hit": 38, "snare_bottom:hit": 40,
    "snare:rim": 40, "snare:ghost": 41, "snare:crosstick": 39,
    "hihat:closed": 48, "hihat:pedal": 43, "hihat:open_1": 45, "hihat:open_2": 46,
    "hihat:open_3": 47, "hihat:closed_edge": 49, "hihat:tight_tip": 51,
    "hihat:tight_edge": 52, "hihat:closed_tip": 50, "hihat:break": 53, "hihat:open": 44,
    "tom_10inch:hit": 57, "tom_12inch:hit": 59, "tom_16inch:hit": 60, "tom:hit": 62,
    "crash_18inch:hit": 65, "crash_18inch:choke": 66, "crash_19inch:hit": 67, "crash_19inch:choke": 68,
    "crash:hit": 69, "crash:choke": 70,
    "splash:hit": 72, "splash:choke": 73,
    "china:hit": 75, "china:choke": 76,
    "stack:hit": 77,
    "ride:bow": 81, "ride:bell": 82, "ride:edge": 83, "ride:hit": 84,
}

DEFAULT_OUTPUT_TRACKS = {
    "kick:Close": 0, "kick:Direct": 0,
    "kick_sub:Close": 1, "kick_sub:Direct": 1,
    "snare:Close": 2, "snare_top:Close": 2, "snare_bottom:Close": 3,
    "tom_10inch:Close": 4, "tom_12inch:Close": 5, "tom_16inch:Close": 6, "tom:Close": 4,
    "hihat:Close": 7,
    "crash_18inch:Close": 8, "crash_19inch:Close": 9, "crash:Close": 8,
    "splash:Close": 10, "china:Close": 11, "ride:Close": 12,
    "stack:Close": 13, "stack:Direct": 13,
    "Overhead:Overhead": 20, "Room:Room": 21,
}

DEFAULT_IDENTIFIERS = {
    "kick": {"type": "instrument", "value": "kick"},
    "kck": {"type": "instrument", "value": "kick"},
    "sub": {"type": "instrument", "value": "kick_sub"},
    "snare": {"type": "instrument", "value": "snare"},
    "snr": {"type": "instrument", "value": "snare"},
    "top": {"type": "instrument", "value": "snare_top"},
    "bottom": {"type": "instrument", "value": "snare_bottom"},
    "10x": {"type": "instrument", "value": "tom_10inch"},
    "12x": {"type": "instrument", "value": "tom_12inch"},
    "16x": {"type": "instrument", "value": "tom_16inch"},
    "18": {"type": "instrument", "value": "crash_18inch"},
    "19": {"type": "instrument", "value": "crash_19inch"},
    "rim": {"type": "articulation", "value": "rim"},
    "ghost": {"type": "articulation", "value": "ghost"},
    "bell": {"type": "articulation", "value": "bell"},
    "edge": {"type": "articulation", "value": "edge"},
    "oh": {"type": "bus", "value": "Overhead"},
    "overhead": {"type": "bus", "value": "Overhead"},
    "rm": {"type": "bus", "value": "Room"},
    "room": {"type": "bus", "value": "Room"},
    "cls": {"type": "bus", "value": "Close"},
    "close": {"type": "bus", "value": "Close"},
}

AUDIO_EXTENSIONS = {".wav", ".wave", ".flac", ".aif", ".aiff", ".mp3", ".ogg", ".opus"}
RR_REG = re.compile(r"^(?:RR|R)(\d+)$", re.I)
VEL_REG = re.compile(r"^(?:V|Vel)(\d+)$", re.I)

class DrumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drum Sample Inventory & SFZ Generator")
        self.root.geometry("1150x820")
        
        self.apply_refined_theme()

        self.midi_notes = DEFAULT_MIDI_NOTES.copy()
        self.output_tracks = DEFAULT_OUTPUT_TRACKS.copy()
        self.identifiers = DEFAULT_IDENTIFIERS.copy()
        
        self.selected_folder = tk.StringVar()
        self.csv_filename_var = tk.StringVar(value="Inventory_Database")
        self.sfz_filename_var = tk.StringVar(value="Instrument")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.setup_processor_tab()
        self.setup_settings_tab()
        self.setup_csv_viewer_tab()

    def apply_refined_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg_color = "#22252a"
        card_bg = "#2a2e35"
        fg_color = "#e6edf3"
        field_bg = "#181a1f"
        accent_color = "#30363d"
        accent_hover = "#384250"
        select_bg = "#264f78"

        self.root.configure(bg=bg_color)

        style.configure(".", background=bg_color, foreground=fg_color, fieldbackground=field_bg, bordercolor="#3b4252")
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("TLabelframe", background=card_bg, foreground=fg_color, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=card_bg, foreground="#3fb950", font=("Segoe UI", 10, "bold"))
        
        # Buttons
        style.configure("TButton", background="#30363d", foreground=fg_color, bordercolor="#484f58", focusthickness=1, focuscolor="#3fb950", padding=8, relief="flat")
        style.map("TButton", background=[("active", "#384250")], bordercolor=[("active", "#6e7681")])

        style.configure("Accent.TButton", background=accent_color, foreground="#ffffff", bordercolor="#388bfd", font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        style.map("Accent.TButton", background=[("active", accent_hover)])

        # Notebook Tabs: Selected tab pops out (raised, lighter #323842, taller padding), unselected tabs stay recessed/indented (#15171c)
        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background="#15171c", foreground="#8b949e", padding=[18, 8], font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("TNotebook.Tab", 
                  background=[("selected", "#323842"), ("active", "#1e2229")], 
                  foreground=[("selected", "#ffffff"), ("active", fg_color)],
                  padding=[("selected", [18, 12, 18, 10])])

        # Treeview Tables
        style.configure("Treeview", background=field_bg, foreground=fg_color, fieldbackground=field_bg, bordercolor="#30363d", rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#21262d", foreground="#3fb950", relief="flat", font=("Segoe UI", 10, "bold"), padding=4)
        style.map("Treeview", background=[("selected", select_bg)], foreground=[("selected", "#ffffff")])

        # Combobox
        style.configure("TCombobox", fieldbackground=field_bg, background="#30363d", foreground=fg_color, padding=4)
        style.map("TCombobox", fieldbackground=[('readonly', field_bg)], background=[('active', '#384250')])

        self.root.option_add("*TCombobox*Listbox.background", field_bg)
        self.root.option_add("*TCombobox*Listbox.foreground", fg_color)
        self.root.option_add("*TCombobox*Listbox.selectBackground", select_bg)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    def setup_processor_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" Processor ")

        f_frame = ttk.LabelFrame(tab, text=" Sample Library Folder ", padding=15)
        f_frame.pack(fill="x", padx=10, pady=10)

        ttk.Entry(f_frame, textvariable=self.selected_folder, width=72, font=("Segoe UI", 10)).pack(side="left", padx=5)
        ttk.Button(f_frame, text="Browse...", command=self.browse_folder).pack(side="left", padx=5)

        n_frame = ttk.LabelFrame(tab, text=" Custom File Naming Options ", padding=15)
        n_frame.pack(fill="x", padx=10, pady=5)

        grid_f = ttk.Frame(n_frame)
        grid_f.pack(fill="x", padx=5)

        ttk.Label(grid_f, text="Inventory CSV Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(grid_f, textvariable=self.csv_filename_var, width=35).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(grid_f, text=".csv", foreground="#8b949e").grid(row=0, column=2, sticky="w")

        ttk.Label(grid_f, text="Multitrack SFZ Name:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(grid_f, textvariable=self.sfz_filename_var, width=35).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(grid_f, text=".sfz", foreground="#8b949e").grid(row=1, column=2, sticky="w")

        act_frame = ttk.Frame(tab, padding=10)
        act_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Button(act_frame, text="Run Inventory & Generate SFZ", command=self.run_workflow, style="Accent.TButton").pack(fill="x", pady=5)

        self.log_box = tk.Text(act_frame, wrap="word", height=16, bg="#181a1f", fg="#3fb950", insertbackground="white", font=("Consolas", 10), relief="flat", highlightthickness=1, highlightbackground="#30363d")
        self.log_box.pack(fill="both", expand=True, pady=5)
        self.log_box.insert("end", "Ready. Select your sample folder and click Run.\n")

    def setup_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" Settings ")

        sub_notebook = ttk.Notebook(tab)
        sub_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab 1: MIDI Mappings ---
        t_midi = ttk.Frame(sub_notebook, padding=10)
        sub_notebook.add(t_midi, text=" MIDI Mappings ")

        m_ctrl = ttk.Frame(t_midi, padding=5)
        m_ctrl.pack(side="bottom", fill="x", pady=5)
        self.m_key_var, self.m_val_var = tk.StringVar(), tk.StringVar()
        ttk.Label(m_ctrl, text="Key (Inst:Art):").pack(side="left", padx=5)
        ttk.Entry(m_ctrl, textvariable=self.m_key_var, width=25).pack(side="left", padx=5)
        ttk.Label(m_ctrl, text="MIDI Note:").pack(side="left", padx=5)
        ttk.Entry(m_ctrl, textvariable=self.m_val_var, width=8).pack(side="left", padx=5)
        ttk.Button(m_ctrl, text="Add / Update", command=self.add_midi_mapping).pack(side="left", padx=10)
        ttk.Button(m_ctrl, text="Delete Selected", command=self.delete_midi_mapping).pack(side="left", padx=5)

        m_tree_c = ttk.Frame(t_midi)
        m_tree_c.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.midi_tree = ttk.Treeview(m_tree_c, columns=("key", "note"), show="headings", height=15)
        self.midi_tree.heading("key", text="Instrument : Articulation")
        self.midi_tree.heading("note", text="MIDI Note")
        self.midi_tree.pack(fill="both", expand=True, side="left")
        self.midi_tree.bind("<Double-1>", self.load_midi_to_edit)
        
        m_scroll = ttk.Scrollbar(m_tree_c, orient="vertical", command=self.midi_tree.yview)
        m_scroll.pack(side="right", fill="y")
        self.midi_tree.configure(yscrollcommand=m_scroll.set)

        # --- Tab 2: Output Tracks ---
        t_tracks = ttk.Frame(sub_notebook, padding=10)
        sub_notebook.add(t_tracks, text=" Output Tracks ")

        tr_ctrl = ttk.Frame(t_tracks, padding=5)
        tr_ctrl.pack(side="bottom", fill="x", pady=5)
        self.t_key_var, self.t_val_var = tk.StringVar(), tk.StringVar()
        ttk.Label(tr_ctrl, text="Key (Inst:Bus):").pack(side="left", padx=5)
        ttk.Entry(tr_ctrl, textvariable=self.t_key_var, width=25).pack(side="left", padx=5)
        ttk.Label(tr_ctrl, text="Track #:").pack(side="left", padx=5)
        ttk.Entry(tr_ctrl, textvariable=self.t_val_var, width=8).pack(side="left", padx=5)
        ttk.Button(tr_ctrl, text="Add / Update", command=self.add_track_mapping).pack(side="left", padx=10)
        ttk.Button(tr_ctrl, text="Delete Selected", command=self.delete_track_mapping).pack(side="left", padx=5)

        tr_tree_c = ttk.Frame(t_tracks)
        tr_tree_c.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.track_tree = ttk.Treeview(tr_tree_c, columns=("key", "track"), show="headings", height=15)
        self.track_tree.heading("key", text="Instrument : Bus")
        self.track_tree.heading("track", text="Track Index")
        self.track_tree.pack(fill="both", expand=True, side="left")
        self.track_tree.bind("<Double-1>", self.load_track_to_edit)

        tr_scroll = ttk.Scrollbar(tr_tree_c, orient="vertical", command=self.track_tree.yview)
        tr_scroll.pack(side="right", fill="y")
        self.track_tree.configure(yscrollcommand=tr_scroll.set)

        # --- Tab 3: Filename Identifiers ---
        t_idents = ttk.Frame(sub_notebook, padding=10)
        sub_notebook.add(t_idents, text=" Filename Identifiers ")

        id_ctrl = ttk.Frame(t_idents, padding=5)
        id_ctrl.pack(side="bottom", fill="x", pady=5)
        self.i_keyword_var = tk.StringVar()
        self.i_type_var = tk.StringVar(value="instrument")
        self.i_val_var = tk.StringVar()

        ttk.Label(id_ctrl, text="Keyword:").pack(side="left", padx=2)
        ttk.Entry(id_ctrl, textvariable=self.i_keyword_var, width=12).pack(side="left", padx=2)
        
        ttk.Label(id_ctrl, text="Type:").pack(side="left", padx=2)
        self.i_type_combo = ttk.Combobox(id_ctrl, textvariable=self.i_type_var, values=["instrument", "bus", "articulation"], width=13, state="readonly")
        self.i_type_combo.pack(side="left", padx=2)

        ttk.Label(id_ctrl, text="Target Value:").pack(side="left", padx=2)
        ttk.Entry(id_ctrl, textvariable=self.i_val_var, width=15).pack(side="left", padx=2)
        ttk.Button(id_ctrl, text="Add / Update", command=self.add_identifier).pack(side="left", padx=10)
        ttk.Button(id_ctrl, text="Delete Selected", command=self.delete_identifier).pack(side="left", padx=5)

        id_tree_c = ttk.Frame(t_idents)
        id_tree_c.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.ident_tree = ttk.Treeview(id_tree_c, columns=("keyword", "type", "value"), show="headings", height=15)
        self.ident_tree.heading("keyword", text="Filename Keyword")
        self.ident_tree.heading("type", text="Property Type")
        self.ident_tree.heading("value", text="Mapped Target Value")
        self.ident_tree.pack(fill="both", expand=True, side="left")
        self.ident_tree.bind("<Double-1>", self.load_ident_to_edit)

        id_scroll = ttk.Scrollbar(id_tree_c, orient="vertical", command=self.ident_tree.yview)
        id_scroll.pack(side="right", fill="y")
        self.ident_tree.configure(yscrollcommand=id_scroll.set)

        self.refresh_settings_tables()

    def setup_csv_viewer_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" CSV Viewer ")

        top_ctrl = ttk.Frame(tab, padding=10)
        top_ctrl.pack(fill="x", padx=10, pady=5)

        ttk.Button(top_ctrl, text="Load Generated Inventory CSV", command=self.load_generated_csv).pack(side="left", padx=5)
        ttk.Button(top_ctrl, text="Browse External CSV...", command=self.browse_external_csv).pack(side="left", padx=5)
        
        self.csv_path_label = ttk.Label(top_ctrl, text="No CSV loaded", foreground="#8b949e")
        self.csv_path_label.pack(side="left", padx=15)

        table_frame = ttk.Frame(tab, padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.csv_tree = ttk.Treeview(table_frame, show="headings")
        
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.csv_tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.csv_tree.xview)
        self.csv_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.csv_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.csv_menu = tk.Menu(self.root, tearoff=0)
        self.csv_menu.add_command(label="Copy Cell Value", command=self.copy_csv_cell)
        self.csv_menu.add_command(label="Copy Entire Row", command=self.copy_csv_row)
        
        self.csv_tree.bind("<Button-3>", self.show_csv_context_menu)

    def show_csv_context_menu(self, event):
        region = self.csv_tree.identify("region", event.x, event.y)
        if region == "cell":
            self.clicked_row = self.csv_tree.identify_row(event.y)
            self.clicked_col = self.csv_tree.identify_column(event.x)
            self.csv_tree.selection_set(self.clicked_row)
            self.csv_menu.post(event.x_root, event.y_root)

    def copy_csv_cell(self):
        if hasattr(self, 'clicked_row') and hasattr(self, 'clicked_col'):
            item = self.csv_tree.item(self.clicked_row)
            values = item["values"]
            col_idx = int(self.clicked_col.replace("#", "")) - 1
            if 0 <= col_idx < len(values):
                val = str(values[col_idx])
                self.root.clipboard_clear()
                self.root.clipboard_append(val)

    def copy_csv_row(self):
        selected = self.csv_tree.selection()
        if not selected: return
        item = self.csv_tree.item(selected[0])
        row_str = "\t".join(map(str, item["values"]))
        self.root.clipboard_clear()
        self.root.clipboard_append(row_str)

    def load_csv_file(self, file_path):
        path = Path(file_path)
        if not path.exists():
            messagebox.showerror("Error", f"File not found:\n{path}")
            return

        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers:
                    messagebox.showwarning("Warning", "The CSV file is empty.")
                    return

                self.csv_tree.delete(*self.csv_tree.get_children())
                self.csv_tree["columns"] = headers
                for h in headers:
                    self.csv_tree.heading(h, text=h)
                    self.csv_tree.column(h, width=130, anchor="w", stretch=False)

                for row in reader:
                    self.csv_tree.insert("", "end", values=row)

            self.csv_path_label.config(text=str(path), foreground="#3fb950")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse CSV:\n{e}")

    def load_generated_csv(self):
        folder = self.selected_folder.get().strip()
        if not folder:
            messagebox.showerror("Error", "Please select a sample library folder in the Processor tab first.")
            return
        
        csv_name = self.csv_filename_var.get().strip() or "Inventory_Database"
        if not csv_name.endswith(".csv"):
            csv_name += ".csv"
            
        csv_path = Path(folder) / "Inventory_Database" / csv_name
        self.load_csv_file(csv_path)

    def browse_external_csv(self):
        file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.load_csv_file(file_path)

    def refresh_settings_tables(self):
        for row in self.midi_tree.get_children(): self.midi_tree.delete(row)
        for k, v in sorted(self.midi_notes.items()):
            self.midi_tree.insert("", "end", values=(k, v))

        for row in self.track_tree.get_children(): self.track_tree.delete(row)
        for k, v in sorted(self.output_tracks.items(), key=lambda x: str(x[0])):
            self.track_tree.insert("", "end", values=(k, v))

        for row in self.ident_tree.get_children(): self.ident_tree.delete(row)
        for k, info in sorted(self.identifiers.items()):
            self.ident_tree.insert("", "end", values=(k, info["type"], info["value"]))

    def load_midi_to_edit(self, event):
        selected = self.midi_tree.selection()
        if selected:
            vals = self.midi_tree.item(selected[0])["values"]
            self.m_key_var.set(vals[0])
            self.m_val_var.set(vals[1])

    def load_track_to_edit(self, event):
        selected = self.track_tree.selection()
        if selected:
            vals = self.track_tree.item(selected[0])["values"]
            self.t_key_var.set(vals[0])
            self.t_val_var.set(vals[1])

    def load_ident_to_edit(self, event):
        selected = self.ident_tree.selection()
        if selected:
            vals = self.ident_tree.item(selected[0])["values"]
            self.i_keyword_var.set(vals[0])
            self.i_type_var.set(vals[1])
            self.i_val_var.set(vals[2])

    def add_midi_mapping(self):
        k, v = self.m_key_var.get().strip(), self.m_val_var.get().strip()
        if k and v.isdigit():
            self.midi_notes[k] = int(v)
            self.refresh_settings_tables()
            self.m_key_var.set(""); self.m_val_var.set("")
        else:
            messagebox.showerror("Invalid Input", "Provide valid Inst:Art key and numeric note.")

    def delete_midi_mapping(self):
        selected = self.midi_tree.selection()
        if selected:
            key = self.midi_tree.item(selected)["values"][0]
            if key in self.midi_notes:
                del self.midi_notes[key]
                self.refresh_settings_tables()

    def add_track_mapping(self):
        k, v = self.t_key_var.get().strip(), self.t_val_var.get().strip()
        if k and v.isdigit():
            self.output_tracks[k] = int(v)
            self.refresh_settings_tables()
            self.t_key_var.set(""); self.t_val_var.set("")
        else:
            messagebox.showerror("Invalid Input", "Provide valid Inst:Bus key and numeric track index.")

    def delete_track_mapping(self):
        selected = self.track_tree.selection()
        if selected:
            key = self.track_tree.item(selected)["values"][0]
            if key in self.output_tracks:
                del self.output_tracks[key]
                self.refresh_settings_tables()

    def add_identifier(self):
        kw = self.i_keyword_var.get().strip().lower()
        kind = self.i_type_var.get().strip().lower()
        val = self.i_val_var.get().strip()
        if kw and kind in ["instrument", "bus", "articulation"] and val:
            self.identifiers[kw] = {"type": kind, "value": val}
            self.refresh_settings_tables()
            self.i_keyword_var.set(""); self.i_val_var.set("")
        else:
            messagebox.showerror("Invalid Input", "Provide keyword, valid type from dropdown, and target value.")

    def delete_identifier(self):
        selected = self.ident_tree.selection()
        if selected:
            key = self.ident_tree.item(selected)["values"][0]
            if key in self.identifiers:
                del self.identifiers[key]
                self.refresh_settings_tables()

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select sample library folder")
        if folder: self.selected_folder.set(folder)

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.root.update_idletasks()

    def parse_filename(self, path):
        tokens = path.stem.split("-")
        kept, rr, velocity = [], None, None
        for t in tokens:
            m_rr, m_vel = RR_REG.fullmatch(t), VEL_REG.fullmatch(t)
            if m_rr: rr = int(m_rr.group(1))
            elif m_vel: velocity = int(m_vel.group(1))
            else: kept.append(t)

        library = "-".join(kept[:2]) if len(kept) >= 2 else (kept[0] if kept else "Unknown")
        remaining = kept[2:] if len(kept) >= 2 else kept
        sample_group = "-".join(kept)
        name_lower = path.stem.lower()

        instrument = "unknown"
        output_bus = "Direct"
        articulation = "hit"

        for kw, info in self.identifiers.items():
            if kw in name_lower:
                if info["type"] == "instrument":
                    instrument = info["value"]
                elif info["type"] == "bus":
                    output_bus = info["value"]
                elif info["type"] == "articulation":
                    articulation = info["value"]

        if instrument == "unknown":
            instrument = "tom"

        if articulation == "hit":
            if "snare" in instrument:
                articulation = "rim" if "rim" in name_lower else ("ghost" if any(k in name_lower for k in ["gst", "ghost"]) else ("crosstick" if any(k in name_lower for k in ["crsstk", "cross", "crosstick", "crs"] ) else "hit"))
            elif "crash" in instrument or instrument in ["splash", "china"]:
                articulation = "choke" if any(k in name_lower for k in ["chk", "choke"]) else "hit"
            elif "ride" in instrument:
                articulation = "bell" if "bell" in name_lower else ("edge" if "edge" in name_lower else "bow")
            elif "hihat" in instrument:
                rules = [("opn1", "open_1"), ("opn2", "open_2"), ("opn3", "open_3"), ("open1", "open_1"), ("open2", "open_2"), ("open3", "open_3"), ("clsdedg", "closed_edge"), ("chk", "closed"), ("clsd", "closed"), ("pdl", "pedal"), ("brk", "break"), ("open", "open"), ("opn", "open")]
                for p, l in rules:
                    if p in name_lower:
                        articulation = l
                        break

        midi_key = f"{instrument}:{articulation}"
        midi_note = self.midi_notes.get(midi_key, self.midi_notes.get(f"{instrument.split('_')[0]}:{articulation}", ""))

        track_key = f"{instrument}:{output_bus}"
        default_track = self.output_tracks.get(track_key, self.output_tracks.get(f"{output_bus}:{output_bus}", 0))

        return {
            "filename": path.name, "path": str(path.resolve()), "extension": path.suffix.lower(),
            "sample_group": sample_group, "library": library, "instrument_name": "-".join(remaining) or instrument,
            "instrument_type": instrument, "articulation_type": articulation, "midi_note": midi_note,
            "velocity": velocity, "rr": rr, "output_bus": output_bus, "output_track": default_track,
        }

    def scan_files(self, folder):
        file_map = {}
        for path in Path(folder).rglob("*"):
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                tokens = path.stem.split("-")
                kept, rr, vel = [], None, None
                for t in tokens:
                    m_rr, m_vel = RR_REG.fullmatch(t), VEL_REG.fullmatch(t)
                    if m_rr: rr = int(m_rr.group(1))
                    elif m_vel: vel = int(m_vel.group(1))
                    else: kept.append(t)
                group = "-".join(kept)
                file_map[(group, vel, rr)] = path
        return file_map

    def run_workflow(self):
        folder = self.selected_folder.get().strip()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", "Please select a valid sample library folder first.")
            return

        folder_path = Path(folder)
        output_dir = folder_path / "Inventory_Database"
        output_dir.mkdir(exist_ok=True)

        self.log(f"\n--- Starting Scan: {folder_path.name} ---")
        
        samples, total_discovered, error_count = [], 0, 0
        for path in folder_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                total_discovered += 1
                try: samples.append(self.parse_filename(path))
                except Exception: error_count += 1

        groups = defaultdict(list)
        for s in samples:
            groups[(s["library"], s["sample_group"], s["instrument_type"], s["instrument_name"], s["articulation_type"], s["output_bus"], s["output_track"])].append(s)

        rows = []
        for _, files in sorted(groups.items()):
            vels = sorted({s["velocity"] for s in files if s["velocity"] is not None})
            rrs = sorted({s["rr"] for s in files if s["rr"] is not None})
            rows.append({
                "library": files[0]["library"], "sample_group": files[0]["sample_group"],
                "instrument_name": files[0]["instrument_name"], "instrument_type": files[0]["instrument_type"],
                "articulation_type": files[0]["articulation_type"], "midi_note": files[0]["midi_note"],
                "output_bus": files[0]["output_bus"], "output_track": files[0]["output_track"], "extension": files[0]["extension"],
                "total_velocities": len(vels), "velocity_values": ",".join(map(str, vels)),
                "total_round_robins": len(rrs), "rr_values": ",".join(map(str, rrs)),
                "sample_files_count": len(files),
            })

        fields = ["library", "sample_group", "instrument_name", "instrument_type", "articulation_type", "midi_note", "output_bus", "output_track", "extension", "total_velocities", "velocity_values", "total_round_robins", "rr_values", "sample_files_count"]
        
        csv_name = self.csv_filename_var.get().strip() or "Inventory_Database"
        if not csv_name.endswith(".csv"): csv_name += ".csv"
        csv_path = output_dir / csv_name
        
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        self.log(f"Inventory saved: {csv_path.name}")

        sample_map = self.scan_files(folder_path)
        
        sfz_name = self.sfz_filename_var.get().strip() or "Instrument"
        if not sfz_name.endswith(".sfz"): sfz_name += ".sfz"
        output_sfz = folder_path / sfz_name

        sfz_lines = ["<global>", "default_path=.", "master_volume=0", ""]
        group_count, region_count = 0, 0

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                group_name = row["sample_group"]
                midi = row["midi_note"]
                out_track = row.get("output_track", "0")
                inst_type = row.get("instrument_type", "unknown").lower()
                articulation = row.get("articulation_type", "hit")
                bus = row.get("output_bus", "Direct")
                
                if not midi: continue

                vels = sorted([int(v) for v in row["velocity_values"].split(",")] if row["velocity_values"] else [])
                rrs = sorted([int(r) for r in row["rr_values"].split(",")] if row["rr_values"] else [])
                if not vels or not rrs: continue

                num_vels = len(vels)
                seq_len = len(rrs)

                for i, v in enumerate(vels):
                    lovel = 1 if i == 0 else int((i / num_vels) * 127) + 1
                    hivel = 127 if i == num_vels - 1 else int(((i + 1) / num_vels) * 127)

                    valid_regions = []
                    for r_idx, r in enumerate(rrs):
                        sample_path = sample_map.get((group_name, v, r))
                        if sample_path:
                            try:
                                rel_path = sample_path.relative_to(folder_path)
                            except ValueError:
                                rel_path = sample_path.name
                            
                            seq_pos = r_idx + 1
                            valid_regions.append(f"<region> sample={rel_path} seq_position={seq_pos}")

                    if valid_regions:
                        group_count += 1
                        sfz_lines.append(f"// {inst_type.upper()} ({articulation}) - {bus} - Vel{v:02d}")
                        sfz_lines.append(f"<group> key={midi} lovel={lovel} hivel={hivel} seq_length={seq_len} output={out_track}")
                        sfz_lines.extend(valid_regions)
                        sfz_lines.append("")
                        region_count += len(valid_regions)

        with open(output_sfz, "w", encoding="utf-8") as sfz:
            sfz.write("\n".join(sfz_lines))

        self.log(f"SFZ Generated: {output_sfz.name} ({group_count} groups, {region_count} regions)")
        self.log(f"Stats: Found {total_discovered} | Indexed {len(samples)} | Errors {error_count} | Rows {len(rows)}")
        self.log("--- Workflow Complete Successfully ---\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = DrumApp(root)
    root.mainloop()