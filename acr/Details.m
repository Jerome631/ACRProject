close all
clear all 
clc
%%
[pathname,filename]=uiputfile('*.xls','Select file to write results to');
file=strcat(filename,pathname);
%%
prompt={'Centre:','System:' 'Software:', 'Year of Manufacture:','Serial Number:', 'Tester(s):', 'Date:'};
name='Test Details';
answer=inputdlg(prompt,name);

prompt1={'Magnetic Field Strength:','Resonant Frequency:', 'RF Amplifier Voltage:'};
name1='System Parameters';
answer1=inputdlg(prompt1,name1);

success1=xlswrite(file,answer(1),'ACR T1 Series','B1');
success2=xlswrite(file,answer(2),'ACR T1 Series','D1');
success3=xlswrite(file,answer(3),'ACR T1 Series','F1');
success4=xlswrite(file,answer(4),'ACR T1 Series','B2');
success5=xlswrite(file,answer(5),'ACR T1 Series','D2');
success6=xlswrite(file,answer(6),'ACR T1 Series','H2');
success7=xlswrite(file,answer(7),'ACR T1 Series','F2');
success8=xlswrite(file,answer1(1),'ACR T1 Series','B5');
success9=xlswrite(file,answer1(2),'ACR T1 Series','D5');
success10=xlswrite(file,answer1(3),'ACR T1 Series','F5');
%%
MRI_QA
