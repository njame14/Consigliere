from consigliere.lib.cogs.utils import MusicUtils
from discord.ext.commands import Cog
from discord.ext.commands.context import Context
from discord.ext.commands import command
import asyncio

class MusicCog(Cog):
    INACTIVITY_TIMEOUT = 120  # seconds
    def __init__(self, bot):
        self._bot = bot
        self._database = bot.database
        self.MusicData = bot.database.context.MusicData

    #Checks if user is in a voice channel when requesting bot to play music 
    async def ensure_voice(self, ctx : Context):
        #If bot is not connected to a voice channel
        if ctx.voice_client is None:
            #Check if user is in a voice channel
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("❌ Please connect to a voice channel first.")
            return
        #If bot and user are in the same voice channel
        elif ctx.voice_client.channel == ctx.author.voice.channel:
            return
        #If bot and user are not in the same voice channel
        #Stop playing music and just connect to user's voice channel
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.author.voice.channel.connect()
            return
        


    @command(brief="Join a voice channel", description="Makes the bot join the user's current voice channel.")
    async def join(self, ctx: Context):
        """
        Makes the bot join the user's voice channel.

        Parameters:
        - ctx (Context): The context in which the command was invoked.

        Usage:
        - $join
        """
        # Check if the user is in a voice channel
        if ctx.author.voice:
            channel = ctx.author.voice.channel

            if ctx.voice_client is not None and ctx.voice_client.channel == ctx.author.voice.channel:
                await ctx.send(f'❌ Already in {channel.name}!')
                return

            # Check if the bot is already in a voice channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
                await ctx.send(f"Moved to {channel.name}!")
            else:
                await channel.connect()
                await ctx.send(f"Joined {channel.name}!")
        else:
            await ctx.send("❌ You are not connected to a voice channel.")



    @command(brief="Leave the voice channel", description="Makes the bot leave the current voice channel.")
    async def leave(self, ctx: Context):

        # Check if the bot is connected to a voice channel
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("🚀 Left the voice channel. Until next time bozo! ✨")
        else:
            await ctx.send("❌ The bot not connected to any voice channel.")



    @command(brief="Play a song or add to queue", description="Plays a song from the given URL. Adds to the queue if a song is already playing.")
    async def play(self, ctx: Context, url = None):
        """
        Plays a song from the provided URL or adds it to the queue if a song is already playing.

        Parameters:
        - ctx (Context): The context in which the command was invoked.
        - url (str): The URL of the song to be played.

        Usage:
        - $play <URL>
        """
        await self.ensure_voice(ctx)
        if not ctx.voice_client:
            return await ctx.send("❌ The bot is not connected to a voice channel.")

        if url is None:
            return await ctx.send(" ❌ Try again. Please provide a url to play!")
        
        server_id = ctx.guild.id
        requester = ctx.message.author

        try:
            with self._database.Session() as session:
                if not MusicUtils.validateUrl(url):
                    return await ctx.send("That is not a valid URL.")

                # Consider optimizing this query for large queues
                previous_song = session.query(self.MusicData)\
                    .filter(self.MusicData.server_id == server_id)\
                    .order_by(self.MusicData.queue_pos.desc()).first()
                position = 1 if previous_song is None else previous_song.queue_pos + 1

                song = self.MusicData(
                    server_id=server_id,
                    requester_id=requester.id,
                    url=url,
                    queue_pos=position
                )
                session.add(song)
                session.commit()

            if ctx.voice_client.is_playing() or position > 1:
                await ctx.send(f'🎶 Adding to queue! Queue now has {position} songs!')
            else:
                player = await MusicUtils.YTDLSource.from_url(url, loop=self._bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: self.handle_playback_error(e, ctx, url))
                await ctx.send(f'▶️ Now Playing: {player.title}.')

        except Exception as e:
            print(e)
            await ctx.send("❌ An error occurred while processing your request.")



    @command(brief="Pause the music", description="Pauses the currently playing song.")
    async def pause(self, ctx: Context):
        voice_client = ctx.voice_client

        # Check if the bot is connected to a voice channel and is playing music
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("⏸️ Music paused.")

        else:
            await ctx.send("❌ No music is currently playing.")



    @command(brief="Resume playing music", description="Resumes the playback of a paused song.")
    async def resume(self, ctx: Context):
    # Function implementation

        voice_client = ctx.voice_client

        # Check if the bot is connected to a voice channel and music is paused
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Resumed!")
        else:
            await ctx.send("❌ Music is not paused.")



    command(brief="Stop playing and clear queue", description="Stops the currently playing song, clears the queue, and disconnects the bot from the voice channel.")
    async def stop(self, ctx: Context):
        voice_client = ctx.voice_client

        # Check if the bot is connected to a voice channel
        if not voice_client:
            await ctx.send("❌ The bot not connected to any voice channel.")
            return

        # Check if the user is in the same voice channel as the bot
        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send("❌ You need to be in the same voice channel to stop the music.")
            return
        
        # Stop the music and clear the queue
        try:
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()

            with self._database.Session() as session:
                session.query(self.MusicData)\
                    .filter(self.MusicData.server_id == ctx.guild.id)\
                    .delete()
                session.commit()

            await ctx.send("⏹️ Music is stopped and queue is cleared.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {e}")



    @command(brief="Remove a song from the queue", description="Removes the song at the specified position from the queue.")
    async def remove(self, ctx: Context, position: int):
    # Function implementation

        """
        Resumes the playback of a paused song.

        Parameters:
        - ctx (Context): The context in which the command was invoked.

        Usage:
        - $resume
        """
        server_id = ctx.guild.id

        with self._database.Session() as session:
            # If no position is provided, show the queue
            if position is None:
                queue = session.query(self.MusicData)\
                    .filter(self.MusicData.server_id == server_id)\
                    .order_by(self.MusicData.queue_pos)\
                    .all()

                if queue:
                    queue_display = "\n".join([f"{idx + 1}. {song.url}" for idx, song in enumerate(queue)])
                    await ctx.send(f"Current Queue:\n{queue_display}\n\Select which song to remove.")
                else:
                    await ctx.send("The queue is currently empty.")
                return

            # Validate the position argument
            if position < 1:
                await ctx.send("❌ Try again. Please provide a valid position number.")
                return

            # Fetch the song at the specified position
            song_to_remove = session.query(self.MusicData)\
                .filter(self.MusicData.server_id == server_id)\
                .order_by(self.MusicData.queue_pos)\
                .offset(position - 1)\
                .first()

            if song_to_remove:
                session.delete(song_to_remove)

                # Update positions of remaining songs
                remaining_songs = session.query(self.MusicData)\
                    .filter(self.MusicData.server_id == server_id, self.MusicData.queue_pos > song_to_remove.queue_pos)\
                    .order_by(self.MusicData.queue_pos)

                for song in remaining_songs:
                    song.queue_pos -= 1

                session.commit()
                await ctx.send("🗑️ Removed song {position} from the queue.")

            else:
                await ctx.send("❌ There is no song at that position in the queue.")

            

    @command(brief="Skip the current song", description="Skips the currently playing song and plays the next song in the queue.")
    async def skip(self, ctx: Context):
        """
        Skips the currently playing song and plays the next song in the queue, if available.

        Parameters:
        - ctx (Context): The context in which the command was invoked.

        Usage:
        - $skip
        """
        voice_client = ctx.voice_client

        # Check if the bot is connected and playing music.
        if voice_client and voice_client.is_playing():
            with self._database.Session() as session:
                server_id = ctx.guild.id

                # Get the currently playing song to remove it from the queue.
                current_song = session.query(self.MusicData)\
                    .filter(self.MusicData.server_id == server_id)\
                    .order_by(self.MusicData.queue_pos)\
                    .first()

                if current_song:
                    session.delete(current_song)
                    session.commit()

            # Stop the current song and initiate playing the next song.
            voice_client.stop()  # This will trigger the after callback, which should call play_next
            await ctx.send("⏭️ Skipping.")
            await self.play_next(ctx)
        else:
            await ctx.send("❌ No song is currently playing.")

    @command(brief="Show the music queue", description="Displays the current music queue.")
    async def queue(self, ctx: Context):
    # Function implementation

        """
        Displays the current music queue.

        Parameters:
        - ctx (Context): The context in which the command was invoked.

        Usage:
        - $queue
        """
        server_id = ctx.guild.id

        with self._database.Session() as session:
            queue = session.query(self.MusicData)\
                .filter(self.MusicData.server_id == server_id)\
                .order_by(self.MusicData.queue_pos)\
                .all()

            if queue:
                queue_display = "\n".join([f"{idx + 1}. {song.url}" for idx, song in enumerate(queue)])
                await ctx.send(f"Current Queue:\n{queue_display}")
            else:
                await ctx.send("The queue is currently empty.")

    @command(brief="Show now playing", description="Displays information about the currently playing song.", aliases=['np', 'current'])
    async def now_playing(self, ctx: Context):
        """
        Displays information about the currently playing song.

        Parameters:
        - ctx (Context): The context in which the command was invoked.

        Usage:
        - $np
        """
        voice_client = ctx.voice_client

        if voice_client and voice_client.source:
            # Assuming voice_client.source is a YTDLSource or similar with a 'title' attribute
            current_song = voice_client.source.title
            await ctx.send(f"Now playing: {current_song}")
        else:
            await ctx.send("❌ No song is currently playing.")



    def handle_playback_error(self, error, ctx, url):
        if error:
            print(f'❌ Player error: {error}')
            self._bot.loop.create_task(self.play_next(ctx, url))


    async def play_next(self, ctx: Context, last_url = None):
        server_id = ctx.guild.id

        with self._database.Session() as session:
            try:
                # Efficiently find and remove the last song from the queue
                last_song = session.query(self.MusicData)\
                    .filter(self.MusicData.server_id == server_id, self.MusicData.url == last_url)\
                    .first()
                if last_song:
                    session.delete(last_song)
                    session.commit()

                # Get the next song
                next_song = session.query(self.MusicData)\
                    .filter(self.MusicData.server_id == server_id)\
                    .order_by(self.MusicData.queue_pos)\
                    .first()

                if next_song:
                    player = await MusicUtils.YTDLSource.from_url(next_song.url, loop=self._bot.loop, stream=True)
                    if not ctx.voice_client.is_playing():
                        ctx.voice_client.play(player, after=lambda e: self.handle_playback_error(e, ctx, next_song.url))
                        await ctx.send(f"Now Playing: {player.title}.")
                else:
                    # Consider what to do if there are no more songs in the queue
                    await ctx.send('Queue is empty!')
                    self.tick(ctx)
            except Exception as e:
                print(f"❌ Error in play_next: {e}")
                await ctx.send("❌ An error occurred while trying to play the next song.")


    async def tick(self, ctx):
        client = ctx.voice_client
        time = 0
        while client and client.is_connected():
            await asyncio.sleep(1)
            time = (time + 1) if not (client.is_playing() or client.is_paused()) else 0

            if time >= self.INACTIVITY_TIMEOUT:
                try:
                    await ctx.send("Disconnected due to inactivity. Gabagool!")
                    await client.disconnect()
                except Exception as e:
                    print(f"❌ Error during disconnection: {e}")
                break

    @Cog.listener()
    async def on_ready(self):
        print("MusicCog loaded successfully.")

async def setup(bot):
   await bot.add_cog(MusicCog(bot))
   