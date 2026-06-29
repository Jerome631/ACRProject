def unix_format(dos_style_string):
    unix_style_string = dos_style_string
    unix_style_string = unix_style_string.replace('\\', '/')
    unix_style_string = unix_style_string.replace('C:', '/c')
    unix_style_string = unix_style_string.replace('D:', '/d')
    unix_style_string = unix_style_string.replace('E:', '/e')
    unix_style_string = unix_style_string.replace('F:', '/f')
    unix_style_string = unix_style_string.replace('G:', '/g')
    if ' ' in dos_style_string:
        unix_style_string = unix_style_string.replace(' ', '\\ ')
    return unix_style_string
