import sys
import os
import tkinter as tk
from tkinter import font as tkfont

# Import the test modules
import test_geom_acc
import Slice_Position_Accuracy
import SliceThicknessFWHM
import Uniformity
import SNR
import Percent_Signal_Ghosting
import Low_Contrast_Detectability
import High_Contrast_Spatial_Res
import Details

class QAApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("MRI Quality Assurance Tool")
        self.geometry("620x580")
        self.configure(bg="#0f172a") # Slate 900
        self.resizable(False, False)
        
        # Styles
        self.title_font = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.btn_font = tkfont.Font(family="Helvetica", size=11, weight="bold")
        self.footer_font = tkfont.Font(family="Helvetica", size=9)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header container
        header_frame = tk.Frame(self, bg="#0f172a")
        header_frame.pack(fill="x", pady=25)
        
        title_label = tk.Label(
            header_frame, 
            text="ACR MRI PHANTOM QA PIPELINE", 
            font=self.title_font, 
            fg="#3b82f6", # Blue 500
            bg="#0f172a"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame, 
            text="Select a test below to process images and record results", 
            font=self.footer_font, 
            fg="#94a3b8", # Slate 400
            bg="#0f172a"
        )
        subtitle_label.pack(pady=5)
        
        # Button Grid Frame
        grid_frame = tk.Frame(self, bg="#1e293b", bd=2, relief="groove", padx=20, pady=20) # Slate 800
        grid_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Define buttons
        tests = [
            ("Geometric Accuracy", self.run_geom_acc, 0, 0),
            ("Slice Position Accuracy", self.run_slice_pos, 0, 1),
            ("Slice Thickness (FWHM)", self.run_slice_thickness, 1, 0),
            ("Image Intensity Uniformity", self.run_uniformity, 1, 1),
            ("Signal-to-Noise Ratio (SNR)", self.run_snr, 2, 0),
            ("Percent Signal Ghosting", self.run_ghosting, 2, 1),
            ("Low-Contrast Detectability", self.run_low_contrast, 3, 0),
            ("High-Contrast Spatial Res", self.run_high_contrast, 3, 1),
        ]
        
        for text, command, row, col in tests:
            btn = self.create_button(grid_frame, text, command)
            btn.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
        # Configure columns/rows to resize equally
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        for r in range(4):
            grid_frame.rowconfigure(r, weight=1)
            
        # Bottom Actions Frame
        bottom_frame = tk.Frame(self, bg="#0f172a")
        bottom_frame.pack(fill="x", side="bottom", pady=15, padx=30)
        
        details_btn = tk.Button(
            bottom_frame,
            text="Edit Test Details",
            font=self.btn_font,
            fg="#ffffff",
            bg="#10b981", # Emerald 500
            activeforeground="#ffffff",
            activebackground="#059669",
            bd=0,
            padx=15,
            pady=8,
            command=self.run_details
        )
        details_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        exit_btn = tk.Button(
            bottom_frame,
            text="Exit Pipeline",
            font=self.btn_font,
            fg="#ffffff",
            bg="#ef4444", # Red 500
            activeforeground="#ffffff",
            activebackground="#dc2626",
            bd=0,
            padx=15,
            pady=8,
            command=self.destroy
        )
        exit_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
    def create_button(self, parent, text, command):
        btn = tk.Button(
            parent,
            text=text,
            font=self.btn_font,
            fg="#ffffff",
            bg="#3b82f6", # Blue 500
            activeforeground="#ffffff",
            activebackground="#1d4ed8", # Blue 700
            bd=0,
            relief="flat",
            padx=10,
            pady=15,
            command=command
        )
        
        # Hover animations
        def on_enter(e):
            btn['background'] = '#2563eb' # Blue 600
        def on_leave(e):
            btn['background'] = '#3b82f6'
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
        
    # Wrapper callbacks that minimize the main window during execution
    def run_test(self, test_func):
        self.withdraw()
        try:
            test_func()
        except Exception as e:
            print(f"Error running test: {e}")
        finally:
            self.deiconify()
            
    def run_geom_acc(self):
        self.run_test(test_geom_acc.main)
        
    def run_slice_pos(self):
        self.run_test(Slice_Position_Accuracy.main)
        
    def run_slice_thickness(self):
        self.run_test(SliceThicknessFWHM.main)
        
    def run_uniformity(self):
        self.run_test(Uniformity.main)
        
    def run_snr(self):
        self.run_test(SNR.main)
        
    def run_ghosting(self):
        self.run_test(Percent_Signal_Ghosting.main)
        
    def run_low_contrast(self):
        self.run_test(Low_Contrast_Detectability.main)
        
    def run_high_contrast(self):
        self.run_test(High_Contrast_Spatial_Res.main)
        
    def run_details(self):
        self.run_test(Details.main)

def main():
    app = QAApp()
    app.mainloop()

if __name__ == '__main__':
    main()
