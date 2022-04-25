# The purpose of this script is to apply missing 'Name' tags to ebs snapshots (based on ec2 instance Name)

import boto3
import botocore
ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

# return list of owned snapshot ids
for i in ec2.snapshots.filter(OwnerIds=['self']):

    try:
        snapshot_id = i.id
        snapshot_tag = i.tags
        snapshot_volume_id = i.volume_id

        # Preventing a "no snapshot tags" failure
        if snapshot_tag is None:
            snapshot_tag = [{'Key': 'dlm:managed', 'Value': 'true'}]

        # return all values in list of dict
        list_of_all_tag_values = [value for elem in snapshot_tag for value in elem.values()]
        VALUE = 'Name'

        # check if 'Name' tag is absent
        if VALUE not in list_of_all_tag_values:

            # return volume_id ec2 association
            response = client.describe_volumes(VolumeIds=[snapshot_volume_id])

            # logic for attached ebs volumes
            if response["Volumes"][0]["State"] == "in-use":
                instance_id = response["Volumes"][0]["Attachments"][0]["InstanceId"]
                response = client.describe_instances(InstanceIds=[instance_id])
                name_tag = response["Reservations"][0]['Instances'][0]['Tags']

                # return the 'Name' tag value and put into a var
                for tag in name_tag:
                    if tag['Key']=='Name':
                        new_tag_value = tag['Value']

                        # create 'Name' tag for snapshot with the source ec2 instance's 'Name' tag
                        snapshot = ec2.Snapshot(snapshot_id)
                        snapshot.create_tags(Tags=[{'Key': 'Name','Value': new_tag_value}])

                        # print action taken
                        print(f"A '{new_tag_value}' tag has been applied to snapshot {snapshot_id}")

            # logic for unattached ebs volumes
            else:
                print(f"{snapshot_id}'s ebs volume {snapshot_volume_id} is not attached to an ec2 instance, a generic Name tag is being added to this snapshot")
                snapshot = ec2.Snapshot(snapshot_id)
                snapshot.create_tags(Tags=[{'Key': 'Name','Value': 'ebs_volume_not_attached'}])

    # error handling for missing ebs volumes
    except botocore.exceptions.ClientError as error:
        print(f"{snapshot_id}'s ebs volume {snapshot_volume_id} is missing, a generic Name tag is being added to this snapshot")
        snapshot = ec2.Snapshot(snapshot_id)
        snapshot.create_tags(Tags=[{'Key': 'Name','Value': 'ebs_volume_deleted'}])

# declare success
print("All snapshots are tagged!")
