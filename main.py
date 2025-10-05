"""
Discord Bot Main Entry Point
마인크래프트 서버 관리를 위한 디스코드 봇

Author: DoubleLatte
License: MIT
"""

import sys
import os
from typing import Optional
import yaml
import discord
from discord.ext import commands
from discord import Game, Status


# ==================== 유틸리티 함수 ====================

def resource_path(relative_path: str) -> str:
    """
    리소스 파일의 절대 경로 반환
    PyInstaller 환경과 일반 실행 환경 모두 지원
    
    Args:
        relative_path: 상대 경로
        
    Returns:
        str: 절대 경로
    """
    try:
        # PyInstaller 환경에서 임시 폴더 경로
        base_path = sys._MEIPASS
    except AttributeError:
        # 일반 실행 환경에서 현재 디렉토리
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def load_config(config_path: str = "config.yml") -> dict:
    """
    YAML 설정 파일 로드
    
    Args:
        config_path: 설정 파일 경로 (기본값: config.yml)
        
    Returns:
        dict: 설정 딕셔너리
        
    Raises:
        SystemExit: 파일을 찾을 수 없거나 읽기 실패 시
    """
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            print(f"✅ 설정 파일 로드 완료: {config_path}")
            return config
            
    except FileNotFoundError:
        sys.exit(f"❌ 오류: {config_path} 파일을 찾을 수 없습니다.")
        
    except yaml.YAMLError as e:
        sys.exit(f"❌ 오류: {config_path} 파일 파싱 실패 - {e}")
        
    except Exception as e:
        sys.exit(f"❌ 오류: 설정 파일 로드 중 예상치 못한 오류 - {e}")


# ==================== 봇 클래스 ====================

class MinecraftBot(commands.Bot):
    """
    마인크래프트 서버 관리 디스코드 봇
    
    Attributes:
        config: 설정 딕셔너리
        administrator_role_ids: 관리자 역할 ID 리스트
        extensions_list: 로드할 확장 기능 리스트
    """
    
    def __init__(self, config: dict):
        """
        봇 초기화
        
        Args:
            config: 설정 딕셔너리
        """
        # 모든 인텐트 활성화
        intents = discord.Intents.all()
        
        # Bot 부모 클래스 초기화
        super().__init__(
            command_prefix="!",  # 텍스트 명령어 접두사 (슬래시 명령어 사용 시 불필요)
            intents=intents,
            application_id=config.get("application_id")
        )
        
        # 설정 저장
        self.config = config
        self.administrator_role_ids = config.get("administrator_role_ids", [])
        
        # 로드할 확장 기능 목록
        self.extensions_list = [
            "command.example",      # 예시 명령어
            "command.dev",          # 개발자 도구
            "command.minecraft"     # 마인크래프트 관리
        ]
        
        print(f"✅ 봇 초기화 완료: {len(self.extensions_list)}개 확장 대기 중")
    
    async def setup_hook(self):
        """
        봇 초기 설정 및 확장 기능 로드
        discord.py의 setup_hook을 오버라이드하여 봇 시작 시 자동 실행
        """
        print("\n" + "="*50)
        print("🔧 확장 기능 로드 중...")
        print("="*50)
        
        # 확장 기능 로드
        loaded_count = 0
        failed_count = 0
        
        for ext in self.extensions_list:
            try:
                await self.load_extension(ext)
                print(f"  ✅ {ext}")
                loaded_count += 1
                
            except commands.ExtensionNotFound:
                print(f"  ❌ {ext} - 확장 파일을 찾을 수 없습니다")
                failed_count += 1
                
            except commands.ExtensionAlreadyLoaded:
                print(f"  ⚠️  {ext} - 이미 로드되어 있습니다")
                
            except commands.ExtensionFailed as e:
                print(f"  ❌ {ext} - 로드 실패: {e.original}")
                failed_count += 1
                
            except Exception as e:
                print(f"  ❌ {ext} - 예상치 못한 오류: {e}")
                failed_count += 1
        
        print("="*50)
        print(f"📦 로드 완료: {loaded_count}개 성공, {failed_count}개 실패")
        print("="*50 + "\n")
        
        # 슬래시 명령어 동기화
        await self._sync_commands()
    
    async def _sync_commands(self):
        """슬래시 명령어를 Discord와 동기화"""
        print("🔄 슬래시 명령어 동기화 중...")
        
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)}개 명령어 동기화 완료\n")
            
        except discord.HTTPException as e:
            print(f"❌ 명령어 동기화 실패: {e}\n")
            
        except Exception as e:
            print(f"❌ 예상치 못한 동기화 오류: {e}\n")
    
    async def on_ready(self):
        """
        봇이 준비되었을 때 실행되는 이벤트
        Discord 서버와 연결 완료 시 자동 호출
        """
        print("\n" + "="*50)
        print("🤖 봇 온라인 상태")
        print("="*50)
        print(f"  봇 이름: {self.user.name}")
        print(f"  봇 ID: {self.user.id}")
        print(f"  서버 수: {len(self.guilds)}개")
        print(f"  Discord.py 버전: {discord.__version__}")
        print("="*50 + "\n")
        
        # 봇 상태 메시지 설정
        await self._set_presence()
    
    async def _set_presence(self):
        """봇의 상태 메시지 및 활동 설정"""
        try:
            activity = Game(name="마인크래프트 서버 관리 중")
            await self.change_presence(
                status=Status.online,
                activity=activity
            )
            print("✅ 봇 상태 메시지 설정 완료\n")
            
        except Exception as e:
            print(f"⚠️  상태 메시지 설정 실패: {e}\n")
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """
        명령어 오류 발생 시 처리
        
        Args:
            ctx: 명령어 컨텍스트
            error: 발생한 오류
        """
        if isinstance(error, commands.CommandNotFound):
            return  # 존재하지 않는 명령어는 무시
        
        print(f"⚠️  명령어 오류: {error}")


# ==================== 메인 실행 함수 ====================

def validate_config(config: dict) -> bool:
    """
    설정 파일의 필수 항목 검증
    
    Args:
        config: 설정 딕셔너리
        
    Returns:
        bool: 검증 통과 여부
    """
    required_keys = ["token", "application_id"]
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        print(f"❌ 오류: config.yml에 다음 항목이 누락되었습니다: {', '.join(missing_keys)}")
        return False
    
    # 관리자 역할 확인 (경고만)
    if not config.get("administrator_role_ids"):
        print("⚠️  경고: administrator_role_ids가 설정되지 않았습니다.")
        print("   관리자 전용 명령어를 사용하려면 config.yml에 역할 ID를 추가하세요.\n")
    
    return True


def main():
    """
    봇 메인 실행 함수
    설정 로드 → 검증 → 봇 시작
    """
    print("\n" + "="*50)
    print("🚀 Discord Bot 시작 중...")
    print("="*50 + "\n")
    
    # 설정 파일 로드
    config = load_config()
    
    # 설정 검증
    if not validate_config(config):
        sys.exit(1)
    
    # 봇 인스턴스 생성
    bot = MinecraftBot(config)
    
    # 봇 실행
    try:
        print("🔌 Discord 서버에 연결 중...\n")
        bot.run(config["token"])
        
    except discord.LoginFailure:
        print("\n" + "="*50)
        print("❌ 로그인 실패")
        print("="*50)
        print("토큰이 올바른지 확인하세요.")
        print("Discord Developer Portal: https://discord.com/developers/applications")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n" + "="*50)
        print("👋 봇 종료 중...")
        print("="*50)
        sys.exit(0)
        
    except Exception as e:
        print("\n" + "="*50)
        print("❌ 예상치 못한 오류 발생")
        print("="*50)
        print(f"오류 내용: {e}")
        print(f"오류 타입: {type(e).__name__}")
        sys.exit(1)


# ==================== 프로그램 진입점 ====================

if __name__ == "__main__":
    main()
