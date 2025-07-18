import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import time

# Local imports
from sceneCreator import agent as create_scenes
from imgCreator import generate_scene_image, load_scenes_from_json

# Page configuration
st.set_page_config(
    page_title="광고 웹툰 컨텐츠 생성기",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Session state 초기화"""
    if 'scenes_data' not in st.session_state:
        st.session_state.scenes_data = None
    if 'current_scene' not in st.session_state:
        st.session_state.current_scene = 1
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = {}
    if 'scene_creation_complete' not in st.session_state:
        st.session_state.scene_creation_complete = False

def display_scene_data(scenes_data):
    """씬 데이터를 표시하는 함수"""
    if not scenes_data:
        return
    
    st.subheader("📋 생성된 씬 데이터")
    
    # 씬 선택 탭
    scene_tabs = st.tabs([f"씬 {i}" for i in range(1, 19)])
    
    for i, tab in enumerate(scene_tabs, 1):
        with tab:
            scene_key = f"scene_{i}"
            if scene_key in scenes_data['scenes']:
                scene = scenes_data['scenes'][scene_key]
                st.write(f"**대사/스크립트:** {scene['script']}")
                st.write(f"**메인 키워드:** {scene['main_keyword']}")
            else:
                st.error(f"씬 {i} 데이터를 찾을 수 없습니다.")

def save_scenes_to_json(scenes_data, filename=None):
    """씬 데이터를 JSON 파일로 저장"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scenes_{timestamp}.json"
    
    filepath = os.path.join(os.getcwd(), filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(scenes_data, f, ensure_ascii=False, indent=4)
    
    return filepath

def main():
    """메인 애플리케이션"""
    initialize_session_state()
    
    st.title("🎨 광고 웹툰 컨텐츠 생성기")
    st.markdown("---")
    
    # 사이드바 - 프로세스 상태
    with st.sidebar:
        st.header("📊 진행 상황")
        
        # 씬 생성 상태
        if st.session_state.scenes_data:
            st.success("✅ 씬 생성 완료")
        else:
            st.info("🔄 씬 생성 대기 중")
        
        # 이미지 생성 상태
        if st.session_state.generated_images:
            total_images = len(st.session_state.generated_images)
            st.success(f"🖼️ 이미지 생성: {total_images}/18")
        else:
            st.info("🖼️ 이미지 생성 대기 중")
    
    # 섹션 1: 입력 섹션 (프롬프트 입력)
    with st.container():
        st.header("📝 1. 프롬프트 입력")
        
        # 예시 프롬프트 표시
        with st.expander("💡 예시 프롬프트 보기"):
            st.text_area(
                "예시",
                value="""눈 앞에 날파리가 떠다니는 거슬리는 비문증, 2주만에 싹 말끔해질 줄 누가 알았겠어요?
비문증 방치하면 실명될 수도 있다고 해서 치료 받아야하나 하던 차에 친구가 이거 한번 먹어보라 하더라고요. 그냥 하루에 한 알씩 챙겨 먹기 시작했는데 날파리 갯수가 점점 줄어들면서 시야가 맑아지는게 느껴지더라고요
그래서 약사 선생님한테 이거 괜찮냐고 물어봤더니 요즘 비문증 있는 사람들 사이에서는 유명한 제품이라네요.
일단 국내 최초로 루테인, 아스타잔틴, 지아잔틴을 배합해서 만든 비문증 개선 특허 성분이 들어있는데, 이게 유리체에 쌓인 찌꺼기를 싹 다 녹여 없애주고 노화로 약해진 망막도 개선시켜준다고 하더라구요. 
병원가도 치료 못하는거라고 해서 포기해야하나 했는데, 이거 한알씩만 먹으면 해결된다는걸 이제야 알아서 허무하네요.. 
약국에서는 항상 품절상태일 정도로 인기 많아서 구하기 힘들다던데 지금 운좋게 소량입고 돼서 쟁여놨네요. 
효과 없으면 100% 환불에 지금 34% 할인까지 한다니까 비문증 때문에 고생하고 계시다면 할인할 때 싸게 사세요""",
                height=200,
                disabled=True
            )
        
        # 사용자 프롬프트 입력
        user_prompt = st.text_area(
            "광고 웹툰 프롬프트를 입력하세요:",
            height=200,
            placeholder="제품이나 서비스에 대한 자연스러운 체험담을 입력해주세요..."
        )
        
        # 모델 선택
        col1, col2 = st.columns([3, 1])
        with col2:
            selected_model = st.selectbox(
                "모델 선택:",
                ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                index=0
            )
        
        # 씬 생성 버튼
        if st.button("🚀 18개 씬 생성하기", type="primary", use_container_width=True):
            if user_prompt.strip():
                with st.spinner("씬을 생성하는 중입니다... 잠시만 기다려주세요."):
                    try:
                        # 씬 생성
                        result = create_scenes(user_prompt, model=selected_model)
                        
                        # 결과를 딕셔너리로 변환
                        st.session_state.scenes_data = result.model_dump()
                        st.session_state.scene_creation_complete = True
                        
                        # JSON 파일로 저장
                        saved_file = save_scenes_to_json(st.session_state.scenes_data)
                        
                        st.success(f"✅ 18개 씬이 성공적으로 생성되었습니다!")
                        st.success(f"📁 파일 저장됨: {saved_file}")
                        
                    except Exception as e:
                        st.error(f"❌ 씬 생성 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("⚠️ 프롬프트를 입력해주세요.")
    
    st.markdown("---")
    
    # 섹션 2: 씬 결과 확인 섹션
    with st.container():
        st.header("📊 2. 씬 결과 확인")
        
        if st.session_state.scenes_data:
            display_scene_data(st.session_state.scenes_data)
            
            # JSON 다운로드 버튼
            json_str = json.dumps(st.session_state.scenes_data, ensure_ascii=False, indent=4)
            st.download_button(
                label="📥 씬 데이터 JSON 다운로드",
                data=json_str,
                file_name=f"scenes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        else:
            st.info("먼저 프롬프트를 입력하고 씬을 생성해주세요.")
    
    st.markdown("---")
    
    # 섹션 3: 이미지 생성 섹션
    with st.container():
        st.header("🖼️ 3. 이미지 생성")
        
        if st.session_state.scenes_data:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # 씬 선택
                scene_options = [f"씬 {i}" for i in range(1, 19)]
                selected_scene_str = st.selectbox("생성할 씬 선택:", scene_options)
                selected_scene_num = int(selected_scene_str.split()[1])
            
            with col2:
                # 이미지 생성 모델 선택
                image_model = st.selectbox(
                    "이미지 모델:",
                    ["dall-e-3", "dall-e-2"],
                    index=0
                )
            
            with col3:
                st.write("")  # 공간 조정
                st.write("")  # 공간 조정
                
                # 단일 씬 이미지 생성
                if st.button("🎨 이미지 생성", type="primary"):
                    # 임시 JSON 파일 생성
                    temp_json_file = "temp_scenes.json"
                    save_scenes_to_json(st.session_state.scenes_data, temp_json_file)
                    
                    with st.spinner(f"씬 {selected_scene_num} 이미지를 생성하는 중..."):
                        try:
                            # 이미지 디렉토리 생성
                            os.makedirs("generated_images", exist_ok=True)
                            
                            # 이미지 생성
                            image_path = generate_scene_image(
                                temp_json_file, 
                                selected_scene_num, 
                                "generated_images"
                            )
                            
                            # 세션 상태에 저장
                            st.session_state.generated_images[selected_scene_num] = image_path
                            
                            st.success(f"✅ 씬 {selected_scene_num} 이미지가 생성되었습니다!")
                            
                            # 임시 파일 정리
                            if os.path.exists(temp_json_file):
                                os.remove(temp_json_file)
                                
                        except Exception as e:
                            st.error(f"❌ 이미지 생성 중 오류가 발생했습니다: {str(e)}")
                            
                            # 임시 파일 정리
                            if os.path.exists(temp_json_file):
                                os.remove(temp_json_file)
            
            # 전체 이미지 생성 버튼
            st.markdown("---")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("🎨 전체 18개 씬 이미지 생성 (연속)", type="secondary", use_container_width=True):
                    # 임시 JSON 파일 생성
                    temp_json_file = "temp_scenes_all.json"
                    save_scenes_to_json(st.session_state.scenes_data, temp_json_file)
                    
                    # 진행률 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # 이미지 디렉토리 생성
                        os.makedirs("generated_images", exist_ok=True)
                        
                        for scene_num in range(1, 19):
                            status_text.text(f"씬 {scene_num}/18 이미지 생성 중...")
                            
                            try:
                                image_path = generate_scene_image(
                                    temp_json_file,
                                    scene_num,
                                    "generated_images"
                                )
                                
                                # 세션 상태에 저장
                                st.session_state.generated_images[scene_num] = image_path
                                
                                # 진행률 업데이트
                                progress = scene_num / 18
                                progress_bar.progress(progress)
                                
                                # API 제한 대기 (첫 17개 씬에만 적용)
                                if scene_num < 18:
                                    time.sleep(12)  # 12초 대기
                                
                            except Exception as e:
                                st.error(f"씬 {scene_num} 이미지 생성 실패: {str(e)}")
                                continue
                        
                        status_text.text("✅ 모든 이미지 생성 완료!")
                        st.success("🎉 전체 18개 씬의 이미지가 생성되었습니다!")
                        
                        # 임시 파일 정리
                        if os.path.exists(temp_json_file):
                            os.remove(temp_json_file)
                            
                    except Exception as e:
                        st.error(f"❌ 전체 이미지 생성 중 오류가 발생했습니다: {str(e)}")
                        
                        # 임시 파일 정리
                        if os.path.exists(temp_json_file):
                            os.remove(temp_json_file)
            
            with col2:
                st.info("⏱️ 전체 생성 시 약 3-4분 소요됩니다 (API 제한으로 인한 대기시간 포함)")
        
        else:
            st.info("이미지를 생성하려면 먼저 씬 데이터를 생성해주세요.")
    
    st.markdown("---")
    
    # 섹션 4: 결과 갤러리 섹션
    with st.container():
        st.header("🖼️ 4. 결과 갤러리")
        
        if st.session_state.generated_images:
            # 생성된 이미지 개수 표시
            total_generated = len(st.session_state.generated_images)
            st.success(f"총 {total_generated}개의 이미지가 생성되었습니다.")
            
            # 갤러리 표시 옵션
            col1, col2 = st.columns([3, 1])
            with col2:
                view_mode = st.radio(
                    "보기 모드:",
                    ["격자 뷰", "슬라이드 뷰"],
                    index=0
                )
            
            if view_mode == "격자 뷰":
                # 격자 형태로 이미지 표시
                cols_per_row = 3
                scene_numbers = sorted(st.session_state.generated_images.keys())
                
                for i in range(0, len(scene_numbers), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        if i + j < len(scene_numbers):
                            scene_num = scene_numbers[i + j]
                            image_path = st.session_state.generated_images[scene_num]
                            
                            with col:
                                if os.path.exists(image_path):
                                    st.image(image_path, caption=f"씬 {scene_num}")
                                    
                                    # 씬 정보 표시
                                    if st.session_state.scenes_data:
                                        scene_key = f"scene_{scene_num}"
                                        scene_data = st.session_state.scenes_data['scenes'][scene_key]
                                        with st.expander(f"씬 {scene_num} 정보"):
                                            st.write(f"**대사:** {scene_data['script']}")
                                            st.write(f"**키워드:** {scene_data['main_keyword']}")
                                else:
                                    st.error(f"씬 {scene_num} 이미지 파일을 찾을 수 없습니다.")
            
            else:  # 슬라이드 뷰
                # 씬 선택 슬라이더
                scene_numbers = sorted(st.session_state.generated_images.keys())
                selected_scene = st.select_slider(
                    "씬 선택:",
                    options=scene_numbers,
                    format_func=lambda x: f"씬 {x}"
                )
                
                # 선택된 씬 이미지 표시
                if selected_scene in st.session_state.generated_images:
                    image_path = st.session_state.generated_images[selected_scene]
                    
                    if os.path.exists(image_path):
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.image(image_path, caption=f"씬 {selected_scene}")
                        
                        # 씬 정보 표시
                        if st.session_state.scenes_data:
                            scene_key = f"scene_{selected_scene}"
                            scene_data = st.session_state.scenes_data['scenes'][scene_key]
                            
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                st.write(f"**대사:** {scene_data['script']}")
                            with col2:
                                st.write(f"**키워드:** {scene_data['main_keyword']}")
                    else:
                        st.error(f"씬 {selected_scene} 이미지 파일을 찾을 수 없습니다.")
            
            # 이미지 다운로드 기능
            st.markdown("---")
            st.subheader("📥 이미지 다운로드")
            
            # ZIP 파일로 전체 이미지 다운로드 (간단한 방법으로 구현)
            if st.button("📦 모든 이미지를 ZIP으로 다운로드"):
                st.info("💡 생성된 이미지들은 'generated_images' 폴더에서 확인할 수 있습니다.")
        
        else:
            st.info("아직 생성된 이미지가 없습니다. 먼저 이미지를 생성해주세요.")

if __name__ == "__main__":
    main()