# 수강후기를 SQLite 데이터베이스(reviews.db 파일)에 저장하고 꺼내는 일만 맡는 파일이에요
# (화면 만드는 일은 app.py, 클래스 CSV 읽는 일은 data.py 담당)

# sqlite3: 파이썬에 기본으로 들어 있는 SQLite 도구예요 (따로 설치할 필요 없어요)
import sqlite3
# Path: 파일 위치(경로)를 다루는 도구예요
from pathlib import Path
# datetime: 지금 날짜·시간을 알려 주는 도구예요 (저장 시각 기록용)
from datetime import datetime

# 이 파일(db.py)이 있는 폴더(D21-flask) 안의 reviews.db를 가리켜요
# 파일이 없으면 처음 연결할 때 SQLite가 알아서 새로 만들어요
DB_PATH = Path(__file__).resolve().parent / "reviews.db"


# DB와 연결(전화 연결)을 하나 만들어서 돌려줘요
def get_connection():
    # reviews.db 파일과 연결해요
    conn = sqlite3.connect(DB_PATH)
    # 꺼낸 줄을 row["nickname"]처럼 칸 이름으로 읽을 수 있게 해요 (기본은 row[2]처럼 번호로만 읽혀요)
    conn.row_factory = sqlite3.Row
    return conn


# reviews 표가 없으면 새로 만들어요 (이미 있으면 아무 일도 안 해요)
def init_db():
    conn = get_connection()
    # try/finally: 중간에 에러가 나도 finally 부분(연결 끊기)은 꼭 실행돼요
    try:
        # 표 만들기. IF NOT EXISTS 덕분에 서버를 여러 번 켜도 안전해요
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                -- 리뷰 고유 번호. 1, 2, 3… 자동으로 매겨져요
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                -- 어느 클래스의 리뷰인지 (CSV의 클래스 id)
                class_id   INTEGER NOT NULL,
                -- 닉네임: 1~20자 (app.py의 NICKNAME_MAX와 같은 숫자)
                nickname   TEXT    NOT NULL CHECK (length(nickname) BETWEEN 1 AND 20),
                -- 별점: 1~5만 허용
                rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                -- 후기 내용: 1~500자 (app.py의 CONTENT_MAX와 같은 숫자)
                content    TEXT    NOT NULL CHECK (length(content) BETWEEN 1 AND 500),
                -- 저장 시각: '2026-11-11 14:30:05' 같은 글자
                created_at TEXT    NOT NULL
            )
        """)
        # 찾아보기(색인) 만들기: class_id로 리뷰를 빨리 찾을 수 있어요
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_class
            ON reviews (class_id, created_at)
        """)
        # 지금까지 한 일을 파일에 확정 저장해요 (commit 안 하면 저장이 안 돼요!)
        conn.commit()
    finally:
        # 연결을 끊어요 (전화 끊기)
        conn.close()


# 리뷰 한 개를 표에 넣고, 새로 생긴 리뷰 번호(id)를 돌려줘요
def add_review(class_id, nickname, rating, content):
    # 지금 시각을 '년-월-일 시:분:초' 글자로 만들어요
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        # 사용자 값은 SQL 글자에 직접 붙이지 않고 ? 자리에 따로 넘겨요
        # → 누가 닉네임에 SQL 명령을 써도 그냥 "글자"로만 저장돼요 (SQL 인젝션 방지)
        cur = conn.execute(
            "INSERT INTO reviews (class_id, nickname, rating, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            # 위의 ? 다섯 개에 순서대로 들어갈 값이에요
            (class_id, nickname, rating, content, created_at),
        )
        # 파일에 확정 저장해요
        conn.commit()
        # 방금 넣은 줄의 id를 돌려줘요
        return cur.lastrowid
    finally:
        conn.close()


# 클래스 하나의 리뷰를 최신순으로 꺼내서 딕셔너리 리스트로 돌려줘요
def get_reviews(class_id):
    conn = get_connection()
    try:
        # class_id도 바깥에서 온 값이라 ? 자리로 넘겨요
        # ORDER BY: 저장 시각이 늦은 것부터(DESC), 시각이 같으면 번호가 큰 것부터
        rows = conn.execute(
            "SELECT id, class_id, nickname, rating, content, created_at "
            "FROM reviews "
            "WHERE class_id = ? "
            "ORDER BY created_at DESC, id DESC",
            # ? 가 하나일 때도 끝에 쉼표를 붙여야 "묶음(튜플)"이 돼요
            (class_id,),
        ).fetchall()
        # 연결을 끊은 뒤에도 쓸 수 있게 한 줄씩 보통 딕셔너리로 바꿔요
        return [dict(row) for row in rows]
    finally:
        conn.close()
