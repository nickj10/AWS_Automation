# Automated mounting of EBS Volumes with snapshots
#
# Author: Nicole Marie Jimenez
#
# This script will search for all the instances with the tag 'backup' or
# 'Backup' and check if there is an existing snapshot related to the
# instance and AMI. Then, it mounts a new EBS Volume using the snapshot
#
# Backbone: lambdaBackup.py and lambdaCleanUp.py by Robert Kozora 


import boto3

client = boto3.client('ec2')
ec2 = boto3.resource('ec2') #defines the connection
volumes = ec2.volumes.all() #gets all the volumes


#images = ec2.images.filter(Owners=["self"])

def lambda_handler(event, context):
	reservations = client.describe_instances(
		Filters=[
			{'Name': 'tag-key', 'Values': ['backup', 'Backup']},
		]
		).get(
			'Reservations', []
		)
	instances = sum(
		[
			[i for i in r['Instances']]
			for r in reservations
		], [])

	print "Found %d instances that need evaluated" % len(instances)

	#empty list of volumes to be detached
	toBeDetached = []

	for instance in instances:
		
		for v in volumes:
			v.load() # loads attachments for each volume
			if v.attachments[0]['InstanceId'] == instance['InstanceId']:
				print "Volume id: ", v.id
				#print "Instance: ", instance['InstanceId']
				#print "Instance id attached: ", v.attachments[0]['InstanceId']
				
				# includes the volume to the list of volumes to be detached later on
				if str(v.id) not in toBeDetached:
					toBeDetached.insert(0,str(v.id))
					
	
	print ""
	print "Volumes to be detached"
	print "======================"
	for det in toBeDetdached:
		print det
	
	print ""
	
	snapshots = ec2.snapshots.all() # gets all snapshots
	#myAccount = boto3.client('sts').get_caller_identity()['Account']
    #snapshots = client.describe_snapshots(MaxResults=1000)
	
	# chech if there are any snapshots related to the volumes in toBeDetached
	#for vol in toBeDetached:
	#for snaps in snapshots:
	#	print "hello"
		#if snaps['Description'].find(vol[index]) > 0:
		#	print "hello"