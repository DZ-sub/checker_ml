import uvicorn

def main():
    # FastAPIアプリを起動
    uvicorn.run(
        "src.infrastructure.fastapi.app:app",  # ← app.py 内の app
        host="0.0.0.0",
        port=8080,
    )


if __name__ == "__main__":
    main()