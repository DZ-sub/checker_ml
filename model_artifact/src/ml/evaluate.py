from src.gpt_ml.gameplay import play


# アルゴリズム評価
def evaluate_algorithm_of(label, next_actions, EP_GAME_COUNT=100):
    """
    next_actions回ゲームを繰り返してその平均成績を見る

    label: アルゴリズム名（ログ出力用）
    next_actions: [先手の行動選択関数, 後手の行動選択関数]
    EP_GAME_COUNT: 対戦回数

    return: 先手プレイヤーの平均ポイント（0〜1）
    """
    total_point = 0.0

    # 複数回の対戦を繰り返す
    for i in range(EP_GAME_COUNT):
        # 1ゲームの実行
        if i % 2 == 0:
            # latest が先手
            total_point += play(next_actions)
        else:
            # 先手後手を入れ替えて実行（latest を後手に）
            total_point += 1 - play(list(reversed(next_actions)))

        # 進捗表示
        print(f"\rEvaluate {i + 1}/{EP_GAME_COUNT}", end="")
    print("")

    # 平均ポイントを計算
    average_point = total_point / EP_GAME_COUNT
    print(f"VS_{label} {average_point:.3f}")
    return average_point
