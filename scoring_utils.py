# Updated scoring system

def calculate_score(data):
    if not data:
        return 0
    score = sum(item['score'] for item in data)
    return score / len(data)

# Validation function

def validate_score(score):
    return 0 <= score <= 100
