# API Gateway の作成
resource "aws_apigatewayv2_api" "api_gateway" {
    name          = "${var.project_name}-api-gateway"
    protocol_type = "HTTP"
}

# Lambda との統合設定
resource "aws_apigatewayv2_integration" "lambda_integration" {
    api_id                 = aws_apigatewayv2_api.api_gateway.id
    integration_type       = "AWS_PROXY"
    integration_uri        = aws_lambda_function.checker_lambda.arn
    integration_method     = "POST"
    payload_format_version = "2.0"
}

# ルートの作成（POST /action）
resource "aws_apigatewayv2_route" "post_route" {
    api_id    = aws_apigatewayv2_api.api_gateway.id
    route_key = "POST /action"
    target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# ステージ（$default に自動デプロイ）
resource "aws_apigatewayv2_stage" "default_stage" {
    api_id      = aws_apigatewayv2_api.api_gateway.id
    name        = "$default"
    auto_deploy = true
}

# Lambda に API Gateway からの呼び出し権限を付与
resource "aws_lambda_permission" "api_gateway_permission" {
    statement_id  = "AllowAPIGatewayInvoke"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.checker_lambda.arn
    principal     = "apigateway.amazonaws.com"
    source_arn    = "${aws_apigatewayv2_api.api_gateway.execution_arn}/*/*"
}

# 出力
output "api_invoke_url" {
  value = aws_apigatewayv2_api.api_gateway.api_endpoint
}
