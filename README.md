# CICD-one
This is the First step towards CICD.

## First we need to put the entire code in Cloudformation template


### Commands tested:

1. Creating a stack for testing (Please note pcprod is the profile name)

cd test

aws cloudformation create-stack --stack-name myteststack --template-body file://test-iam.yaml --region us-west-2 --profile pcprod --capabilities CAPABILITY_NAMED_IAM

2. Deleting the stack

aws cloudformation delete-stack --stack-name myteststack --region us-west-2

![image](https://user-images.githubusercontent.com/19222886/139279827-b6286fe6-9b52-4c00-96de-5b637c68320c.png)
