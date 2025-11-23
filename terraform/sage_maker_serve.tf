# sagemaker_serve

# モデルの作成
resource "aws_sagemaker_model" "checker_realtime_model" {
    name = "${var.project_name}-realtime-model"

    execution_role_arn = aws_iam_role.sagemaker_execution_role.arn

    primary_container {
        image = "${var.ecr_image_uri}"
        environment = {
            S3_BUCKET_NAME            = aws_s3_bucket.s3.bucket
            TF_FORCE_GPU_ALLOW_GROWTH = "true" # GPUメモリを必要に応じて確保する設定
        }
    }

    vpc_config {
        security_group_ids = [aws_security_group.sagemaker_sg.id]
        subnets            = [
            aws_subnet.private_subnet_1.id,
            aws_subnet.private_subnet_2.id
        ]
    }
  
}

# エンドポイント設定の作成

# インスタンスタイプ
variable "endpoint_instance_type" {
    default = "ml.g4dn.xlarge" # イメージに合わせて変更
    # default = "ml.m5.xlarge"
}

# エンドポイント設定の作成
resource "aws_sagemaker_endpoint_configuration" "checker_realtime_endpoint_config" {
    name = "${var.project_name}-realtime-endpoint-config"
    production_variants {
        variant_name           = "AllTraffic" # 任意の名前
        model_name             = aws_sagemaker_model.checker_realtime_model.name
        initial_instance_count = 1 # インスタンス数
        instance_type          = var.endpoint_instance_type
    }
}

# エンドポイントの作成
resource "aws_sagemaker_endpoint" "checker_realtime_endpoint" {
    name                 = "${var.project_name}-realtime-endpoint"
    endpoint_config_name = aws_sagemaker_endpoint_configuration.checker_realtime_endpoint_config.name
}