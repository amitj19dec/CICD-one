4TE="./MyLambdaFunction.yml"
FILENAME="$(basename "$TEMPLATE")"
STACK_NAME="${FILENAME%.*}"

aws cloudformation package \
  --template-file "$TEMPLATE" \
  --s3-bucket my-bucket \
  --s3-prefix cloudformation/packages \
  --output-template-file "${TEMPLATE}.packaged"
aws cloudformation deploy \
  --template-file "${TEMPLATE}.packaged" \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM
