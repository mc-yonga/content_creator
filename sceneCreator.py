from pydantic import BaseModel, Field, field_validator
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
import json
from dotenv import load_dotenv

load_dotenv()


class Scene(BaseModel):
    script: str = Field(description="Scene dialogue/script text")
    main_keyword: str = Field(description="Main keywords for image generation")


class Result(BaseModel):
    scenes: Dict[str, Scene] = Field(description="Dictionary of 18 scenes with scene_N as keys")
    
    @field_validator('scenes')
    def validate_18_scenes(cls, v):
        if len(v) != 18:
            raise ValueError(f"Must have exactly 18 scenes, got {len(v)}")
        
        for i in range(1, 19):
            scene_key = f"scene_{i}"
            if scene_key not in v:
                raise ValueError(f"Missing required scene: {scene_key}")
        
        return v

def agent(user_prompt, model="gpt-4o-mini"):
    llm = ChatOpenAI(model=model, temperature=0)
    parser = PydanticOutputParser(pydantic_object=Result)
    
    system_prompt = """광고 웹툰용 18개 씬 생성 전문가입니다.

    Script 규칙:
    - 간결하고 핵심적인 대사만 작성 (한 문장 또는 짧은 구문)
    - 1인칭 체험담 ("~더라고요", "~했는데", "~네요")
    - 자연스러운 연결어 ("그래서", "그냥", "일단")
    - 홀수 씬(1,3,5,7,9,11,13,15,17): 미완성 문장 ("~는데", "~해서", "~더니", "~니까")
    - 짝수 씬(2,4,6,8,10,12,14,16,18): 완성 문장 ("~더라고요", "~네요", "~겠어요?", "~세요")
    
    18개 씬 구조:
    1-3: 문제+충격 발견 | 4-6: 해결책+시작 | 7-11: 검증+설명 | 12-13: 감정반전 | 14-17: 구매유도
    
    Main_keyword: 띄어쓰기 없는 복합어 (예: "날파리떠다니는시야", "친구추천충격")

    {format_instructions}

    사용자 입력: {input}"""
    
    prompt = PromptTemplate(
        template=system_prompt,
        input_variables=["format_instructions", "input"]
    )
    
    chain = prompt | llm | parser
    result = chain.invoke({
        "format_instructions": parser.get_format_instructions(),
        "input": user_prompt
    })
    return result

if __name__ == "__main__":
    user_prompt = """
    눈 앞에 날파리가 떠다니는 거슬리는 비문증, 2주만에 싹 말끔해질 줄 누가 알았겠어요?
    비문증 방치하면 실명될 수도 있다고 해서 치료 받아야하나 하던 차에 친구가 이거 한번 먹어보라 하더라고요. 그냥 하루에 한 알씩 챙겨 먹기 시작했는데 날파리 갯수가 점점 줄어들면서 시야가 맑아지는게 느껴지더라고요
    그래서 약사 선생님한테 이거 괜찮냐고 물어봤더니 요즘 비문증 있는 사람들 사이에서는 유명한 제품이라네요.
    일단 국내 최초로 루테인, 아스타잔틴, 지아잔틴을 배합해서 만든 비문증 개선 특허 성분이 들어있는데, 이게 유리체에 쌓인 찌꺼기를 싹 다 녹여 없애주고 노화로 약해진 망막도 개선시켜준다고 하더라구요. 
    병원가도 치료 못하는거라고 해서 포기해야하나 했는데, 이거 한알씩만 먹으면 해결된다는걸 이제야 알아서 허무하네요.. 
    약국에서는 항상 품절상태일 정도로 인기 많아서 구하기 힘들다던데 지금 운좋게 소량입고 돼서 쟁여놨네요. 
    효과 없으면 100% 환불에 지금 34% 할인까지 한다니까 비문증 때문에 고생하고 계시다면 할인할 때 싸게 사세요
    
    """
    result = agent(user_prompt)
    
    with open("result4.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=4)

    print('Done')