import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import concurrent.futures
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_spreadsheet_data(sheet_url, sheet_name):
    # API 범위 설정
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    # 서비스 계정 인증 정보 (JSON 파일)
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', scope)
    
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_url(sheet_url)
    worksheet = sheet.worksheet(sheet_name)
    data = worksheet.get_all_records()

    df = pd.DataFrame(data)
    
    return df, worksheet, sheet

def filtered_column(df, columns_name):
    # 데이터프레임 복사
    df = df.copy()
    df = df[columns_name]
    return df

# 쓰레드 안전성을 위한 OpenAI API 호출 함수 제거
# openai_lock = threading.Lock()

def get_llm(model_name: str = "gpt-4o-mini"):
    """
    모델 이름에 따라 적절한 LLM 인스턴스를 반환하는 함수
    
    Args:
        model_name (str): 사용할 모델 이름 ("gpt-4o-mini", "gemini-pro" 등)
    """
    if model_name.startswith("gemini"):
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0
        )
    else:
        return ChatOpenAI(
            model_name=model_name,
            temperature=0
        )

def analyst(system_prompt, user_prompt, model_name="gpt-4o-mini"):
    """
    AI 모델을 사용하여 분석을 수행하는 함수
    
    Args:
        system_prompt (str): 시스템 프롬프트
        user_prompt (str): 사용자 프롬프트
        model_name (str): 사용할 모델 이름 (기본값: "gpt-4o-mini")
    """
    llm = get_llm(model_name)
    
    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.content

def process_row(data, system_prompt, model_name="gpt-4o-mini"):
    # 네임드튜플에서 데이터 추출
    row_dict = {col: getattr(data, col) for col in data._fields if col != 'Index'}
    
    # 데이터를 JSON 형태로 구조화
    formatted_json = json.dumps(row_dict, ensure_ascii=False, indent=2)
    
    result = analyst(system_prompt, formatted_json, model_name)
    
    # 결과와 행 인덱스를 함께 반환
    return {"result": result, "row_index": data.Index + 2}  # +2는 헤더행(1) + 0-인덱스 보정(1)

# 열 인덱스(숫자)를 스프레드시트 열 문자(A, B, ..., Z, AA, AB, ...)로 변환하는 함수
def col_num_to_letter(n):
    """숫자를 스프레드시트 열 문자로 변환 (1=A, 2=B, ..., 27=AA, ...)"""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def analyze_data_with_ai_and_update_sheet(input_url, input_sheet_name, input_columns_name, system_prompt, new_column_name, model_name="gpt-4o-mini"):
    """
    스프레드시트의 데이터를 AI로 분석하고 결과를 스프레드시트에 업데이트하는 함수
    
    Args:
        input_url (str): 구글 스프레드시트 URL
        input_sheet_name (str): 작업할 시트 이름
        input_columns_name (list): 분석에 사용할 열 이름 목록
        system_prompt (str): AI 모델에 전달할 시스템 프롬프트
        new_column_name (str): 결과를 저장할 새 열 이름
        model_name (str): 사용할 AI 모델 이름 (기본값: "gpt-4o-mini")
    """
    df, worksheet, sheet = get_spreadsheet_data(input_url, input_sheet_name)
    filtered_df = filtered_column(df, input_columns_name)

    print(filtered_df)
    
    total_result = []
    
    # 멀티쓰레딩을 사용하여 병렬 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        # 각 행에 대한 작업 제출
        future_to_row = {
            executor.submit(process_row, data, system_prompt, model_name): data 
            for data in filtered_df.itertuples()
        }
        
        # 결과 수집
        for future in concurrent.futures.as_completed(future_to_row):
            try:
                result = future.result()
                total_result.append(result)
                print(f"행 {result['row_index']} 분석 완료")
            except Exception as exc:
                data = future_to_row[future]
                print(f'행 {data.Index + 2} 처리 중 오류 발생: {exc}')
    
    # 행 인덱스 기준으로 정렬
    total_result.sort(key=lambda x: x["row_index"])
    
    try:
        # 스프레드시트 크기 확장 (열만)
        headers = worksheet.row_values(1)
        current_cols = len(headers)
        
        # 새 컬럼이 없으면 확장 및 헤더 추가
        if new_column_name not in headers:
            try:
                # 열 개수 확장
                sheet.batch_update({
                    "requests": [
                        {
                            "updateSheetProperties": {
                                "properties": {
                                    "sheetId": worksheet.id,
                                    "gridProperties": {
                                        "columnCount": current_cols + 10
                                    }
                                },
                                "fields": "gridProperties.columnCount"
                            }
                        }
                    ]
                })
                print(f"스프레드시트 열 개수를 {current_cols}에서 {current_cols + 10}로 확장했습니다.")
                
                # 새 컬럼 헤더 추가
                col_index = current_cols + 1
                worksheet.update_cell(1, col_index, new_column_name)
                print(f"새 열 '{new_column_name}'을(를) {col_index}번 위치에 추가했습니다.")
                
                # 헤더 다시 가져오기
                headers = worksheet.row_values(1)
            except Exception as e:
                print(f"스프레드시트 확장 중 오류 발생: {e}")
                raise
        
        # 결과 데이터를 일괄 업데이트할 배치 요청 생성
        col_index = headers.index(new_column_name) + 1
        print(f"새 열의 인덱스: {col_index}, 열 문자: {col_num_to_letter(col_index)}")
        
        # 업데이트할 셀 데이터 준비 (일괄 업데이트용)
        batch_data = []
        for result_item in total_result:
            cell_value = result_item["result"]
            row_index = result_item["row_index"]
            col_letter = col_num_to_letter(col_index)
            
            batch_data.append({
                "range": f"{input_sheet_name}!{col_letter}{row_index}",
                "values": [[cell_value]]
            })
        
        # 모든 데이터를 한 번에 업데이트
        if batch_data:
            body = {
                'valueInputOption': 'RAW',
                'data': batch_data
            }
            
            sheet.values_batch_update(body)
            print(f"모든 데이터({len(batch_data)}개)를 한 번에 업데이트했습니다.")
            print("모든 데이터가 스프레드시트에 성공적으로 업데이트되었습니다.")
        else:
            print("업데이트할 데이터가 없습니다.")
    
    except Exception as e:
        print(f"데이터 일괄 업데이트 중 오류 발생: {e}")
        if 'batch_data' in locals() and batch_data:
            print(f"첫 번째 배치 항목 예시: {batch_data[0]}")
    
    return total_result

if __name__ == "__main__":
    # API 사용 예시
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1R7Dk4l49vwTEgQ88OQtULRBHnKS5QBPaZ2CnKqMPieU/edit?gid=0#gid=0"
    SHEET_NAME = "이미지분석"
    COLUMN_NAME = "분석결과"
    MODEL_NAME = "gemini-2.0-flash"  # 기본 모델 설정
    new_column_name = "테스트3"
    system_prompt = """
    해당 제품 정보를 바탕으로 아마존 유저들이 해다 ㅇ제품을 구매하기 위해 입력할 수 있는 검색어 리스트를 만들어봐
    """   
    
    result = analyze_data_with_ai_and_update_sheet(
        SPREADSHEET_URL, 
        SHEET_NAME, 
        [COLUMN_NAME], 
        system_prompt, 
        new_column_name,
        MODEL_NAME
    )

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)