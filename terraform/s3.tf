# s3 バケットの作成
resource "aws_s3_bucket" "s3" {
    bucket = "${var.project_name}-bucket"

    tags = {
        Name        = "${var.project_name}-bucket"
        Environment = "Dev"
    }
}
# saved_model オブジェクトの作成
resource "aws_s3_object" "saved_model_dir" {
    bucket = aws_s3_bucket.s3.bucket
    key    = "saved_model/"
    content = ""
}
# data オブジェクトの作成
resource "aws_s3_object" "data_dir" {
    bucket = aws_s3_bucket.s3.bucket
    key    = "data/"
    content = ""
}