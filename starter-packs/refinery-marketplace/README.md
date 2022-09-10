
aws cloudformation validate-template --template-body file://refinery.yaml

aws cloudformation create-stack --template-body file://refinery.yaml \
  --stack-name irving-refinery \
  --capabilities CAPABILITY_IAM \
  --on-failure DO_NOTHING \
  --parameters file://stack_parameters.json

aws cloudformation update-stack --template-body file://refinery.yaml \
  --stack-name irving-refinery \
  --capabilities CAPABILITY_IAM \
  --parameters file://stack_parameters.json
