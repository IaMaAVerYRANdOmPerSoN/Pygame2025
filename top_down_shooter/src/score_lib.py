import os

SCORE_FILE = "scores.txt"

def save_score(name, score):
    with open(SCORE_FILE, "a") as f:
        f.write(f"{name}: {score}\n")

def get_scores():
    if not os.path.exists(SCORE_FILE):
        return []
    scores = []
    with open(SCORE_FILE, "r") as f:
        for line in f:
            if ":" in line:
                name, score = line.strip().rsplit(":", 1)
                try:
                    scores.append((name.strip(), int(score.strip())))
                except ValueError:
                    continue
    return sorted(scores, key=lambda x: x[1], reverse=True)