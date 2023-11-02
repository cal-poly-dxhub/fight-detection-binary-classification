@echo off
echo === archiver.bat ===
echo %date% %time%

set BUCKETNAME=pilot-uploads
 
set CUR_YYYY=%date:~10,4%
set CUR_MM=%date:~4,2%
set CUR_DD=%date:~7,2%
set CUR_HH=%time:~0,2%
if %CUR_HH% lss 10 (set CUR_HH=0%time:~1,1%)
set CUR_NN=%time:~3,2%
set CUR_SS=%time:~6,2%
set CUR_MS=%time:~9,2%
set SUBFILENAME=%CUR_YYYY%%CUR_MM%%CUR_DD%-%CUR_HH%%CUR_NN%%CUR_SS%
set FULLFILENAME=archive_%SUBFILENAME%.7z
 
7zr a %FULLFILENAME% ../software/image_grab/* ../software/logs/*.log -sdel
aws s3 cp %FULLFILENAME% s3://%BUCKETNAME%/%FULLFILENAME%
del %FULLFILENAME%