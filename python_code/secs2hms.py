import math

def secs2hms(time_in_secs):
    time_string = ''
    nhours = 0
    nmins = 0
    if time_in_secs >= 3600:
        nhours = math.floor(time_in_secs / 3600)
        if nhours > 1:
            hour_string = ' hours, '
        else:
            hour_string = ' hour, '
        time_string = f"{nhours}{hour_string}"
    
    if time_in_secs >= 60:
        nmins = math.floor((time_in_secs - 3600 * nhours) / 60)
        if nmins > 1:
            minute_string = ' mins, '
        else:
            minute_string = ' min, '
        time_string = f"{time_string}{nmins}{minute_string}"
        
    nsecs = time_in_secs - 3600 * nhours - 60 * nmins
    time_string = f"{time_string}{nsecs:2.1f} secs"
    return time_string
