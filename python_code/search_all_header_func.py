import os

def search_all_header_func(filename, searchstring):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Could not find file {filename}")
        
    scan_parameter_value = '0'
    with open(filename, 'r', encoding='latin1') as f:
        for line in f:
            tline = line.strip('\n\r')
            if searchstring in tline:
                # parameters are separated by ' = ' or ': '
                if ' = ' in tline:
                    param_begin = tline.find(' = ') + 3
                elif ': ' in tline:
                    param_begin = tline.find(': ') + 2
                else:
                    param_begin = len(tline)
                
                scan_parameter_value = tline[param_begin:].strip()
                break
                
    if scan_parameter_value == '0':
        scan_parameter_value = '-1'
        
    return scan_parameter_value
