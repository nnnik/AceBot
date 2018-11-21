import discord
from discord.ext import commands

from datetime import datetime, timedelta

from utils.database import db, LogEntry
from cogs.base import TogglableCogMixin

MEDALS = ['🥇', '🥈', '🥉', '🏅', '🏅']

class Stats(TogglableCogMixin):
	'''Show stats about the bot.'''
	
	def __init__(self, bot):
		super().__init__(bot)
		
		self.bot.before_invoke(self.on_invoke)
		
	async def __local_check(self, ctx):
		return await self._is_used(ctx)
		
	async def on_invoke(self, ctx):
		await LogEntry.create(
			guild_id=ctx.guild.id,
			channel_id=ctx.channel.id,
			author_id=ctx.author.id,
			date=datetime.now(),
			command=ctx.command.qualified_name
		)
	
	def create_list(self, cmds, members=None):
		value = ''
		for index, cmd in enumerate(cmds):
			value += f'\n{MEDALS[index]} {members[index] if members else cmd[1]} ({cmd[0]} uses)'
		
		if not len(value):
			raise commands.CommandError('No stats found!')
		
		return value[1:]
	
	async def guild_stats(self, guild):
		now = datetime.now() - timedelta(days=1)
		
		uses = await db.first('SELECT COUNT(*) FROM log WHERE guild_id=$1', guild.id)
		
		query = """ SELECT
						COUNT(id), command
					FROM log
					WHERE guild_id = $1
					AND date > $2
					GROUP BY command
					ORDER BY COUNT DESC
					LIMIT 5
				"""
		
		today = await db.all(query, guild.id, now)
		
		query = """ SELECT
						COUNT(id), command
					FROM log
					WHERE guild_id = $1
					GROUP BY command
					ORDER BY COUNT DESC
					LIMIT 5
				"""
		
		all_time = await db.all(query, guild.id)
		
		query = """ SELECT
						COUNT(id), author_id
					FROM log
					WHERE guild_id = $1
					GROUP BY author_id
					ORDER BY COUNT DESC
					LIMIT 5
				"""
		
		top_users = await db.all(query, guild.id)
		
		query = """ SELECT
						COUNT(id), author_id
					FROM log
					WHERE guild_id = $1
					AND date > $2
					GROUP BY author_id
					ORDER BY COUNT DESC
					LIMIT 5
				"""
		
		top_users_today = await db.all(query, guild.id, now)
		
		topu, topt = [], []
		for row in top_users:
			member = guild.get_member(row[1])
			topu.append(member.mention if member else 'Unknown')
		for row in top_users_today:
			member = guild.get_member(row[1])
			topt.append(member.mention if member else 'Unknown')
		
		e = discord.Embed(description=f'{uses[0]} total commands issued.')
		e.set_author(name=guild.name, icon_url=guild.icon_url)
		
		e.add_field(
			name='Top Commands',
			value=self.create_list(all_time),
		)
		
		e.add_field(
			name="Today's Top Commands",
			value=self.create_list(today),
		)
		
		e.add_field(
			name='Top Users',
			value=self.create_list(top_users, topu),
			inline=True
		)
		
		e.add_field(
			name="Today's Top Users",
			value=self.create_list(top_users_today, topt),
		)
		
		return e
	
	async def user_stats(self, member):
		uses = await db.first('SELECT COUNT(*) FROM log WHERE author_id=$1', member.id)
		
		query = """ SELECT
						COUNT(id), command
					FROM log
					WHERE author_id = $1
					AND date > $2
					GROUP BY command
					ORDER BY COUNT DESC
					LIMIT 5
				"""
		
		today = await db.all(query, member.id, datetime.now() - timedelta(days=1))
		
		query = """ SELECT
						COUNT(id), command
					FROM log
					WHERE author_id = $1
					GROUP BY command
					ORDER BY COUNT DESC
					LIMIT 5
				"""
		
		all_time = await db.all(query, member.id)
		
		e = discord.Embed(description=f'{uses[0]} total commands issued.')
		e.set_author(name=member.name, icon_url=member.avatar_url)
		
		value = ''
		for index, cmd in enumerate(all_time):
			value += f'\n{MEDALS[index]}: {cmd[1]} ({cmd[0]})'
		
		e.add_field(
			name='Most Used Commands',
			value=self.create_list(all_time),
			inline=False
		)
		
		e.add_field(
			name='Most Used Commands Today',
			value=self.create_list(today),
			inline=False
		)
		
		return e
		
	@commands.command()
	async def stats(self, ctx, member: discord.Member = None):
		await ctx.send(embed=
			await self.user_stats(member)
			if member else
			await self.guild_stats(ctx.guild)
		)
	
def setup(bot):
	bot.add_cog(Stats(bot))