import requests

url = "http://localhost:8000/action"

state = {
    "board": [
        [0, 1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, -1, 0, 0, -1, 0],
        [0, 0, 0, 0, 0, 0],
    ],
    "turn": 1,
    "turn_count": 10,
}

res = requests.post(url, json=state)
print(res.status_code)
print(res.json())
