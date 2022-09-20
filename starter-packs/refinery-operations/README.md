# Refinery Starter Pack

This is the Starter Pack for Refinery day 2 operations. It creates the boards, queries, triggers and SLOs that you'd need to operate Honeycomb Refinery.

### Prerequisites
You must have `terraform` installed. Follow [these directions](https://learn.hashicorp.com/tutorials/terraform/install-cli) to install for your platform.

You will need a Honeycomb API key with the adequate permissions to create boards, queries etc.. Once you have the API key, you can set it like so:

```
export HONEYCOMB_API_KEY="<YOUR_API_KEY>"
```

Or define it via the `api_key` variable.

### Quickstart
Then, to run terraform plan or apply for all modules in this directory (`terraform`), run:

```
terraform init
terraform plan
terraform apply
```

### Video Walkthrough

https://user-images.githubusercontent.com/3537368/191327560-f2d6d20a-0cd6-4b66-9400-f98aebd808c8.mp4

