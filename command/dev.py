import discord
from discord import app_commands, Interaction
from discord.ext import commands


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


class DevCommands(commands.Cog):
    """개발자를 위한 명령어 관리 Cog"""
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    # ==================== 확장 목록 조회 ====================
    
    @app_commands.command(
        name="list_extensions", 
        description="현재 로드된 모든 확장 기능을 표시합니다"
    )
    @has_admin_role()
    async def list_extensions(self, interaction: Interaction) -> None:
        loaded_extensions = list(self.bot.extensions.keys())
        
        if not loaded_extensions:
            await self.send_response(
                interaction, 
                "현재 로드된 확장 기능이 없습니다.", 
                False
            )
            return
        
        embed = discord.Embed(
            title="📦 로드된 확장 기능 목록", 
            color=discord.Color.blue(),
            description=f"총 {len(loaded_extensions)}개의 확장 기능이 로드되어 있습니다."
        )
        
        for i, ext in enumerate(loaded_extensions, 1):
            embed.add_field(
                name=f"{i}. {ext}", 
                value="✅ 로드됨", 
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ==================== 에러 핸들러 ====================
    
    async def cog_app_command_error(
        self, 
        interaction: Interaction, 
        error: app_commands.AppCommandError
    ):
        """Cog 레벨 에러 핸들러"""
        if isinstance(error, app_commands.CheckFailure):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ 이 명령어를 사용할 권한이 없습니다.", 
                    ephemeral=True
                )
        else:
            print(f"DevCommands에서 오류 발생: {error}")
            
            error_message = "❌ 명령어 실행 중 오류가 발생했습니다."
            
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    error_message, 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    error_message, 
                    ephemeral=True
                )


async def setup(bot: commands.Bot) -> None:
    """Cog 설정 함수"""
    await bot.add_cog(DevCommands(bot))
    print("✅ DevCommands cog가 성공적으로 로드되었습니다.")
 유틸리티 메서드 ====================
    
    async def send_response(
        self, 
        interaction: Interaction, 
        message: str, 
        success: bool
    ) -> None:
        """
        공통 응답 메시지를 전송하는 유틸리티 함수
        
        Args:
            interaction: Discord Interaction 객체
            message: 전송할 메시지
            success: 성공 여부 (True: ✅, False: ❌)
        """
        emoji = "✅" if success else "❌"
        await interaction.response.send_message(
            f"{emoji} {message}", 
            ephemeral=True
        )
    
    # ==================== 확장 관리 명령어 ====================
    
    @app_commands.command(
        name="reload", 
        description="지정한 Cog를 다시 로드합니다"
    )
    @app_commands.describe(extension="다시 로드할 확장 기능 이름 (예: command.minecraft)")
    @has_admin_role()
    async def reload_command(self, interaction: Interaction, extension: str) -> None:
        try:
            await self.bot.reload_extension(extension)
            await self.send_response(
                interaction, 
                f"`{extension}` 확장 기능이 성공적으로 다시 로드되었습니다.", 
                True
            )
        except commands.ExtensionError as e:
            await self.send_response(
                interaction, 
                f"`{extension}` 확장 기능 로드 중 오류 발생: {str(e)}", 
                False
            )
    
    @app_commands.command(
        name="load", 
        description="새 Cog를 로드합니다"
    )
    @app_commands.describe(extension="로드할 확장 기능 이름 (예: command.minecraft)")
    @has_admin_role()
    async def load_command(self, interaction: Interaction, extension: str) -> None:
        try:
            await self.bot.load_extension(extension)
            await self.bot.tree.sync()
            await self.send_response(
                interaction, 
                f"`{extension}` 확장 기능이 성공적으로 로드되었습니다.", 
                True
            )
        except commands.ExtensionError as e:
            await self.send_response(
                interaction, 
                f"`{extension}` 확장 기능 로드 중 오류 발생: {str(e)}", 
                False
            )
    
    @app_commands.command(
        name="unload", 
        description="Cog를 언로드합니다"
    )
    @app_commands.describe(extension="언로드할 확장 기능 이름 (예: command.minecraft)")
    @has_admin_role()
    async def unload_command(self, interaction: Interaction, extension: str) -> None:
        # 개발 명령어 자체는 언로드 불가
        if extension == "command.dev":
            await self.send_response(
                interaction, 
                "개발 명령어 자체는 언로드할 수 없습니다.", 
                False
            )
            return
        
        try:
            await self.bot.unload_extension(extension)
            await self.bot.tree.sync()
            await self.send_response(
                interaction, 
                f"`{extension}` 확장 기능이 성공적으로 언로드되었습니다.", 
                True
            )
        except commands.ExtensionError as e:
            await self.send_response(
                interaction, 
                f"`{extension}` 확장 기능 언로드 중 오류 발생: {str(e)}", 
                False
            )
    
    # ==================== 명령어 동기화 ====================
    
    @app_commands.command(
        name="sync", 
        description="슬래시 명령어를 동기화합니다"
    )
    @has_admin_role()
    async def sync_command(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        
        try:
            synced = await self.bot.tree.sync()
            await interaction.followup.send(
                f"✅ {len(synced)}개의 명령어가 성공적으로 동기화되었습니다.", 
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"❌ 명령어 동기화 중 오류 발생: {str(e)}", 
                ephemeral=True
            )
    
    # ====================