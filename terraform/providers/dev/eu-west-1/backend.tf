terraform {
  backend "s3" {
    profile = "jf_dev"
    key = "zebra-object-detection/dev.tfstate"
    region = "eu-west-1"
    bucket = "jf-dev-tf-state"
  }
}