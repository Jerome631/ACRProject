
%% High-Contrast Spatial Resolution

%  This test assesses the scanners ability to resolve small objects when
%  the contrast-to-noise ratio is high enough that it does not limit that
%  ability.

%%
close all
clear all 
clc

[pathname,filename]=uiputfile('*.xls','Please select file to write results to');
file=strcat(filename,pathname);

ButtonName = questdlg('What series?', ...
                         'Spatial Resolution', ...
                         'ACR T1 series', 'ACR T2 series', 'ACR T1 series');

if ButtonName=='ACR T1 series'
    cell1='B19';
    cell2='B20';
elseif ButtonName=='ACR T2 series'
    cell1='B11';
    cell2='B12';
end

%%
[filename,pathname]=uigetfile('*.dcm','Select Slice 1');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);
I = dicomread(info);
I=double(I);
figure(1), imshow(I, []);

width=double(info.Width);
f=(width/256);
rect=[60*f 150*f 130*f 50*f];
I2=imcrop(I, rect);
I3=imresize(I2,3);
pause(2)
figure(1), imshow(I3,[]);
imcontrast
a=('Adjust the contrast as required. Use the upper left array to determine the horizontal resolution and the lower right array to determine the vertical resolution. Strike any key when the resolution has been determined.');
msgbox(a,'MESSAGE')
pause
%% 
prompt={'Enter the horizontal resolution:','Enter the vertical resolution:'};
name='Spatial Resolution Results';
answer=inputdlg(prompt,name);
close 

horiz=str2double(answer{1});
vert=str2double(answer{2});

success1=xlswrite(file,horiz,ButtonName,cell1);
success2=xlswrite(file,vert,ButtonName,cell2);
if success1==1 && success2==1
    b='The results have been successfully written to Excel.';
else
    b='Error: Results have NOT been written to Excel.';
end

msgbox(b, 'RESULTS');
pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA
