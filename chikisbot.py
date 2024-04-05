# Posibles funcionalidades para agregar
# 1. Letra de canciones (si es japones, mandar romaji y hiragana/kanji)
#   1.1 Posiblemente hacer que stremee un karaoke (opcional)
# 3. Stats de diferentes juegos
# 4. Reacciones a comandos que los usuarios usen
# 5. Comando !help

# Dependencias para el bot
import os, asyncio, dotenv, pykakasi, urllib.request
from deep_translator import GoogleTranslator
from langdetect import detect
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from mcstatus import JavaServer

# Token y el ID del canal por donde hablara el bot (NO MODIFICAR)
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)
bot_token = os.getenv("DISCORD_TOKEN")
os.environ["B_SERVER"] = str(urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8'))
dotenv.set_key(dotenv_file, "B_SERVER", os.environ["B_SERVER"])

# Inicializacion del bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Servidor de Minecraft
mc_server = JavaServer(host=f"{os.getenv('B_SERVER')}", port=25565)

# Traductores
traductor = GoogleTranslator(target='spanish')
kks = pykakasi.kakasi()

# Eventos/Comandos
@bot.event
async def on_ready():
    # Mensaje de inicializacion del bot
    print("Se ejecuto con exito.")
    channel = bot.get_channel(int(os.getenv("CHANNEL_ID")))
    await channel.send("Buenas, sean libres de usar mis comandos. Cuando me desconectan, elimino todo lo que hayan mandado por este canal.")

    # Visualizar en terminal si estan todos los comandos
    try:
        synced = await bot.tree.sync()
        print(f"Encontre {len(synced)} comandos")
    except Exception as e:
        print(e)

# Funcion para desconectar el cliente
@bot.command(name='Disconnect Bot Client', aliases=['die', 'close', 'bye', 'cls', 'adios', 'cya'])
@commands.is_owner()
async def disconnect(ctx):
    #Mensajes de despedida
    print("Cerrando el cliente...")
    await ctx.send("Adios, nos vemos. Borrando todo lo que mandaron...")
    await asyncio.sleep(3)

    # Se elimina el canal y se crea una copia vacia de este
    await ctx.channel.delete()
    new_channel = await ctx.channel.clone(reason="Channel was purged")
    await new_channel.edit(position=ctx.channel.position)

    # Se guarda el identificador del nuevo canal en el archivo .env
    os.environ["CHANNEL_ID"] = str(new_channel.id)
    dotenv.set_key(dotenv_file, "CHANNEL_ID", os.environ["CHANNEL_ID"])

    # Se cierra el cliente del bot
    await bot.close()

# Manda el IP del host (en caso de que el admin hostee un servidor)
# Usar con precaucion porque manda la direccion IP publica
@bot.command(name="Send server IP (if it's hosted on admin's PC)", aliases=['ip', 'host'])
@commands.is_owner()
async def ip(ctx):
    await ctx.send(f"La IP del servidor es: {(os.getenv('B_SERVER'))}", delete_after=10)

# Funcion de traduccion (estable)
@bot.tree.command(name="traduccion")
@app_commands.describe(texto="Escribe lo que quieres que traduzca:")
@app_commands.choices(idioma_a_traducir=[
    discord.app_commands.Choice(name=f"{lenguaje}", value=abreviacion) 
    for lenguaje, abreviacion in GoogleTranslator().get_supported_languages(as_dict=True).items()
    if lenguaje in [
        'spanish', 'english', 'french', 'italian', 'german', 'japanese',
        'arabic', 'chinese (simplified)', 'russian', 'korean', 'portuguese',
        'latin', 'hebrew', 'catalan'
        ]
    ])
async def translation(interaction: discord.Interaction, texto: str, idioma_a_traducir: Optional[discord.app_commands.Choice[str]]):
    # Caso: El texto que se mando no se encuentra vacio
    if not texto == None or not texto == '':
        # En caso de no seleccionar un lenguaje, se traduce al español por default
        if idioma_a_traducir == None:
            # Como el idioma a traducir por defecto es el español, se cambia el target/idioma a traducir
            # por el ingles si es que se manda texto en español
            if detect(text=texto)=="spanish" or detect(text=texto)=="es":
                traductor.target = 'en'
                embed = discord.Embed(title='Traducción')
                embed.add_field(name=f"{interaction.user} mandó:", value=texto, inline=False)
                embed.add_field(name=f"que se traduce como:", value=traductor.translate(text=texto), inline=False)
                traductor.target = 'es'
                await interaction.response.send_message(embed=embed)
            # Se traduce normal al español
            else:
                embed = discord.Embed(title='Traducción')
                embed.add_field(name=f"{interaction.user} mandó:", value=texto, inline=False)
                embed.add_field(name=f"que se traduce como:", value=traductor.translate(text=texto), inline=False)
                await interaction.response.send_message(embed=embed)
        # Se traduce al lenguaje seleccionado
        else:
            traductor.target = idioma_a_traducir
            embed = discord.Embed(title='Traducción')
            embed.add_field(name=f"{interaction.user} mandó:", value=texto, inline=False)
            embed.add_field(name=f"que se traduce como:", value=traductor.translate(text=texto), inline=False)
            traductor.target = 'es'
            await interaction.response.send_message(embed=embed)
    # Manda un mensaje cuando el usuario no mando nada
    else:
        embed = discord.Embed(title='Traducción')
        embed.add_field(name=f"No mandaste nada, {interaction.user}.", value=texto, inline=False)
        await interaction.response.send_message(embed=embed)

# Funcion de traduccion de Kanji (estable)
@bot.tree.command(name='traduccion_jap')
@app_commands.describe(texto_jap="Escribe lo que quieres que traduzca: (SOLO JAP Y 25 CARACTERES O MENOS)")
async def traduccion_jap(interaction: discord.Interaction, texto_jap: str):
    # Checa si el texto que se pasa es un numero
    if not texto_jap.isdigit():
        # Verifica que el texto que se pasa son caracteres japoneses
        if detect(text=texto_jap) == "japanese" or detect(text=texto_jap) == 'ja':
            traduccion = GoogleTranslator(target='english').translate(text=texto_jap)
            traduccion_jp = kks.convert(text=texto_jap)
            embed = discord.Embed(title="Traducción JP")
            # Como es un diccionario el que se pasa al hacer la conversion (kanji -> hiragana -> romaji)
            # se lee dicho diccionario y se agrega al embed message dependiendo de la division
            for item in traduccion_jp:
                embed.add_field(name="Japonés", value=item['orig'], inline=False)
                embed.add_field(name="Hiragana", value=item['hira'], inline=True)
                embed.add_field(name="Romaji", value=item['hepburn'], inline=True)
                embed.add_field(name="------------", value='', inline=False)
            embed.add_field(name="Traducción:", value=traduccion, inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="Traducción JP")
            embed.add_field(name="ERROR!" ,value="Lo que mandaste no está en Japonés. Recuerda utilizar el alfabeto del lenguaje.")
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Traducción JP")
        embed.add_field(name="ERROR!" ,value="Lo que mandaste son puros dígitos.")
        await interaction.response.send_message(embed=embed)

# Funciones para el servidor de Minecraft
# Funcion para mostrar el estado del servidor
@bot.tree.command(name='server_status', description="Mostrar el estado del servidor de Minecraft hosteado por mi amo.")
@commands.has_role([1047699195160707142, 768897058290532403, 1048470500994719744]) # Misionero, Arzobispo y Papa respectivamente
async def server_status(interaction: discord.Interaction):
    embed = discord.Embed(title="Status del servidor de Minecraft")
    try:
        mc_status = await (await JavaServer.async_lookup(f"{os.getenv('B_SERVER')}")).async_status()
    except Exception as e:
        print(e)
    query = mc_server.query()
    if mc_status.players.online == 0:
        embed.add_field(name="Parece que el servidor esta vacío.", value='')
    else:
        embed.add_field(name=query.map, value='', inline=False)
        embed.add_field(name=f"Están jugando: ({mc_status.players.online})", value=f"{', '.join(query.players.names)}", inline=False)
        
    await interaction.response.send_message(embed=embed)

bot.run(bot_token)