

import gradio as gr
import re
import random

# -------------------------
# 텍스트 처리 기본 함수
# -------------------------
STOPWORDS = {
    "a","an","the","and","or","but","if","then","so","because","as","of","in","on","at","to","for","from","by","with",
    "about","into","through","during","before","after","above","below","up","down","out","over","under","again","further",
    "here","there","when","where","why","how","all","any","both","each","few","more","most","other","some","such","no",
    "nor","not","only","own","same","so","than","too","very","can","will","just","should","now",
    "이","그","저","것","수","등","및","또는","그리고","그래서","또한","은","는","이","가","을","를","의","에","에서","으로","로","와","과","도","만"
}
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|[0-9]+(?:\.[0-9]+)?|[가-힣]+")

def split_sentences(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text2 = re.sub(r'([\.!\?。？！]|다\.)\s+', r'\1\n', text)
    parts = [p.strip() for p in text2.split('\n') if p.strip()]
    return [p for p in parts if len(p) >= 5]

def tokenize(text):
    return [m.group(0).lower() for m in WORD_PATTERN.finditer(text)]

# -------------------------
# 토론 주제 생성
# -------------------------
def generate_discussion_topics(text, num=3, seed=None):
    rnd = random.Random(seed)
    sents = split_sentences(text)
    topics = []
    for s in sents:
        if len(topics) >= num:
            break
        topic = f"'{s}'에 대해 어떤 의미가 있으며, 사회적/역사적 영향은 무엇일까?"
        topics.append(topic)
    return topics

# -------------------------
# OX 문제 생성
# -------------------------
def make_true_false(sent, rnd=None):
    if rnd is None: rnd = random.Random()
    s = sent
    truth = True
    nums = re.findall(r'([0-9]+(?:\.[0-9]+)?)', s)
    if nums and rnd.random() < 0.8:
        n = rnd.choice(nums)
        try:
            val = float(n)
            delta = max(1.0, abs(val) * 0.1)
            new_val = round(val + (delta if rnd.random() < 0.5 else -delta), 2)
            s = s.replace(n, str(new_val), 1)
            truth = False
        except:
            pass
    else:
        for a,b in [("있다","없다"),("이다","아니다")]:
            if a in s and rnd.random() < 0.6:
                s = s.replace(a,b,1)
                truth = False
                break
    return s, truth, sent

# -------------------------
# 빈칸 문제 생성
# -------------------------
def make_fill_in_blank(sent):
    toks = tokenize(sent)
    candidates = [t for t in toks if t not in STOPWORDS and len(t) >= 3]
    if not candidates:
        return None, None
    target = max(candidates, key=len)
    question = re.sub(re.escape(target), "____", sent, count=1, flags=re.IGNORECASE)
    return question, target

# -------------------------
# 퀴즈 생성
# -------------------------
def generate_quiz(text, num_tf=3, num_blank=3, seed=None):
    rnd = random.Random(seed)
    sents = [s for s in split_sentences(text)]
    tf, blank = [], []
    for s in sents:
        if len(tf) < num_tf:
            q, truth, ref = make_true_false(s, rnd=rnd)
            if q: tf.append({"statement":q, "answer":truth, "reference_true":ref})
        if len(blank) < num_blank:
            q, ans = make_fill_in_blank(s)
            if q: blank.append({"question":q, "answer":ans})
        if len(tf) >= num_tf and len(blank) >= num_blank:
            break
    return {"tf":tf, "blank":blank}

# -------------------------
# 결과 출력 포맷
# -------------------------
def format_output_with_explanation(discussions, quiz):
    out = ""
    out += "### 토론 주제\n"
    for i, t in enumerate(discussions, 1):
        out += f"{i}) {t}\n"
    out += "\n### OX 문제\n"
    for i,q in enumerate(quiz.get("tf",[]),1):
        out += f"{i}) {q['statement']}\n"
        answer_str = 'O(참)' if q['answer'] else 'X(거짓)'
        out += f"   정답: {answer_str}\n"
        explanation = f"   해설: 원문 '{q['reference_true']}'에 근거하여 {'사실이므로 참(O)입니다.' if q['answer'] else '틀렸으므로 거짓(X)입니다.'}"
        out += explanation + "\n"
    out += "\n### 빈칸 채우기\n"
    for i,q in enumerate(quiz.get("blank",[]),1):
        out += f"{i}) {q['question']}\n"
        out += f"   정답: {q['answer']}\n"
    return out

# -------------------------
