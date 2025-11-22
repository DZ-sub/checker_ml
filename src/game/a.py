import requests

url = "https://4djo1pd0h8.execute-api.ap-northeast-1.amazonaws.com/action"

state = {
    "board": [
        [0, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, -1, 0, 0, -1, 0],
        [0, 0, 0, 0, 0, 0],
    ],
    "turn": 1, #赤か青
    "turn_count": 10, #ターン数
}

res = requests.post(url, json=state)
print(res.status_code)
print(res.json())