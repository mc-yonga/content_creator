import streamlit as st
import os
import zipfile
from io import BytesIO
from PIL import Image
import datetime
from typing import List, Dict, Optional
import base64


class ImageGallery:
    """이미지 갤러리 표시 및 다운로드 관리 클래스"""
    
    def __init__(self):
        """갤러리 초기화"""
        self.columns_per_row = 3
        
    def display_gallery(self, images: List[Dict[str, any]], scene_info: Optional[Dict] = None):
        """
        이미지 갤러리를 3열 그리드로 표시
        
        Args:
            images: 이미지 정보 리스트 (path, filename, created_at 등)
            scene_info: 씬 정보 딕셔너리
        """
        if not images:
            st.info("표시할 이미지가 없습니다.")
            return
            
        # 씬 정보 표시
        if scene_info:
            self._display_scene_info(scene_info)
            
        # 전체 다운로드 버튼
        if len(images) > 1:
            self._create_bulk_download(images, scene_info)
            
        # 이미지 그리드 표시
        st.markdown("### 📸 생성된 이미지")
        
        # 3열 그리드 생성
        for idx in range(0, len(images), self.columns_per_row):
            cols = st.columns(self.columns_per_row)
            
            for col_idx in range(self.columns_per_row):
                img_idx = idx + col_idx
                if img_idx < len(images):
                    with cols[col_idx]:
                        self._display_single_image(images[img_idx], img_idx)
                        
    def _display_scene_info(self, scene_info: Dict):
        """씬 정보 표시"""
        with st.expander("🎬 씬 정보", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**씬 번호:** {scene_info.get('scene_number', 'N/A')}")
                st.write(f"**제목:** {scene_info.get('title', 'N/A')}")
                st.write(f"**장르:** {scene_info.get('genre', 'N/A')}")
                
            with col2:
                st.write(f"**생성 시간:** {scene_info.get('created_at', 'N/A')}")
                st.write(f"**이미지 수:** {scene_info.get('image_count', 0)}개")
                
            if scene_info.get('description'):
                st.write("**설명:**")
                st.write(scene_info['description'])
                
    def _display_single_image(self, image_info: Dict, index: int):
        """개별 이미지 표시 및 다운로드 버튼"""
        try:
            # 이미지 파일 경로
            image_path = image_info.get('path')
            if not os.path.exists(image_path):
                st.error(f"이미지를 찾을 수 없습니다: {image_path}")
                return
                
            # 이미지 로드 및 표시
            image = Image.open(image_path)
            
            # 썸네일 표시 (클릭하면 확대)
            with st.container():
                # 이미지 정보
                st.caption(f"이미지 {index + 1}")
                
                # 이미지 표시 (클릭 시 확대)
                if st.button(f"🔍 확대", key=f"expand_{index}"):
                    self._show_enlarged_image(image, image_info)
                
                # 썸네일 표시
                st.image(image, use_container_width=True)
                
                # 다운로드 버튼
                download_filename = self._generate_filename(image_info, index)
                with open(image_path, "rb") as file:
                    st.download_button(
                        label="⬇️ 다운로드",
                        data=file.read(),
                        file_name=download_filename,
                        mime="image/png",
                        key=f"download_{index}"
                    )
                    
                # 이미지 정보 표시
                if st.checkbox("정보 보기", key=f"info_{index}"):
                    self._display_image_metadata(image_info, image)
                    
        except Exception as e:
            st.error(f"이미지 표시 오류: {str(e)}")
            
    def _show_enlarged_image(self, image: Image.Image, image_info: Dict):
        """확대된 이미지를 모달로 표시"""
        # Streamlit의 제한으로 인해 실제 모달 대신 확대된 이미지 표시
        st.image(image, caption=image_info.get('filename', ''), use_container_width=True)
        
    def _display_image_metadata(self, image_info: Dict, image: Image.Image):
        """이미지 메타데이터 표시"""
        metadata = {
            "파일명": image_info.get('filename', 'N/A'),
            "크기": f"{image.width} x {image.height}",
            "생성 시간": image_info.get('created_at', 'N/A'),
            "프롬프트": image_info.get('prompt', 'N/A')[:100] + "..." if image_info.get('prompt') else 'N/A'
        }
        
        for key, value in metadata.items():
            st.text(f"{key}: {value}")
            
    def _create_bulk_download(self, images: List[Dict], scene_info: Optional[Dict] = None):
        """전체 이미지 ZIP 다운로드 생성"""
        st.markdown("### 📦 전체 다운로드")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # ZIP 파일명 생성
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            scene_title = scene_info.get('title', 'images') if scene_info else 'images'
            # 파일명에 사용할 수 없는 문자 제거
            safe_title = "".join(c for c in scene_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            zip_filename = f"{safe_title}_{timestamp}.zip"
            
        with col2:
            st.metric("총 이미지 수", len(images))
            
        with col3:
            # ZIP 다운로드 버튼
            zip_data = self._create_zip_file(images)
            if zip_data:
                st.download_button(
                    label="⬇️ 전체 다운로드 (ZIP)",
                    data=zip_data,
                    file_name=zip_filename,
                    mime="application/zip",
                    key="download_all"
                )
                
    def _create_zip_file(self, images: List[Dict]) -> Optional[bytes]:
        """이미지들을 ZIP 파일로 압축"""
        try:
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for idx, image_info in enumerate(images):
                    image_path = image_info.get('path')
                    if os.path.exists(image_path):
                        # ZIP 내부 파일명 생성
                        archive_name = self._generate_filename(image_info, idx)
                        zip_file.write(image_path, archive_name)
                        
            zip_buffer.seek(0)
            return zip_buffer.read()
            
        except Exception as e:
            st.error(f"ZIP 파일 생성 오류: {str(e)}")
            return None
            
    def _generate_filename(self, image_info: Dict, index: int) -> str:
        """다운로드용 파일명 생성"""
        # 기본 파일명
        base_name = image_info.get('filename')
        if base_name:
            return base_name
            
        # 파일명이 없을 경우 자동 생성
        timestamp = image_info.get('created_at', datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        scene_number = image_info.get('scene_number', 0)
        
        return f"scene{scene_number}_image{index + 1}_{timestamp}.png"
        

def show_image_preview_modal(image_path: str, title: str = "이미지 미리보기"):
    """이미지 미리보기 모달 표시 (Streamlit 방식)"""
    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption=title, use_container_width=True)
    else:
        st.error("이미지를 찾을 수 없습니다.")
        

def create_download_link(file_path: str, link_text: str = "다운로드") -> str:
    """파일 다운로드 링크 생성 (대체 방법)"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
        return href
    except Exception as e:
        return f"다운로드 링크 생성 실패: {str(e)}"


# 테스트용 메인 함수
def main():
    """갤러리 모듈 테스트"""
    st.set_page_config(page_title="이미지 갤러리", layout="wide")
    st.title("🖼️ 이미지 갤러리 테스트")
    
    # 샘플 데이터
    sample_images = [
        {
            "path": "sample1.png",
            "filename": "scene1_image1.png",
            "created_at": "2024-01-01 10:00:00",
            "prompt": "A beautiful landscape"
        },
        {
            "path": "sample2.png",
            "filename": "scene1_image2.png",
            "created_at": "2024-01-01 10:05:00",
            "prompt": "A cityscape at night"
        }
    ]
    
    sample_scene_info = {
        "scene_number": 1,
        "title": "테스트 씬",
        "genre": "판타지",
        "created_at": "2024-01-01 10:00:00",
        "image_count": 2,
        "description": "이것은 테스트 씬입니다."
    }
    
    # 갤러리 표시
    gallery = ImageGallery()
    gallery.display_gallery(sample_images, sample_scene_info)
    

if __name__ == "__main__":
    main()