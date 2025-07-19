"""
Streamlit utilities for content creator application
"""

import os
import json
import shutil
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import streamlit as st
from functools import wraps
import traceback


# ===== 설정 및 상수 정의 =====
DEFAULT_TEMP_DIR = "temp"
LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 파일 크기 제한
MAX_FILE_SIZE_MB = 100
MAX_IMAGE_SIZE_MB = 10

# 지원 파일 형식
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
SUPPORTED_DOCUMENT_FORMATS = ['.txt', '.pdf', '.docx', '.doc', '.pptx', '.ppt']

# Session state 기본 키
SESSION_KEYS = {
    'user_data': 'user_data',
    'project_data': 'project_data',
    'current_step': 'current_step',
    'temp_files': 'temp_files',
    'error_log': 'error_log',
    'settings': 'settings'
}


# ===== 로깅 설정 =====
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """로깅 설정 초기화"""
    # 로그 디렉토리 생성
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일명 (날짜별)
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 로거 설정
    logger = logging.getLogger("content_creator")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 전역 로거 인스턴스
logger = setup_logging()


# ===== 에러 처리 데코레이터 =====
def handle_errors(func):
    """에러 처리를 위한 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
            # Session state에 에러 로그 추가
            if 'error_log' not in st.session_state:
                st.session_state.error_log = []
            
            st.session_state.error_log.append({
                'timestamp': datetime.now().isoformat(),
                'function': func.__name__,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            
            # Streamlit 에러 메시지 표시
            st.error(f"오류가 발생했습니다: {str(e)}")
            
            # 디버그 모드에서는 상세 정보 표시
            if st.session_state.get('debug_mode', False):
                with st.expander("오류 상세 정보"):
                    st.code(traceback.format_exc())
            
            return None
    return wrapper


# ===== 파일 관리 유틸리티 =====
class FileManager:
    """파일 관리를 위한 유틸리티 클래스"""
    
    @staticmethod
    @handle_errors
    def create_temp_dir(prefix: str = "content_") -> str:
        """임시 디렉토리 생성"""
        temp_dir = Path(DEFAULT_TEMP_DIR)
        temp_dir.mkdir(exist_ok=True)
        
        # 고유한 임시 폴더 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = temp_dir / f"{prefix}{timestamp}"
        temp_path.mkdir(exist_ok=True)
        
        logger.info(f"Created temp directory: {temp_path}")
        return str(temp_path)
    
    @staticmethod
    @handle_errors
    def cleanup_temp_dir(temp_path: Union[str, Path], force: bool = False) -> bool:
        """임시 디렉토리 정리"""
        temp_path = Path(temp_path)
        
        if not temp_path.exists():
            logger.warning(f"Temp directory not found: {temp_path}")
            return False
        
        # 안전 확인: temp 디렉토리 내부인지 확인
        if not force and DEFAULT_TEMP_DIR not in str(temp_path):
            logger.error(f"Safety check failed: {temp_path} is not in temp directory")
            return False
        
        try:
            shutil.rmtree(temp_path)
            logger.info(f"Cleaned up temp directory: {temp_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory: {e}")
            return False
    
    @staticmethod
    @handle_errors
    def cleanup_old_temp_files(days: int = 1) -> int:
        """오래된 임시 파일 정리"""
        temp_dir = Path(DEFAULT_TEMP_DIR)
        if not temp_dir.exists():
            return 0
        
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for item in temp_dir.iterdir():
            if item.is_dir() and item.stat().st_mtime < cutoff_time:
                if FileManager.cleanup_temp_dir(item, force=True):
                    cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old temp directories")
        return cleaned_count
    
    @staticmethod
    @handle_errors
    def save_uploaded_file(uploaded_file, destination_dir: Union[str, Path]) -> Optional[str]:
        """업로드된 파일 저장"""
        if uploaded_file is None:
            return None
        
        destination_dir = Path(destination_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = destination_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        logger.info(f"Saved uploaded file: {file_path}")
        return str(file_path)
    
    @staticmethod
    def get_file_size_mb(file_path: Union[str, Path]) -> float:
        """파일 크기를 MB로 반환"""
        file_path = Path(file_path)
        if not file_path.exists():
            return 0.0
        return file_path.stat().st_size / (1024 * 1024)
    
    @staticmethod
    def is_valid_file_type(file_path: Union[str, Path], allowed_formats: List[str]) -> bool:
        """파일 형식 유효성 검사"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in allowed_formats


# ===== Session State 관리 =====
class SessionStateManager:
    """Streamlit session state 관리"""
    
    @staticmethod
    def init_session_state(defaults: Dict[str, Any] = None) -> None:
        """Session state 초기화"""
        if defaults is None:
            defaults = {
                SESSION_KEYS['user_data']: {},
                SESSION_KEYS['project_data']: {},
                SESSION_KEYS['current_step']: 0,
                SESSION_KEYS['temp_files']: [],
                SESSION_KEYS['error_log']: [],
                SESSION_KEYS['settings']: {
                    'debug_mode': False,
                    'auto_cleanup': True,
                    'language': 'ko'
                }
            }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
                logger.debug(f"Initialized session state key: {key}")
    
    @staticmethod
    def get_value(key: str, default: Any = None) -> Any:
        """Session state 값 가져오기"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set_value(key: str, value: Any) -> None:
        """Session state 값 설정"""
        st.session_state[key] = value
        logger.debug(f"Set session state: {key} = {value}")
    
    @staticmethod
    def update_value(key: str, updates: Dict[str, Any]) -> None:
        """Session state 딕셔너리 값 업데이트"""
        if key not in st.session_state:
            st.session_state[key] = {}
        
        if isinstance(st.session_state[key], dict):
            st.session_state[key].update(updates)
            logger.debug(f"Updated session state: {key}")
        else:
            logger.error(f"Cannot update non-dict session state: {key}")
    
    @staticmethod
    def clear_value(key: str) -> None:
        """Session state 값 삭제"""
        if key in st.session_state:
            del st.session_state[key]
            logger.debug(f"Cleared session state: {key}")
    
    @staticmethod
    def reset_all() -> None:
        """모든 Session state 초기화"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        logger.info("Reset all session state")
    
    @staticmethod
    @handle_errors
    def export_session_data() -> Dict[str, Any]:
        """Session state 데이터 내보내기"""
        export_data = {}
        for key in SESSION_KEYS.values():
            if key in st.session_state:
                export_data[key] = st.session_state[key]
        
        export_data['export_timestamp'] = datetime.now().isoformat()
        return export_data
    
    @staticmethod
    @handle_errors
    def import_session_data(data: Dict[str, Any]) -> bool:
        """Session state 데이터 가져오기"""
        try:
            for key, value in data.items():
                if key != 'export_timestamp':
                    st.session_state[key] = value
            logger.info("Imported session data successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to import session data: {e}")
            return False


# ===== JSON 데이터 처리 =====
class JsonHandler:
    """JSON 데이터 처리 유틸리티"""
    
    @staticmethod
    @handle_errors
    def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> bool:
        """JSON 파일 저장"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            logger.info(f"Saved JSON file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}")
            return False
    
    @staticmethod
    @handle_errors
    def load_json(file_path: Union[str, Path]) -> Optional[Any]:
        """JSON 파일 로드"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"JSON file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded JSON file: {file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            return None
    
    @staticmethod
    def to_json_string(data: Any, indent: int = 2) -> str:
        """데이터를 JSON 문자열로 변환"""
        try:
            return json.dumps(data, ensure_ascii=False, indent=indent)
        except Exception as e:
            logger.error(f"Failed to convert to JSON string: {e}")
            return "{}"
    
    @staticmethod
    def from_json_string(json_str: str) -> Optional[Any]:
        """JSON 문자열을 데이터로 변환"""
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse JSON string: {e}")
            return None


# ===== 유틸리티 함수들 =====
@handle_errors
def create_download_link(file_path: Union[str, Path], link_text: str = "다운로드") -> str:
    """파일 다운로드 링크 생성"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"File not found for download: {file_path}")
        return ""
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    import base64
    b64 = base64.b64encode(file_data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_path.name}">{link_text}</a>'
    
    return href


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """파일명 정리 (특수문자 제거)"""
    import re
    # 파일명에 사용할 수 없는 문자 제거
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 연속된 언더스코어를 하나로
    sanitized = re.sub(r'_+', '_', sanitized)
    # 앞뒤 공백 및 점 제거
    sanitized = sanitized.strip('. ')
    
    return sanitized or "unnamed"


def get_timestamp_string(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """타임스탬프 문자열 생성"""
    return datetime.now().strftime(format_str)


@handle_errors
def validate_api_key(api_key: str, service: str) -> bool:
    """API 키 유효성 검사 (형식만 확인)"""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # 서비스별 API 키 패턴 (예시)
    patterns = {
        'openai': r'^sk-[a-zA-Z0-9]{48}$',
        'anthropic': r'^sk-ant-[a-zA-Z0-9]{95}$',
        'google': r'^[a-zA-Z0-9\-_]{39}$'
    }
    
    pattern = patterns.get(service.lower())
    if pattern:
        import re
        return bool(re.match(pattern, api_key))
    
    # 기본적인 길이 확인
    return len(api_key) >= 20


def show_progress(current: int, total: int, text: str = "진행 중...") -> None:
    """진행률 표시"""
    progress = current / total if total > 0 else 0
    st.progress(progress, text=f"{text} ({current}/{total})")


def create_info_box(title: str, content: str, type: str = "info") -> None:
    """정보 박스 생성"""
    box_types = {
        'info': st.info,
        'success': st.success,
        'warning': st.warning,
        'error': st.error
    }
    
    box_func = box_types.get(type, st.info)
    with box_func(title):
        st.write(content)


# ===== 디버깅 유틸리티 =====
class DebugHelper:
    """디버깅을 위한 헬퍼 클래스"""
    
    @staticmethod
    def show_session_state() -> None:
        """Session state 내용 표시"""
        with st.expander("🔍 Session State Debug"):
            for key, value in st.session_state.items():
                st.write(f"**{key}:**")
                if isinstance(value, (dict, list)):
                    st.json(value)
                else:
                    st.write(value)
                st.divider()
    
    @staticmethod
    def show_error_log() -> None:
        """에러 로그 표시"""
        error_log = st.session_state.get('error_log', [])
        if error_log:
            with st.expander(f"❌ Error Log ({len(error_log)} errors)"):
                for i, error in enumerate(reversed(error_log[-10:])):  # 최근 10개만
                    st.write(f"**Error {i+1}:**")
                    st.write(f"- Time: {error['timestamp']}")
                    st.write(f"- Function: {error['function']}")
                    st.write(f"- Error: {error['error']}")
                    if st.checkbox(f"Show traceback {i+1}", key=f"tb_{i}"):
                        st.code(error['traceback'])
                    st.divider()
    
    @staticmethod
    def log_performance(func):
        """함수 실행 시간 측정 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
            
            if st.session_state.get('debug_mode', False):
                st.caption(f"⏱️ {func.__name__}: {execution_time:.4f}s")
            
            return result
        return wrapper


# ===== 설정 관리 =====
class SettingsManager:
    """애플리케이션 설정 관리"""
    
    DEFAULT_SETTINGS = {
        'debug_mode': False,
        'auto_cleanup': True,
        'language': 'ko',
        'theme': 'light',
        'max_retries': 3,
        'timeout': 30,
        'log_level': 'INFO'
    }
    
    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """현재 설정 가져오기"""
        if SESSION_KEYS['settings'] not in st.session_state:
            st.session_state[SESSION_KEYS['settings']] = SettingsManager.DEFAULT_SETTINGS.copy()
        
        return st.session_state[SESSION_KEYS['settings']]
    
    @staticmethod
    def update_settings(updates: Dict[str, Any]) -> None:
        """설정 업데이트"""
        settings = SettingsManager.get_settings()
        settings.update(updates)
        st.session_state[SESSION_KEYS['settings']] = settings
        logger.info(f"Updated settings: {updates}")
    
    @staticmethod
    def reset_settings() -> None:
        """설정 초기화"""
        st.session_state[SESSION_KEYS['settings']] = SettingsManager.DEFAULT_SETTINGS.copy()
        logger.info("Reset settings to defaults")
    
    @staticmethod
    @handle_errors
    def save_settings_to_file(file_path: Union[str, Path] = "settings.json") -> bool:
        """설정을 파일로 저장"""
        settings = SettingsManager.get_settings()
        return JsonHandler.save_json(settings, file_path)
    
    @staticmethod
    @handle_errors
    def load_settings_from_file(file_path: Union[str, Path] = "settings.json") -> bool:
        """파일에서 설정 로드"""
        settings = JsonHandler.load_json(file_path)
        if settings:
            SettingsManager.update_settings(settings)
            return True
        return False


# ===== 초기화 함수 =====
def initialize_app() -> None:
    """애플리케이션 초기화"""
    # Session state 초기화
    SessionStateManager.init_session_state()
    
    # 오래된 임시 파일 정리
    if SettingsManager.get_settings().get('auto_cleanup', True):
        FileManager.cleanup_old_temp_files()
    
    # 로깅 레벨 설정
    log_level = SettingsManager.get_settings().get('log_level', 'INFO')
    logger.setLevel(getattr(logging, log_level))
    
    logger.info("Application initialized")


# ===== 유틸리티 익스포트 =====
__all__ = [
    # 클래스
    'FileManager',
    'SessionStateManager',
    'JsonHandler',
    'DebugHelper',
    'SettingsManager',
    
    # 함수
    'setup_logging',
    'handle_errors',
    'create_download_link',
    'format_file_size',
    'sanitize_filename',
    'get_timestamp_string',
    'validate_api_key',
    'show_progress',
    'create_info_box',
    'initialize_app',
    
    # 상수
    'SESSION_KEYS',
    'SUPPORTED_VIDEO_FORMATS',
    'SUPPORTED_AUDIO_FORMATS',
    'SUPPORTED_IMAGE_FORMATS',
    'SUPPORTED_DOCUMENT_FORMATS',
    
    # 로거
    'logger'
]