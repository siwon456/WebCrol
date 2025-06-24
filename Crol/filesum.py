import pandas as pd
import glob
import os

# 합칠 CSV 파일들이 있는 폴더 경로를 지정하세요.
folder_path = 'D:/_DeepNLP25/melon/review/'  # 실제 폴더 경로로 변경해주세요.

# 해당 폴더의 모든 CSV 파일 목록을 가져옵니다.
all_files = glob.glob(os.path.join(folder_path, "*.csv"))

# 빈 DataFrame을 생성하여 합쳐진 데이터를 저장합니다.
combined_df = pd.DataFrame()

# 각 CSV 파일을 읽어서 combined_df에 추가합니다.
for f in all_files:
    try:
        df = pd.read_csv(f)
        combined_df = pd.concat([combined_df, df], ignore_index=True)
        print(f"'{f}' 파일을 합쳤습니다.")
    except FileNotFoundError:
        print(f"오류: '{f}' 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"'{f}' 파일을 읽는 중 오류 발생: {e}")

# 중복된 행을 제거합니다.
print("\n중복 제거 전 행 수:", len(combined_df))
combined_df_no_duplicates = combined_df.drop_duplicates()
print("중복 제거 후 행 수:", len(combined_df_no_duplicates))

# 합쳐지고 중복치가 제거된 DataFrame을 확인합니다.
print("\n합쳐지고 중복치가 제거된 DataFrame의 처음 몇 행:")
print(combined_df_no_duplicates.head())

# 합쳐지고 중복치가 제거된 DataFrame을 새로운 CSV 파일로 저장 (선택 사항)
output_file = 'combined_reviews2.csv'
combined_df_no_duplicates.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n합쳐진 후 중복치가 제거된 데이터를 '{output_file}'로 저장했습니다.")