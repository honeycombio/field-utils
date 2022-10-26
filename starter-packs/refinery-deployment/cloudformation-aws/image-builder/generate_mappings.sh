#!/bin/bash
set -e -o pipefail

IMAGE_NAME='refinery-marketplace-image-builder-*'
IMAGE_OWNERID="939023695662"

printf "Mappings:\n  AMIRegionMap:\n"

regions=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text)
for region in $regions; do
  amiid=$(aws --region $region ec2 describe-images \
  --owners $IMAGE_OWNERID \
  --filters "Name=name,Values=${IMAGE_NAME}" \
  --query "sort_by(Images, &CreationDate)[*].ImageId | [-1]" \
  --output "text")

  # skip the entries where there's no image
  if [[ $amiid == "None" ]]; then
    continue
  fi

  printf "    $region:\n      arm64: $amiid\n"
done
