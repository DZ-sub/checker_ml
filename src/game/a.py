import requests
import json

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

AI_data=res.json()
AI_selected_piece = AI_data['action']['selected_piece'] 
AI_move_to = AI_data['action']['move_to'] 
AI_captured_piece = AI_data['action']['captured_pieces'][0]
print(AI_selected_piece)
print(AI_move_to)
print(AI_captured_piece)