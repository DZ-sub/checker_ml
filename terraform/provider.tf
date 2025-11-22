variable "aws_access_key" {
    description = "AWS Access Key"
    type        = string
}

variable "aws_secret_key" {
    description = "AWS Secret Key"
    type        = string
}

provider "aws" {
    region     = "ap-northeast-1"
    access_key = var.aws_access_key
    secret_key = var.aws_secret_key
}