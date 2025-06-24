import streamlit as st
import pandas as pd
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
import pickle # joblib 대신 pickle을 사용합니다.
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import os

# --- 기본 설정 ---
# 한글 폰트 설정 (윈도우 기본 폰트 사용)
# Colab, Linux 등 다른 환경에서는 NanumGothic 등 별도 폰트 설치가 필요할 수 있습니다.
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False
# 워드클라우드용 폰트 경로 (윈도우 기준)
FONT_PATH = "c:/Windows/Fonts/malgun.ttf"


# --- 1. 모델과 토크나이저 로드 (캐시 사용) ---
@st.cache_resource
def load_model_and_tokenizer():
    # 상대 경로로 수정
    model_path = "models/game_review_model.keras"
    tokenizer_path = "models/tokenizer.pkl"

    # 파일 존재 여부 확인
    if not os.path.exists(model_path) or not os.path.exists(tokenizer_path):
        st.error("모델 또는 토크나이저 파일을 'models' 폴더에서 찾을 수 없습니다. 훈련을 먼저 완료해주세요.")
        return None, None
        
    model = tf.keras.models.load_model(model_path)
    with open(tokenizer_path, 'rb') as f:
        tokenizer = pickle.load(f) # pickle.load로 수정
    return model, tokenizer

model, tokenizer = load_model_and_tokenizer()


# --- 2. 텍스트 처리 및 예측 함수 ---
def predict_sentiment(text):
    """단일 텍스트에 대한 감성을 예측합니다."""
    if model is None or tokenizer is None:
        return "모델 로드 실패", 0.0

    seq = tokenizer.texts_to_sequences([text])
    padded_seq = pad_sequences(seq, maxlen=100)
    pred = model.predict(padded_seq)
    label_idx = pred.argmax(axis=1)[0]
    label_map = {0: "부정", 1: "중립", 2: "긍정"}
    confidence = float(pred[0][label_idx]) # float으로 형변환
    return label_map.get(label_idx, "알 수 없음"), confidence

def preprocess_text_for_viz(text):
    """시각화를 위해 명사와 동사, 형용사만 추출하고 불용어를 제거합니다."""
    okt = Okt()
    # 의미있는 품사(명사, 동사, 형용사)만 추출
    morphs = okt.pos(text, stem=True)
    words = [word for word, pos in morphs if pos in ['Noun', 'Verb', 'Adjective'] and len(word) > 1]
    return words

# --- 3. 스트림릿 UI 구성 ---
st.title("🎮 게임 리뷰 감성 분석 데모")
st.markdown("---")

# 섹션 1: 단일 리뷰 분석
st.header("1. 텍스트 감성 분석")
user_input = st.text_area("분석할 리뷰 텍스트를 입력하세요:", height=100)

if st.button("분석 실행"):
    if not user_input.strip():
        st.warning("텍스트를 입력해 주세요.")
    else:
        with st.spinner('분석 중...'):
            label, confidence = predict_sentiment(user_input)
            if label == "긍정":
                st.success(f"**{label}** 리뷰입니다. (확신도: {confidence:.2f})")
            elif label == "부정":
                st.error(f"**{label}** 리뷰입니다. (확신도: {confidence:.2f})")
            else:
                st.info(f"**{label}** 리뷰입니다. (확신도: {confidence:.2f})")

st.markdown("---")

# 섹션 2: 파일 업로드 및 전체 데이터 분석
st.header("2. CSV 파일 전체 분석")
uploaded_file = st.file_uploader("리뷰 데이터가 포함된 CSV 파일을 업로드하세요.", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("**업로드된 데이터 미리보기:**", df.head())

        # 리뷰가 담긴 컬럼 선택
        review_column = st.selectbox("리뷰가 포함된 컬럼을 선택하세요:", df.columns)
        
        if review_column:
            # 데이터 처리 (캐시 사용으로 반복 계산 방지)
            @st.cache_data
            def process_data(dataf, col):
                dataf.dropna(subset=[col], inplace=True)
                all_reviews_text = " ".join(dataf[col].astype(str).tolist())
                processed_words = preprocess_text_for_viz(all_reviews_text)
                return Counter(processed_words)

            word_counts = process_data(df, review_column)

            st.subheader("주요 단어 분석")
            top_n = st.slider("차트에 표시할 상위 단어 개수", 10, 100, 30)

            # 막대 그래프
            top_words = word_counts.most_common(top_n)
            top_df = pd.DataFrame(top_words, columns=['단어', '빈도수'])

            fig_bar, ax = plt.subplots(figsize=(12, 8))
            sns.barplot(x='빈도수', y='단어', data=top_df, palette='viridis', ax=ax)
            ax.set_title(f'가장 많이 등장한 단어 TOP {top_n}')
            st.pyplot(fig_bar)

            # 워드클라우드
            st.subheader("워드클라우드 시각화")
            # WordCloud 객체 생성 시 폰트 경로 확인
            try:
                wc = WordCloud(width=800, height=400, background_color='white', font_path=FONT_PATH).generate_from_frequencies(word_counts)
                fig_wc, ax = plt.subplots(figsize=(12, 6))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig_wc)
            except Exception as e:
                st.error(f"워드클라우드 생성 중 오류: {e}")
                st.info("폰트 파일을 찾을 수 없는 경우 발생할 수 있습니다. `FONT_PATH` 변수를 확인해주세요.")

    except Exception as e:
        st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")