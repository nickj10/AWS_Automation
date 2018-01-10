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
import time

client = boto3.client('ec2')
ec2 = boto3.resource('ec2') #defines the connection
volumes = ec2.volumes.all() #gets all the volumes
myAccount = boto3.client('sts').get_caller_identity()['Account']
snapshots = client.describe_snapshots(MaxResults=1000, OwnerIds=[myAccount])['Snapshots']

#images = ec2.images.filter(Owners=["self"])

def lambda_handler(event, context):
	# 1) Gets the instance ids that have 'Backup' as tag ==> DevAF01a
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
		
	# 2) Gets the instance ids that have 'Target' as tag ==> DevAF01b
	targets = client.describe_instances(
		Filters=[
			{'Name': 'tag-key', 'Values': ['target', 'Target']},
		]
		).get(
			'Reservations', []
		)
	target_instances = sum(
		[
			[j for j in t['Instances']]
			for t in targets
		], [])

	print "Found %d instances that need backed up" % len(instances)
	print "Found %d target instances" % len(target_instances)

	#empty lists
	attachedToDev = []
	foundInDesc = []
	newVolumes =[]
	devices = []
	volumesExist = False

	# 4) Find volumes attached to DevAF01b so that they can be detached later on
	for instance in target_instances:
		for v in volumes:
			v.load() # loads attachments for each volume
			try:
				#find the volumes attached to DevAF01b
				if v.attachments[0]['InstanceId'] == instance['InstanceId']:
					attachedToDev.insert(0,v)
			except IndexError:
				volumesExist = False
					
	
	print ""
	print "Volumes attached to DevAF01b"
	print "======================"
	for att in attachedToDev:
		print att
	
	print ""
	if volumesExist == True:
		print "There are volumes that need to be deleted"
	else:
		# check if there are any snapshots related to the instances
		for i in instances:
			for snaps in snapshots:
				# 3) Find snapshots connected to DevAF01a
				if snaps['Description'].find(i['InstanceId']) > 0:
					#print "Volume id", vol,"found in description of",snaps['SnapshotId']
					print "Instance id", i['InstanceId'],"found in description of",snaps['SnapshotId']
					if snaps['SnapshotId'] not in foundInDesc:
						foundInDesc.insert(0,str(snaps['SnapshotId']))
						print snaps['StartTime']
						
		print ""
		print "Snapshots related to DevAF01a"
		print "===================="
		
		if not foundInDesc:
			print "There are no snapshots in the list"
		else:
			for j in foundInDesc:
				print j
		print ""
		print "===="
		print "Creating new volumes"
		print "===="

		# 5) Create new volumes for each snapshot
		for s in foundInDesc:
			newVol = client.create_volume(SnapshotId=s, AvailabilityZone='eu-central-1b')
			print "Volume created! Volume Id:", newVol['VolumeId']
			newVolumes.insert(0,str(newVol['VolumeId'])) # we add this to the list of new volumes created

		# wait until the new volumes are available
		time.sleep(30) #sleep for 30 seconds
		flag = 0
		print ""
		print "===="
		print "Detaching old volumes"
		print "===="
		
		#  6) Detach old volumes from DevAF01b
		for a in attachedToDev:
		 	a.load()
		 	print "Device name for volume", a.attachments[0]['VolumeId'], ":", a.attachments[0]['Device']
		 	devices.insert(0,str(a.attachments[0]['Device'])) #adds device to list of device
 		 	try:
		 		resp = a.detach_from_instance(
		 			Device = a.attachments[0]['Device'],
		 			Force = False,
		 			InstanceId = target_instances[0]['InstanceId'],
		 			DryRun = False
		 		)
		 		print "Volume", flag, "successfully detached!"
		 		flag = flag + 1
		 	except IndexError:
		 		print "Volume", flag, "was not detached. Moving on to the next one."
		 		flag = flag + 1
		 	
		# 7) After detaching the volume, we attach the new one created
		flag2 = len(newVolumes) - 1
		
		time.sleep(30) # wait for a while until the volumes are fully detached
		
		print ""
		print "===="
		print "Attaching new volumes"
		print "===="
		
		for a in newVolumes:
			try:
				n = ec2.Volume(a)
				print "Device name to be used:", devices[flag2], "with volume", a, "attaching to", target_instances[0]['InstanceId']
				resp2 = n.attach_to_instance(
		 			Device = devices[flag2],
					InstanceId = target_instances[0]['InstanceId'],
		 			DryRun = False
		 		)
				print "New volume is attached to the instance"
		 		flag2 = flag2 - 1
		 	except IndexError:
		 		print "The new volume", a, "was not attached to the instance."
		 		flag2 = flag2 - 1
			
		 
