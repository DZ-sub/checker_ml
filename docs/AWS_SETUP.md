## AWS セットアップ手順 (terraform/ を参照)

このドキュメントはリポジトリ内の `terraform/` ディレクトリを使って AWS のインフラ (S3, VPC, IAM, Lambda, API Gateway, SageMaker など) を構築する手順をまとめたものです。

重要: SageMaker エンドポイントや NAT Gateway などは課金が発生します。不要になったら必ず `terraform destroy` でリソースを削除してください。

## 前提

- AWS アカウント
- AWS CLI がインストールされていること
- Terraform (>= 1.0、HashiCorp Terraform) がインストールされていること
- 必要に応じて Docker / ECR の操作ができる環境（カスタム推論コンテナを利用する場合）

推奨: AWS の認証情報はローカルでプロファイルまたは環境変数で管理してください。provider は `terraform/provider.tf` によって `aws_access_key` / `aws_secret_key` 変数を想定していますが、セキュリティの観点から環境変数やプロファイルの利用を推奨します。

## terraform/ ディレクトリ概要

主要なファイル:

- `provider.tf` — AWS プロバイダー定義（region と credential 変数）
- `version.tf` — Terraform と provider のバージョン要件
- `iam.tf` — SageMaker / Lambda 用の IAM ロールとポリシー
- `s3.tf` — モデルやデータ保存用の S3 バケット定義
- `vpc.tf` — VPC / Subnet / NAT / Route 設定（SageMaker 用の VPC 設定）
- `lambda.tf` — `src/infrastructure/aws/lambda_func.py` を zip 化して Lambda を作成
- `api_gateway.tf` — Lambda と統合した API Gateway (HTTP API)
- `sage_maker.tf` および `sage_maker_serve.tf` — SageMaker モデル / エンドポイント定義

各ファイルの詳細は Terraform のリソース定義内のコメントも参照してください。

## 必要な変数

Terraform の定義内でいくつかの変数 (例: `project_name`, `az`, `ecr_image_uri`, `aws_access_key`, `aws_secret_key` など) が参照されています。これらは `terraform.tfvars` を作成するか、`-var` オプションで渡してください。例:

terraform.tfvars (例)

```hcl
aws_access_key = "YOUR_AWS_ACCESS_KEY"
aws_secret_key = "YOUR_AWS_SECRET_KEY"
project_name   = "my-checker"
az             = "ap-northeast-1"
ecr_image_uri  = "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/my-repo:latest"
# 必要に応じて endpoint_instance_type などを指定
```

注意: `aws_access_key` / `aws_secret_key` は平文ファイルに置くのは推奨されません。代わりに環境変数や AWS CLI プロファイルを使用してください。例: PowerShell の環境変数設定（セッション）:

```powershell
# $env:AWS_ACCESS_KEY_ID = 'AKIA...'
# $env:AWS_SECRET_ACCESS_KEY = '...'
# $env:AWS_REGION = 'ap-northeast-1'
```

Terraform の provider は変数 `aws_access_key` / `aws_secret_key` を使う設定になっています。環境変数を使う場合は `provider.tf` を環境変数読み取りに変更するか、`terraform plan -var "aws_access_key=$env:AWS_ACCESS_KEY_ID" -var "aws_secret_key=$env:AWS_SECRET_ACCESS_KEY"` のように渡してください。

## 初期化・デプロイ手順（PowerShell 例）

1. リポジトリのルートから `terraform` ディレクトリに移動します。

```powershell
Set-Location -Path .\terraform
```

2. 必要に応じて `terraform.tfvars` を作成するか、環境変数/プロファイルを用意します。

3. Terraform の初期化

```powershell
terraform init
```

4. フォーマットと検証（任意）

```powershell
terraform fmt
terraform validate
```

5. 計画を確認

```powershell
terraform plan -var-file="terraform.tfvars"
```

6. 適用（インフラ作成）

```powershell
terraform apply -var-file="terraform.tfvars"
```

7. 出力の確認（API のエンドポイント URL など）

```powershell
terraform output
terraform output api_invoke_url
```

## 重要な注意点

- SageMaker エンドポイントや EC2 / NAT Gateway などは課金が発生します。
- `terraform apply` を実行する前に、`terraform plan` で作成されるリソースを必ず確認してください。
- `ecr_image_uri` 変数には、SageMaker にデプロイするコンテナイメージの URI を指定する必要があります。ECR にイメージを push してから参照してください。
- Lambda は `src/infrastructure/aws/lambda_func.py` を zip 化してデプロイします。ローカルの相対パスが正しいことを確認してください。

## リソース削除（クリーンアップ）

使用を終えたら必ずリソースを削除してコストを抑えてください。

```powershell
terraform destroy -var-file="terraform.tfvars"
```

## トラブルシューティング

- 権限エラー: IAM ユーザーに必要な権限（S3, SageMaker, ECR, Lambda, VPC 周り）を付与してください。`iam.tf` で作成されるロールにはいくつかのフルアクセス権限が付与されますが、実際のアカウントでの最小権限設定は要検討です。
- 変数エラー: 変数が未指定の場合、`terraform plan` が失敗します。必要な変数を `terraform.tfvars` または `-var` で渡してください。
- パスエラー: `lambda.tf` の `source_file` は `terraform` ディレクトリから見た相対パスで `../src/infrastructure/aws/lambda_func.py` を参照します。パスが存在することを確認してください。

## 参考

- このリポジトリの `terraform/` ディレクトリ内の各ファイルを参照してください。

---

作成者: リポジトリ自動生成ドキュメント
