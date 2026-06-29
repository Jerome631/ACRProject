%% GEOMETRIC ACCURACY

close all
clear all
clc

%% LOCALIZER
[pathname,filename]=uiputfile('*.xls','Select file to write results to:');
file=strcat(filename,pathname);

msgbox('This test should only be performed on the ACR T1 series','GEOMETRIC ACCURACY');

[filename,pathname]=uigetfile('*.dcm','Select Localizer Image');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);
I = dicomread(info);
I=double(I);

figure(1), imshow(I, []), title('Original Image');
pause(1)

bw=edge(I, 100);
figure(1), imshow(bw,[])

[u,v]=find(bw==1);
Nbin=max(u)-min(u);
figure(2), hist(u, Nbin);

a=hist(u,Nbin);
[y]=find(a>(max(a)/2));
width=double(info.Width);
f=(width/250);
dist=(y(2)-y(1))/f;

success1=xlswrite(file,dist,'ACR T1 series','B10');
a=num2str(dist);
a=strcat(a, ' mm.');
b=('The Localizer end-to-end length is....');
b=strcat(b,a);
c=(' It should be 148mm +/- 2mm. ');
c=strcat(b,c);
if success1==1
    d=(' The result has been successfully written to Excel.');
else
    d=(' Error: The result has not been written to Excel.');
end
d=strcat(c,d);
msgbox(d,'RESULT')

%% SLICE 1
[filename,pathname]=uigetfile('*.dcm','Select Slice 1:');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);
I2= dicomread(info);
width=double(info.Width);
f=(width/250);

I2=double(I2);
rect=[round(10*f) round(10*f) (width-round(20*f)) (width-round(20*f))];
I2=imcrop(I2,rect);
figure(1), imshow(I2, []);
pause(1)
bw2=edge(I2);
figure(1), imshow(bw2,[])
impixelinfo
hold on
[u2,v2]=find(bw2==1);
maxy2=max(u2);
miny2=min(u2);
midpty=(miny2+((maxy2-miny2)/2))
maxx2=max(v2);
minx2=min(v2);
midptx=(minx2+((maxx2-minx2)/2))
lineyv=linspace(miny2, maxy2)
linexv=(ones(size(lineyv)))*(midptx);
figure(1), plot(linexv, lineyv, 'r','LineWidth',2)
linexh=linspace(minx2, maxx2)
lineyh=(ones(size(linexh)))*(midpty);
figure(1), plot(linexh, lineyh, 'r','LineWidth',2)
hold off
disttopbotSlice1=(maxy2-miny2)/f;
success2=xlswrite(file,disttopbotSlice1,'ACR T1 series','B12');

distleftrightSlice1=(maxx2-minx2)/f;
success3=xlswrite(file,distleftrightSlice1,'ACR T1 series','C12');

a1=num2str(disttopbotSlice1);
a1=strcat(a1, ' mm.');
a2=num2str(distleftrightSlice1);
a2=strcat(a2, ' mm.');
b1=('The vertical diameter of Slice 1 is....');
b1=strcat(b1,a1);
b2=('The horizontal diameter of Slice 1 is....');
b2=strcat(b2,a2);
c=(' The diameter should be 190 mm +/- 2 mm. ');
c=strcat(b1,b2,c);
if success2==1 && success3==1
    d=(' Results have been successfully written to Excel.');
else
    d=(' Error: Results have not been written to Excel.');
end
d=strcat(c,d);
msgbox(d,'RESULT')

%% SLICE 5

[filename,pathname]=uigetfile('*.dcm','Select Slice 5:');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);
I3= dicomread(info);
I3=double(I3);
I3=imcrop(I3,rect);
figure(1), imshow(I3, []);
pause(1)
bw3=edge(I3);
figure(1), imshow(bw3,[])
pause(1)
hold on
[u3,v3]=find(bw3==1);
maxy3=max(u3);
miny3=min(u3);
midpty=(miny3+((maxy3-miny3)/2))
maxx3=max(v3);
minx3=min(v3);
midptx=(minx3+((maxx3-minx3)/2))
lineyv=linspace(miny3, maxy3)
linexv=(ones(size(lineyv)))*(midptx);
figure(1), plot(linexv, lineyv, 'r','LineWidth',2)
linexh=linspace(minx3, maxx3)
lineyh=(ones(size(linexh)))*(midpty);
figure(1), plot(linexh, lineyh, 'r','LineWidth',2)
hold off

disttopbotSlice5=(maxy3-miny3)/f;
success4=xlswrite(file,disttopbotSlice5,'ACR T1 series','B14');

distleftrightSlice5=(maxx3-minx3)/f;
success5=xlswrite(file,distleftrightSlice5,'ACR T1 series','C14');


I4=imrotate(I3,45,'bilinear');

bw4=edge(I4);
figure(1), imshow(bw4,[])
pause(1)
hold on
[u4,v4]=find(bw4==1);
maxy4=max(u4);
miny4=min(u4);
midpty=(miny4+((maxy4-miny4)/2))
maxx4=max(v4);
minx4=min(v4);
midptx=(minx4+((maxx4-minx4)/2))
lineyv=linspace(miny4, maxy4)
linexv=(ones(size(lineyv)))*(midptx);
figure(1), plot(linexv, lineyv, 'r','LineWidth',2)
linexh=linspace(minx4, maxx4)
lineyh=(ones(size(linexh)))*(midpty);
figure(1), plot(linexh, lineyh, 'r','LineWidth',2)
hold off
distdiag1=(maxx2-minx2)/f;
success6=xlswrite(file,distdiag1,'ACR T1 series','D14');
distdiag2=(maxy2-miny2)/f;
success7=xlswrite(file,distdiag2,'ACR T1 series','E14');


av1=num2str(disttopbotSlice5);
av1=strcat(av1, ' mm.');
ah1=num2str(distleftrightSlice1);
ah1=strcat(ah1, ' mm.');
bv1=('The vertical diameter of Slice 5 is....');
bv1=strcat(bv1,av1);
bh1=('The horizontal diameter of Slice 5 is....');
bh1=strcat(bh1,ah1);

ad1=num2str(distdiag1);
ad1=strcat(ad1, ' mm.');
ad2=num2str(distdiag2);
ad2=strcat(ad2, ' mm.');
bd1=('The first diagonal diameter of Slice 5 is....');
bd1=strcat(bd1,ad1);
bd2=('The second diagonal diameter of Slice 5 is....');
bd2=strcat(bd2,ad2);



c=(' The diameter should be 190 mm +/- 2 mm. ');
c=strcat(bv1, bh1, bd1, bd2, c);
if success4==1 && success5==1 && success6==1 && success7==1
    d=(' Results have been successfully written to Excel.');
else
    d=(' Error: Results have not been written to Excel.');
end
d=strcat(c,d);
msgbox(d,'RESULT')

pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA
