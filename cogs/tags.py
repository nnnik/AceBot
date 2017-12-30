import discord
from discord.ext import commands

import datetime, re
from peewee import *

db = SqliteDatabase('lib/tags.db')

def make_lower(s: str): return s.lower()

class Tags:
	"""Tag system."""

	def __init__(self, bot):
		self.bot = bot
		self.reserved_names = ['create', 'edit', 'delete', 'info', 'list', 'top', 'raw', 'get']

	async def get_tag(self, tag_name: make_lower, guild_id, alias=True):
		for tag_obj in Tag.select().where(Tag.guild == guild_id):
			if tag_name == tag_obj.name:
				return tag_obj
			if alias and tag_name == tag_obj.alias:
				return tag_obj
		return None

	def name_ban(self, tag_name: make_lower):
		if len(tag_name) < 2:
			return 'Tag name too short.'
		if len(tag_name) > 16:
			return 'Tag name too long.'
		if tag_name in self.reserved_names:
			return f"Tag name '{tag_name}' is reserved."
		return None

	"""
	todo

	just save the tags as .lower() to start off with to make it a lot simpler...
	allow removal of alias, just make last default to None and check for that
	add tag raw <tag_name>
	"""

	@commands.group(aliases=['t'])
	async def tag(self, ctx):
		"""Create tags."""

		# send tag
		if ctx.invoked_subcommand is None:
			tag_name = make_lower(ctx.message.content[ctx.message.content.find(' ') + 1:])
			get_tag = await self.get_tag(tag_name, ctx.guild.id)

			if get_tag is None:
				return

			get_tag.uses += 1
			get_tag.save()

			await ctx.send(get_tag.content)

	@tag.group()
	async def create(self, ctx, tag_name: make_lower, *, content: str):
		"""Create a tag."""

		ban = self.name_ban(tag_name)
		if ban:
			return await ctx.send(ban)

		if await self.get_tag(tag_name, ctx.guild.id):
			return await ctx.send(f"Tag '{tag_name}' already exists.")

		date = datetime.datetime.now()
		new_tag = Tag(name=tag_name, content=content, owner=ctx.author.id, guild=ctx.guild.id, created_at=date, edited_at=date, uses=0, alias='')
		new_tag.save()

		await ctx.send(f"Tag '{tag_name}' created.")

	@tag.group()
	async def edit(self, ctx, tag_name: make_lower, *, new_content: str):
		"""Edit an existing tag."""
		get_tag = await self.get_tag(tag_name, ctx.guild.id)

		if get_tag is None:
			return await ctx.send('Could not find tag.')

		if not get_tag.owner == ctx.author.id:
			return await ctx.send('You do not own this tag.')

		get_tag.content = new_content
		get_tag.edited_at = datetime.datetime.now()
		get_tag.save()

		await ctx.send('Tag edited.')

	@tag.group()
	async def delete(self, ctx, *, tag_name: make_lower):
		"""Delete a tag."""

		get_tag = await self.get_tag(tag_name, ctx.guild.id)

		if get_tag is None:
			return await ctx.send('Could not find tag.')

		if not get_tag.owner == ctx.author.id:
			return await ctx.send('You do not own this tag.')

		deleted = get_tag.delete_instance()

		if not deleted:
			await ctx.send('Deleting of tag failed.')
		else:
			await ctx.send(f"Tag '{get_tag.name}' deleted.")

	@tag.group()
	async def alias(self, ctx, tag_name: make_lower, alias: make_lower = None):
		"""Set an alias to a tag."""

		if tag_name == alias:
			return await ctx.send('Tag name and Alias can not be identical.')

		get_tag = await self.get_tag(tag_name, ctx.guild.id, alias=False)

		if get_tag is None:
			return await ctx.send('Could not find tag.')

		if alias is None:
			get_tag.alias = ''
			get_tag.save()
			return await ctx.send(f"Alias for '{tag_name}' removed.")

		ban = self.name_ban(alias)
		if ban:
			return await ctx.send(ban)

		get_tag.alias = alias
		get_tag.save()

		await ctx.send(f"Set alias for '{get_tag.name}' to '{alias}'")

	@tag.group()
	async def raw(self, ctx, *, tag_name: make_lower):
		"""Get raw content of tag.

		Useful for editing! Code taken from Danny's RoboDanny bot.
		"""

		get_tag = await self.get_tag(tag_name, ctx.guild.id)

		if get_tag is None:
			return await ctx.send('Could not find tag.')

		transformations = {
			re.escape(c): '\\' + c
			for c in ('*', '`', '_', '~', '\\', '<')
			}

		def replace(obj):
			return transformations.get(re.escape(obj.group(0)), '')

		pattern = re.compile('|'.join(transformations.keys()))
		await ctx.send(pattern.sub(replace, get_tag.content))


	@tag.group()
	async def list(self, ctx, *, member: discord.Member = None):
		"""List tags from the server or a user."""

		max_tags = 6

		names, uses, tags = '', '', 0

		list = Tag.select()\
			.where(Tag.owner == (Tag.owner if member is None else member.id), Tag.guild == ctx.guild.id)\
			.order_by(Tag.uses.desc())

		for index, get_tag in enumerate(list):
			if (tags < max_tags):
				names += f'\n{get_tag.name}'
				if not get_tag.alias == '':
					names += f' ({get_tag.alias})'
				uses += f'\n{get_tag.uses}'
			tags += 1

		if not tags:
			return await ctx.send('No tags found.')

		e = discord.Embed()
		e.add_field(name='Tag', value=names, inline=True)
		e.add_field(name='Uses', value=uses, inline=True)
		e.description = f'{tags if tags < max_tags else max_tags}/{tags} tags'

		if member is None:
			nick = ctx.guild.name
			avatar = ctx.guild.icon_url
		else:
			nick = member.display_name
			avatar = member.avatar_url

		e.set_author(name=nick, icon_url=avatar)

		await ctx.send(embed=e)

	@tag.group()
	async def info(self, ctx, *, tag_name: make_lower):
		"""Show info about a tag."""

		get_tag = await self.get_tag(tag_name, ctx.guild.id)

		if get_tag is None:
			return await ctx.send("Could not find tag.")

		created_at = str(get_tag.created_at)[0: str(get_tag.created_at).find('.')]
		edited_at = str(get_tag.edited_at)[0: str(get_tag.edited_at).find('.')]
		edited_at = None if created_at == edited_at else edited_at

		member = ctx.guild.get_member(get_tag.owner)

		if member is None:
			nick = 'User not found'
			avatar = ctx.guild.icon_url
		else:
			nick = member.display_name
			avatar = member.avatar_url

		e = discord.Embed()
		e.description = f'**{get_tag.name}**'
		e.set_author(name=nick, icon_url=avatar)
		e.add_field(name='Owner', value=member.mention if member else nick)
		e.add_field(name='Uses', value=get_tag.uses)
		if get_tag.alias:
			e.add_field(name='Alias', value=get_tag.alias)

		footer = f'Created at: {created_at}'
		if edited_at:
			footer += f' (edited: {edited_at})'

		e.set_footer(text=footer)

		await ctx.send(embed=e)

	@commands.command()
	async def tags(self, ctx):
		"""Short manual on the tag system."""


class Tag(Model):
	name = CharField()
	content = TextField()
	owner = IntegerField()
	guild = IntegerField()
	created_at = DateTimeField()
	edited_at = DateTimeField()
	uses = IntegerField()
	alias = CharField()

	class Meta:
		database = db

def setup(bot):
	db.connect()
	try:
		db.create_tables([Tag])
	except:
		pass

	bot.add_cog(Tags(bot))