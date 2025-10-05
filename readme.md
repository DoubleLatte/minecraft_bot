# Discord Bot Frame - PYTHON

마인크래프트 서버 관리를 위한 디스코드 봇 프레임워크

## 📋 목차
- [기능 소개](#-기능-소개)
- [설치 방법](#-설치-방법)
- [설정 방법](#-설정-방법)
- [명령어 목록](#-명령어-목록)
- [프로젝트 구조](#-프로젝트-구조)

---

## ✨ 기능 소개

### 🎮 마인크래프트 서버 관리
- **RCON 연동**: 디스코드에서 마인크래프트 서버 제어
- **화이트리스트 관리**: 플레이어 추가/제거/목록 조회
- **OP 권한 관리**: 관리자 권한 부여/제거
- **플레이어 관리**: 킬, 공지 전송 등
- **서버 명령어**: 직접 명령어 실행 (시간 변경, 날씨 등)

### 🔐 권한 시스템
- **관리자 전용 명령어**: 관리자 역할이 없으면 명령어가 보이지 않음
- **역할 기반 권한**: config.yml에서 관리자 역할 설정

### 🛠️ 개발자 도구
- **핫 리로드**: 봇 재시작 없이 Cog 다시 로드
- **확장 관리**: 동적 로드/언로드
- **명령어 동기화**: 즉시 명령어 업데이트

---

## 📦 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/DoubleLatte/Discord_Bot_Frame-PYTHON.git
cd Discord_Bot_Frame-PYTHON
```

### 2. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 마인크래프트 서버 RCON 활성화

`server.properties` 파일 수정:
```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_secure_password_here
```

서버 재시작 필수!

---

## ⚙️ 설정 방법

### config.yml 설정
```yaml
application_id: "봇의 애플리케이션 ID"

token: "봇 토큰"

administrator_role_ids:
  - 123456789012345678  # 관리자 역할 ID

minecraft_rcon:
  host: "localhost"      # 마인크래프트 서버 주소
  port: 25575           # RCON 포트
  password: "rcon비밀번호"  # RCON 비밀번호
```

### 봇 토큰 발급 방법
1. [Discord Developer Portal](https://discord.com/developers/applications) 접속
2. `New Application` 클릭
3. `Bot` 메뉴에서 토큰 복사
4. `OAuth2` > `URL Generator`에서 `bot` 및 `applications.commands` 선택
5. 생성된 URL로 봇 초대

### 관리자 역할 ID 찾기
1. 디스코드 `설정` > `고급` > `개발자 모드` 활성화
2. 역할 우클릭 > `ID 복사`

---

## 📝 명령어 목록

### 🎮 마인크래프트 서버 관리 (관리자 전용)

#### 화이트리스트
- `/화이트리스트추가 [플레이어]` - 화이트리스트에 플레이어 추가
- `/화이트리스트제거 [플레이어]` - 화이트리스트에서 플레이어 제거
- `/화이트리스트목록` - 등록된 플레이어 목록 확인

#### OP 권한
- `/op추가 [플레이어]` - OP 권한 부여
- `/op제거 [플레이어]` - OP 권한 제거

#### 플레이어 관리
- `/킬 [플레이어]` - 특정 플레이어 킬
- `/서버공지 [메시지]` - 서버에 공지 전송

#### 서버 제어
- `/서버명령어 [명령어]` - 직접 RCON 명령어 실행
  - 예시: `time set day`, `weather clear`, `gamemode creative @a`

### 👥 공개 명령어
- `/온라인플레이어` - 현재 접속한 플레이어 목록 (모든 사용자 사용 가능)

### 🛠️ 개발자 명령어 (관리자 전용)
- `/reload [확장명]` - Cog 다시 로드
- `/load [확장명]` - 새 Cog 로드
- `/unload [확장명]` - Cog 언로드
- `/sync` - 슬래시 명령어 동기화
- `/list_extensions` - 로드된 확장 목록 확인

---

## 📁 프로젝트 구조

```
Discord_Bot_Frame-PYTHON/
├── main.py                 # 봇 메인 실행 파일
├── config.yml              # 설정 파일
├── requirements.txt        # 필수 패키지 목록
├── .gitignore             # Git 제외 파일
├── LICENSE                # MIT 라이선스
├── README.md              # 프로젝트 설명서
└── command/               # 명령어 모듈 디렉토리
    ├── dev.py            # 개발자 명령어
    ├── example.py        # 예시 명령어
    └── minecraft.py      # 마인크래프트 관리 명령어
```

---

## 🔧 코드 구조 설명

### has_admin_role() 데코레이터
```python
def has_admin_role():
    """관리자만 명령어 실행 가능 + 명령어 숨김 처리"""
    async def predicate(interaction: Interaction) -> bool:
        admin_role_ids = interaction.client.config.get('administrator_role_ids', [])
        return any(role.id in admin_role_ids for role in interaction.user.roles)
    
    check = app_commands.check(predicate)
    
    def wrapper(func):
        func = check(func)
        func.default_permissions = discord.Permissions(administrator=True)
        return func
    
    return wrapper
```
- **권한 검사**: config.yml의 역할 ID로 권한 확인
- **명령어 숨김**: `default_permissions`로 관리자 외 명령어 안보임

### RCON 비동기 처리
```python
async def execute_rcon_command(self, command: str) -> tuple[bool, str]:
    """RCON 명령어 비동기 실행으로 봇 멈춤 방지"""
    try:
        loop = asyncio.get_event_loop()
        with self.get_rcon_connection() as mcr:
            mcr.connect()
            response = await loop.run_in_executor(None, mcr.command, command)
            return True, response
    except Exception as e:
        return False, f"오류: {str(e)}"
```
- 블로킹 작업을 비동기로 처리하여 봇 성능 유지

---

## 🚀 실행 방법

```bash
python main.py
```

봇이 정상적으로 시작되면:
```
봇 시작 중...
확장 기능 로드 성공: command.example
확장 기능 로드 성공: command.dev
확장 기능 로드 성공: command.minecraft
9개 명령어 동기화 완료

===============
봇 온라인 상태
이름: YourBotName
ID: 123456789012345678
===============
```

---

## ⚠️ 주의사항

### 보안
- `config.yml`은 절대 GitHub에 업로드하지 마세요 (`.gitignore`에 포함됨)
- RCON 비밀번호는 강력하게 설정하세요
- 관리자 역할 ID는 신중하게 설정하세요

### 마인크래프트 서버
- RCON 포트가 방화벽에서 허용되어야 합니다
- 로컬 서버: `host: "localhost"`
- 원격 서버: `host: "서버IP주소"`

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🤝 기여

버그 제보 및 기능 제안은 [Issues](https://github.com/DoubleLatte/Discord_Bot_Frame-PYTHON/issues)에서 받습니다.

---

## 📞 문의

프로젝트 관련 문의: [GitHub Issues](https://github.com/DoubleLatte/Discord_Bot_Frame-PYTHON/issues)
