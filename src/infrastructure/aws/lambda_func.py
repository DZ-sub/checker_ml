import os
import json
import boto3

runtime = boto3.client("sagemaker-runtime", region_name="ap-northeast-1")
ENDPOINT_NAME = os.environ.get("SM_ENDPOINT_NAME")


def lambda_handler(event, context):
    print("EVENT:", json.dumps(event))

    # ① API Gateway (Lambda proxy) だと、リクエストボディは event["body"] に文字列で入る
    if "body" in event and event["body"]:
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Invalid JSON in request body"}),
            }
    else:
        body = {}

    # ② body からパラメータを取り出す（なければデフォルト）
    board = body.get(
        "board",
        [
            [0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, -1, 0, -1, 0, -1],
            [-1, 0, -1, 0, -1, 0],
        ],
    )
    turn = body.get("turn", 1)
    turn_count = body.get("turn_count", 10)

    payload = {
        "board": board,
        "turn": turn,
        "turn_count": turn_count,
    }

    # ③ SageMaker エンドポイント呼び出し
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps(payload).encode("utf-8"),
    )

    result = json.loads(response["Body"].read())
    print("RESULT:", result)

    # ④ API Gateway 用レスポンス形式で返す
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(result),
    }
