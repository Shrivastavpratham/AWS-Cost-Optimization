
# EBS Snapshot Cleanup Automation - AWS Lambda Function

## Project Overview

This project automates the deletion of unused and old EBS (Elastic Block Store) snapshots in AWS. The Lambda function is triggered to scan for all snapshots owned by the AWS account and deletes those that:
- Are not attached to any active volume, **AND**
- Were created more than 30 days ago.

This ensures efficient storage management and helps reduce costs by automatically cleaning up unused resources.

## Features

- **Automated Snapshot Deletion**: Deletes snapshots older than 30 days that are not attached to any running instances or volumes.
- **Cost Optimization**: Reduces unnecessary storage costs by cleaning up outdated resources.
- **Error Handling**: Manages edge cases like invalid or missing volumes.
- **Serverless Architecture**: The project uses AWS Lambda for serverless execution, reducing overhead and simplifying infrastructure management.

## Prerequisites

- AWS account with access to Lambda, EC2, and IAM roles.
- IAM Role with necessary permissions for the Lambda function:
  - `ec2:DescribeSnapshots`
  - `ec2:DeleteSnapshot`
  - `ec2:DescribeVolumes`
  - `ec2:DescribeInstances`
- Python 3.x
- Boto3 (AWS SDK for Python)

## How it Works

1. The Lambda function retrieves all snapshots owned by the account using `ec2.describe_snapshots()`.
2. For each snapshot, it checks if the snapshot is associated with any volume.
3. If a snapshot is not associated with a volume and is **older than 30 days**, it is deleted using `ec2.delete_snapshot()`.
4. If a snapshot is associated with a volume, the function checks if the volume is attached to any running instance.
5. If the volume is not attached to any instance, the snapshot is deleted.
6. Snapshots younger than 30 days are retained.

## Code Overview

```python
import boto3
from datetime import datetime, timedelta

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
```

## Setup Instructions

1. **Create the Lambda Function**:
    - Go to the AWS Management Console and create a new Lambda function.
    - Select the Python runtime.
    - Paste the code into the Lambda function editor.

2. **Assign IAM Role**:
    - Assign an IAM role to the Lambda function with the necessary permissions:
      - `ec2:DescribeSnapshots`
      - `ec2:DeleteSnapshot`
      - `ec2:DescribeVolumes`
      - `ec2:DescribeInstances`

3. **Configure Lambda Triggers**:
    - Set the function to trigger on a schedule using AWS CloudWatch Events.
    - Define a schedule (e.g., run the function once a day).

4. **Test the Function**:
    - Run the function manually or wait for the scheduled trigger.
    - Check the logs in CloudWatch to verify that snapshots older than 30 days are being deleted.

## Enhancements

- **Notifications**: Integrate with AWS SNS to send notifications when a snapshot is deleted.
- **Tag-Based Deletion**: Implement deletion rules based on snapshot tags (e.g., only delete snapshots with a specific tag).
- **Logging**: Add more detailed logging to monitor which snapshots are deleted and why.


