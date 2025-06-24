import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Bidirectional, LSTM, Dense, Dropout # 1. 드롭아웃 임포트
from tensorflow.keras.callbacks import EarlyStopping # 2. 조기종료 임포트

# --- 데이터 로드 및 전처리 ---

df = pd.read_csv('D:/_DeepNLP25/melon/model/merged_label_final.csv')
df.dropna(subset=['content', 'label'], inplace=True)
df['label'] = df['label'].astype(int)
df = df[df['label'].isin([0, 1, 2])].copy()

reviews = df['content'].values
labels = df['label'].values

# --- 토크나이저 및 패딩 ---

tokenizer = Tokenizer()
tokenizer.fit_on_texts(reviews)
with open('tokenizer.pkl', 'wb') as f:
    pickle.dump(tokenizer, f)

vocab_size = len(tokenizer.word_index) + 1
sequences = tokenizer.texts_to_sequences(reviews)
max_len = 147
padded_sequences = pad_sequences(sequences, maxlen=max_len, padding='post')

# --- 훈련/검증 데이터 분리 ---

X_train, X_val, y_train, y_val = train_test_split(padded_sequences, labels, test_size=0.2, random_state=42)

# --- BiLSTM 모델 정의 (드롭아웃 추가) ---

model = Sequential([
    Embedding(vocab_size, 64, input_length=max_len),
    Bidirectional(LSTM(64)),
    Dropout(0.5),  # [1. 드롭아웃 추가] BiLSTM 레이어 다음에 40% 드롭아웃
    Dense(32, activation='relu'),
    Dropout(0.4),  # [1. 드롭아웃 추가] Dense 레이어 다음에 30% 드롭아웃
    Dense(3, activation='softmax')
])

# --- 모델 컴파일 ---

optimizer = tf.keras.optimizers.Adam(learning_rate=0.0001, clipnorm=1.0)
model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# --- 조기 종료(EarlyStopping) 콜백 정의 ---

# [2. 조기 종료 추가]
# val_loss를 지켜보다가, 3번의 epoch 동안 개선이 없으면 훈련을 중단합니다.
# restore_best_weights=True는 가장 좋았던 시점의 가중치로 모델을 자동 복원합니다.
early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

# --- 모델 훈련 (조기 종료 적용) ---

# epochs는 넉넉하게 50으로 설정해도, 조기 종료가 알아서 최적의 시점에 멈춰줍니다.
model.fit(X_train, y_train, 
          validation_data=(X_val, y_val), 
          epochs=50, 
          batch_size=32,
          callbacks=[early_stopping]) # [2. 조기 종료 추가] 콜백 적용

# --- 훈련된 모델 저장 ---

model.save('game_review_model.keras')
print("모델(game_review_model.keras)과 토크나이저(tokenizer.pkl) 저장 완료!")