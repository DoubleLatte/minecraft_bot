import discord
from discord import app_commands, Interaction, Embed
from discord.ext import commands
from discord.ui import Select, View
from mcrcon import MCRcon
import asyncio
from typing import Optional
import re

def has_admin_role():
    """관리자 역할을 가진 사용자만 명령어를 실행할 수 있도록 확인하는 데코레이터"""
    async def predicate(interaction: Interaction) -> bool:
        admin_role_ids = interaction.client.config.get('administrator_role_ids', [])
        return any(role.id in admin_role_ids for role in interaction.user.roles)
   
    check = app_commands.check(predicate)
   
    def wrapper(func):
        func = check(func)
        func.default_permissions = discord.Permissions(administrator=True)
        return func
   
    return wrapper

class MinecraftCommands(commands.Cog):
    """마인크래프트 RCON 명령어 관리 Cog"""
   
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.rcon_config = bot.config.get('minecraft_rcon', {})
   
    def get_rcon_connection(self):
        """RCON 연결 반환"""
        host = self.rcon_config.get('host', 'localhost')
        port = self.rcon_config.get('port', 25575)
        password = self.rcon_config.get('password', '')
        return MCRcon(host, password, port)
   
    async def execute_rcon_command(self, command: str) -> tuple[bool, str]:
        """RCON 명령어 실행 (비동기)"""
        try:
            loop = asyncio.get_event_loop()
            with self.get_rcon_connection() as mcr:
                mcr.connect()
                response = await loop.run_in_executor(None, mcr.command, command)
                return True, response
        except Exception as e:
            return False, f"오류: {str(e)}"
   
    class MinecraftSelect(Select):
        """마인크래프트 명령어 선택 메뉴"""
        def __init__(self, bot: commands.Bot, is_admin: bool):
            options = []
            # 모든 사용자에게 표시되는 명령어
            options.extend([
                discord.SelectOption(label="온라인 플레이어", description="현재 접속 중인 플레이어 목록 확인", value="list_players"),
                discord.SelectOption(label="서버인원 확인", description="현재 서버 인원 수 확인", value="server_status"),
            ])
            # 관리자에게만 표시되는 명령어
            if is_admin:
                options.extend([
                    discord.SelectOption(label="화이트리스트 추가", description="플레이어를 화이트리스트에 추가", value="whitelist_add"),
                    discord.SelectOption(label="화이트리스트 제거", description="플레이어를 화이트리스트에서 제거", value="whitelist_remove"),
                    discord.SelectOption(label="화이트리스트 목록", description="화이트리스트에 등록된 플레이어 목록 확인", value="whitelist_list"),
                    discord.SelectOption(label="서버 명령어", description="직접 서버 명령어 실행", value="server_command"),
                    discord.SelectOption(label="OP 추가", description="플레이어에게 OP 권한 부여", value="op_add"),
                    discord.SelectOption(label="OP 제거", description="플레이어의 OP 권한 제거", value="op_remove"),
                    discord.SelectOption(label="플레이어 킬", description="특정 플레이어 킬", value="kill_player"),
                    discord.SelectOption(label="서버 공지", description="서버에 공지 메시지 전송", value="say_message"),
                ])
            super().__init__(placeholder="명령어를 선택하세요...", min_values=1, max_values=1, options=options)
            self.bot = bot

        async def callback(self, interaction: Interaction):
            value = self.values[0]
            await interaction.response.defer(ephemeral=True)

            if value in ["whitelist_add", "whitelist_remove", "op_add", "op_remove", "kill_player"]:
                # 플레이어 이름을 입력받아야 하는 명령어
                await interaction.followup.send("플레이어 이름을 입력해주세요:", ephemeral=True)
                try:
                    msg = await self.bot.wait_for(
                        "message",
                        check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                        timeout=30.0
                    )
                    player = msg.content.strip()
                    await msg.delete()  # 입력 메시지 삭제
                    command = {
                        "whitelist_add": f"whitelist add {player}",
                        "whitelist_remove": f"whitelist remove {player}",
                        "op_add": f"op {player}",
                        "op_remove": f"deop {player}",
                        "kill_player": f"kill {player}",
                    }[value]
                    success, response = await self.bot.get_cog("MinecraftCommands").execute_rcon_command(command)
                    title = {
                        "whitelist_add": "🎮 화이트리스트 추가",
                        "whitelist_remove": "🎮 화이트리스트 제거",
                        "op_add": "⭐ OP 권한 부여",
                        "op_remove": "⭐ OP 권한 제거",
                        "kill_player": "💀 플레이어 킬",
                    }[value]
                    embed = Embed(
                        title=title,
                        color=discord.Color.green() if success else discord.Color.red()
                    )
                    embed.add_field(name="플레이어", value=player, inline=True)
                    embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
                    embed.add_field(name="응답", value=response, inline=False)
                    await interaction.followup.send(embed=embed, ephemeral=True)

                except asyncio.TimeoutError:
                    await interaction.followup.send("⏰ 입력 시간이 초과되었습니다.", ephemeral=True)

            elif value == "server_command":
                # 서버 명령어 입력
                await interaction.followup.send("실행할 명령어를 입력해주세요:", ephemeral=True)
                try:
                    msg = await self.bot.wait_for(
                        "message",
                        check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                        timeout=30.0
                    )
                    command = msg.content.strip()
                    await msg.delete()  # 입력 메시지 삭제
                    success, response = await self.bot.get_cog("MinecraftCommands").execute_rcon_command(command)
                    embed = Embed(
                        title="⚙️ 서버 명령어 실행",
                        color=discord.Color.green() if success else discord.Color.red()
                    )
                    embed.add_field(name="명령어", value=f"`{command}`", inline=False)
                    embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
                    embed.add_field(name="응답", value=f"```{response}```" if response else "응답 없음", inline=False)
                    await interaction.followup.send(embed=embed, ephemeral=True)

                except asyncio.TimeoutError:
                    await interaction.followup.send("⏰ 입력 시간이 초과되었습니다.", ephemeral=True)

            elif value == "say_message":
                # 공지 메시지 입력
                await interaction.followup.send("전송할 공지 메시지를 입력해주세요:", ephemeral=True)
                try:
                    msg = await self.bot.wait_for(
                        "message",
                        check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                        timeout=30.0
                    )
                    message = msg.content.strip()
                    await msg.delete()  # 입력 메시지 삭제
                    success, response = await self.bot.get_cog("MinecraftCommands").execute_rcon_command(f"say {message}")
                    embed = Embed(
                        title="📢 서버 공지",
                        color=discord.Color.green() if success else discord.Color.red()
                    )
                    embed.add_field(name="메시지", value=message, inline=False)
                    embed.add_field(name="결과", value="✅ 전송 성공" if success else "❌ 전송 실패", inline=True)
                    await interaction.followup.send(embed=embed, ephemeral=True)

                except asyncio.TimeoutError:
                    await interaction.followup.send("⏰ 입력 시간이 초과되었습니다.", ephemeral=True)

            elif value == "server_status":
                # 서버인원 확인
                success, response = await self.bot.get_cog("MinecraftCommands").execute_rcon_command("list")
                embed = Embed(
                    title="📊 서버인원 확인",
                    color=discord.Color.blue() if success else discord.Color.red()
                )
                if success:
                    # 응답 형식 예: "There are 2 of a max of 20 players online: player1, player2"
                    match = re.match(r"There are (\d+) of a max of (\d+) players online: (.*)", response)
                    if match:
                        current_players, max_players, player_list = match.groups()
                        embed.add_field(name="현재 인원", value=current_players, inline=True)
                        embed.add_field(name="최대 인원", value=max_players, inline=True)
                        embed.add_field(name="접속 중인 플레이어", value=player_list if player_list else "없음", inline=False)
                    else:
                        embed.add_field(name="상태", value="응답을 파싱할 수 없습니다.", inline=False)
                else:
                    embed.add_field(name="상태", value="서버에 연결할 수 없습니다.", inline=False)
                await interaction.followup.send(embed=embed, ephemeral=True)

            else:
                # 입력이 필요 없는 명령어 (whitelist_list, list_players)
                command = "whitelist list" if value == "whitelist_list" else "list"
                success, response = await self.bot.get_cog("MinecraftCommands").execute_rcon_command(command)
                embed = Embed(
                    title="📋 화이트리스트 목록" if value == "whitelist_list" else "👥 온라인 플레이어",
                    color=discord.Color.blue() if success else discord.Color.red()
                )
                embed.add_field(
                    name="목록" if value == "whitelist_list" else "플레이어",
                    value=response if response else ("플레이어 없음" if value == "whitelist_list" else "서버에 연결할 수 없습니다."),
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="서버관리", description="마인크래프트 서버 관리 명령어를 실행합니다")
    async def server_management(self, interaction: Interaction) -> None:
        """마인크래프트 서버 관리 명령어 메뉴"""
        is_admin = await self.has_admin_role_check(interaction)
        
        # 임베드 생성
        embed = Embed(
            title="🎮 마인크래프트 서버 관리",
            description=(
                "아래 메뉴에서 원하는 명령어를 선택하세요.\n"
                f"{'관리자 권한으로 모든 관리 명령어를 사용할 수 있습니다.' if is_admin else '일반 사용자는 서버 상태 확인 명령어만 사용할 수 있습니다.'}"
            ),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="서버 정보",
            value=(
                f"**호스트**: {self.rcon_config.get('host', 'localhost')}\n"
                f"**포트**: {self.rcon_config.get('port', 25575)}"
            ),
            inline=False
        )
        embed.set_footer(text="60초 내에 선택해주세요.")

        view = View(timeout=60.0)
        view.add_item(self.MinecraftSelect(self.bot, is_admin))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def has_admin_role_check(self, interaction: Interaction) -> bool:
        """관리자 역할 확인"""
        admin_role_ids = self.bot.config.get('administrator_role_ids', [])
        return any(role.id in admin_role_ids for role in interaction.user.roles)

    # 에러 핸들러
    async def cog_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "❌ 이 명령어를 사용할 권한이 없습니다.",
                ephemeral=True
            )
        else:
            print(f"Minecraft 명령어에서 오류 발생: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 명령어 실행 중 오류가 발생했습니다.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ 명령어 실행 중 오류가 발생했습니다.",
                    ephemeral=True
                )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MinecraftCommands(bot))
    print("MinecraftCommands cog가 성공적으로 로드되었습니다.")