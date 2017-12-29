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
myAccount = boto3.client('sts').get_caller_identity()['Account']
snapshots = client.describe_snapshots(MaxResults=1000, OwnerIds=[myAccount])['Snapshots']

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
	foundInDesc = []
	volumesExist = False

	for instance in instances:
		
		for v in volumes:
			v.load() # loads attachments for each volume
			try:
				if v.attachments[0]['InstanceId'] == instance['InstanceId']:
					#print "Volume id: ", v.id
					#print "Instance: ", instance['InstanceId']
					#print "Instance id attached: ", v.attachments[0]['InstanceId']
				
					# includes the volume to the list of volumes to be detached later on
					if str(v.id) not in toBeDetached:
						toBeDetached.insert(0,str(v.id))
			except IndexError:
				volumesExist = True
					
	
	print ""
	print "Volumes to be detached"
	print "======================"
	for det in toBeDetached:
		print det
	
	print ""
	if volumesExist == True:
		print "There are volumes that need to be deleted"
	else:
		# check if there are any snapshots related to the volumes in toBeDetached
		for vol in toBeDetached:
			for snaps in snapshots:
				if snaps['Description'].find(vol) > 0:
					print "Volume id", vol,"found in description of",snaps['SnapshotId']
					if snaps['SnapshotId'] not in foundInDesc:
						foundInDesc.insert(0,str(snaps['SnapshotId']))
						print snaps['StartTime']
						
		print ""
		print "Snapshots to be used"
		print "===================="
		print ""
		
		if not foundInDesc:
			print "There are no snapshots in the list"
		else:
			for j in foundInDesc:
				print j
				
		
		#create new volumes for each snapshot
		for s in foundInDesc:
			newVol = client.create_volume(SnapshotId=s, AvailabilityZone='eu-central-1b')
			print "Volume created! Volume Id:", newVol['VolumeId']
			volume = ec2.Volume(newVol['VolumeId'])
			volume.load()
			try:
				print "Device of new volume:", volume.attachments[0]['Device']
			except IndexError:
				print "Volume does not have a device yet"
			for vols in toBeDetached:
		 		#get the device name
		 		volDet = ec2.Volume(vols)
		 		volDet.load()
		 		print volDet.attachments[0]['Device']
		 	
		 	
