import boto3
import time

# ----------------------------
# CONFIGURATION
# ----------------------------
REGION = "ap-south-1"
ROLE_NAME = "EC2-S3-Access-Role"
BUCKET_NAME = f"aws-auto-bucket-{int(time.time())}"

ec2 = boto3.client("ec2", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
iam = boto3.client("iam")
ssm = boto3.client("ssm", region_name=REGION)


# ----------------------------
# GET LATEST UBUNTU AMI
# ----------------------------
def get_latest_ubuntu_ami():
    print("[INFO] Fetching latest Ubuntu AMI...")

    response = ssm.get_parameter(
        Name="/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
    )

    ami_id = response["Parameter"]["Value"]
    print(f"[INFO] Ubuntu AMI ID: {ami_id}")
    return ami_id


# ----------------------------
# GET EXISTING IAM ROLE
# ----------------------------
def get_iam_role():
    try:
        role = iam.get_role(RoleName=ROLE_NAME)
        print(f"[INFO] Reusing IAM Role: {ROLE_NAME}")
        return role["Role"]["Arn"]

    except iam.exceptions.NoSuchEntityException:
        print(f"[ERROR] IAM Role '{ROLE_NAME}' not found.")
        print("Create it in AWS Console (EC2 trusted + S3FullAccess)")
        exit(1)


# ----------------------------
# CREATE S3 BUCKET
# ----------------------------
def create_s3_bucket():
    print("[INFO] Creating S3 bucket...")

    if REGION == "us-east-1":
        s3.create_bucket(Bucket=BUCKET_NAME)
    else:
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": REGION}
        )

    print(f"[SUCCESS] S3 Bucket created: {BUCKET_NAME}")
    return BUCKET_NAME


# ----------------------------
# LAUNCH EC2 INSTANCE
# ----------------------------
def launch_ec2_instance():
    print("[INFO] Launching EC2 (Ubuntu + t3.micro)...")

    ami_id = get_latest_ubuntu_ami()

    response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType="t3.micro",
        MinCount=1,
        MaxCount=1,
        KeyName="my-key-pair",  # must exist in Mumbai region
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "Auto-Ubuntu-EC2"}
                ]
            }
        ]
    )

    instance_id = response["Instances"][0]["InstanceId"]
    print(f"[SUCCESS] EC2 Launched: {instance_id}")

    # Wait until running
    print("[INFO] Waiting for EC2 to be in running state...")
    ec2.get_waiter("instance_running").wait(InstanceIds=[instance_id])
    print("[SUCCESS] EC2 is running")

    return instance_id


# ----------------------------
# ATTACH IAM ROLE TO EC2
# ----------------------------
def attach_iam_role_to_ec2(instance_id):
    print("[INFO] Attaching IAM Role to EC2...")

    ec2.associate_iam_instance_profile(
        IamInstanceProfile={
            "Name": ROLE_NAME
        },
        InstanceId=instance_id
    )

    print("[SUCCESS] IAM Role attached to EC2")


# ----------------------------
# MAIN EXECUTION
# ----------------------------
if __name__ == "__main__":
    print("\n===== AWS RESOURCE PROVISIONING STARTED =====\n")

    # IAM Role (reuse)
    role_arn = get_iam_role()

    # S3 Bucket
    bucket = create_s3_bucket()

    # EC2 Instance
    instance_id = launch_ec2_instance()

    # Attach IAM Role
    attach_iam_role_to_ec2(instance_id)

    # Final Output
    print("\n===== FINAL SUMMARY =====")
    print(f"IAM Role  : {role_arn}")
    print(f"S3 Bucket : {bucket}")
    print(f"EC2 ID    : {instance_id}")

    print("\n===== PROJECT COMPLETED SUCCESSFULLY =====")