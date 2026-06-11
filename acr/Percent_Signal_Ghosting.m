% Program to calculate Percent-Signal Ghosting
close all hidden
clear all 
clc

msgbox('This test should only be performed on the ACR T1 series','PERCENT-SIGNAL GHOSTING');

[pathname,filename]=uiputfile('*.xls','Please select files to write results to');
file=strcat(filename,pathname);
% Read in and display DICOM image 
[filename,pathname]=uigetfile('*.dcm','Select Slice 7');
pathname=char(pathname)
cd (pathname)
info=dicominfo(filename);
I = dicomread(info);
I=double(I);
figure(1), imshow(I, []);
pause(1)
% Create averaging filters of required size (length width ratio 4:1 and 
% total area of 10 cm^2)

width=double(info.Width);
f=(width/250);

% Threshold image to discount background and find midpont of circle
[x,y]=find(I>500);
maxx=max(x);
minx=min(x);
maxy=max(y);
miny=min(y);
midptx=round(minx+((maxx-minx)/2));
midpty=round(miny+((maxy-miny)/2));

h=fspecial('average', [(round(16*f)) (round(64*f))]);
Ifilt=imfilter(I, h);
figure(1), imshow(Ifilt, []);
pause(1)
c3=[(midpty-(round((64*f)/2))) (midpty-(round((64*f)/2))) (midpty+(round((64*f)/2))) (midpty+(round((64*f)/2)))];
r3=[((minx/2)-(round((16*f)/2))) ((minx/2)+(round((16*f)/2))) ((minx/2)+(round((16*f)/2))) ((minx/2)-(round((16*f)/2)))];
BW3 = roipoly(I,c3,r3);
figure(1), imshow(BW3)
pause(1)

c4=[(midpty-(round((64*f)/2))) (midpty-(round((64*f)/2))) (midpty+(round((64*f)/2))) (midpty+(round((64*f)/2)))];
r4=[(width-((width-maxx)/2)-(round((16*f)/2))) (width-((width-maxx)/2)+(round((16*f)/2))) (width-((width-maxx)/2)+(round((16*f)/2))) (width-((width-maxx)/2)-(round((16*f)/2)))];
BW4 = roipoly(I,c4,r4);
figure(1), imshow(BW4)
pause(1)


h2=fspecial('average', [round(64*f) round(16*f)]);
Ifilt2=imfilter(I, h2);
figure(1), imshow(Ifilt2, []);
pause(1)
c=[((miny/2)-(round((16*f)/2))) ((miny/2)+(round((16*f)/2))) ((miny/2)+(round((16*f)/2))) ((miny/2)-(round((16*f)/2)))];
r=[(midptx-(round((64*f)/2))) (midptx-(round((64*f)/2))) (midptx+(round((64*f)/2))) (midptx+(round((64*f)/2)))];
BW = roipoly(I,c,r);
figure(1), imshow(BW)
pause(1)

c2=[(width-((width-maxy)/2)-(round((16*f)/2))) (width-((width-maxy)/2)+(round((16*f)/2))) (width-((width-maxy)/2)+(round((16*f)/2))) (width-((width-maxy)/2)-(round((16*f)/2)))];
r2=[(midptx-(round((64*f)/2))) (midptx-(round((64*f)/2))) (midptx+(round((64*f)/2))) (midptx+(round((64*f)/2)))];
BW2 = roipoly(I,c2,r2);
figure(1), imshow(BW2)
pause(1)
BW=BW+BW2+BW3+BW4;
BW=BW.*800;
J=I+BW;

figure(1), imshow(J,[])
pause(1)
% Create circular averaging filter of required size (195-205 cm^2)
h3=fspecial('disk', round(79*f));
Ifilt3=imfilter(I, h3);
figure(1), imshow(Ifilt3, []);
pause(1)


% Find mean pixel value for large circular ROI
largeROI=Ifilt3(midptx,midpty);

% Select suitable points on the top, bottom, left and right of the image
% and apply suitable averaging filter

xtop=midpty;
ytop=round(minx/2);
top=Ifilt(ytop,xtop);

xbottom=midpty;
ybottom=round(width-((width-maxx)/2));
bottom=Ifilt(ybottom,xbottom);

xleft=round(miny/2);
yleft=midptx;
left=Ifilt2(yleft,xleft);

xright=round(maxx+((256*f-maxx)/2));
yright=midptx;
right=Ifilt2(yright,xright);

% Calculate Ghosting Ratio
ghostingratio=abs(((top+bottom)-(left+right))/(2*largeROI));

success=xlswrite(file,ghostingratio,'ACR T1 series','B67');

dist=sqrt(((y-midpty).^2)+((x-midptx).^2));
[u]=find(dist<79*f);
pixels=length(u);
x1=x(u);
y1=y(u);
i=1;
for i=1:pixels
    
    J(x1(i),y1(i))=1;
    i=i+1;
end
figure(1), imshow(J, [])
%%
if success==1
    s=('. The result has been successfully written to Excel.');
else
    s=('Error: The result has not been written to Excel.');
end
a=num2str(ghostingratio);
b=('The Ghosting Ratio is....');
c=strcat(b,a,s);
msgbox(c,'RESULT')

pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA
