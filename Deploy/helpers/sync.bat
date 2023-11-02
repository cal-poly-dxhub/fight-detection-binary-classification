@echo off
echo === sync.bat ===
echo %date% %time%
aws s3 cp s3://deploy/software/main.py ../software
aws s3 cp s3://deploy/software/requirements.txt ../software
aws s3 cp s3://deploy/software/camera_endpoints.csv ../software
aws s3 cp s3://deploy/software/model.pth ../software

aws s3 cp s3://deploy/helpers/kill_task.bat ../helpers
aws s3 cp s3://deploy/helpers/run_software.bat ../helpers
aws s3 cp s3://deploy/helpers/archiver.bat ../helpers