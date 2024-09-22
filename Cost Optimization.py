import boto3
from datetime import datetime, timedelta
Lambda-code-for-cost-optimization
def lambda_handler(event, context):
    ec2 = boto3.client('ec2')

    # Get all EBS snapshots
    response = ec2.describe_snapshots(OwnerIds=['self'])

    # Get all active EC2 instance IDs
    instances_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    active_instance_ids = set()

    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            active_instance_ids.add(instance['InstanceId'])

    # Get the current time and define the 30-day threshold
    current_time = datetime.utcnow()
    threshold_time = current_time - timedelta(days=30)

    # Iterate through each snapshot and delete if it's not attached to any volume or the volume is not attached to a running instance
    for snapshot in response['Snapshots']:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')
        snapshot_start_time = snapshot['StartTime']  # Snapshot creation time

        # Check if the snapshot is older than 30 days
        if snapshot_start_time < threshold_time:
            if not volume_id:
                # Delete the snapshot if it's not attached to any volume
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                print(f"Deleted EBS snapshot {snapshot_id} as it was not attached to any volume and is older than 30 days.")
            else:
                # Check if the volume still exists
                try:
                    volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                    if not volume_response['Volumes'][0]['Attachments']:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        print(f"Deleted EBS snapshot {snapshot_id} as it was taken from a volume not attached to any running instance and is older than 30 days.")
                except ec2.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                        # The volume associated with the snapshot is not found (it might have been deleted)
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        print(f"Deleted EBS snapshot {snapshot_id} as its associated volume was not found and it is older than 30 days.")
        else:
            print(f"Snapshot {snapshot_id} is not older than 30 days and will not be deleted.")
