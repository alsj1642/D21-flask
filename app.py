# Flask 도구 상자에서 꺼내 와요
# Flask: 식당을 만드는 틀 / render_template: 화면 틀에 내용을 채워 주는 도구 / request: 손님 주문서(주소 뒤 ?값 포함)
# abort: "더 진행하지 말고 이 상태 코드로 끝내!"라고 외치는 도구예요 (예: abort(404))
# jsonify: 파이썬 딕셔너리·리스트를 JSON 응답으로 바꿔 주는 도구예요
# redirect: "이 주소로 다시 가세요"(302)라고 브라우저에게 알려 주는 도구예요
# url_for: 함수 이름으로 주소를 만들어 주는 도구예요 (예: class_detail → /class/3)
# flash: 다음 화면에 "딱 한 번만" 보여 줄 안내 문구를 맡겨 두는 도구예요
# session: 브라우저(손님)마다 따로 기억해 두는 보관함이에요 (찜 목록을 여기에 담아요)
from flask import Flask, render_template, request, abort, jsonify, redirect, url_for, flash, session
# os: 컴퓨터의 환경 변수(비밀 값 등)를 읽는 도구예요
import os
# Path: 파일 위치(경로)를 다루는 도구예요
from pathlib import Path
# load_dotenv: .env 파일에 적힌 값을 환경 변수로 불러와 주는 도구예요 (python-dotenv)
from dotenv import load_dotenv

# 이 파일(app.py) 옆에 있는 .env를 읽어서 환경 변수로 등록해요
# .env가 없으면(배포 서버 등) 조용히 넘어가요 → 그때는 서버 설정 화면에 적은 환경 변수를 써요
load_dotenv(Path(__file__).resolve().parent / ".env")

# 우리가 만든 db.py에서 리뷰 저장·꺼내기 함수들을 가져와요
from db import init_db, add_review, get_reviews

# 우리가 만든 data.py에서 데이터 다루는 함수들을 가져와요
from data import (
    load_classes,
    get_categories,
    get_class,
    filter_and_sort,
    count_by_category,
    get_stats,
)

# 우리 식당(웹 앱)을 하나 열어요. __name__은 "이 파일이 식당 본점"이라는 표시예요
app = Flask(__name__)

# JSON에서 한글을 공 같은 암호 대신 "공예" 그대로 내보내요
app.json.ensure_ascii = False
# JSON 칸 순서를 가나다/abc순으로 섞지 말고, 우리가 적은 순서 그대로 내보내요
app.json.sort_keys = False

# session·flash를 쓰려면 비밀 열쇠가 꼭 있어야 해요
# (보관함(session) 내용을 쿠키에 담아 브라우저에 맡기는데, 손님이 몰래 고치지 못하게 도장을 찍는 열쇠예요)
# 열쇠는 코드에 적지 않고 .env(또는 서버 환경 변수)의 SECRET_KEY에서 읽어요
secret_key = os.environ.get("SECRET_KEY")
# 열쇠가 없으면 서버를 켜지 않고 이유를 알려 줘요
# (아무 열쇠나 대충 쓰고 켜지는 것보다, 처음부터 멈추는 게 더 안전해요)
if not secret_key:
    raise RuntimeError("SECRET_KEY가 없어요. .env.example을 보고 .env 파일에 SECRET_KEY를 적어 주세요.")
app.secret_key = secret_key

# 정렬 상자에 보여 줄 선택지예요: (주소에 들어갈 값, 화면에 보일 글자)
SORT_OPTIONS = [("", "기본순"), ("price", "가격 낮은 순"), ("rating", "평점 높은 순")]

# 서버가 켜질 때 reviews 표가 없으면 만들어 둬요 (이미 있으면 그대로 둬요)
# 이제 후기는 reviews.db 파일에 저장돼서 서버를 껐다 켜도 남아 있어요
init_db()

# 글자 수 제한이에요. 화면(HTML)과 서버 검사에서 같은 숫자를 써요
# (db.py의 CHECK 숫자와도 맞춰 두었어요. 바꿀 때는 두 곳을 같이 바꿔요)
NICKNAME_MAX = 20
CONTENT_MAX = 500


# ───────── 찜하기 도우미 ─────────

# 보관함(session)에서 내 찜 목록(클래스 번호 리스트, 예: [3, 7])을 꺼내요. 처음이면 빈 리스트예요
def get_wishlist():
    return session.get("wishlist", [])


# context_processor: 모든 화면(템플릿)에 자동으로 값을 넣어 줘요
# 그래서 base.html 메뉴의 '찜 목록 (개수)'가 어느 화면에서든 보여요
@app.context_processor
def inject_wish_count():
    return {"wish_count": len(get_wishlist())}


# 메뉴판 첫 줄: 손님이 주소 "/"(첫 화면)로 오면 아래 함수가 담당해요
@app.route("/")
def home():
    # CSV에서 클래스 목록을 읽어요
    classes = load_classes()
    # home.html에 전체 개수와 카테고리별 개수({"공예": 11, ...})를 넘겨줘요
    return render_template(
        "home.html", total=len(classes), category_counts=count_by_category(classes)
    )


# 메뉴판 두 번째 줄: 서비스 소개 화면
@app.route("/about")
def about():
    return render_template("about.html")


# 메뉴판 세 번째 줄: "/hello/" 뒤에 오는 글자를 name으로 받아요
@app.route("/hello/<name>")
def hello(name):
    # 템플릿이 위험한 글자를 자동으로 안전하게 바꿔 줘요 (자동 이스케이프)
    return render_template("hello.html", name=name)


# 메뉴판 네 번째 줄: 클래스 목록 화면
# 예) /classes?category=공예&sort=price
@app.route("/classes")
def class_list():
    # 주소의 ? 뒤에서 category 값을 꺼내요. 없으면 빈 글자("")
    category = request.args.get("category", "")
    # 주소의 ? 뒤에서 sort 값을 꺼내요. 없으면 빈 글자("")
    sort = request.args.get("sort", "")

    # CSV에서 클래스 목록을 읽어요
    all_classes = load_classes()
    # 고른 카테고리로 거르고, 고른 순서로 정렬해요
    result = filter_and_sort(all_classes, category, sort)

    # classes.html에 필요한 재료를 모두 넘겨줘요
    return render_template(
        "classes.html",
        classes=result,                            # 화면에 보여 줄 클래스들
        categories=get_categories(all_classes),    # 카테고리 상자에 넣을 선택지
        sort_options=SORT_OPTIONS,                 # 정렬 상자에 넣을 선택지
        selected_category=category,                # 지금 고른 카테고리 (상자에 표시해 두려고)
        selected_sort=sort,                        # 지금 고른 정렬 (상자에 표시해 두려고)
    )


# 메뉴판 다섯 번째 줄: 클래스 하나의 상세 화면 + 수강후기
# <int:class_id>는 "숫자만 받아요"라는 뜻이에요. /class/abc처럼 숫자가 아니면 바로 404가 나요
# methods=["GET", "POST"]: 엽서(GET, 화면 보기)와 봉투(POST, 후기 저장)를 둘 다 받아요
@app.route("/class/<int:class_id>", methods=["GET", "POST"])
def class_detail(class_id):
    # 번호로 클래스를 찾아요
    c = get_class(load_classes(), class_id)
    # 못 찾았으면(None) 여기서 멈추고 404로 끝내요 → 아래 not_found 함수가 화면을 그려 줘요
    if c is None:
        abort(404)

    # 칸별 안내 문구를 담을 빈 딕셔너리예요. 비어 있으면 "문제 없음"이에요
    errors = {}
    # 폼 칸에 다시 채워 줄 값이에요. 처음엔 모두 빈칸이에요
    form = {"nickname": "", "rating": "", "content": ""}

    # 봉투(POST)가 왔을 때만, 즉 저장 버튼을 눌렀을 때만 아래를 실행해요
    if request.method == "POST":
        # 봉투 안(request.form)에서 닉네임을 꺼내고 앞뒤 공백을 지워요
        form["nickname"] = request.form.get("nickname", "").strip()
        # 봉투 안에서 별점을 꺼내요. 아직 글자 상태예요 (예: "5")
        form["rating"] = request.form.get("rating", "")
        # 봉투 안에서 후기 내용을 꺼내고 앞뒤 공백을 지워요
        form["content"] = request.form.get("content", "").strip()

        # 닉네임이 비었으면 안내 문구를 적어 둬요
        if form["nickname"] == "":
            errors["nickname"] = "닉네임을 적어 주세요."
        # 닉네임이 너무 길면 안내 문구를 적어 둬요
        elif len(form["nickname"]) > NICKNAME_MAX:
            errors["nickname"] = f"닉네임은 {NICKNAME_MAX}자까지 쓸 수 있어요."

        # 별점이 "1"~"5" 중 하나가 아니면 안내 문구를 적어 둬요 (누가 몰래 "99"를 보내도 막아요)
        if form["rating"] not in ["1", "2", "3", "4", "5"]:
            errors["rating"] = "별점을 1~5점 중에서 골라 주세요."

        # 후기 내용이 비었으면 안내 문구를 적어 둬요
        if form["content"] == "":
            errors["content"] = "후기 내용을 적어 주세요."
        # 후기 내용이 너무 길면 안내 문구를 적어 둬요
        elif len(form["content"]) > CONTENT_MAX:
            errors["content"] = f"후기는 {CONTENT_MAX}자까지 쓸 수 있어요."

        # 안내 문구가 하나도 없으면 = 모든 칸이 올바르면 저장해요
        if not errors:
            # 후기 한 개를 DB(reviews.db)에 넣어요. 저장 시각은 db.py가 알아서 적어요
            add_review(
                class_id,              # 어느 클래스의 후기인지
                form["nickname"],      # 닉네임
                int(form["rating"]),   # 별점 ("5" → 숫자 5)
                form["content"],       # 후기 내용
            )
            # 성공 안내를 맡겨 둬요. 다음 화면에서 딱 한 번 보여 주고 사라져요
            # "success"는 안내 종류 이름표예요 (화면에서 색을 다르게 칠할 때 써요)
            flash("후기가 저장됐어요", "success")
            # ── PRG의 R(Redirect) ──
            # 저장했으면 같은 주소로 다시 가라고 알려 줘요(302) → 브라우저가 GET으로 다시 열어요
            # 그래서 브라우저의 "마지막 요청"이 POST가 아니라 GET이 돼요 → 새로고침해도 GET만 다시 가요
            # _anchor="reviews": 주소 끝에 #reviews를 붙여서 후기 목록 위치로 바로 내려가요
            return redirect(url_for("class_detail", class_id=class_id, _anchor="reviews"))

    # DB에서 이 클래스의 후기만 최신순으로 꺼내요 (거르기·정렬은 db.py의 SQL이 해 줘요)
    reviews = get_reviews(class_id)

    # 안내 문구가 있으면(잘못 보냈으면) 400, 아니면 200(정상)이에요
    status = 400 if errors else 200
    # 상세 화면에 클래스 정보, 후기 목록, 폼 값, 안내 문구를 함께 넘겨줘요
    return render_template(
        "class_detail.html",
        c=c,
        reviews=reviews,
        form=form,
        errors=errors,
        is_wished=class_id in get_wishlist(),   # 이미 찜했는지 (버튼 글자를 바꾸려고)
        nickname_max=NICKNAME_MAX,
        content_max=CONTENT_MAX,
    ), status


# 찜하기 / 찜 취소 버튼이 보내는 곳이에요
# 값을 바꾸는 일이라 POST만 받아요 (주소창에 쳐서 들어오는 GET은 405로 막혀요)
@app.route("/class/<int:class_id>/wish", methods=["POST"])
def toggle_wish(class_id):
    # 없는 클래스 번호면 404로 끝내요 (이상한 번호가 찜 목록에 쌓이지 않게)
    if get_class(load_classes(), class_id) is None:
        abort(404)

    # 지금 찜 목록을 복사해서 꺼내요 (list(...)로 새 리스트를 만들어요)
    wishlist = list(get_wishlist())
    # 이미 찜한 클래스면 → 목록에서 빼요 (찜 취소)
    if class_id in wishlist:
        wishlist.remove(class_id)
    # 아직 안 찜한 클래스면 → 목록 맨 뒤에 넣어요 (찜하기)
    else:
        wishlist.append(class_id)
    # 바뀐 목록을 보관함에 다시 넣어요. 이렇게 "새로 넣어야" Flask가 바뀐 걸 알아채고 쿠키를 고쳐 보내요
    session["wishlist"] = wishlist

    # PRG: 상세 화면으로 다시 보내요(302) → 새로고침해도 찜이 다시 바뀌지 않아요
    return redirect(url_for("class_detail", class_id=class_id))


# 내 찜 목록 화면
@app.route("/wishlist")
def wishlist():
    # 클래스 번호로 바로 찾을 수 있게 {번호: 클래스} 사전을 만들어요
    by_id = {c["id"]: c for c in load_classes()}
    # 찜 목록의 번호를 최근에 찜한 것부터(reversed) 꺼내서 클래스 정보로 바꿔요
    # if i in by_id: CSV에서 사라진 클래스 번호는 건너뛰어요
    classes = [by_id[i] for i in reversed(get_wishlist()) if i in by_id]
    return render_template("wishlist.html", classes=classes)


# ───────── 여기부터 JSON API (사람 대신 프로그램이 읽는 주소) ─────────
# 빈칸은 파이썬 None으로 담겨 있어서, jsonify가 JSON의 null로 자동으로 바꿔 줘요


# API 1: 전체 목록. 예) /api/classes?category=공예
@app.route("/api/classes")
def api_classes():
    # 주소의 ? 뒤에서 category 값을 꺼내요. 없으면 빈 글자("") → 전체
    category = request.args.get("category", "")
    # 화면 목록과 같은 함수로 걸러요 (정렬은 안 함 = id 순)
    result = filter_and_sort(load_classes(), category)
    # 개수와 목록을 함께 JSON으로 돌려줘요 (상태 코드는 기본값 200)
    return jsonify({"count": len(result), "classes": result})


# API 2: 클래스 하나. 예) /api/classes/2
@app.route("/api/classes/<int:class_id>")
def api_class_detail(class_id):
    # 번호로 클래스를 찾아요
    c = get_class(load_classes(), class_id)
    # 못 찾았으면 404로 끝내요 → 아래 not_found가 /api/ 주소인 걸 보고 JSON 에러를 돌려줘요
    if c is None:
        abort(404)
    # 찾았으면 그 클래스 하나를 JSON으로 돌려줘요
    return jsonify(c)


# API 3: 통계. 예) /api/stats
@app.route("/api/stats")
def api_stats():
    # 계산은 data.py의 get_stats가 하고, 여기서는 JSON으로 내보내기만 해요
    return jsonify(get_stats(load_classes()))


# 404가 생기면 언제나 이 함수가 응답을 만들어요 (없는 번호, 없는 주소 모두)
@app.errorhandler(404)
def not_found(error):
    # 주소가 /api/로 시작하면 프로그램이 읽는 곳이니까 JSON으로 에러를 알려 줘요
    if request.path.startswith("/api/"):
        return jsonify({"error": "not_found", "message": "찾는 데이터가 없어요"}), 404
    # 그 밖의 주소는 사람이 보는 화면으로 돌려줘요
    # 쉼표 뒤에 404를 안 쓰면 화면은 404처럼 보여도 상태 코드는 200(정상)이 돼 버려요!
    return render_template("404.html"), 404


# 코드에서 예상 못 한 에러가 나면(500) 이 함수가 응답을 만들어요
# (debug가 켜진 내 컴퓨터에서는 이 화면 대신 자세한 에러 화면이 나와요. 배포 서버에서만 보여요)
# 에러 내용 자체는 Flask가 서버 로그에 자동으로 적어 줘요 → 손님에게는 자세한 내용을 숨겨요
@app.errorhandler(500)
def server_error(error):
    # /api/ 주소면 프로그램이 읽는 곳이니까 JSON으로 알려 줘요
    if request.path.startswith("/api/"):
        return jsonify({"error": "server_error", "message": "잠시 문제가 생겼어요"}), 500
    # 사람이 보는 화면은 친절한 안내 화면으로 보여 줘요. 상태 코드 500을 꼭 같이 돌려줘요
    return render_template("500.html"), 500


# 이 파일을 직접 실행했을 때만 아래 줄이 동작해요 (python app.py)
# 배포 서버의 gunicorn은 이 부분을 거치지 않아서 debug가 켜지지 않아요
if __name__ == "__main__":
    # .env의 FLASK_DEBUG가 "1"일 때만 debug를 켜요 → 내 컴퓨터에서만 켜져요
    debug = os.environ.get("FLASK_DEBUG") == "1"
    # 식당 문을 열어요. debug가 켜지면 코드를 고쳤을 때 자동으로 다시 켜져요
    app.run(debug=debug)
