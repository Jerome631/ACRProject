import os
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, filedialog
from fm_calc_main import fm_calc_main

class FMCallerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("B0 Fieldmapping Suite")
        self.geometry("680x640")
        self.configure(bg="#0f172a") # Slate 900
        self.resizable(True, True)

        # Styles
        self.title_font = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.header_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.btn_font = tkfont.Font(family="Helvetica", size=11, weight="bold")
        self.label_font = tkfont.Font(family="Helvetica", size=10)
        self.footer_font = tkfont.Font(family="Helvetica", size=9)

        self.setup_ui()

    def setup_ui(self):
        # Header frame
        header_frame = tk.Frame(self, bg="#0f172a")
        header_frame.pack(fill="x", pady=15)

        title_label = tk.Label(
            header_frame,
            text="B0 FIELDMAPPING SUITE",
            font=self.title_font,
            fg="#3b82f6", # Blue 500
            bg="#0f172a"
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="Calculate B0 fieldmaps from multi-echo magnitude & phase NIfTI images",
            font=self.footer_font,
            fg="#94a3b8", # Slate 400
            bg="#0f172a"
        )
        subtitle_label.pack(pady=3)

        # Preset selection frame
        preset_frame = tk.LabelFrame(
            self,
            text="Presorted Examples & Presets",
            font=self.header_font,
            fg="#38bdf8", # Sky 400
            bg="#1e293b", # Slate 800
            bd=2,
            relief="groove",
            padx=15,
            pady=10
        )
        preset_frame.pack(fill="x", padx=30, pady=10)

        case1_btn = self.create_btn(preset_frame, "Load Case 1 (6D NIfTI, dicom_sort_convert)", lambda: self.load_case(1))
        case1_btn.pack(fill="x", pady=5)

        case2_btn = self.create_btn(preset_frame, "Load Case 2 (6D NIfTI, Specify TEs, RBW, PE dir)", lambda: self.load_case(2))
        case2_btn.pack(fill="x", pady=5)

        case3_btn = self.create_btn(preset_frame, "Load Case 3 (Separate Mag/Phase 5D NIfTI)", lambda: self.load_case(3))
        case3_btn.pack(fill="x", pady=5)

        # Custom configuration frame
        self.config_frame = tk.LabelFrame(
            self,
            text="Custom Execution Parameters",
            font=self.header_font,
            fg="#38bdf8",
            bg="#1e293b",
            bd=2,
            relief="groove",
            padx=15,
            pady=10
        )
        self.config_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Form fields variables
        self.n_channels_var = tk.StringVar(value="8")
        self.sep_echoes_var = tk.StringVar(value="no")
        self.sep_pm_var = tk.StringVar(value="no")
        self.root_dir_var = tk.StringVar(value="/tmp/fm_example_data/")
        self.readfile_dirs_var = tk.StringVar(value="6D")
        self.writefile_dir_var = tk.StringVar(value="/tmp/fm_example_results/case1")
        self.method_var = tk.StringVar(value="sep-channel")
        self.unwrap_method_var = tk.StringVar(value="prelude")
        self.do_grad_thresh_var = tk.StringVar(value="yes")

        # Layout form fields in grid
        fields = [
            ("Root Directory:", self.root_dir_var, 0, True),
            ("Write Directory:", self.writefile_dir_var, 1, True),
            ("Read Sub-dirs (comma-separated):", self.readfile_dirs_var, 2, False),
            ("Number of Channels (Coils):", self.n_channels_var, 3, False),
            ("Separate Echo Files (yes/no):", self.sep_echoes_var, 4, False),
            ("Separate Mag/Phase Files (yes/no):", self.sep_pm_var, 5, False),
            ("Phase Combination Method:", self.method_var, 6, False),
            ("Unwrapping Method:", self.unwrap_method_var, 7, False),
            ("Limit Gradients (yes/no):", self.do_grad_thresh_var, 8, False),
        ]

        for label_text, var, row, is_dir in fields:
            lbl = tk.Label(self.config_frame, text=label_text, font=self.label_font, fg="#e2e8f0", bg="#1e293b", anchor="w")
            lbl.grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
            
            entry = tk.Entry(self.config_frame, textvariable=var, bg="#0f172a", fg="#ffffff", bd=1, insertbackground="white", width=45)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            
            if is_dir:
                btn = tk.Button(self.config_frame, text="Browse", bg="#475569", fg="#ffffff", activebackground="#64748b", bd=0, padx=8,
                                command=lambda v=var: self.browse_directory(v))
                btn.grid(row=row, column=2, padx=(5, 0), pady=3)

        self.config_frame.columnconfigure(1, weight=1)

        # Bottom Actions Frame
        bottom_frame = tk.Frame(self, bg="#0f172a")
        bottom_frame.pack(fill="x", side="bottom", pady=15, padx=30)

        run_btn = tk.Button(
            bottom_frame,
            text="Run Fieldmapping Pipeline",
            font=self.btn_font,
            fg="#ffffff",
            bg="#10b981", # Emerald 500
            activeforeground="#ffffff",
            activebackground="#059669",
            bd=0,
            padx=15,
            pady=10,
            command=self.run_pipeline
        )
        run_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        exit_btn = tk.Button(
            bottom_frame,
            text="Exit",
            font=self.btn_font,
            fg="#ffffff",
            bg="#ef4444", # Red 500
            activeforeground="#ffffff",
            activebackground="#dc2626",
            bd=0,
            padx=15,
            pady=10,
            command=self.destroy
        )
        exit_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def create_btn(self, parent, text, command):
        btn = tk.Button(
            parent,
            text=text,
            font=self.label_font,
            fg="#ffffff",
            bg="#3b82f6", # Blue 500
            activeforeground="#ffffff",
            activebackground="#1d4ed8",
            bd=0,
            pady=6,
            command=command
        )
        def on_enter(e):
            btn['background'] = '#2563eb'
        def on_leave(e):
            btn['background'] = '#3b82f6'
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def browse_directory(self, var):
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)

    def load_case(self, case_num):
        if case_num == 1:
            self.n_channels_var.set("8")
            self.sep_echoes_var.set("no")
            self.sep_pm_var.set("no")
            self.root_dir_var.set("/tmp/fm_example_data/")
            self.readfile_dirs_var.set("6D")
            self.writefile_dir_var.set("/tmp/fm_example_results/case1")
            self.do_grad_thresh_var.set("yes")
            self.method_var.set("sep-channel")
            self.unwrap_method_var.set("prelude")
        elif case_num == 2:
            self.n_channels_var.set("8")
            self.sep_echoes_var.set("no")
            self.sep_pm_var.set("no")
            self.root_dir_var.set("/tmp/fm_example_data/")
            self.readfile_dirs_var.set("6D")
            self.writefile_dir_var.set("/tmp/fm_example_results/case2")
            self.do_grad_thresh_var.set("yes")
            self.method_var.set("sep-channel")
            self.unwrap_method_var.set("prelude")
        elif case_num == 3:
            self.n_channels_var.set("8")
            self.sep_echoes_var.set("no")
            self.sep_pm_var.set("yes")
            self.root_dir_var.set("/tmp/fm_example_data/5D")
            self.readfile_dirs_var.set("mag,phase")
            self.writefile_dir_var.set("/tmp/fm_example_results/case3")
            self.do_grad_thresh_var.set("no")
            self.method_var.set("sep-channel")
            self.unwrap_method_var.set("prelude")
        messagebox.showinfo("Preset Loaded", f"Case {case_num} parameters loaded successfully!")

    def run_pipeline(self):
        self.withdraw()
        try:
            # Parse readfile_dirs
            read_dirs = [d.strip() for d in self.readfile_dirs_var.get().split(",") if d.strip()]
            
            data = {
                'n_channels': int(self.n_channels_var.get()),
                'sep_files_for_echoes': self.sep_echoes_var.get(),
                'sep_files_for_pm': self.sep_pm_var.get(),
                'root_dir': self.root_dir_var.get(),
                'readfile_dirs': read_dirs,
                'writefile_dir': self.writefile_dir_var.get(),
                'do_gradient_thresholding': self.do_grad_thresh_var.get(),
                'method': self.method_var.get(),
                'unwrap_method': self.unwrap_method_var.get()
            }

            # Extra config for Case 2 parameters since there are no headers
            if self.writefile_dir_var.get().endswith("case2"):
                data['TEs'] = [5040.0, 13040.0]
                data['rbw'] = 1055.0
                data['PE_dir'] = '-y'

            print("Starting Fieldmapping Pipeline...")
            fm_calc_main(data)
            messagebox.showinfo("Finished", "B0 Fieldmapping pipeline finished successfully!")

        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred during execution:\n{e}")
        finally:
            self.deiconify()

def main():
    app = FMCallerApp()
    app.mainloop()

if __name__ == '__main__':
    main()
