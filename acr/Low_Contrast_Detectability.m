
%% Low-Contrast Object Detectability

%  This test assesses the extent to which objects of low contrast are
%  discernable in the images.

%%
close all
clear all 
clc

[pathname,filename]=uiputfile('*.xls','Please select file to write results to');
file=strcat(filename,pathname);

ButtonName = questdlg('What series?', ...
                         'Signal-Noise Ratio', ...
                         'ACR series', 'Site series','ACR series');
                     h=strcmp(ButtonName, 'ACR series')
                     if h==1
                     ButtonName = questdlg('What series?', ...
                         'Signal-Noise Ratio', ...
                         'ACR T1 series', 'ACR T2 series','ACR T1 series'); 
                     else
                     ButtonName = questdlg('What series?', ...
                         'Signal-Noise Ratio', ...
                         'Site T1 series', 'Site T2 series','Site T1 series');
                     end
h=strcmp(ButtonName, 'ACR T1 series')
if h==1
   cell1='B104';
   cell2='B105';
   cell3='B106';
   cell4='B107';
   cell5='B109';
else
    h2=strcmp(ButtonName, 'ACR T2 series')
    if h2==1
       cell1='B91';
   cell2='B92';
   cell3='B93';
   cell4='B94';
   cell5='B96';
    else
        h3=strcmp(ButtonName, 'Site T1 series')
    if  h3==1
       cell1='B37';
   cell2='B38';
   cell3='B39';
   cell4='B40';
   cell5='B42';
    else
        h4=strcmp(ButtonName, 'Site T2 series')
    if  h4==1
        cell1='B37';
   cell2='B38';
   cell3='B39';
   cell4='B40';
   cell5='B42';
    end 
    end  
    end
    end

%%

[filename,pathname]=uigetfile('*.dcm','Select Slice 11');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);
I = dicomread(info);
I=double(I);
figure(1), imshow(I, []);
imcontrast
a=('Adjust the contrast as required. Strike any key when finished');
msgbox(a,'MESSAGE')
pause
prompt={'How many complete spokes are resolved?'};
name='Low-Contrast Detectability Results';
answer1=inputdlg(prompt,name);
answer1=str2double(answer1);
success1=xlswrite(file,answer1,ButtonName,cell1)
close 

%%
[filename,pathname]=uigetfile('*.dcm','Select Slice 10');
pathname=char(pathname)
cd (pathname)

info2=dicominfo(filename);
I2 = dicomread(info2);
I2=double(I2);
figure(2), imshow(I2, []);
imcontrast
a=('Adjust the contrast as required. Strike any key when finished');
msgbox(a,'MESSAGE')
pause
prompt={'How many complete spokes are resolved?'};
name='Low-Contrast Detectability Results';
answer2=inputdlg(prompt,name);
answer2=str2double(answer2);
success2=xlswrite(file,answer2,ButtonName,cell2)
close 
%%
[filename,pathname]=uigetfile('*.dcm','Select Slice 9');
pathname=char(pathname)
cd (pathname)

info3=dicominfo(filename);
I3 = dicomread(info3);
I3=double(I3);
figure(3), imshow(I3, []);
imcontrast
a=('Adjust the contrast as required. Strike any key when finished');
msgbox(a,'MESSAGE')
pause
prompt={'How many complete spokes are resolved?'};
name='Low-Contrast Detectability Results';
answer3=inputdlg(prompt,name);
answer3=str2double(answer3);
success3=xlswrite(file,answer3,ButtonName,cell3)
close 
%%
[filename,pathname]=uigetfile('*.dcm','Select Slice 8');
pathname=char(pathname)
cd (pathname)

info4=dicominfo(filename);
I4 = dicomread(info4);
I4=double(I4);
figure(4), imshow(I4, []);
imcontrast
a=('Adjust the contrast as required. Strike any key when finished');
msgbox(a,'MESSAGE')
pause
prompt={'How many complete spokes are resolved?'};
name='Low-Contrast Detectability Results';
answer4=inputdlg(prompt,name)
answer4=str2double(answer4);
success4=xlswrite(file,answer4,ButtonName,cell4)
close 
%%
total=answer1+answer2+answer3+answer4;
success5=xlswrite(file,total,ButtonName,cell5)
%%
if success1==1 && success2==1 && success3==1 && success4==1 && success5==1
    b='The results have been successfully written to Excel.';
else
    b='Error: Results have NOT been written to Excel.';
end

msgbox(b, 'RESULTS');

pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA
