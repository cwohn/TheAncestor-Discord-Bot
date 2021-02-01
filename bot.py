import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random
import asyncio

#Load Enviroment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN') #Identifies the user (the bot)

command_prefix = "!"
bot = commands.Bot(command_prefix=command_prefix)

##Global Parameters

#Minimum  time between barks
bot.frequency = 3

#Booleon to control whether the bot is barking
bot.barking = False

#Chance of skipping this bark
bot.skip_chance = .5

#amount of time in seconds between skip checks
bot.skip_delay = 5

#The context in which the bot barks
bot.bark_ctx = None

#Whether the bot displays filenames when playing quotes
bot.show_filenames = False

#A "bark" is when a quote is played; this includes a message and playing a sound
async def bark(ctx,ogg_filename=None):
    txt_filename = None
    transcript = None

    #Get a random quote, if filename is unspecified
    if ogg_filename is None:
        ogg_filename,transcript = random.choice(list(quotes.items()))
    else:
        txt_filename = quotes[ogg_filename]
    
    await ctx.send(transcript)

    #Play the audio
    if bot.show_filenames:
        await ctx.send(f"({ogg_filename})")
    await play(ctx,ogg_filename)

#The quote command plays a specific file
@bot.command(name="quote",help="I shall dispense the desired quotation\n")
async def quote_command(ctx, *, query):
    #TODO: implement an advanced search based on keywords to find quotes
    if query.startswith("("):
        query = query[1:]
    if query.endswith(")"):
        query = query[:-1]
    if not query.startswith("snd/"):
        query = "snd/" + query
    if not query.endswith(".ogg"):
        query = query + ".ogg"
    query = query.replace(".wav",".ogg").replace(".mp3",".ogg")
    if query in quotes:
        await bark(ctx,query)
    else:
        await ctx.send(f"My search for \'{query}\' yielded naught but dust.")
        await bark(ctx)

#The speak command plays a random quote
@bot.command(name="speak",
             help="You ask only that I speak; what I say will be up to fate.\n")
async def speak_command(ctx):
    await bark(ctx)

#A task which plays random sounds at semi-regular intervals
#It waits for at least a certain amount of time between barks
#Then, it randomly decides whether to play the sound, or wait a while longer
async def bark_cycle_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        while bot.bark_ctx is not None:
            if random.random() < bot.skip_chance:
                await asyncio.sleep(bot.skip_delay)
            else:
                await bark(bot.bark_ctx)
                await asyncio.sleep(bot.frequency*60)
        await asyncio.sleep(5)

@bot.command(name="start",
             help="Start making quotes a semi-regular intervals.\n")
async def start_command(ctx):
    if bot.bark_ctx is None:
        bot.bark_ctx = ctx
    else:
        #TODO alternative responses to !start being invoked twice include...
            #*Start a new task, so that there are two cycles going at once
            #*Switch to a new voice channel if the command is invoked by somebody
                #in a different voice channel
        await ctx.send("You cannot start what has already begun...")

@bot.command(name="stop",
             help="Stop the endless cycle of maddening barks!\n")
async def stop_command(ctx):
    bot.bark_ctx = None

@bot.command(name="set-frequency",
             help="Adjust the frequency of barks, in minutes\n")
async def set_frequency_command(ctx, *, query):
    try:
        bot.frequency = float(query)
    except ValueError:
        await ctx.send("Cease your incomprehensible babbling!")

@bot.command(name="show-filenames",
             help="Show filenames when playing a quote\n")
async def show_filenames_command(ctx):
    bot.show_filenames = True

@bot.command(name="hide-filenames",
             help="Don't show filenames when playing a quote\n")
async def hide_filenames_command(ctx):
    bot.show_filenames = False

#Play the given audio file
async def play(ctx, filename):
    await ensure_voice(ctx)
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename))
    ctx.voice_client.play(source,
                          after=lambda e: print("Player error: " e) if e else None)
    print(f"Now playing: {filename}")

#Connect to a voice channel if not already connected
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()


#What to do when you connect
@bot.event
async def on_ready():
    print(bot)
    print(bot.guilds)
    bot.loop.create_task(bark_cycle_task())



#Read the quotes from the drive
quotes = {}
for ogg_fn in os.listdir("snd"):
    txt_fn = "txt/"+ogg_fn.replace(".ogg",".txt")
    with open(txt_fn) as f:
        quotes["snd/"+ogg_fn] = f.read()

#Start the bot client
bot.run(TOKEN)

