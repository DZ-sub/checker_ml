import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
import tempfile
import pickle
from keras.models import load_model
from keras.models import Model

load_dotenv()

PROFILE_NAME = os.getenv("AWS_PROFILE_NAME")
REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


def connect_to_backet():
    try:
        # # 環境に合わせて切り替え
        # #ローカル
        # session = boto3.Session(
        #     profile_name=PROFILE_NAME,
        #     region_name=REGION,
        # )
        # s3_client = session.client("s3")
        # # aws上 or docker上
        s3_client = boto3.client("s3", region_name=REGION)
    except Exception as e:
        print(f"バケットへの接続に失敗しました: {e}")
        raise e
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"バケット {BUCKET_NAME} は存在します。")
    except ClientError as e:
        print(f"バケット {BUCKET_NAME} は存在しません。: {e}")
        raise e

    return s3_client


def upload_bytes_to_s3(dir_name: str, file_name: str, body: bytes) -> None:
    """
    任意のバイト列データを S3 にアップロードする関数。
        body : S3 にそのまま保存するバイト列データ
        dir_name : S3 上のディレクトリ名
        file_name : S3 上のファイル名
    """
    s3_client = connect_to_backet()
    object_key = f"{dir_name}/{file_name}"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
        Body=body,
    )

    print(f"ファイルがS3にアップロードされました: s3://{BUCKET_NAME}/{object_key}")


def load_bytes_from_s3(dir_name: str, file_name: str) -> bytes:
    """
    S3 上のファイルを bytes として取得
    存在しない場合は b"" を返す
    """
    s3_client = connect_to_backet()
    object_key = f"{dir_name}/{file_name}"

    try:
        resp = s3_client.get_object(Bucket=BUCKET_NAME, Key=object_key)
        data = resp["Body"].read()
        print(f"ファイルがS3から取得されました: s3://{BUCKET_NAME}/{object_key}")
        return data
    except s3_client.exceptions.NoSuchKey:
        print(f"ファイルがS3に存在しません: s3://{BUCKET_NAME}/{object_key}")
        return b""


def load_some_pickles_from_s3(
    dir_name: str, file_prefix: str, max_files: int
) -> list[bytes]:
    """
    S3 上の指定ディレクトリ内のファイルをいくつか bytes として取得
    存在しない場合は空リストを返す
    """
    s3_client = connect_to_backet()
    prefix = f"{dir_name}/{file_prefix}"

    try:
        resp = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
        contents = resp.get("Contents", [])
        if not contents:
            print(f"S3 に {prefix}*.pkl が見つかりません。")
            return []

        # 更新日時でソート
        sorted_contents = sorted(contents, key=lambda obj: obj["Key"])
        # max_files が指定されている場合は「新しい方から」max_files 個に絞る
        if max_files is not None:
            sorted_contents = sorted_contents[-max_files:]
        # ファイルを順番に取得
        all_history = []
        for obj in sorted_contents:
            key = obj["Key"]
            # dir_nameとfile_nameを分割
            _, file_name = key.split(f"{dir_name}/", 1)
            body = load_bytes_from_s3(dir_name, file_name)
            history = pickle.loads(body)
            all_history.extend(history)
        return all_history
    # ファイルが一つも見つからなかった場合
    except s3_client.exceptions.NoSuchKey:
        print(f"S3 に {prefix}*.pkl が見つかりません。")
        return []
    # その他のエラー
    except Exception as e:
        print(f"S3 からのファイル取得中にエラーが発生しました: {e}")
        return []


# ========== keras 用のモデル保存・読み込み関数 ==========


# モデル保存
def upload_model_to_s3(dir_name: str, file_name: str, model: Model) -> None:
    """
    Keras モデルを S3 に保存する関数。
    """
    # 一時ファイルに保存 → バイト列で読み出し → S3 にアップロード → 一時ファイル削除
    with tempfile.NamedTemporaryFile(suffix=".keras", delete=False) as tmp:
        tmp_path = tmp.name

    # Keras の save はパス指定が一番安定するので一度だけローカルに書く
    model.save(tmp_path)

    with open(tmp_path, "rb") as f:
        body = f.read()

    # S3 にアップロード
    upload_bytes_to_s3(dir_name, file_name, body)

    # 一時ファイル削除
    os.remove(tmp_path)

    print(
        f"Keras モデルが S3 に保存されました: s3://{BUCKET_NAME}/{dir_name}/{file_name}"
    )


# モデル読み込み
def load_model_from_s3(dir_name: str, file_name: str) -> Model:
    """
    S3 上の .keras ファイルを bytes で取得し、
    一時ファイルに書き出してから Keras モデルとしてロードする。
    """
    body = load_bytes_from_s3(dir_name, file_name)
    if not body:
        raise FileNotFoundError(f"S3 に {dir_name}/{file_name} が見つかりません。")

    # 一時ファイルに書き出してから load_model する（最も安定）
    with tempfile.NamedTemporaryFile(suffix=".keras", delete=False) as tmp:
        tmp.write(body)
        tmp_path = tmp.name

    model = load_model(tmp_path, compile=False)

    # 一時ファイル削除
    os.remove(tmp_path)

    return model
