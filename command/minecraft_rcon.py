import discord
from discord import app_commands, Interaction, Embed
from discord.ext import commands
from mcrcon import MCRcon
import asyncio
from typing import Optional


def has_admin_role():
    """관리자 역할을 가진 사용자만 명령어를 실행할 수 있도록 확인하는 데코레이터"""
    async def predicate(interaction: Interaction) -> bool:
        admin_role_ids = interaction.client.config.get('administrator_role_ids', [])
        return any(role.id in admin_role_ids for role in interaction.user.roles)
    
    check = app_commands.check(predicate)
    
    # 명령어가 관리자에게만 보이도록 설정
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
    
    @app_commands.command(name="화이트리스트추가", description="마인크래프트 서버에 플레이어를 화이트리스트에 추가합니다")
    @app_commands.describe(player="추가할 플레이어 이름")
    @has_admin_role()
    async def whitelist_add(self, interaction: Interaction, player: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command(f"whitelist add {player}")
        
        embed = Embed(
            title="🎮 화이트리스트 추가",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="플레이어", value=player, inline=True)
        embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
        embed.add_field(name="응답", value=response, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="화이트리스트제거", description="마인크래프트 서버에서 플레이어를 화이트리스트에서 제거합니다")
    @app_commands.describe(player="제거할 플레이어 이름")
    @has_admin_role()
    async def whitelist_remove(self, interaction: Interaction, player: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command(f"whitelist remove {player}")
        
        embed = Embed(
            title="🎮 화이트리스트 제거",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="플레이어", value=player, inline=True)
        embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
        embed.add_field(name="응답", value=response, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="화이트리스트목록", description="화이트리스트에 등록된 플레이어 목록을 확인합니다")
    @has_admin_role()
    async def whitelist_list(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command("whitelist list")
        
        embed = Embed(
            title="📋 화이트리스트 목록",
            color=discord.Color.blue() if success else discord.Color.red()
        )
        embed.add_field(name="목록", value=response if response else "플레이어 없음", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="서버명령어", description="마인크래프트 서버에 직접 명령어를 실행합니다")
    @app_commands.describe(command="실행할 명령어 (예: list, stop, say 등)")
    @has_admin_role()
    async def server_command(self, interaction: Interaction, command: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command(command)
        
        embed = Embed(
            title="⚙️ 서버 명령어 실행",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="명령어", value=f"`{command}`", inline=False)
        embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
        embed.add_field(name="응답", value=f"```{response}```" if response else "응답 없음", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="온라인플레이어", description="현재 서버에 접속한 플레이어 목록을 확인합니다")
    async def list_players(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        success, response = await self.execute_rcon_command("list")
        
        embed = Embed(
            title="👥 온라인 플레이어",
            color=discord.Color.blue() if success else discord.Color.red(),
            description=response if success else "서버에 연결할 수 없습니다."
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="op추가", description="플레이어에게 OP 권한을 부여합니다")
    @app_commands.describe(player="OP 권한을 부여할 플레이어 이름")
    @has_admin_role()
    async def op_add(self, interaction: Interaction, player: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command(f"op {player}")
        
        embed = Embed(
            title="⭐ OP 권한 부여",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="플레이어", value=player, inline=True)
        embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
        embed.add_field(name="응답", value=response, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="op제거", description="플레이어의 OP 권한을 제거합니다")
    @app_commands.describe(player="OP 권한을 제거할 플레이어 이름")
    @has_admin_role()
    async def op_remove(self, interaction: Interaction, player: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command(f"deop {player}")
        
        embed = Embed(
            title="⭐ OP 권한 제거",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="플레이어", value=player, inline=True)
        embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
        embed.add_field(name="응답", value=response, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="킬", description="특정 플레이어를 킬합니다")
    @app_commands.describe(player="킬할 플레이어 이름")
    @has_admin_role()
    async def kill_player(self, interaction: Interaction, player: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command(f"kill {player}")
        
        embed = Embed(
            title="💀 플레이어 킬",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="플레이어", value=player, inline=True)
        embed.add_field(name="결과", value="✅ 성공" if success else "❌ 실패", inline=True)
        embed.add_field(name="응답", value=response, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="서버공지", description="서버에 공지 메시지를 전송합니다")
    @app_commands.describe(message="전송할 메시지")
    @has_admin_role()
    async def say_message(self, interaction: Interaction, message: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        success, response = await self.execute_rcon_command(f"say {message}")
        
        embed = Embed(
            title="📢 서버 공지",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="메시지", value=message, inline=False)
        embed.add_field(name="결과", value="✅ 전송 성공" if success else "❌ 전송 실패", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
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
