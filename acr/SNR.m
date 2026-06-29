%% Signal to Noise Ratio
close all hidden
clear all 
clc

[pathname,filename]=uiputfile('*.xls','Select file to write results to:');
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
   cell='B99'
else
    h2=strcmp(ButtonName, 'ACR T2 series')
    if h2==1
       cell='B86'
    else
        h3=strcmp(ButtonName, 'Site T1 series')
    if  h3==1
        cell='B10'
    else
        h4=strcmp(ButtonName, 'Site T2 series')
    if  h4==1
        cell='B10'
    end 
    end  
    end
    end

%% Original Phantom Image - Slice Location 7 of ACR Phantom
%  The image was read into MATLAB, converted to class |double| for further
%  processing and displayed in Figure 1
[filename,pathname]=uigetfile('*.dcm','Select Slice 7');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);
I = dicomread(info);
I=double(I);
figure(1), imshow(I, []);
pause(1)

%% Filtered Phantom Image
%  Here we applied a circular averaging filter to our image. Our circle has
%  a radius of 80 pixels 
[x,y]=find(I>500);
maxx=max(x);
minx=min(x);
maxy=max(y);
miny=min(y);
midptx=round(minx+((maxx-minx)/2));
midpty=round(miny+((maxy-miny)/2));


%%
% Apply circular averaging filter - circle 195-205 cm^2
width=double(info.Width);
f=(width/256);

h=fspecial('disk', (round(79*f)));
Ifilt=imfilter(I, h);
figure(1), imshow(Ifilt, []);
pause(1)
% Find the mean signal intensity
intensity=Ifilt(midptx,midpty);

% Select centre point of small circular region of interest
noisex=width-(round(30*f));
noisey=width-(round(30*f));
noisex1=round(30*f);
noisey1=round(30*f);
noisex2=round(30*f);
noisey2=width-(round(30*f));
noisex3=width-(round(30*f));
noisey3=round(30*f);
% Threshold image to include only background pixels
[u,v]=find(I<500);

% Only include those pixels within 20 mm of centre of small ROI
dist=sqrt(((v-noisey).^2)+((u-noisex).^2));
dist1=sqrt(((v-noisey1).^2)+((u-noisex1).^2));
dist2=sqrt(((v-noisey2).^2)+((u-noisex2).^2));
dist3=sqrt(((v-noisey3).^2)+((u-noisex3).^2));
[w]=find(dist<round(20*f));
[w1]=find(dist1<round(20*f));
[w2]=find(dist2<round(20*f));
[w3]=find(dist3<round(20*f));
% Find the number of pixels included and the x and y co-ordinates of these 
% pixels
pixels=length(w);
pixels1=length(w1);
u1=u(w);
v1=v(w);
u2=u(w1);
v2=v(w1);
u3=u(w2);
v3=v(w2);
u4=u(w3);
v4=v(w3);

% store intensity values of these pixels in an array and set them to a high
% value to display the ROI

i=1;

for i=1:pixels
    noise3(i,1)=I(u4(i),v4(i));
    noise2(i,1)=I(u3(i),v3(i));
    noise1(i,1)=I(u2(i),v2(i));
    noise(i,1)=I(u1(i),v1(i));
    I(u1(i),v1(i))=2000;
    I(u2(i),v2(i))=2000;
    I(u3(i),v3(i))=2000;
    I(u4(i),v4(i))=2000;
    
    i=i+1;
end





% Calculate the standard deviation of the pixels
SD1=std(noise);
SD2=std(noise1);
SD3=std(noise2);
SD4=std(noise3);
SD=(SD1+SD2+SD3+SD4)/4;

% Calculate the signal to noise ratio
SignalNoiseRatio=0.655*(intensity/SD);


success=xlswrite(file,SignalNoiseRatio,ButtonName,cell);

%% 
dist=sqrt(((y-midpty).^2)+((x-midptx).^2));
[u]=find(dist<(round(79*f)));
pixels=length(u);
x1=x(u);
y1=y(u);
i=1;
for i=1:pixels
    intensity(i,1)=I(x1(i),y1(i));
    I(x1(i),y1(i))=2000;
    i=i+1;
end
figure(1), imshow(I, [])
pause(5)
close
%%
if success==1
    s=('. The result has been successfully written to Excel.');
else
    s=('Error: The result has not been written to Excel.');
end
a=num2str(SignalNoiseRatio);
b=('The Signal-Noise Ratio is....');
c=strcat(b,a,s);
msgbox(c,'RESULT')

pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA

