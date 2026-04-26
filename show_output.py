import boto3

REGION = "ap-south-1"
ROLE_NAME = "EC2-S3-Access-Role"

ec2 = boto3.client("ec2", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
iam = boto3.client("iam")


print("\n===== AWS RESOURCE SUMMARY (SCREENSHOT MODE) =====\n")

# ----------------------------
# IAM ROLE
# ----------------------------
try:
    role = iam.get_role(RoleName=ROLE_NAME)
    print("[IAM ROLE FOUND]")
    print(role["Role"]["Arn"])
except:
    print("[IAM ROLE NOT FOUND]")


# ----------------------------
# S3 BUCKETS
# ----------------------------
print("\n[S3 BUCKETS]")
buckets = s3.list_buckets()

for b in buckets["Buckets"]:
    print("-", b["Name"])


# ----------------------------
# EC2 INSTANCES
# ----------------------------
print("\n[EC2 INSTANCES]")
instances = ec2.describe_instances()

for reservation in instances["Reservations"]:
    for instance in reservation["Instances"]:
        print("ID:", instance["InstanceId"])
        print("State:", instance["State"]["Name"])
        print("Type:", instance["InstanceType"])
        print("---")

print("\n===== END OUTPUT =====")