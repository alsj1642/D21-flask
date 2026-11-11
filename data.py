# 클래스 데이터를 읽고, 거르고, 정렬하는 일만 맡는 파일이에요 (화면 만드는 일은 app.py 담당)

# csv: 쉼표로 나뉜 표 파일을 읽는 파이썬 기본 도구예요 (따로 설치할 필요 없어요)
import csv
# Path: 파일 위치(경로)를 다루는 도구예요
from pathlib import Path

# 이 파일(data.py)이 있는 폴더(D21-flask) "안"의 data/classes.csv를 가리켜요
# 프로젝트 폴더 안에 있어야 git에 같이 올라가서 배포 서버에서도 찾을 수 있어요
CSV_PATH = Path(__file__).resolve().parent / "data" / "classes.csv"


# 글자를 숫자로 바꿔 주는 도우미예요. 비어 있으면 0이 아니라 None(값 없음)을 돌려줘요
def to_number(text):
    # 앞뒤 공백을 지워요. 값이 아예 없을 때(None)를 대비해 빈 글자로 바꿔 둬요
    text = (text or "").strip()
    # 빈 글자이거나 "nan"이라고 적혀 있으면 "값 없음"으로 처리해요
    if text == "" or text.lower() == "nan":
        return None
    # "25000.0" 같은 글자를 숫자 25000.0으로 바꿔요
    return float(text)


# CSV 파일을 읽어서 클래스 한 개당 딕셔너리 한 개씩 담긴 리스트로 돌려줘요
def load_classes():
    # 결과를 담을 빈 리스트예요
    classes = []
    # 파일을 열어요. utf-8-sig는 파일 맨 앞의 보이지 않는 표시(BOM)를 지워 줘요
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        # 한 줄씩 읽어요. 첫 줄(제목 줄)이 각 칸의 이름이 돼요
        for row in csv.DictReader(f):
            # 정가, 할인가, 평점, 리뷰수를 숫자로 바꿔요 (비어 있으면 None)
            list_price = to_number(row["정가"])
            discount = to_number(row["할인가"])
            rating = to_number(row["평점"])
            reviews = to_number(row["리뷰수"])

            # 판매가: 할인가가 있으면 할인가, 없으면 정가 (둘 다 없으면 None)
            sale_price = discount if discount is not None else list_price

            # 할인 중인지: 정가와 할인가가 둘 다 있고, 할인가가 더 쌀 때만 True
            on_sale = (
                list_price is not None
                and discount is not None
                and discount < list_price
            )

            # 화면에서 쓰기 좋게 정리해서 리스트에 넣어요
            classes.append({
                "id": int(row["id"]),
                "category": row["카테고리"].strip(),
                "region": row["지역"].strip(),
                "title": row["클래스명"].strip(),
                # 가격은 25000.0 → 25000처럼 정수로 바꿔요. None이면 그대로 None
                "list_price": int(list_price) if list_price is not None else None,
                "sale_price": int(sale_price) if sale_price is not None else None,
                "on_sale": on_sale,
                # 평점은 소수점 그대로 둬요 (예: 4.4)
                "rating": rating,
                # 리뷰 수가 비어 있으면 0개로 봐요 (리뷰 "개수"라서 0이 맞는 뜻이에요)
                "reviews": int(reviews) if reviews is not None else 0,
            })
            # 리뷰가 있는 클래스인지 미리 계산해서 같이 넣어 둬요 (목록·상세 화면이 똑같이 씀)
            classes[-1]["has_reviews"] = has_reviews(classes[-1])
    # 다 담은 리스트를 돌려줘요
    return classes


# 카테고리 이름을 중복 없이 가나다순으로 모아 줘요 (예: ["공예", "드로잉", ...])
def get_categories(classes):
    return sorted({c["category"] for c in classes})


# 리뷰가 있는 클래스인지 확인해요: 평점이 있고 리뷰가 1개 이상이어야 해요
def has_reviews(c):
    return c["rating"] is not None and c["reviews"] > 0


# 카테고리마다 클래스가 몇 개인지 세어요. 예) {"공예": 11, "드로잉": 8, ...}
def count_by_category(classes):
    # 카테고리 이름마다 0으로 시작하는 칸을 만들어요 (가나다순)
    counts = {cat: 0 for cat in get_categories(classes)}
    # 클래스를 하나씩 보면서 자기 카테고리 칸에 1씩 더해요
    for c in classes:
        counts[c["category"]] += 1
    return counts


# 숫자 리스트의 평균을 구해요. 리스트가 비어 있으면 0이 아니라 None(값 없음)
def average(numbers):
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


# 전체 통계를 계산해요 (/api/stats에서 써요)
def get_stats(classes):
    # 판매가가 있는 클래스의 판매가만 모아요 (빈칸=None은 빼요)
    prices = [c["sale_price"] for c in classes if c["sale_price"] is not None]
    # 평점이 있는 클래스의 평점만 모아요 (빈칸=None은 빼요)
    ratings = [c["rating"] for c in classes if c["rating"] is not None]

    # 평균을 구해요. 값이 없으면 None
    avg_price = average(prices)
    avg_rating = average(ratings)

    return {
        # 전체 클래스 수
        "total": len(classes),
        # 평균 판매가: 원 단위라 소수점 없이 반올림 (값이 없으면 None → JSON에서 null)
        "avg_sale_price": round(avg_price) if avg_price is not None else None,
        # 가격 문의 수: 판매가가 빈칸인 클래스 수 = 전체 - 가격 있는 클래스
        "price_inquiry_count": len(classes) - len(prices),
        # 평균 평점: 소수점 둘째 자리까지 반올림
        "avg_rating": round(avg_rating, 2) if avg_rating is not None else None,
        # 리뷰 없음 수: 리뷰가 없는 클래스 수 (화면의 '아직 리뷰가 없어요'와 같은 기준)
        "no_review_count": sum(1 for c in classes if not c["has_reviews"]),
        # 카테고리별 개수
        "category_counts": count_by_category(classes),
    }


# 번호(id)로 클래스 하나를 찾아요. 없으면 None을 돌려줘요
def get_class(classes, class_id):
    # 하나씩 보면서 번호가 같은 클래스를 찾으면 바로 돌려줘요
    for c in classes:
        if c["id"] == class_id:
            return c
    # 끝까지 못 찾았으면 "없음"
    return None


# 카테고리로 거르고, 원하는 순서로 정렬해서 돌려줘요
def filter_and_sort(classes, category="", sort=""):
    # 카테고리를 골랐다면 그 카테고리만 남겨요 (안 골랐으면 전부)
    if category:
        classes = [c for c in classes if c["category"] == category]

    # 싼 순: 가격 문의(None)는 맨 뒤로 보내고, 나머지는 판매가가 낮은 순서로
    if sort == "price":
        # (True/False, 가격) 짝으로 비교해요. False가 True보다 앞이라 가격 있는 것이 먼저 와요
        classes = sorted(classes, key=lambda c: (c["sale_price"] is None, c["sale_price"] or 0))
    # 평점순: 리뷰 없는 클래스는 맨 뒤로, 나머지는 평점 높은 순 → 같으면 리뷰 많은 순
    elif sort == "rating":
        classes = sorted(
            classes,
            key=lambda c: (not c["has_reviews"], -(c["rating"] or 0), -c["reviews"]),
        )
    # 정렬을 안 골랐으면 파일에 적힌 순서(id 순) 그대로예요

    # 결과 리스트를 돌려줘요
    return classes
