import time
import csv
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 Safari/537.36"
)

def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={PC_USER_AGENT}")
    return webdriver.Chrome(options=options)

def get_game_app_ids(keyword, max_apps=5):
    search_url = f"https://play.google.com/store/search?q={quote(keyword)}&c=games&hl=ko&gl=US"
    driver = create_driver()
    driver.get(search_url)

    app_ids = []
    seen = set()

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@href, "/store/apps/details?id=")]'))
        )
        links = driver.find_elements(By.XPATH, '//a[contains(@href, "/store/apps/details?id=")]')

        for link in links:
            href = link.get_attribute("href")
            if href and "/store/apps/details?id=" in href:
                app_id = href.split("id=")[-1].split("&")[0]
                if app_id not in seen:
                    seen.add(app_id)
                    app_ids.append(app_id)
            if len(app_ids) >= max_apps:
                break

        print(f"🎯 추출된 앱 ID 목록: {app_ids}")

    except Exception as e:
        print("❌ 앱 ID 추출 실패:", e)

    driver.quit()
    return app_ids

def collect_reviews(app_id, max_reviews=10000):
    url = f"https://play.google.com/store/apps/details?id={app_id}&hl=ko&gl=US"
    driver = create_driver()
    driver.get(url)

    reviews = []
    seen_texts = set()

    try:
        review_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'VfPpkd-LgbsSe') and (contains(., '평점 및 리뷰') or contains(., '리뷰 모두 보기'))]"))
        )
        review_button.click()
        print(f" [{app_id}] 리뷰 탭 클릭됨")
        time.sleep(2)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.fysCi'))
        )

        scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div.fysCi')

        scroll_count = 0
        max_scroll = 1000
        stagnant_scrolls = 0
        last_count = 0

        while len(reviews) < max_reviews and scroll_count < max_scroll:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(2)
            scroll_count += 1

            review_elements = driver.find_elements(By.CSS_SELECTOR, 'div.RHo1pe')
            print(f"🔄 스크롤 {scroll_count}: 리뷰 {len(review_elements)}개")

            for elem in review_elements:
                try:
                    text = elem.find_element(By.CSS_SELECTOR, 'div.h3YV2d').text.strip()
                    rating_text = elem.find_element(By.CSS_SELECTOR, 'div[role="img"]').get_attribute("aria-label")

                    #  평점 정확히 추출
                    if "만점에" in rating_text:
                        rating = rating_text.split("만점에")[-1].split("개")[0].strip()
                    else:
                        rating = ""

                    if text and text not in seen_texts:
                        reviews.append((app_id, rating, text))
                        seen_texts.add(text)
                        if len(reviews) >= max_reviews:
                            break
                except Exception:
                    continue

            if len(reviews) == last_count:
                stagnant_scrolls += 1
                if stagnant_scrolls >= 5:
                    print("⏹ 더 이상 로딩되지 않음, 종료")
                    break
            else:
                stagnant_scrolls = 0
                last_count = len(reviews)

        print(f"✅ [{app_id}] 총 {len(reviews)}개 리뷰 수집 완료")

    except Exception as e:
        print(f"⚠️ [{app_id}] 리뷰 수집 실패: {e}")

    driver.quit()
    return reviews

def save_reviews_all(all_reviews, filename="all_game_reviews11.csv"):
    try:
        # 저장 디렉토리 확인 및 생성
        folder = os.path.dirname(filename)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        with open(filename, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["앱ID", "평점", "리뷰"])

            if not all_reviews:
                print("⚠️ 저장할 리뷰가 없습니다. 헤더만 저장합니다.")
            else:
                for app_id, rating, review in all_reviews:
                    writer.writerow([app_id, rating, review])

        print(f"💾 전체 리뷰 저장 완료: {os.path.abspath(filename)}")

    except Exception as e:
        print(f"❌ 리뷰 저장 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    keyword = input("게임 키워드를 입력하세요: ").strip()
    app_ids = get_game_app_ids(keyword, max_apps=5)

    all_reviews = []
    for app_id in app_ids:
        reviews = collect_reviews(app_id, max_reviews=10000)
        all_reviews.extend(reviews)

    save_reviews_all(all_reviews)
    print("🎉 모든 게임 리뷰 수집 및 통합 저장 완료!")
