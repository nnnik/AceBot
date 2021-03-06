import discord, asyncio
from discord.ext import commands

from cogs.base import TogglableCogMixin

NEXT_EMOJI = '⏩'
PREV_EMOJI = '⏪'
STOP_EMOJI = '⏹'
FIRST_EMOJI = '⏮'
LAST_EMOJI = '⏭'
HELP_EMOJI = '❔'


# rip is just the signature command ripped from the lib, but with alias support removed.
def get_signature(command):
	"""Returns a POSIX-like signature useful for help command output."""
	result = []
	parent = command.full_parent_name

	name = command.name if not parent else parent + ' ' + command.name
	result.append(name)

	if command.usage:
		result.append(command.usage)
		return ' '.join(result)

	params = command.clean_params
	if not params:
		return ' '.join(result)

	for name, param in params.items():
		if param.default is not param.empty:
			# We don't want None or '' to trigger the [name=value] case and instead it should
			# do [name] since [name=None] or [name=] are not exactly useful for the user.
			should_print = param.default if isinstance(param.default, str) else param.default is not None
			if should_print:
				result.append('[%s=%s]' % (name, param.default))
			else:
				result.append('[%s]' % name)
		elif param.kind == param.VAR_POSITIONAL:
			result.append('[%s...]' % name)
		else:
			result.append('<%s>' % name)

	return ' '.join(result)


class EmbedHelp:
	per_page = 8
	ignore_cogs = ('Verify', 'Roles', 'Help')

	def __init__(self, ctx):
		self.ctx = ctx
		self.bot = ctx.bot
		self.pages = []
		self.embed = discord.Embed()
		self.index = 0

	def add_page(self, cog_name, cog_desc, cmds):
		'''Will split into several pages to accomodate the per_page limit.'''

		for cmnds in [cmds[i:i + self.per_page] for i in range(0, len(cmds), self.per_page)]:
			self.pages.append(dict(cog_name=cog_name, cog_desc=cog_desc, commands=cmnds))

	def add_command(self, cmd_list, command, brief=True):
		if not command.hidden:
			hlp = command.brief or command.help
			if not command.hidden:
				cmd_list.append((get_signature(command), hlp.split('\n')[0] if brief else hlp))

	@property
	def use_buttons(self):
		return len(self.pages) > 1

	@classmethod
	def from_bot(cls, ctx):
		self = cls(ctx)

		bot = self.bot
		cogs = list(filter(lambda cog: cog.__class__.__name__ not in cls.ignore_cogs, bot.cogs.values()))

		for index, cog in enumerate(cogs):
			cog_name = cog.__class__.__name__
			cog_desc = cog.__doc__

			cmds = []

			for command_or_group in sorted(bot.get_cog_commands(cog_name), key=lambda cmd: cmd.name):
				if command_or_group.hidden:
					continue

				self.add_command(cmds, command_or_group)

				if isinstance(command_or_group, commands.Group):
					for command in sorted(command_or_group.commands, key=lambda cmd: cmd.name):
						self.add_command(cmds, command)

			self.add_page(cog_name, cog_desc, cmds)

		return self

	@classmethod
	def from_command(cls, ctx, command):
		self = cls(ctx)

		cmds = []

		cog_name = command.cog_name

		self.add_command(cmds, command, brief=False)

		if isinstance(command, commands.Group):
			for cmd in sorted(command.commands, key=lambda cmd: cmd.name):
				self.add_command(cmds, cmd, brief=False)

		self.add_page(cog_name, None, cmds)

		return self

	@classmethod
	def from_cog(cls, ctx, cog):
		self = cls(ctx)

		cmds = []

		cog_name = cog.__class__.__name__

		for cmd in sorted(self.bot.get_cog_commands(cog_name), key=lambda cd: cd.name):
			self.add_command(cmds, cmd, brief=False)

			if isinstance(cmd, commands.Group):
				for gcmd in sorted(cmd.commands, key=lambda cd: cd.name):
					self.add_command(cmds, gcmd, brief=False)

		self.add_page(cog_name, cog.__doc__, cmds)

		return self

	async def get_embed(self):
		page = self.pages[self.index]

		self.embed.clear_fields()

		author = page['cog_name'] + ' Commands'

		if isinstance(self.bot.get_cog(page['cog_name']), TogglableCogMixin):
			used = await self.bot.uses_module(self.ctx, page['cog_name'])
			author += f" ({'enabled' if used else 'disabled'})"

		self.embed.set_author(name=author, icon_url=self.bot.user.avatar_url)
		self.embed.description = page['cog_desc']

		for name, value in page['commands']:
			self.embed.add_field(name=name, value=value, inline=False)

		if len(self.pages) > 1:
			self.embed.set_footer(text=f'Page {self.index + 1}/{len(self.pages)}')
		else:
			self.embed.set_footer()

		return self.embed

	def help(self):
		self.embed.clear_fields()
		self.embed.set_footer()
		self.embed.set_author(name='How do I use the bot?', icon_url=self.bot.user.avatar_url)

		self.embed.description = (
			'Invoke a command by sending the prefix followed by a command name.\n\n'
			'For example, the command signature `define <query>` can be invoked by doing `.define bot`\n\n'
			'The different argument brackets mean:'
		)

		self.embed.add_field(name='<argument>', value='means the argument is required.', inline=False)
		self.embed.add_field(name='[argument]', value='means the argument is optional.', inline=False)

		return self.embed

	async def next(self):
		if len(self.pages) - 1 != self.index:
			self.index += 1
		return await self.get_embed()

	async def prev(self):
		if self.index != 0:
			self.index -= 1
		return await self.get_embed()

	async def first(self):
		self.index = 0
		return await self.get_embed()

	async def last(self):
		self.index = len(self.pages) - 1
		return await self.get_embed()


class Help:
	emojis = (FIRST_EMOJI, PREV_EMOJI, NEXT_EMOJI, LAST_EMOJI, STOP_EMOJI, HELP_EMOJI)

	def __init__(self, bot):
		self.bot = bot

	@commands.command(hidden=True)
	@commands.bot_has_permissions(add_reactions=True)
	async def help(self, ctx, *, command: str = None):
		'''Help command.'''

		if command is not None:
			command = command.lower()
			cog = None
			for cog_name, current_cog in ctx.bot.cogs.items():
				if cog_name.lower() == command and cog_name not in EmbedHelp.ignore_cogs:
					cog = current_cog
					break
			if cog is not None:
				eh = EmbedHelp.from_cog(ctx, cog)
			else:
				command = ctx.bot.get_command(command)
				if command is None or command.cog_name in EmbedHelp.ignore_cogs:
					raise commands.CommandError('Couldn\'t find command/cog.')
				eh = EmbedHelp.from_command(ctx, command)
		else:
			eh = EmbedHelp.from_bot(ctx)

		embed = await eh.get_embed()
		msg = await ctx.send(embed=embed)

		def pred(reaction, user):
			return reaction.message.id == msg.id and user != self.bot.user

		if eh.use_buttons:
			if len(eh.pages) < 3:
				emojis = filter(lambda e: e not in (FIRST_EMOJI, LAST_EMOJI), self.emojis)
			else:
				emojis = self.emojis

			for emoji in emojis:
				await msg.add_reaction(emoji)

		while True:
			try:
				reaction, user = await self.bot.wait_for('reaction_add', check=pred, timeout=120.0)
			except asyncio.TimeoutError:
				break
			else:
				if reaction.emoji == STOP_EMOJI:
					await msg.delete()
					return

				await msg.remove_reaction(reaction.emoji, user)

				if user != ctx.author:
					continue

				if reaction.emoji == NEXT_EMOJI:
					e = await eh.next()
				elif reaction.emoji == PREV_EMOJI:
					e = await eh.prev()
				elif reaction.emoji == FIRST_EMOJI:
					e = await eh.first()
				elif reaction.emoji == LAST_EMOJI:
					e = await eh.last()
				elif reaction.emoji == HELP_EMOJI:
					await msg.edit(embed=eh.help())
					continue
				else:
					continue

				await msg.edit(embed=e)
				await msg.remove_reaction(reaction.emoji, user)

		try:
			await msg.clear_reactions()
		except discord.NotFound:
			pass


def setup(bot):
	bot.add_cog(Help(bot))
