"""
Streamlit Image Handler
imgCreator.py의 함수들을 Streamlit용으로 래핑하여
진행률 추적, rate limit 처리, 실시간 로그 업데이트, 에러 처리 등을 제공합니다.
"""

import streamlit as st
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
import os
import json
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

from imgCreator import (
    ImageCreator,
    create_single_image,
    create_multiple_images
)

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class StreamlitImageHandler:
    """Streamlit 환경에서 이미지 생성을 관리하는 핸들러"""
    
    def __init__(self):
        self.image_creator = ImageCreator()
        self.log_queue = Queue()
        self.current_status = {}
        self.rate_limit_delay = 12  # 12초 대기
        
    def add_log(self, message: str, level: str = "info"):
        """로그 메시지를 큐에 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.log_queue.put(log_entry)
        
    def update_status(self, key: str, value: Any):
        """상태 업데이트"""
        self.current_status[key] = value
        
    def handle_rate_limit(self, container):
        """Rate limit 대기 시각화"""
        self.add_log(f"Rate limit 대기 중... ({self.rate_limit_delay}초)", "warning")
        
        progress_bar = container.progress(0)
        status_text = container.empty()
        
        for i in range(self.rate_limit_delay):
            progress = (i + 1) / self.rate_limit_delay
            progress_bar.progress(progress)
            status_text.text(f"⏳ Rate limit 대기 중... {self.rate_limit_delay - i}초 남음")
            time.sleep(1)
            
        progress_bar.empty()
        status_text.empty()
        self.add_log("Rate limit 대기 완료", "info")
        
    def create_single_image_with_progress(
        self,
        prompt: str,
        output_dir: str,
        container,
        quality: str = "standard",
        size: str = "1024x1024",
        style: str = "vivid"
    ) -> Optional[str]:
        """단일 이미지 생성 with 진행률 표시"""
        
        with container.container():
            status = st.status("이미지 생성 준비 중...", expanded=True)
            
            try:
                # 시작 로그
                self.add_log(f"이미지 생성 시작: '{prompt[:50]}...'", "info")
                status.update(label="이미지 생성 중...", state="running")
                
                # 진행률 표시
                progress_bar = status.progress(0)
                status_text = status.empty()
                
                # 이미지 생성 요청
                status_text.text("🎨 DALL-E 3 API 요청 중...")
                progress_bar.progress(30)
                
                result = create_single_image(
                    prompt=prompt,
                    output_dir=output_dir,
                    quality=quality,
                    size=size,
                    style=style
                )
                
                if result:
                    progress_bar.progress(90)
                    status_text.text("✅ 이미지 생성 완료!")
                    self.add_log(f"이미지 저장 완료: {result}", "success")
                    
                    # 완료
                    progress_bar.progress(100)
                    status.update(label="✅ 이미지 생성 완료", state="complete", expanded=False)
                    
                    # 이미지 미리보기
                    with status:
                        st.image(result, caption=f"생성된 이미지: {os.path.basename(result)}")
                    
                    return result
                else:
                    raise Exception("이미지 생성 실패")
                    
            except Exception as e:
                self.add_log(f"에러 발생: {str(e)}", "error")
                status.update(label=f"❌ 에러: {str(e)}", state="error", expanded=True)
                return None
                
    def create_multiple_images_with_progress(
        self,
        prompts: List[str],
        output_dir: str,
        container,
        quality: str = "standard",
        size: str = "1024x1024",
        style: str = "vivid",
        max_workers: int = 1
    ) -> List[Optional[str]]:
        """여러 이미지 생성 with 진행률 표시"""
        
        results = []
        total_prompts = len(prompts)
        
        with container.container():
            # 전체 진행률
            overall_progress = st.progress(0, text=f"전체 진행률: 0/{total_prompts}")
            
            # 개별 이미지 상태 표시
            status_container = st.container()
            
            for idx, prompt in enumerate(prompts):
                with status_container.container():
                    st.write(f"**이미지 {idx + 1}/{total_prompts}**")
                    
                    # Rate limit 처리 (첫 번째 이미지가 아닌 경우)
                    if idx > 0:
                        rate_limit_container = st.container()
                        self.handle_rate_limit(rate_limit_container)
                    
                    # 이미지 생성
                    image_container = st.container()
                    result = self.create_single_image_with_progress(
                        prompt=prompt,
                        output_dir=output_dir,
                        container=image_container,
                        quality=quality,
                        size=size,
                        style=style
                    )
                    
                    results.append(result)
                    
                    # 전체 진행률 업데이트
                    progress = (idx + 1) / total_prompts
                    overall_progress.progress(
                        progress,
                        text=f"전체 진행률: {idx + 1}/{total_prompts} ({int(progress * 100)}%)"
                    )
                    
                    # 성공/실패 카운트
                    success_count = sum(1 for r in results if r is not None)
                    fail_count = len(results) - success_count
                    st.info(f"✅ 성공: {success_count} | ❌ 실패: {fail_count}")
                    
        return results
        
    def retry_failed_images(
        self,
        failed_prompts: List[Tuple[int, str]],
        output_dir: str,
        container,
        quality: str = "standard",
        size: str = "1024x1024",
        style: str = "vivid",
        max_retries: int = 3
    ) -> Dict[int, Optional[str]]:
        """실패한 이미지 재시도"""
        
        retry_results = {}
        
        with container.container():
            st.write("### 🔄 실패한 이미지 재시도")
            
            for retry_num in range(max_retries):
                if not failed_prompts:
                    break
                    
                st.write(f"**재시도 {retry_num + 1}/{max_retries}**")
                remaining_failures = []
                
                for idx, prompt in failed_prompts:
                    # Rate limit 처리
                    if len(retry_results) > 0:
                        rate_limit_container = st.container()
                        self.handle_rate_limit(rate_limit_container)
                    
                    # 재시도
                    retry_container = st.container()
                    with retry_container:
                        st.write(f"재시도: 이미지 #{idx + 1}")
                        
                    result = self.create_single_image_with_progress(
                        prompt=prompt,
                        output_dir=output_dir,
                        container=retry_container,
                        quality=quality,
                        size=size,
                        style=style
                    )
                    
                    if result:
                        retry_results[idx] = result
                        self.add_log(f"재시도 성공: 이미지 #{idx + 1}", "success")
                    else:
                        remaining_failures.append((idx, prompt))
                        self.add_log(f"재시도 실패: 이미지 #{idx + 1}", "error")
                
                failed_prompts = remaining_failures
                
                if not failed_prompts:
                    st.success("✅ 모든 이미지 재시도 성공!")
                    break
                else:
                    st.warning(f"⚠️ {len(failed_prompts)}개 이미지 여전히 실패")
                    
        return retry_results
        
    def display_logs(self, container, max_logs: int = 50):
        """실시간 로그 표시"""
        logs = []
        
        # 큐에서 로그 가져오기
        while not self.log_queue.empty() and len(logs) < max_logs:
            logs.append(self.log_queue.get())
        
        if logs:
            with container.expander("📋 실행 로그", expanded=False):
                for log in reversed(logs[-max_logs:]):
                    level_icon = {
                        "info": "ℹ️",
                        "success": "✅",
                        "warning": "⚠️",
                        "error": "❌"
                    }.get(log["level"], "📝")
                    
                    st.text(f"{log['timestamp']} {level_icon} {log['message']}")
                    
    def get_generation_summary(self, results: List[Optional[str]]) -> Dict[str, Any]:
        """생성 결과 요약"""
        total = len(results)
        success = sum(1 for r in results if r is not None)
        failed = total - success
        
        summary = {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "generated_files": [r for r in results if r is not None]
        }
        
        return summary
        
    def save_generation_report(
        self,
        output_dir: str,
        prompts: List[str],
        results: List[Optional[str]],
        settings: Dict[str, Any]
    ) -> str:
        """생성 리포트 저장"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "settings": settings,
            "summary": self.get_generation_summary(results),
            "details": []
        }
        
        for idx, (prompt, result) in enumerate(zip(prompts, results)):
            report["details"].append({
                "index": idx + 1,
                "prompt": prompt,
                "result": result,
                "status": "success" if result else "failed"
            })
            
        # 리포트 파일 저장
        report_path = os.path.join(output_dir, "generation_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        self.add_log(f"생성 리포트 저장: {report_path}", "info")
        return report_path


# Streamlit 컴포넌트 헬퍼 함수들
def create_image_generation_ui():
    """이미지 생성 UI 컴포넌트"""
    
    st.header("🎨 AI 이미지 생성")
    
    # 설정
    with st.expander("⚙️ 생성 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quality = st.selectbox(
                "품질",
                options=["standard", "hd"],
                help="standard: 빠른 생성, hd: 고품질 (2배 비용)"
            )
            
        with col2:
            size = st.selectbox(
                "크기",
                options=["1024x1024", "1792x1024", "1024x1792"],
                help="정사각형 또는 가로/세로 형식"
            )
            
        with col3:
            style = st.selectbox(
                "스타일",
                options=["vivid", "natural"],
                help="vivid: 생동감 있는 스타일, natural: 자연스러운 스타일"
            )
            
    return quality, size, style


def display_generation_results(summary: Dict[str, Any]):
    """생성 결과 표시"""
    
    st.header("📊 생성 결과")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("전체", summary["total"])
        
    with col2:
        st.metric("성공", summary["success"], delta=f"+{summary['success']}")
        
    with col3:
        st.metric("실패", summary["failed"], delta=f"-{summary['failed']}" if summary["failed"] > 0 else "0")
        
    with col4:
        st.metric("성공률", f"{summary['success_rate']:.1f}%")
        
    # 생성된 이미지 갤러리
    if summary["generated_files"]:
        st.subheader("🖼️ 생성된 이미지")
        
        # 그리드 레이아웃으로 이미지 표시
        cols = st.columns(3)
        for idx, img_path in enumerate(summary["generated_files"]):
            with cols[idx % 3]:
                if os.path.exists(img_path):
                    st.image(img_path, caption=os.path.basename(img_path), use_column_width=True)


# 사용 예시 함수
def example_usage():
    """Streamlit 앱에서 사용하는 예시"""
    
    st.title("AI 이미지 생성 도구")
    
    # 핸들러 초기화
    handler = StreamlitImageHandler()
    
    # UI 생성
    quality, size, style = create_image_generation_ui()
    
    # 프롬프트 입력
    prompts = st.text_area(
        "프롬프트 입력 (한 줄에 하나씩)",
        height=150,
        placeholder="햇살이 비치는 아름다운 해변\n귀여운 고양이가 낮잠을 자는 모습\n..."
    ).strip().split("\n")
    
    # 출력 디렉토리
    output_dir = st.text_input("출력 디렉토리", value="./generated_images")
    
    # 생성 버튼
    if st.button("🚀 이미지 생성 시작", type="primary"):
        # 빈 프롬프트 제거
        prompts = [p.strip() for p in prompts if p.strip()]
        
        if not prompts:
            st.error("프롬프트를 입력해주세요!")
            return
            
        # 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 로그 컨테이너
        log_container = st.container()
        
        # 이미지 생성
        generation_container = st.container()
        
        results = handler.create_multiple_images_with_progress(
            prompts=prompts,
            output_dir=output_dir,
            container=generation_container,
            quality=quality,
            size=size,
            style=style
        )
        
        # 실패한 이미지 재시도
        failed_prompts = [
            (idx, prompt) for idx, (prompt, result) in enumerate(zip(prompts, results))
            if result is None
        ]
        
        if failed_prompts:
            retry_container = st.container()
            retry_results = handler.retry_failed_images(
                failed_prompts=failed_prompts,
                output_dir=output_dir,
                container=retry_container,
                quality=quality,
                size=size,
                style=style
            )
            
            # 재시도 결과 반영
            for idx, result in retry_results.items():
                results[idx] = result
                
        # 결과 요약
        summary = handler.get_generation_summary(results)
        display_generation_results(summary)
        
        # 리포트 저장
        settings = {
            "quality": quality,
            "size": size,
            "style": style
        }
        
        report_path = handler.save_generation_report(
            output_dir=output_dir,
            prompts=prompts,
            results=results,
            settings=settings
        )
        
        st.success(f"✅ 생성 완료! 리포트: {report_path}")
        
        # 로그 표시
        handler.display_logs(log_container)


if __name__ == "__main__":
    # Streamlit 앱 실행시 예시 표시
    example_usage()