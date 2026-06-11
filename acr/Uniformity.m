
%% Image Intensity Uniformity
%  The image intensity uniformity test measures the uniformity of the image
%  intensity over a large water-only region of the phantom lying near the
%  middle of the imaged volume and thus near the middle of the head coil.
%  The high-signal and low-signal levels within this large, physically
%  uniform, water-only region of the phantom are measured for the ACR T1
%  and T2 series.

%%
close all
clear all 
clc

[pathname,filename]=uiputfile('*.xls','Save As');
file=strcat(filename,pathname);

ButtonName = questdlg('What series?', ...
                         'Uniformity', ...
                         'ACR T1 series', 'ACR T2 series', 'ACR T1 series');

if ButtonName=='ACR T1 series'
    cell='B62'
    
elseif ButtonName=='ACR T2 series'
    cell='B54'
    
end

%% Original Phantom Image 
%  The image at slice 7 of the ACR phantom was read into MATLAB, converted 
%  to class |double| for further processing and is displayed in Figure 1.
[filename,pathname]=uigetfile('*.dcm','Select Slice 7');
pathname=char(pathname);
cd (pathname)

info=dicominfo(filename);
I = dicomread(info);
I=double(I);
figure('Name','Original Image - Slice 7','NumberTitle','off'), imshow(I, []);
xlabel({'Figure 1. Original Image - Slice 7 of ACR Phantom'});

width=double(info.Width);
f=(width/250); %pixels/mm
%% Filtered Phantom Image
%  A circular averaging filter was applied to the original image. This 
%  essentially defined small regions of interest (1cm^2) throughout the
%  image and computed the mean pixel value for these ROI's. 
%  The resulting image is displayed in Figure 2.
h=fspecial('disk', (6*f));
Ifilt=imfilter(I, h);
figure('Name','Filtered Image','NumberTitle','off'), imshow(Ifilt, []);
xlabel({'Figure 2. Filtered Image - 1cm^2 Circular Averaging Filter'});
%% Large Region of Interest
%  The image was thresholded in order to discount the background 
%  pixels using a threshold pixel value of 500.  The co-ordinates of all non-background pixels were found 
%  and the midpoint of the circle was computed. Only pixels within 7.3 cm 
%  of the mid-point were processed further thus defining a 200 cm^2 region 
%  of interest at the centre of the water-only region of the phantom. 
%  This region of interest is displayed in Figure 4.


[x,y]=find(I>500);
maxx=max(x);
minx=min(x);
maxy=max(y);
miny=min(y);
midptx=minx+((maxx-minx)/2);
midpty=miny+((maxy-miny)/2);
dist=sqrt(((y-midpty).^2)+((x-midptx).^2));
[u]=find(dist<(73*f));
pixels=length(u);
x1=x(u);
y1=y(u);
i=1;
for i=1:pixels
    intensity(i,1)=Ifilt(x1(i),y1(i));
    i=i+1;
end

%% Percent Integral Uniformity Result
%  The maximum and minimum signal levels within the large ROI were found. 



high=max(intensity);
low=min(intensity);

%%
[u]=find(dist<(79*f));
pixels=length(u);
x1=x(u);
y1=y(u);
i=1;
for i=1:pixels
    I(x1(i),y1(i))=0;
    i=i+1;
end
figure('Name','ROI','NumberTitle','off'), imshow(I, []);
xlabel({'Figure 4. Black disc shows selected 200cm^2 region of interest'});
%%
%  The Percent Integral Uniformity was calculated from
% 
% $$PIU=100*(1-((high-low)/(high+low)))$$
% 
%  where high is the maximum signal value and low is the minimum signal
%  value.
PIU=100*(1-((high-low)/(high+low)))

success=xlswrite(file,PIU,ButtonName,cell)
if success==1
    s=(' The result has been successfully written to Excel.');
else
    s=('Error: The result has not been written to Excel.');
end
a=num2str(PIU);
b=('The uniformity is....');
c=strcat(b,a, '%. Note: The uniformity should be >= 87.5%.',s);
msgbox(c,'RESULT')

pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA


    
