圧縮ファイルを作成
```powershell
cd model_artifact
tar -czf model.tar.gz .
```

# AWSでのセットアップ

## AWS SageMaker コンテナ一覧
https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg/neo-deployment-hosting-services-container-images.html
https://docs.aws.amazon.com/deep-learning-containers/latest/devguide/dlc-tensorflow-2-19-inference-sagemaker.html
https://docs.aws.amazon.com/ja_jp/sagemaker/latest/dg-ecr-paths/ecr-ap-northeast-1.html?utm_source=chatgpt.com#tensorflow-ap-northeast-1

## 推論用コンテナ
