
%% Slice Position Accuracy

%  This test assesses the accuracy with which slices can be prescribed at
%  specific locations using the localizer image for positional reference.
%%
close all
clear all
clc

[pathname,filename]=uiputfile('*.xls','Save As');
file=strcat(filename,pathname);

ButtonName = questdlg('What series?', ...
                         'Slice Position Accuracy', ...
                         'ACR T1 series', 'ACR T2 series', 'ACR T1 series');

if ButtonName=='ACR T1 series'
    cell1='B56'
    cell2='B57'
elseif ButtonName=='ACR T2 series'
    cell1='B48'
    cell2='B49'
end
%%
[filename,pathname]=uigetfile('*.dcm','Select Slice 1');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);

I = dicomread(info);
I=double(I);
figure(1), imshow(I, []);
pause(1)
close
width=double(info.Width);
f=(width/250);

rect=[round(100*f) round(20*f) round(40*f) round(60*f)];
I2=imcrop(I, rect);
I3=imresize(I2,3);
figure(1), imshow(I3,[])
imcontrast

a=('Adjust the contrast so that the ends of the vertical bars are well defined-not fuzzy. Click on Figure 1 (to make sure it is the active image) and strike any key when finished. Use the mouse to click on the bottom of each bar and press enter. ');
msgbox(a,'MESSAGE')
pause
[C1,R1,P1]=impixel;
close


difference1=abs((R1(1)-R1(2))*(250/(256*f)))

info11=dicominfo(uigetfile('*.dcm','Select Slice 11'));
I11 = dicomread(info11);
I11=double(I11);
figure(1), imshow(I11, []);
I12=imcrop(I11, rect);
I13=imresize(I12,3);
figure(1), imshow(I13,[]);
imcontrast
a=('Adjust the contrast as required. Click on Figure 1 (to make sure it is the active image) and strike any key when finished.');
msgbox(a,'MESSAGE')
pause
[C2,R2,P2]=impixel;
close
difference2=abs((R2(1)-R2(2))*(250/(256*f)));

success1=xlswrite(file,difference1, ButtonName,cell1);
success2=xlswrite(file,difference2,ButtonName,cell2);
if success1==1 && success2==1
    b=(' The results have been successfully written to Excel.');
else
    b=('Error: The results have not been written to Excel.');
end

diff1=num2str(difference1);
diff11=num2str(difference2);
c=strcat('Slice 1: The absolute bar length difference is...',diff1,' mm. Slice 11: The absolute bar length difference is...',diff11,' mm. Note: The absolute bar length difference should be < 5 mm.',b);
msgbox(c,'RESULT')

pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA


