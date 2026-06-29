%% Slice Thickness Accuracy

close all
clear all 
clc
[pathname,filename]=uiputfile('*.xls','Save As');
file=strcat(filename,pathname);

ButtonName = questdlg('What series?', ...
                         'Spatial Resolution', ...
                         'ACR T1 series', 'ACR T2 series', 'ACR T1 series');

if ButtonName=='ACR T1 series'
    cell='B25';
    elseif ButtonName=='ACR T2 series'
    cell='B17';
   
end
%%
[filename,pathname]=uigetfile('*.dcm','Select Slice 1');
pathname=char(pathname)
cd (pathname)

info=dicominfo(filename);
I = dicomread(info);
I=double(I);

width=double(info.Width);
f=(width/250); %pixels/mm

rect=[round(10*f) round(10*f) (width-round(20*f)) (width-round(20*f))];
I=imcrop(I, rect);
figure('Name','Original Image','NumberTitle','off'), imshow(I, []);
xlabel({'Figure 1. Original Image - Slice 1 of ACR Phantom'});

%%
bw=edge(I);
[x,y]=find(bw==1);
maxx=max(x);
minx=min(x);
midptx=round((maxx+minx)/2);
maxy=max(y);
miny=min(y);
midpty=round((maxy+miny)/2);

rect=[(midpty-(f*60)) (midptx-(f*10)) (f*120) (f*20)];
I2=imcrop(I, rect);
figure(2), imshow(I2,[])
%%
bw=edge(I2);
[x,y]=find(bw==1);
maxx=max(x);
minx=min(x);
midptx=round((maxx+minx)/2);

ramp1=midptx-(5);
ramp2=midptx+(5);

a1=ramp1;
a2=ramp1+1;
a3=ramp1+2;
a4=ramp1+3;
a5=ramp1+4;

b1=ramp2;
b2=ramp2-1;
b3=ramp2-2;
b4=ramp2-3;
b5=ramp2-4;

h=fspecial('disk',(f*2));
I2smooth=imfilter(I2,h);

a1a=I2smooth(a1,:);
a2a=I2smooth(a2,:);
a3a=I2smooth(a3,:);
a4a=I2smooth(a4,:);
a5a=I2smooth(a5,:);

b1a=I2smooth(b1,:);
b2a=I2smooth(b2,:);
b3a=I2smooth(b3,:);
b4a=I2smooth(b4,:);
b5a=I2smooth(b5,:);

a=[ a3a
    a4a
    a5a];

b=[ b3a
    b4a
    b5a];

a=mean(a);
figure('Name','FWHM curves','NumberTitle','off'), plot(a,'LineWidth',2,'Color',[.6 0 0])
xlabel({'Pixel Number'});
ylabel({'Pixel Value'});
hold on

b=mean(b);
plot(b,'LineWidth',2,'Color',[0 0 .6])
hold off
grid on
legend('Bottom Ramp', 'Top Ramp');
%%

%I2(a1,:)=1400;
%I2(a2,:)=1400;
I2(a3,:)=1400;
I2(a4,:)=1400;
I2(a5,:)=1400;

%I2(b1,:)=1400;
%I2(b2,:)=1400;
I2(b3,:)=1400;
I2(b4,:)=1400;
I2(b5,:)=1400;


I3=imresize(I2,3);
figure('Name', 'Slice Thickness Insert', 'NumberTitle', 'off'),imshow(I3,[]);
xlabel({'Figure 2. Magnified Image of Slice Thickness Insert showing ramp area selected'});

%%


% Full-Width at Half-Maximum (FWHM) of the waveform y(x)
% The FWHM result in 'width' will be in units of 'x'
%
%
% Rev 1.2, April 2006 (Patrick Egan)

x=1:length(a);
a = a / max(a);
N = length(a);
lev50 = 0.5;
if a(1) < lev50                  % find index of center (max or min) of pulse
    [garbage,centerindex]=max(a);
else
    [garbage,centerindex]=min(a==a);
end


i = 2;
while sign(a(i)-lev50) == sign(a(i-1)-lev50)
    i = i+1;
end                                   %first crossing is between v(i-1) & v(i)
interp = (lev50-a(i-1)) / (a(i)-a(i-1));
tlead = x(i-1) + interp*(x(i)-x(i-1));
i = centerindex+1;                    %start search for next crossing at center
while ((sign(a(i)-lev50) == sign(a(i-1)-lev50)) & (i <= N-1))
    i = i+1;
end
if i ~= N
    Ptype = 1;  
    interp = (lev50-a(i-1)) / (a(i)-a(i-1));
    ttrail = x(i-1) + interp*(x(i)-x(i-1));
    width1 = ttrail - tlead;
else
    Ptype = 2; 
    ttrail = NaN;
    width1 = NaN;
end

%%

%
% Full-Width at Half-Maximum (FWHM) of the waveform y(x)
% The FWHM result in 'width' will be in units of 'x'
%
%
% Rev 1.2, April 2006 (Patrick Egan)
x=1:length(b);

b = b / max(b);
N = length(b);
lev50 = 0.5;
if b(1) < lev50                  % find index of center (max or min) of pulse
    [garbage,centerindex]=max(b);
else
    [garbage,centerindex]=min(b==b);
end
i = 2;
while sign(b(i)-lev50) == sign(b(i-1)-lev50)
    i = i+1;
end                                   %first crossing is between v(i-1) & v(i)
interp = (lev50-b(i-1)) / (b(i)-b(i-1));
tlead = x(i-1) + interp*(x(i)-x(i-1));
i = centerindex+1;                    %start search for next crossing at center
while ((sign(b(i)-lev50) == sign(b(i-1)-lev50)) & (i <= N-1))
    i = i+1;
end
if i ~= N
    Ptype=1;
    interp = (lev50-b(i-1)) / (b(i)-b(i-1));
    ttrail = x(i-1) + interp*(x(i)-x(i-1));
    width2 = ttrail - tlead;
else
    Ptype = 2; 
    ttrail = NaN;
    width2 = NaN;
end

%%
width1=width1*(250/width);
width2=width2*(250/width);
slice_thickness=0.2*((width1*width2)/(width1+width2));

% prompt2={'Enter name of results file:'};
% name2='Excel Filename';
% numlines=1;
% defaultanswer={'C:\Documents and Settings\colletteoneill\My Documents\MATLAB\QA_ACR_MRI\RESULTS.xls'};
% 
% options.Resize='on';
%  
% answer2=inputdlg(prompt2,name2,numlines,defaultanswer,options);
% s=char(answer2);

success1=xlswrite(file,slice_thickness,ButtonName,cell);
if success1==1
    b=(' The result has been successfully written to Excel.');
else
    b=('Error: The result has not been written to Excel.');
end

st=num2str(slice_thickness);
c=strcat('The slice thickness is...',st,' mm. Note: The slice thickness should be 5 mm +/- 0.7 mm.',b);
msgbox(c,'RESULT')

pathname = 'C:\Users\0116574s\Documents\MATLAB\acr';
cd (pathname)
MRI_QA

