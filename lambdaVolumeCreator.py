# Automated mounting of EBS Volumes with snapshots
#
# Author: Nicole Marie Jimenez
#
# This script will search for all the instances with the tag 'backup' or
# 'Backup' and check if there is an existing snapshot related to the
# instance and AMI. Then, it mounts a new EBS Volume using the snapshot
#



import boto3

client = boto3.client('ec2')

