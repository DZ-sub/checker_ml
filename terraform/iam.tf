# 必要なポリシー（フルアクセスはガバガバなので要注意）

# sagemaker
## AmazonSageMakerFullAccess（モデル作成、エンドポイント作成）
## AmazonS3FullAccess（S3へのアクセス権限）
## CloudWatchFullAccess（ログ出力）
## AmazonEC2ContainerRegistryReadOnly（ECRからイメージをpullするための権限）

# IAMロールの作成
resource "aws_iam_role" "sagemaker_execution_role" {
  name = "${var.project_name}-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

# IAMポリシーのアタッチ
resource "aws_iam_role_policy_attachment" "sagemaker_full" {
    role       = aws_iam_role.sagemaker_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}
resource "aws_iam_role_policy_attachment" "s3_full" {
    role       = aws_iam_role.sagemaker_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}
resource "aws_iam_role_policy_attachment" "cloudwatch_full" {
    role       = aws_iam_role.sagemaker_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}
resource "aws_iam_role_policy_attachment" "ecr_readonly" {
    role       = aws_iam_role.sagemaker_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# lambda
## AWSLambdaBasicExecutionRole（CloudWatch Logsへのログ出力権限）
## AmazonSageMakerFullAccess（SageMakerエンドポイントを呼び出す権限）

# IAMロールの作成
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-lambda-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}
# IAMポリシーのアタッチ
resource "aws_iam_role_policy_attachment" "lambda_basic" {
    role       = aws_iam_role.lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy_attachment" "sagemaker_full_for_lambda" {
    role       = aws_iam_role.lambda_execution_role.name
    policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}