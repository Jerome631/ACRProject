import os

def search_text_header_func(filename, searchstring):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Could not find file {filename}")
        
    start_looking = False
    scan_parameter_value = '0'
    with open(filename, 'r', encoding='latin1') as f:
        for line in f:
            tline = line.strip('\n\r')
            if '### ASCCONV BEGIN ###' in tline:
                start_looking = True
                continue
            if start_looking:
                if searchstring in tline:
                    if ' = ' in tline:
                        param_begin = tline.find(' = ') + 3
                    else:
                        param_begin = len(tline)
                    scan_parameter_value = tline[param_begin:].strip()
                    break
                if '### ASCCONV END ###' in tline:
                    scan_parameter_value = '-1'
                    break
                    
    if scan_parameter_value == '0':
        scan_parameter_value = '-1'
        
    return scan_parameter_value
