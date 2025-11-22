# src.infeastructure.aws.lambda_func.py をzip化して Lambda にデプロイする
data "archive_file" "lambda_zip" {
    type        = "zip"
    source_file = "${path.module}/../src/infrastructure/aws/lambda_func.py"
    output_path = "${path.module}/lambda/lambda_func.zip"
}

# Lambda 関数の作成
resource "aws_lambda_function" "checker_lambda" {
    function_name = "${var.project_name}-lambda-function"
    role          = aws_iam_role.lambda_execution_role.arn
    runtime       = "python3.12"
    handler       = "lambda_func.lambda_handler"
    filename      = data.archive_file.lambda_zip.output_path
    source_code_hash = data.archive_file.lambda_zip.output_base64sha256
    timeout       = 30
    memory_size   = 512
    environment {
        variables = {
            SM_ENDPOINT_NAME = aws_sagemaker_endpoint.checker_realtime_endpoint.name
        }
    }
}