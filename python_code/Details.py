import os
from matlab_compat import uiputfile, inputdlg, xlswrite

def main():
    fname, pathname = uiputfile('*.xlsx;*.xls', 'Select file to write results to')
    if not fname:
        print("No file selected. Exiting.")
        return
    file_path = os.path.join(pathname, fname)
    
    prompt = ['Centre:', 'System:', 'Software:', 'Year of Manufacture:', 'Serial Number:', 'Tester(s):', 'Date:']
    name = 'Test Details'
    answer = inputdlg(prompt, name)
    if not answer or len(answer) < len(prompt):
        return
        
    prompt1 = ['Magnetic Field Strength:', 'Resonant Frequency:', 'RF Amplifier Voltage:']
    name1 = 'System Parameters'
    answer1 = inputdlg(prompt1, name1)
    if not answer1 or len(answer1) < len(prompt1):
        return
        
    sheet_name = 'ACR T1 Series'
    xlswrite(file_path, answer[0], sheet_name, 'B1')
    xlswrite(file_path, answer[1], sheet_name, 'D1')
    xlswrite(file_path, answer[2], sheet_name, 'F1')
    xlswrite(file_path, answer[3], sheet_name, 'B2')
    xlswrite(file_path, answer[4], sheet_name, 'D2')
    xlswrite(file_path, answer[5], sheet_name, 'H2')
    xlswrite(file_path, answer[6], sheet_name, 'F2')
    
    xlswrite(file_path, answer1[0], sheet_name, 'B5')
    xlswrite(file_path, answer1[1], sheet_name, 'D5')
    xlswrite(file_path, answer1[2], sheet_name, 'F5')
    
    print("Details successfully written.")
    
    # Relaunch the QA GUI
    if __name__ == '__main__':
        try:
            import MRI_QA
            MRI_QA.main()
        except ImportError:
            pass

if __name__ == '__main__':
    main()
