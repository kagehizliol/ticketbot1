import discord
from discord.ext import commands
import asyncio
from keep_alive import keep_alive
keep_alive()
import io

# --- AYARLAR ---
TOKEN = "MTQ4Njc2NzE0MzAzODA5MTQ1NQ.GasKx8.e8ZGmJJscwh2mYDww0kq21rw_Rffb_o8adUmgw"
TICKET_KATEGORI_ID = 1486769482243510312 
LOG_KANAL_ID = 1486767960436506645
BANNER = "https://i.ibb.co/N2zMsvKh/Aspect-Logo.png"
LOG_COLOR = 0xFFA500 

# --- SİLME ONAY MENÜSÜ ---
class DeleteConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Evet, Sil", style=discord.ButtonStyle.danger, custom_id="confirm_delete_v5")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Bu işlem için yetkiniz yok!", ephemeral=True)
        
        await interaction.response.send_message("Kanal 3 saniye içinde kalıcı olarak siliniyor...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

    @discord.ui.button(label="İptal Et", style=discord.ButtonStyle.secondary, custom_id="cancel_delete_v5")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Silme işlemi iptal edildi.", ephemeral=True)

# --- ARŞİVLEME SONRASI SİLME BUTONU ---
class PostCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket'ı Sil", style=discord.ButtonStyle.secondary, emoji="🗑️", custom_id="aspect_delete_init_v5")
    async def delete_init(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Bunu sadece adminler yapabilir!", ephemeral=True)
        
        view = DeleteConfirmView()
        await interaction.response.send_message("⚠️ **Bu kanalı tamamen silmek istediğinize emin misiniz?**", view=view, ephemeral=True)

# --- KAPATMA BUTONU VE LOGLAMA ---
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, emoji="🔒", custom_id="aspect_close_v5_1")
    async def close_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        channel = interaction.channel
        log_channel = interaction.guild.get_channel(LOG_KANAL_ID)
        
        # 1. Transcript Hazırla (Sadece Log için)
        history_text = f"ASPECT SOFTWARE - TRANSCRIPT\nKanal: {channel.name}\nKapatan: {interaction.user.name}\n" + "-"*30 + "\n\n"
        async for msg in channel.history(limit=None, oldest_first=True):
            if not msg.author.bot:
                time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                history_text += f"[{time_str}] {msg.author.name}: {msg.content}\n"
        
        file_data = io.BytesIO(history_text.encode("utf-8"))
        log_transcript = discord.File(file_data, filename=f"transcript-{channel.name}.txt")

        # 2. Yetki Güncelleme (Kullanıcı erişimi kesilir, isim değişmez)
        try:
            for target in channel.overwrites:
                if isinstance(target, discord.Member) and not target.guild_permissions.administrator:
                    if target != interaction.guild.me:
                        await channel.set_permissions(target, overwrite=None)
        except: pass

        # 3. Log Kanalına Bilgi ve Transcript Gönder
        if log_channel:
            log_embed = discord.Embed(title="Ticket Kapatıldı", color=discord.Color.red())
            log_embed.add_field(name="Kanal", value=channel.name, inline=True)
            log_embed.add_field(name="Kapatan", value=interaction.user.mention, inline=True)
            await log_channel.send(embed=log_embed, file=log_transcript)

        # 4. Ticket Kanalına Bilgi ve Silme Butonunu At (Dosya eklenmez)
        end_embed = discord.Embed(
            title="TICKET ARŞİVLENDİ", 
            description="Kullanıcı erişimi kesildi. Konuşma geçmişi log kanalına iletildi.\nSadece adminler bu kanalı silebilir.", 
            color=LOG_COLOR
        )
        await channel.send(embed=end_embed, view=PostCloseView())

# --- KATEGORİ SEÇİM MENÜSÜ ---
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Media / Streamer", value="media", emoji="🛠️"),
            discord.SelectOption(label="Apply as Reseller", value="reseller", emoji="🎮"),
            discord.SelectOption(label="HWID Reset Request", value="hwid", emoji="💲"),
            discord.SelectOption(label="Support / Question", value="support", emoji="💡"),
            discord.SelectOption(label="Pay with Card / IBAN Shopier", value="pay", emoji="💳"),
        ]
        super().__init__(placeholder="Kategori Seçiniz...", min_values=1, max_values=1, options=options, custom_id="aspect_select_v5_1")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_KATEGORI_ID)
        log_channel = guild.get_channel(LOG_KANAL_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }

        # Kanal ismi: kategori-isim (örn: support-kageviro)
        channel_name = f"{self.values[0]}-{interaction.user.name}"
        channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category)
        
        await interaction.response.send_message(f"✅ Ticket açıldı: {channel.mention}", ephemeral=True)
        
        if log_channel:
            log_embed = discord.Embed(title="Yeni Ticket Açıldı", color=discord.Color.green())
            log_embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=True)
            log_embed.add_field(name="Kanal", value=channel.mention, inline=True)
            await log_channel.send(embed=log_embed)

        embed = discord.Embed(title="ASPECT SOFTWARE | DESTEK", description="Sorununuzu detaylıca yazın. Kapatmak için aşağıdaki butonu kullanın.", color=LOG_COLOR)
        embed.set_thumbnail(url=BANNER)
        await channel.send(embed=embed, view=CloseView())

# --- BOT ANA SINIFI ---
class AspectBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        self.add_view(CloseView())
        self.add_view(PostCloseView())
        self.add_view(DeleteConfirmView())
        v = discord.ui.View(timeout=None)
        v.add_item(TicketSelect())
        self.add_view(v)

    async def on_ready(self):
        print(f'{self.user} AKTİF! Aspect V5.1 Sistem Hazır.')
        await self.tree.sync()

bot = AspectBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def kur(ctx):
    embed = discord.Embed(
        title="ASPECT SOFTWARE #V1", 
        description="✨ **Destek Sistemi Hakkında:**\nAşağıdaki seçeneklerden uygun olanı seçerek hemen bir ticket oluşturabilirsiniz.", 
        color=LOG_COLOR
    )
    embed.set_author(name="ASPECT SOFTWARE #V1", icon_url=BANNER)
    embed.set_thumbnail(url=BANNER)
    embed.set_image(url=BANNER)
    embed.set_footer(text="Aspect Bot's | Ticket Sistemi")
    
    view = discord.ui.View(timeout=None)
    view.add_item(TicketSelect())
    await ctx.send(embed=embed, view=view)

bot.run(TOKEN)
