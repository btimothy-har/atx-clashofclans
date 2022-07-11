from redbot.core import Config, commands, bank
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number, humanize_timedelta, pagify
from copy import deepcopy
from numerize import numerize
from .coc_resources import Clash_APIError, Clash_ClassError, Clash_NotMember, StatTooHigh, Clan, Player, PlayerVerify, Member, challengePass, Challenge, getTroops, getFile, getServerID, clashJsonLock, clashapi_player, clashapi_clan, clashapi_pverify, clashapi_leagueinfo, clashapi_cwl, getMaxTroops, troops
from discord.utils import get
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
from tabulate import tabulate
import time
import asyncio
import discord
import requests
import json
import datetime
import pytz
import random
import math

#shop
from shop.shop import Shop, ShopManager

th_emotes = {
    1:"<:TH7:825570842616397884>",
    2:"<:TH7:825570842616397884>",
    3:"<:TH7:825570842616397884>",
    4:"<:TH7:825570842616397884>",
    5:"<:TH7:825570842616397884>",
    6:"<:TH7:825570842616397884>",
    7:"<:TH7:825570842616397884>",
    8:"<:TH8:825570963533463612>",
    9:"<:TH9:825571026326781963>",
    10:"<:TH10:825571431131119666>",
    11:"<:TH11:825571502643871754>",
    12:"<:TH12:825571612325052427>",
    13:"<:TH13:825662803901415444>",
    14:"<:TH14:831443497994289153>"
    }

hero_emotes = {
    "BK":"<:BarbarianKing:825723990088613899>",
    "AQ":"<:ArcherQueen:825724358512607232>",
    "GW":"<:GrandWarden:825724495896510464>",
    "RC":"<:RoyalChampion:825724608987529226>",
    "BM":"<:BH_HeroStrength:827731911849279507>"
}
clan_roles = {
    "leader":"Leader",
    "coLeader":"Co-Leader",
    "admin":"Elder",
    "member":"Member",
    "None":None
}
war_result = {
    "win":"<:Win:828100053079687188> Won",
    "lose":"<:Lost:828099964076556319> Lost",
    "tie":"<:Clan:825654825509322752> Tied"
}
war_description = {
    "cwl":"<:ClanWarLeagues:825752759948279848>",
    "classic":"<:ClanWars:825753092230086708>"
}
elder_status = {
    "win":"<:Win:828100053079687188>",
    "lose":"<:Lost:828099964076556319>",
    "tie":"<:Clan:825654825509322752>"
}
capitalGoldElderReq = {
    14: 35000,
    13: 30000,
    12: 20000
    }
traDict = {'farm': 'The Farmer Track', 'war': 'The Warpath'}
rewDict = {'challengePoints': 'Challenge Pass Points', 'atc': '<:logo_ATC:971050471110377472>'}

async def clash_embed(ctx, title=None, message=None, url=None, show_author=True, color=None):
    if not title:
        title = ""
    if not message:
        message = ""
    if color == "success":
        color = 0x00FF00
    elif color == "fail":
        color = 0xFF0000
    else:
        color = await ctx.embed_color()
    if url:
        embed = discord.Embed(title=title,url=url,description=message,color=color)
    else:
        embed = discord.Embed(title=title,description=message,color=color)
    if show_author:
        embed.set_author(name=f"{ctx.author.display_name}#{ctx.author.discriminator}",icon_url=ctx.author.avatar_url)
    embed.set_footer(text="Ataraxy Clash of Clans",icon_url="https://i.imgur.com/xXjjWke.png")
    return embed

async def cp_accountselect(self,ctx):
    linked_accounts = await self.config.user(ctx.author).players()

    if len(linked_accounts)==0:
        embed = await clash_embed(
            ctx=ctx,
            title="No accounts available.",
            message="Link your Clash of Clans account using `;myaccount link` to be able to participate in the Ataraxy Challenge Pass. You need to be a member of our Clan and at least Townhall 9 or above.",
            color="fail")
        return await ctx.send(embed=embed)

    user_accounts = []
    for account in linked_accounts:
        try:
            account = Member(ctx,account)
        except Clash_APIError as err:
            ctx.command.reset_cooldown(ctx)
            await clashapi_err(self,ctx,err,account)
            return []
        except:
            ctx.command.reset_cooldown(ctx)
            await clashdata_err(self,ctx)
            return []
        else:
            if account.atxMemberStatus == 'member' and account.homeVillage['townHall']['thLevel'] >= 9:
                user_accounts.append(account)

    user_accounts.sort(key=lambda x:(x.homeVillage['townHall']['thLevel']),reverse=True)

    if len(user_accounts)==0:
        embed = await clash_embed(
            ctx=ctx,
            title="No eligible accounts.",
            message="You have no accounts eligible for the Ataraxy Challenge Pass. To be eligible, you need to be a member of our Clan and at least Townhall 9 or above.",
            color="fail")
        await ctx.send(embed=embed)
        return []
    else:
        return user_accounts

async def clashapi_err(self,ctx,error,tag=None):
    err_msg = error.error_description
    if tag and error.error_code == 404:
        err_msg += f"\n\nTag provided: `{tag}`"
    apierr_embed = await clash_embed(ctx=ctx,message=f"{err_msg}",color="fail")
    await ctx.send(embed=apierr_embed)

async def clashdata_err(self,ctx):
    dataerr_embed = await clash_embed(ctx=ctx,message=f"Oops! My systems seem to be a little busy right now. Please try again in a few minutes.",color="fail")
    await ctx.send(embed=dataerr_embed)

class ClashOfClans(commands.Cog):
    """The Ataraxy Clash Family is a group of Clans bringing a unique community experience to Clash of Clans. While made up of separate clans, we share activity, resources, and a supportive community."""
    def __init__(self):
        self.config = Config.get_conf(self, identifier=828462461169696778,force_registration=True)
        defaults_global = {
            "clanServerID": 0,
            "clanChannelID": 0,
            "clans": [],
            "CGstatus":False,
            "CGseries":"",
            "CGTHreward":[],
            "CWLregistration":False
            }
        defaults_user = {
            "players": []
            }       
        self.config.register_global(**defaults_global)
        self.config.register_user(**defaults_user)    

    @commands.group(name="cocadmin")
    async def cocadmin(self,ctx):
        """Admin settings """

    @cocadmin.command()
    @commands.is_owner()
    async def resetglobal(self,ctx):
        """Reset global variables to default. Does not remove clans."""

        await self.config.clanServerID.set(0)
        await self.config.clanChannelID.set(0)
        await self.config.CGstatus.set(False)
        await self.config.CGseries.set('')
        await self.config.CGTHreward.set([])
        await self.config.CWLregistration.set(False)

        embed = await clash_embed(ctx=ctx,message=f"Global variables reset to default.")
        await ctx.send(embed=embed)

    @cocadmin.command()
    @commands.is_owner()
    async def setserver(self,ctx,serverID=0):
        """Set the Clan Server ID"""

        await self.config.clanServerID.set(serverID)
        embed = await clash_embed(ctx=ctx,message=f"Server ID set to {serverID}")
        await ctx.send(embed=embed)        

    @cocadmin.command()
    @commands.is_owner()
    async def setannouncement(self,ctx,channelID=0):
        """Set the Clan Server ID"""

        await self.config.clanChannelID.set(channelID)
        embed = await clash_embed(ctx=ctx,message=f"Announcement Channel ID set to {channelID}")
        await ctx.send(embed=embed)

    @cocadmin.command()
    @commands.is_owner()
    async def clanset(self,ctx,clan_tag=None):
        """Add/remove clans to be included as part of the Ataraxy family."""        
        registered_clans = await self.config.clans()

        if clan_tag==None:
            if len(registered_clans) == 0:
                embed = await clash_embed(ctx=ctx,message=f"There are no clans registered.")
                return await ctx.send(embed=embed)
            else:
                embed = await clash_embed(ctx=ctx,message=f"The following clans are currently registered. To add/remove a clan, specify the tag.")
                for clan in registered_clans:
                    try:                    
                        clan = Clan(ctx,clan)
                    except:
                        await clashdata_err(self,ctx)
                    else:
                        embed.add_field(
                            name=f"**{clan.clan} ({clan.tag})**",
                            value=f"Level: {clan.level}\u3000Location: {clan.locale['location']['name']} / {clan.locale['language']['name']}"+
                                f"\n```{clan.description}```",
                            inline=False)
                return await ctx.send(embed=embed)
        else:
            try:                    
                clan = Clan(ctx,clan_tag)
            except Clash_APIError as err:
                return await clashapi_err(self,ctx,err,clan_tag)
            except:
                return await clashdata_err(self,ctx)
            else:
                if clan.tag in registered_clans:
                    registered_clans.remove(clan.tag)
                    await self.config.clans.set(registered_clans)
                    embed = await clash_embed(
                        ctx=ctx,
                        message=f"The following clan has been removed from Ataraxy Clash of Clans.",color="fail")
                    embed.set_thumbnail(url=clan.badges['medium'])
                    embed.add_field(
                        name=f"**{clan.clan} ({clan.tag})**",
                        value=f"Level: {clan.level}\u3000\u3000Location: {clan.locale.get('location',{}).get('name','Not specified.')} / {clan.locale.get('language',{}).get('name','Not specified.')}"+
                            f"\n```{clan.description}```",
                        inline=False)
                    return await ctx.send(embed=embed)

                elif clan.tag not in registered_clans:
                    registered_clans.append(clan.tag)
                    await self.config.clans.set(registered_clans)

                    embed = await clash_embed(
                        ctx=ctx,
                        message=f"The following clan has been added to Ataraxy Clash of Clans.",color="success")
                    embed.set_thumbnail(url=clan.badges['medium'])
                    embed.add_field(
                        name=f"**{clan.clan} ({clan.tag})**",
                        value=f"Level: {clan.level}\u3000Location: {clan.locale.get('location',{}).get('name','Not specified.')} / {clan.locale.get('language',{}).get('name','Not specified.')}"+
                            f"\n```{clan.description}```",
                        inline=False)
                    return await ctx.send(embed=embed)

    @commands.group(name="myaccount", autohelp=False)
    async def user_account(self,ctx):
        """Shows your Ataraxy Clash profile.
        Use `;myaccount link` to add/remove accounts."""
        if not ctx.invoked_subcommand:
            registered_accounts = await self.config.user(ctx.author).players()

            embed = await clash_embed(
                ctx=ctx,
                message=f"You've linked the below Clash of Clans accounts.\nTo add/remove an account use `;myaccount link`."
                )
            for account in registered_accounts:
                try:                    
                    player = Player(ctx,account)
                except:
                    await clashdata_err(self,ctx)
                else:
                    try:
                        clan_description = f"{player.clan['role']} of **[{player.clan['clan_info']['name']}](https://www.clashofstats.com/clans/{player.clan['clan_info']['tag'].replace('#','')})**"
                    except:
                        clan_description = "No Clan"
                    embed.add_field(
                        name=f"**{player.player}** ({player.tag})",
                        value=f"<:Exp:825654249475932170> {player.exp}\u3000{th_emotes[player.homeVillage['townHall']['thLevel']]} {player.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {clan_description}",
                        inline=False)                    
            return await ctx.send(embed=embed)

    @user_account.command(name="link")
    async def link(self,ctx):
        """Starts the linking process in your DMs."""

        registered_accounts = await self.config.user(ctx.author).players()

        await ctx.send(f"{ctx.author.mention} I will DM you to continue the linking process. Please ensure your DMs are open!")
        await ctx.author.send("Hello! Let's link your Clash of Clans accounts to Ataraxy. To get started, simply send any message.")

        def dm_check(m):
            return m.author == ctx.author and m.guild is None
        try:
            startmsg = await ctx.bot.wait_for("message",timeout=60,check=dm_check)
        except asyncio.TimeoutError:
            return await ctx.author.send("Sorry, you timed out. Restart the process from the Ataraxy server.")

        await ctx.author.send("```What is the Player Tag of the account you'd like to link?```**The image below shows where you can get your tag.**\nhttps://imgur.com/X0PjMya")
        try:
            msg_player_tag = await ctx.bot.wait_for("message",timeout=120,check=dm_check)
        except asyncio.TimeoutError:
            return await ctx.author.send("Sorry, you timed out. Restart the process from the Ataraxy server.")

        await ctx.author.send("```Please provide your in-game API Token.```**The image below shows how to retrieve your API Token.**\nhttps://imgur.com/Q1JwMzK")
        try:
            msg_api_token = await ctx.bot.wait_for("message",timeout=120,check=dm_check)
        except asyncio.TimeoutError:
            return await ctx.author.send("Sorry, you timed out. Restart the process from the Ataraxy server.")

        player_tag = str(msg_player_tag.content)
        api_token = str(msg_api_token.content)

        waitmsg = await ctx.author.send("Verifying...")

        try:
            player = PlayerVerify(ctx,player_tag,api_token)
        except Clash_APIError as err:
            err_msg = error.error_description
            err_msg += f"\n\nTag provided: `{tag}`"
            apierr_embed = await clash_embed(ctx=ctx,message=f"{err_msg}",color="fail")
            return await ctx.author.send(embed=apierr_embed)
        except:
            dataerr_embed = await clash_embed(ctx=ctx,message=f"Oops! My systems seem to be a little busy right now. Please try again in a few minutes.",color="fail")
            return await ctx.author.send(embed=dataerr_embed)
        else:
            if player.verifyStatus != "ok":
                embed = await clash_embed(
                    ctx=ctx,
                    title="Verification Error!",
                    message="An error occured while verifying this player. Please try again with a new API Token.",
                    color="fail")
                await waitmsg.delete()
                return await ctx.author.send(embed=embed)
            else:            
                global_accounts = []
                user_configs = await self.config.all_users()
                for users in user_configs.values():
                    for key,accounts in users.items():
                        global_accounts.extend(accounts)
                try:
                    clan_description = f"{player.clan['role']} of **[{player.clan['clan_info']['name']}](https://www.clashofstats.com/clans/{player.clan['clan_info']['tag'].replace('#','')})**"
                except:
                    clan_description = "No Clan"
                if player.tag in registered_accounts:
                    registered_accounts.remove(player.tag)
                    await self.config.user(ctx.author).players.set(registered_accounts)                    
                    embed = await clash_embed(
                        ctx=ctx,
                        title="Account Removed.",
                        message="The following account has been removed from your profile.",
                        color="success")
                    try:
                        embed.set_thumbnail(url=player.homeVillage['league']['leagueDetails']['iconUrls']['medium'])
                    except:
                        pass                                        
                    embed.add_field(
                        name=f"**{player.player}** ({player.tag})",
                        value=f"<:Exp:825654249475932170> {player.exp}\u3000{th_emotes[player.homeVillage['townHall']['thLevel']]} {player.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {clan_description}",
                        inline=False)
                    await waitmsg.delete()
                    return await ctx.author.send(embed=embed)

                elif player.tag not in registered_accounts:
                    if player.tag in global_accounts:
                        embed = await clash_embed(
                            ctx=ctx,
                            title="Registration Error.",
                            message="This account has been registered by another user.",
                            color="fail")                            
                        try:
                            embed.set_thumbnail(url=player.homeVillage['league']['leagueDetails']['iconUrls']['medium'])
                        except:
                            pass 
                        embed.add_field(
                            name=f"**{player.player}** ({player.tag})",
                            value=f"<:Exp:825654249475932170> {player.exp}\u3000{th_emotes[player.homeVillage['townHall']['thLevel']]} {player.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {clan_description}",
                            inline=False)
                        await waitmsg.delete()
                        return await ctx.author.send(embed=embed)
                    else:
                        registered_accounts.append(player.tag)
                        await self.config.user(ctx.author).players.set(registered_accounts)

                        embed = await clash_embed(
                            ctx=ctx,
                            title="Registration Successful!",
                            message="The following account has been successfully registered to your profile.",
                            color="success")     
                        try:
                            embed.set_thumbnail(url=player.homeVillage['league']['leagueDetails']['iconUrls']['medium'])
                        except:
                            pass 
                        embed.add_field(
                            name=f"**{player.player}** ({player.tag})",
                            value=f"<:Exp:825654249475932170> {player.exp}\u3000{th_emotes[player.homeVillage['townHall']['thLevel']]} {player.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {clan_description}",
                            inline=False)
                        await waitmsg.delete()
                        return await ctx.author.send(embed=embed)   

    @commands.command(name="getbase")
    async def get_base(self, ctx):
        """
        [Members-only] Get a War Base from Blueprint Base Building.
        """
        embedpaged = []
        is_member = False

        for account in await self.config.user(ctx.author).players():
            try:
                player = Member(ctx,account)
            except:
                return await clashdata_err(self,ctx)
            else:
                if player.atxMemberStatus == 'member':
                    is_member = True
        if is_member:
            try:
                with open(getFile('warbases'),"r") as dataFile:
                    warBases = json.load(dataFile)
            except:
                return await clashdata_err(self,ctx)
            base_types = ['TH14 - CWL','TH14 - War','TH14 - Legends','TH13','TH12','TH11','TH10']
            baseSelect = BotMultipleChoice(ctx,base_types,"Select a Base Type.")
            await baseSelect.run()
            if baseSelect.choice==None:
                return await baseSelect.quit(f"{ctx.author.mention}, Selection Stopped.")            
            baseChoice = baseSelect.choice
            await baseSelect.quit()
            thBases = []
            if baseChoice == 'TH14 - CWL':
                thBases = [b for b in warBases if b['Townhall']==14 and b['Type']=='CWL/ESL' and b['Creator']=='']
            if baseChoice == 'TH14 - War':
                thBases = [b for b in warBases if b['Townhall']==14 and b['Type']=='War' and b['Creator']=='']
            if baseChoice == 'TH14 - Legends':
                thBases = [b for b in warBases if b['Townhall']==14 and b['Type']=='Legends' and b['Creator']=='']
            if baseChoice == 'TH13':
                thBases = [b for b in warBases if b['Townhall']==13 and b['Creator']=='']
            if baseChoice == 'TH12':
                thBases = [b for b in warBases if b['Townhall']==12 and b['Creator']=='']
            if baseChoice == 'TH11':
                thBases = [b for b in warBases if b['Townhall']==11 and b['Creator']=='']
            if baseChoice == 'TH10':
                thBases = [b for b in warBases if b['Townhall']==10 and b['Creator']=='']

            if len(thBases) >= 3:
                thBasesSample = random.sample(thBases, 3)
                for base in thBasesSample:
                    base_name = f"**TH{base['Townhall']}** {base['Type']} - {base['Month']}"
                    base_description = ""
                    
                    if base['Creator'] != "":
                        base_description += f"Base by {base['Source']} ({base['Creator']})"
                    else:
                        base_description += f"Base by {base['Source']}"

                    embed = await clash_embed(ctx=ctx,
                        title=base_name,
                        message=base_description,
                        show_author=True)
                    try:
                        embed.set_image(url=base['Image'])
                    except:
                        pass
                    if base['Comments'] != "":
                        embed.add_field(
                            name="**Recommended Trophy Range**",
                            value=f"{base['Comments']}",
                            inline=False)
                    embed.add_field(
                        name="**Recommended Clan Castle**",
                        value=f"{base['CC']}",
                        inline=False)
                    embed.add_field(
                        name="**Base Link**",
                        value=f"{base['URL']}",
                        inline=False)
                    embedpaged.append(embed)
                if len(embedpaged)>1:
                    paginator = BotEmbedPaginator(ctx,embedpaged)
                    return await paginator.run()
                elif len(embedpaged)==1:
                    return await ctx.send(embed=embed)
        else:
            embed = await clash_embed(ctx=ctx,
                message=f"You must be an active Ataraxy Member to use this command. If you are in our in-game clan(s), ensure that your Clash Account is registered with our Ataraxy bot.",
                color="fail"
                )
            return await ctx.send(embed=embed)

    @commands.command(name="player")
    async def player_info(self, ctx, player_tag=None):
        """
        Gets information about a Clash of Clans player. Will display member stats for Ataraxy members.
        If no tag is provided, it will return information on all your linked accounts. Link accounts with `;myaccount link`.
        """
        action_tags = []
        if player_tag==None:
            for account in await self.config.user(ctx.author).players():
                action_tags.append(account)
        else:
            action_tags.append(player_tag)
        if len(action_tags) == 0:
            embed = await clash_embed(ctx=ctx,
                message=f"You need to provide a tag when running this command, or link a Clash of Clans account to your Discord profile.\n\nRun `;myaccount link` to start the linking process.",
                color="fail"
                )
            return await ctx.send(embed=embed)
        else:
            embedpaged = []
            for action_tag in action_tags:                
                try:                    
                    player = Member(ctx,action_tag)
                except Clash_APIError as err:
                    return await clashapi_err(self,ctx,err,action_tag)
                except:
                    return await clashdata_err(self,ctx)
                else:
                    try:
                        if player.atxMemberStatus == 'member':
                            clan_description = f"**[{player.clan['clan_info']['name']}](https://www.clashofstats.com/clans/{player.clan['clan_info']['tag'].replace('#','')})**"
                        else:
                            clan_description = f"{player.clan['role']} of **[{player.clan['clan_info']['name']}](https://www.clashofstats.com/clans/{player.clan['clan_info']['tag'].replace('#','')})**"
                    except:
                        clan_description = "No Clan"

                    memberStatus = ''
                    if player.atxMemberStatus == 'member':
                        memberStatus = f"**<:logo_ATX_circle:975063153798946917>`Member of Ataraxy`**\n"
                    if player.atxRank != 'none':
                        memberStatus = f"\u3000**<:logo_ATX_circle:975063153798946917>`{player.atxRank} of Ataraxy`**\n"

                    embed = await clash_embed(ctx=ctx,
                        title=f"{player.player} ({player.tag})",
                        message=f"{memberStatus}<:Exp:825654249475932170>{player.exp}\u3000<:Clan:825654825509322752> {clan_description}",
                        url=f"https://www.clashofstats.com/players/{player.tag.replace('#','')}",
                        show_author=True)            
                    try:
                        embed.set_thumbnail(url=player.homeVillage['league']['leagueDetails']['iconUrls']['medium'])
                    except:
                        pass
                    barbarianKing = f"{hero_emotes['BK']} {player.homeVillage['heroes']['barbarianKing']}"
                    archerQueen = f"{hero_emotes['AQ']} {player.homeVillage['heroes']['archerQueen']}"
                    grandWarden = f"{hero_emotes['GW']} {player.homeVillage['heroes']['grandWarden']}"
                    royalChampion = f"{hero_emotes['RC']} {player.homeVillage['heroes']['royalChampion']}"

                    totalHero = barbarianKing + archerQueen

                    hero_description = ""
                    if player.homeVillage['townHall']['thLevel'] >= 7:
                        hero_description = f"\n**Heroes**\n{barbarianKing}"
                    if player.homeVillage['townHall']['thLevel'] >= 9:
                        hero_description += f"\u3000{archerQueen}"
                    if player.homeVillage['townHall']['thLevel'] >= 11:
                        hero_description += f"\u3000{grandWarden}"
                    if player.homeVillage['townHall']['thLevel'] >= 13:
                        hero_description += f"\u3000{royalChampion}"

                    laboratoryLevels = {'troops':0, 'spells':0}
                    all_troops = player.homeVillage['troops']['elixirTroops'] + player.homeVillage['troops']['darkTroops'] + player.homeVillage['troops']['siegeMachines'] + player.homeVillage['troops']['pets']
                    all_spells = player.homeVillage['spells']['elixirSpells'] + player.homeVillage['spells']['darkSpells']
                
                    for troop in all_troops:
                        laboratoryLevels['troops'] += troop['level']
                    for spell in all_spells:
                        laboratoryLevels['spells'] += spell['level']

                    maxTroops = getMaxTroops(player.homeVillage['townHall']['thLevel'])

                    troopStrength = f"<:TotalTroopStrength:827730290491129856> {laboratoryLevels['troops']}/{maxTroops[0]} ({round((laboratoryLevels['troops']/maxTroops[0])*100)}%)"
                    if player.homeVillage['townHall']['thLevel'] >= 5:
                        troopStrength += f"\u3000<:TotalSpellStrength:827730290294259793> {laboratoryLevels['spells']}/{maxTroops[1]} ({round((laboratoryLevels['spells']/maxTroops[1])*100)}%)"                        
                    if player.homeVillage['townHall']['thLevel'] >= 7:
                        troopStrength += f"\n<:TotalHeroStrength:827730291149635596> {sum(player.homeVillage['heroes'].values())}/{maxTroops[2]} ({round((sum(player.homeVillage['heroes'].values())/maxTroops[2])*100)}%)"
            
                    embed.add_field(
                        name="**Home Village**",
                        value=
                            f"{th_emotes[player.homeVillage['townHall']['thLevel']]} {player.homeVillage['townHall']['discordText']}\u3000<:HomeTrophies:825589905651400704> {player.homeVillage['league']['trophies']} (best: {player.homeVillage['league']['bestTrophies']})"+
                            f"{hero_description}"+
                            "\n**Strength**"+
                            f"\n{troopStrength}"+
                            "\n\u200b",
                        inline=False)

                    if player.builderBase['builderHall']:
                        builderTroopLv = 0
                        for troop in player.builderBase['troops']:
                            builderTroopLv += troop['level']
                        embed.add_field(
                            name="**Builder Base**",
                            value=
                                f"<:BuilderHall:825640713215410176> {player.builderBase['builderHall']}\u3000<:BuilderTrophies:825713625586466816> {player.builderBase['league']['trophies']} (best: {player.builderBase['league']['bestTrophies']})"+
                                "\n**Strength**"+
                                f"\n<:BH_TroopStrength:827732057554812939> {builderTroopLv}\u3000{hero_emotes['BM']} {player.builderBase['heroes']['battleMachine']}"+
                                "\n\u200b",
                            inline=False)

                    if player.atxMemberStatus == "member":
                        if isinstance(player.atxLastUpdated,str):
                            lastseen_tdelta = datetime.datetime.now() - datetime.datetime.strptime(player.atxLastUpdated,"%Y-%m-%d %H:%M:%S.%f")
                            lastseen_seconds = lastseen_tdelta.total_seconds()
                            lastseen_days,lastseen_seconds = divmod(lastseen_seconds,86400)
                            lastseen_hours,lastseen_seconds = divmod(lastseen_seconds,3600)
                            lastseen_minutes,lastseen_seconds = divmod(lastseen_seconds,60)

                        elif isinstance(player.atxLastUpdated,float):
                            cnow = time.time()
                            dtime = cnow - player.atxLastUpdated                            
                            dtime_days,dtime = divmod(dtime,86400)
                            dtime_hours,dtime = divmod(dtime,3600)
                            dtime_minutes,dtime = divmod(dtime,60)

                        lastseen_text = ''

                        if dtime_days > 0:
                            lastseen_text += f"{int(dtime_days)} days "
                        if dtime_hours > 0:
                            lastseen_text += f"{int(dtime_hours)} hours "
                        if dtime_minutes > 0:
                            lastseen_text += f"{int(dtime_minutes)} mins "
                        if lastseen_text == '':
                            lastseen_text = "a few seconds "

                        lootGold = numerize.numerize(player.atxLoot['gold']['season'],1)
                        lootElixir = numerize.numerize(player.atxLoot['elixir']['season'],1)
                        lootDarkElixir = numerize.numerize(player.atxLoot['darkElixir']['season'],1)

                        clanCapitalGold = numerize.numerize(player.atxClanCapital['goldContributed']['season'],1)
                        capitalGoldLooted = numerize.numerize(player.atxClanCapital['goldLooted']['season'],1)

                        for achievement in player.homeVillage['achievements']:
                            if achievement['name'] == "Gold Grab" and achievement['value']>=2000000000:
                                lootGold = "max"                                    
                            if achievement['name'] == "Elixir Escapade" and achievement['value']>=2000000000: 
                                lootElixir = "max"                                    
                            if achievement['name'] == "Heroic Heist" and achievement['value']>=2000000000:
                                lootDarkElixir = "max"

                        warStarsOffense = 0
                        for war in player.atxWarLog:
                            warStarsOffense += war['attackStars']
                        
                        with open(getFile('clangames'),"r") as dataFile:
                            clangames_data = json.load(dataFile)

                        clangames_season = list(clangames_data.keys())
                        clangames_season = clangames_season[-1]
                        cg_pts = 0
                        for cg_participant in clangames_data[clangames_season]:
                            if cg_participant['tag'] == player.tag:
                                cg_pts = cg_participant['games_pts']

                        playerLeague = player.homeVillage['league']['leagueDetails']
                        if player.homeVillage['league']['leagueDetails'] != None:
                            elder_req1 = 'win'
                        else:
                            elder_req1 = 'lose'
                        if cg_pts >= 1500:                
                            elder_req2 = 'win'
                        else:
                            elder_req2 = 'lose' 
                        if warStarsOffense >= 20:
                            elder_req3 = 'win'
                        elif player.atxClanCapital['goldContributed']['season'] >= capitalGoldElderReq.get(player.homeVillage['townHall']['thLevel'],10000):
                            elder_req3 = 'win'
                        elif (player.atxDonations['sent']['season'] + player.atxDonations['received']['season']) >= 3000:
                            elder_req3 = 'win'
                        else:
                            elder_req3 = 'lose'
                        embed.add_field(
                            name=f"**Current Season Stats with Ataraxy**",
                                value=
                                    f":stopwatch: Last updated: {lastseen_text}ago"+
                                    f"\n:calendar: {int(player.atxLastSeen['timer']/86400)} days spent in Ataraxy Clans"+
                                    "\n**Donations**"+
                                    f"\n<:donated:825574412589858886> {player.atxDonations['sent']['season']:,}\u3000<:received:825574507045584916> {player.atxDonations['received']['season']:,}"+
                                    "\n**Loot**"+
                                    f"\n<:gold:825613041198039130> {lootGold}\u3000<:elixir:825612858271596554> {lootElixir}\u3000<:darkelixir:825640568973033502> {lootDarkElixir}"+
                                    "\n**Clan Capital**"+
                                    f"\n<:CapitalGoldContributed:971012592057339954> {clanCapitalGold}\u3000<:CapitalGoldLooted:983374303552753664> {capitalGoldLooted}"+                                    
                                    "\n**War Registration**"+
                                    f"\n<:ClanWars:825753092230086708> {player.atxWar['registrationStatus']}\u3000<:Ataraxy:828126720925499402> Priority: {player.atxWar['warPriority']}"+
                                    "\n**War Performance**"+
                                    f"\n<:TotalWars:827845123596746773> {len(player.atxWarLog)}\u3000<:TotalStars:825756777844178944> {player.atxWar['warStars']+player.atxWar['cwlStars']}\u3000<:MissedHits:825755234412396575> {player.atxWar['missedAttacks']}"+
                                    "\n*Use `;mywarlog` to view your War Log.*"+
                                    "\n\u200b",
                                inline=False)
                        embed.add_field(
                            name=f"**Activity Requirements**",
                                value=
                                    f"You need to satisfy **1** criteria from each of the below categories to stay in our Clans."+
                                    f"\n\u200b\n**{elder_status[elder_req1]} Game Activity**"+
                                    f"\n\u3000- Placed in a Trophy League: **{playerLeague.get('name','No League')}**"+
                                    f"\n**{elder_status[elder_req2]} Clan Games**"+
                                    f"\n\u3000- {clangames_season} Season: **{cg_pts:,}** / 1,500"+
                                    f"\n**{elder_status[elder_req3]} Clan Participation**"+
                                    f"\n\u3000- War Stars: **{warStarsOffense} / 20**"+
                                    f"\n\u3000- Capital Gold: **{clanCapitalGold} / {numerize.numerize(capitalGoldElderReq.get(player.homeVillage['townHall']['thLevel'],10000),1)}**"+
                                    f"\n\u3000- Donations: **{(player.atxDonations['sent']['season']+player.atxDonations['received']['season']):,}** / 3,000",
                                inline=False)                
                    embedpaged.append(embed)        
            
            if len(embedpaged)>1:
                paginator = BotEmbedPaginator(ctx,embedpaged)
                await paginator.run()
            elif len(embedpaged)==1:
                await ctx.send(embed=embed)

    @commands.group(name="war")
    async def war(self,ctx):
        """Clan War/War League related commands."""

    @war.command(name="playerlog")
    async def player_warlog(self, ctx, player_tag=None):
        """[Members-only] Displays your Ataraxy War Log for your accounts."""

        action_tags = []
        if player_tag==None:
            for account in await self.config.user(ctx.author).players():
                action_tags.append(account)
        else:
            action_tags.append(player_tag)
        
        if len(action_tags) == 0:
            embed = await clash_embed(ctx=ctx,
                message=f"You need to link a Clash of Clans account to your Discord profile to use this command.\n\nRun `;myaccount link` to start the linking process.",
                color="fail"
                )
            return await ctx.send(embed=embed)
        else:
            embedpaged = []
            for action_tag in action_tags:                
                try:                    
                    player = Member(ctx,action_tag)
                except Clash_APIError as err:
                    return await clashapi_err(self,ctx,err,action_tag)
                except:
                    return await clashdata_err(self,ctx)
                else:                 
                    if player.atxMemberStatus=="member":
                        embed = await clash_embed(ctx=ctx,
                            title=f"{player.player} ({player.tag})",
                            message=f"\n\u200b\u3000<:TotalWars:827845123596746773> {len(player.atxWarLog)}\u3000<:TotalStars:825756777844178944> {player.atxWar['warStars']+player.atxWar['cwlStars']}\u3000<:MissedHits:825755234412396575> {player.atxWar['missedAttacks']}\n\u200b\u3000<:Ataraxy:828126720925499402> Priority: {player.atxWar['warPriority']}",
                            show_author=True)            
                        try:
                            embed.set_thumbnail(url=player.homeVillage['league']['leagueDetails']['iconUrls']['medium'])
                        except:
                            pass

                        for clan in player.atxLastSeen['clans']:
                            clan = Clan(ctx,clan)
                            war_count = 0
                            win_count = 0
                            lost_count = 0
                            draw_count = 0
                            war_log = []
                            for war in player.atxWarLog[::-1]:
                                if clan.tag == war['clan']['tag']:
                                    war_text = {}
                                    if war['result']=="win":
                                        win_count+=1
                                    elif war['result']=="lose":
                                        lost_count+=1
                                    else:
                                        draw_count+=1
                                    war_text['title'] = f"> **{war_description[war['warType']]} vs {war['opponent']['name']}**\u3000{war_result[war['result']]}"
                                    war_attacks = f"> \u200b\u3000<:Attack:828103854814003211>\u3000<:TotalStars:825756777844178944> {war['attackStars']}\u3000:fire: {int(war['attackDestruction'])}%\u3000<:MissedHits:825755234412396575> {war['missedAttacks']}"
                                    war_defense = f"\n> \u200b\u3000<:Defense:828103708956819467>\u3000<:TotalStars:825756777844178944> {war['defenseStars']}\u3000:fire: {int(war['defenseDestruction'])}%"
                                    war_text['text'] = war_attacks + war_defense

                                    war_log.append(war_text)

                            if (win_count + lost_count + draw_count) > 0:
                                embed.add_field(
                                    name=f"**__{clan.clan}: War Log__**",
                                    value=f"```Won {win_count}\u3000Lost {lost_count}\u3000Tied {draw_count}```\n> \u200b**Last 5 Wars**",
                                        inline=False)

                                for war in war_log:
                                    war_count += 1
                                    if war_count <= 5:
                                        embed.add_field(
                                            name=war['title'],
                                            value=war['text'],
                                            inline=False)
                                        
                        embedpaged.append(embed)
            
            if len(embedpaged)>1:
                paginator = BotEmbedPaginator(ctx,embedpaged)
                await paginator.run()
            elif len(embedpaged)==1:
                await ctx.send(embed=embed)

    @war.command()
    async def roster(self,ctx):
        """View the current Clan War lineup for our Ataraxy clans."""
        
        cwlStatus = await self.config.CWLregistration()
        registered_clans = await self.config.clans()
        embedpaged = []

        warType = ["Clan War Leagues", "Clan Wars"]

        if cwlStatus:
            warTypeSelect = BotMultipleChoice(ctx,warType,"Select the War Type to retrieve the roster for.")
            await warTypeSelect.run()

            if warTypeSelect.choice==None:
                return await warTypeSelect.quit()
            else:
                warRosterType = warTypeSelect.choice
                await warTypeSelect.quit()                
        else:
            warRosterType = "Clan Wars"

        embed = await clash_embed(
            ctx=ctx,
            message=f"Fetching data... please wait.")
        init_message = await ctx.send(embed=embed)

        if warRosterType == "Clan Wars":
            for clan in registered_clans:
                war_roster = []
                try:
                    clan = Clan(ctx,clan)
                except Clash_APIError as err:
                    await init_message.delete()
                    return await clashapi_err(self,ctx,err,clan)
                except:
                    await init_message.delete()
                    return await clashdata_err(self,ctx)

                for member in clan.members:
                    try:
                        member = Member(ctx,member['tag'])
                    except Clash_APIError as err:
                        await init_message.delete()
                        return await clashapi_err(self,ctx,err,member['tag'])
                    except:
                        await init_message.delete()
                        return await clashdata_err(self,ctx)
                    if member.atxWar['registrationStatus'] == 'Yes' and member.homeVillage['league']['leagueDetails'] != None and member.atxWar['missedAttacks'] < 6:
                        war_roster.append(member)
            
                #sort by war priority
                war_roster.sort(key=lambda x:(x.atxWar['warPriority'],x.homeVillage['townHall']['thLevel'],(x.atxDonations['sent']['season']+x.atxDonations['received']['season'])),reverse=True)

                #determine eligible war size, capped at 15
                war_size = min(len(war_roster) - (len(war_roster) % 5),50)

                embed = await clash_embed(
                    ctx=ctx,
                    title=f"War Roster for {clan.clan} ({clan.tag})",
                    message=f"Current War Size: {war_size}\nCurrently registered: {len(war_roster)}")

                embed.set_thumbnail(url=clan.badges['medium'])

                if war_size == 0:
                    embed.add_field(
                        name=f"Insufficient participants!",
                        value=f"We require a minimum of 5 participants to host a Clan War.",
                        inline=False)
                else:
                    roster_count = 0
                    for participant in war_roster:
                        if roster_count < war_size:
                            roster_count += 1
                            embed.add_field(
                                name=f"{roster_count}\u3000{participant.player} ({participant.tag})",
                                value=f"{th_emotes[int(participant.homeVillage['townHall']['thLevel'])]} {participant.homeVillage['townHall']['thLevel']}\u3000<:Ataraxy:828126720925499402> Priority: {participant.atxWar['warPriority']}",
                                inline=False)
                        else:
                            break            
                embedpaged.append(embed)

        if warRosterType == "Clan War Leagues":
            war_size = 15
            try:
                with open(getFile('cwlroster'),"r") as dataFile:
                    cwlData = json.load(dataFile)
            except:
                return await clashdata_err(self,ctx)

            for clan in registered_clans:
                try:
                    clan = Clan(ctx,clan)
                except Clash_APIError as err:
                    await init_message.delete()
                    return await clashapi_err(self,ctx,err,clan)
                except:
                    await init_message.delete()
                    return await clashdata_err(self,ctx)

                clanRoster = []
                roster = cwlData[clan.tag]

                for tag, data in roster.items():
                    clanRoster.append(data)

                clanRoster.sort(key=lambda x:(x['priority'],x['townHall'],x['heroLevels']),reverse=True)

                embed = await clash_embed(
                    ctx=ctx,
                    title=f"CWL Roster for {clan.clan} ({clan.tag})",
                    message=f"Current War Size: {war_size}\nCurrently registered: {len(clanRoster)}")

                embed.set_thumbnail(url=clan.badges['medium'])

                roster_count = 0                
                for participant in clanRoster:
                    if roster_count < war_size:
                        roster_count += 1
                        embed.add_field(
                            name=f"{roster_count}\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} {participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)
                    else:
                        embed.add_field(
                            name=f"**SUB**\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} {participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)      

                embedpaged.append(embed)

        await init_message.delete()
        if len(embedpaged)>1:
            paginator = BotEmbedPaginator(ctx,embedpaged)
            return await paginator.run()
        elif len(embedpaged)==1:
            return await ctx.send(embed=embedpaged[0])

    @war.command(name="cwlstart")
    @commands.is_owner()
    async def cwl_start(self,ctx):
        """Activates CWL Period."""

        clanServer_ID = await self.config.clanServerID()
        clanServer = ctx.bot.get_guild(clanServer_ID)
        clanChannel_ID = await self.config.clanChannelID()
        clanAnnouncementChannel = discord.utils.get(clanServer.channels,id=clanChannel_ID)
        registered_clans = await self.config.clans()
        cwlStatus = await self.config.CWLregistration()
        
        if ctx.guild.id != clanServer.id:
            return await ctx.send(f"{ctx.author.mention} please use this command only in Ataraxy server.")
        if cwlStatus:
            return await ctx.send(f"{ctx.author.mention} CWL is already open. Use `cg close` to end the existing CWL registration.")

        try:
            with open(getFile('cwlroster'),"r") as dataFile:
                cwlData = json.load(dataFile)
        except FileNotFoundError:
            pass
        finally:
            cwlData = {}
            with open(getFile('cwlroster'),"w") as dataFile:
                json.dump(cwlData,dataFile,indent=2)

        await self.config.CWLregistration.set(True)
        await ctx.send(f"{ctx.author.mention} CWL is now open.")       

        embed = await clash_embed(
            ctx=ctx,
            title=f":trophy: **CLAN WAR LEAGUES** :trophy:",
            message=f"The next Clan War Leagues are starting soon! \n\n**If you want to participate, do be sure to pay attention to the below instructions.**\n\u200b",
            show_author=False)

        embed.set_image(url="https://i.imgur.com/RpEB4I0.jpg")

        embed.add_field(name=":newspaper2: — **OPTING IN FOR CWL**",
            value=f"1) Join the appropriate clan based on your Townhall level:"+
                f"\n> - #CRYPVGQ0 SoulTakers: TH13, TH14"+
                f"\n> - #2PCRPUPCY Ataraxy: TH12 and below"+
                f"\n\u200b\n\u200b"+
                f"2) Set your in-game War Option to **IN**."+
                f"\n\u200b\n\u200b"+
                f"*Please also ensure that you are placed in a trophy league in-game to be included in CWL.*\n\u200b",
                inline=False
                )
        embed.add_field(name=":black_nib: — **CWL ROSTERING**",
            value=f"- CWL rosters will be finalized when CWL opens in-game. You may check the current roster with `;war roster`.\n\u200b"+
                f"- Rosters will be ordered in the following order:\n"+
                f"> 1) CWL Priority (see below)\n"+
                f"> 2) Townhall Level\n"+
                f"> 3) Total Hero Levels\n\u200b",
                inline=False
                )
        embed.add_field(name=":crossed_swords: — **CWL PRIORITY SYSTEM**",
            value=f"CWL Priority is separate from regular War priority. CWL Priority will be used to determine bonuses and participation:"+
                f"\n\u200b- Participate in War: `-3`"+
                f"\n\u200b- Use your Attack: `+1`"+
                f"\n\u200b- Earn 2 Stars (offense): `+1`"+
                f"\n\u200b- Earn 3 Stars (offense): `+2`"+
                f"\n\u200b\n__An additional bonus/penalty will be applied for hits up and/or down, by Townhall Level:__"+
                f"\n\u200bBonus/Penalty: `(opponent TH level) - (your TH level)` "+
                f"\n\u200b*only applies for hits above 2 stars. ",
                inline=False
                )
        embed.add_field(name="<:Gem:834064925243998279> — **REWARDS**",
            value=f"Bonus CWL Medals will be awarded in accordance to CWL priority.",
            inline=False
            )   

        return await clanAnnouncementChannel.send(embed=embed)

    @war.command(name="cwlend")
    @commands.is_owner()
    async def cwl_end(self,ctx):

        await self.config.CWLregistration.set(False)
        return await ctx.send(content=f"CWL is now closed.")

    @commands.group(name="cg")
    async def cg(self,ctx):
        """Commands to manage Clan Games."""

    @cg.command(name="start")
    @commands.is_owner()
    async def cg_start(self,ctx,th_select=1):

        clanServer_ID = await self.config.clanServerID()
        clanServer = ctx.bot.get_guild(clanServer_ID)

        clanChannel_ID = await self.config.clanChannelID()
        clanAnnouncementChannel = discord.utils.get(clanServer.channels,id=clanChannel_ID)

        registered_clans = await self.config.clans()
        cg_status = await self.config.CGstatus()

        if ctx.guild.id != clanServer_ID:
            return await ctx.send(f"{ctx.author.mention} please use this command only in Ataraxy server.")
        if cg_status:
            return await ctx.send(f"{ctx.author.mention} Clan Games are already active. Use `cg close` to end the existing Clan Games.")

        try:
            clangames_data = json.load(open(getFile('clangames'),"r"))
        except:
            clangames_data = {}

        clangames_series = datetime.datetime.today().strftime("%Y-%m")
        clangames_series_pt = datetime.datetime.today().strftime("%B %Y")
        clangames_data[clangames_series] = {}
        th_reward = [9,10,11,12]

        player_data = []

        for clan in registered_clans:            
            clan = Clan(ctx,clan)
            for member in clan.members:
                member = Member(ctx,member['tag'])
                member_data = {}
                cg_init_pts = 0

                for achievement in member.homeVillage['achievements']:
                    if achievement['name'] == "Games Champion":
                        cg_init_pts = achievement['value']

                member_data['tag'] = member.tag
                member_data['player'] = member.player
                member_data['townhall'] = member.homeVillage['townHall']['thLevel']
                member_data['status'] = 'participant'
                member_data['games_pts'] = 0
                member_data['games_pos'] = 0
                member_data['init_pts'] = cg_init_pts

                player_data.append(member_data)

        clangames_data[clangames_series] = player_data

        with open(getFile('clangames'),"w") as dataFile:
            json.dump(clangames_data,dataFile,indent=2)

        await self.config.CGstatus.set(True)
        await self.config.CGseries.set(clangames_series)

        th_reward_selected = random.sample(th_reward,int(th_select))
        th_reward_selected.sort()
        th_reward_message = ''
        await self.config.CGTHreward.set(th_reward_selected)

        for th in th_reward_selected:
            th_text = f"{th_emotes[th]} TH{th}"
            th_reward_message += f"{th_text}\u3000\u3000"

        embed = await clash_embed(
            ctx=ctx,
            title=f"<:ClanGames:834063648494190602> **CLAN GAMES: {clangames_series_pt}** <:ClanGames:834063648494190602>",
            message=f"It's that time again - the next Clan Games are about to start. Pull up your sleeves and get ready to rumble!\n\u200b",
            show_author=False)

        embed.set_image(url="https://i.imgur.com/9FU4sx5.jpg")

        embed.add_field(name="<:Gem:834064925243998279> — **REWARDS**",
            value=f"In addition to the in-game rewards, Ataraxy members stand to win:"+
                f"\n> - First **10** players who reach 4,000 points will receive **2000 <:logo_ATC:971050471110377472> each**."+
                f"\n> \u200b\n> - First player from the below TH levels to reach 4,000 points will receive a **Gold Pass (USD5 Gift Card) each**.\n> \u3000\u3000**{th_reward_message}**\n\u200b",
                inline=False
                )
        embed.add_field(name=":newspaper2: — **RULES & REGULATIONS**",
            value=f"> 1) Rewards are shared across both our clans. You may participate in any of our clans."+
                f"\n> \u200b\n> 2) Both clans must reach __maxed__ tier to qualify for rewards - help each other!"+
                f"\n> \u200b\n> 3) Only players in our in-game clans __as of__ this announcement are eligible for Rewards. You will be __disqualified__ if you leave our clans at any point during the games.\n\u200b",
                inline=False
                )
        embed.add_field(name="<:WarPriority:828126720925499402> — **TERMS & CONDITIONS**",
            value=f"> 1) Your Clash of Clans account has to be linked to our <@828462461169696778> bot to be eligible for Rewards. Refer to <#803655289034375178> for details."+
                f"\n> \u200b\n> 2) In the event of ineligibility, Gold Pass rewards will be bumped to the next eligible winner. ATC rewards __will not__ be bumped."+
                f"\n> \u200b\n> 3) ATC rewards can be won multiple times from multiple Clash accounts. All other rewards can only be won __once__ per Discord user."+
                f"\n> \u200b\n> 4) For purposes of Gold Pass rewards, your Townhall level is taken __as of__ this announcement.",
                inline=False
                )
        embed.add_field(name="\u200b",
            value=f"**All the best comrades!** You can check the Clan Games leaderboard at any time using `;cg lb` in <#803655289034375178>.\n\nFor any enquiries, please ping <@644530507505336330>.",
                inline=False
                )
        await clanAnnouncementChannel.send(embed=embed)

    @cg.command(name="end")
    @commands.is_owner()
    async def cg_end(self,ctx,dist_result=True):

        gp_shop = "Admin Store"
        gp_item = "[R] COC Gold Pass (USD5 Gift Card)"

        shopcog = ctx.bot.get_cog("Shop")
        shopcog_instance = await shopcog.get_instance(ctx, settings=True)
        all_shops = await shopcog_instance.Shops.all()
        gp_itemdata = deepcopy(all_shops[gp_shop]["Items"][gp_item])
    
        clanServer_ID = await self.config.clanServerID()
        clanServer = ctx.bot.get_guild(clanServer_ID)

        clanChannel_ID = await self.config.clanChannelID()
        clanAnnouncementChannel = discord.utils.get(clanServer.channels,id=clanChannel_ID)

        if ctx.guild.id != clanServer_ID:
            return await ctx.send(f"{ctx.author.mention} please use this command only in Ataraxy server.")

        clangames_data = json.load(open(getFile('clangames'),"r"))
        registered_accounts = await self.config.all_users()
        registered_clans = await self.config.clans()
        clangames_status = await self.config.CGstatus()
        clangames_threward = await self.config.CGTHreward()
        clangames_series = await self.config.CGseries()
        clangames_series_pt = datetime.datetime.strptime(f"{clangames_series}-01","%Y-%m-%d").strftime("%B %Y")
        clangames_atc_reward = 2000

        if clangames_status == False:
            return await ctx.send(f"{ctx.author.mention} clan games isn't active!")

        if dist_result:
            embed = await clash_embed(
                ctx=ctx,
                title=f"<:ClanGames:834063648494190602> **CLAN GAMES RESULTS: {clangames_series_pt}** <:ClanGames:834063648494190602>",
                message="Thank you to everyone who participated in Clan Games! Without further delay, here are the results...\n\u200b",
                show_author=False)
            embed.set_image(url="https://i.imgur.com/9FU4sx5.jpg")

            final_participants = []
            atc_recipients = []
            gp_recipients = []
            gp_users = []

            for participant in clangames_data[clangames_series]:
                if participant['status'] == 'participant' and participant['games_pos'] > 0:
                    final_participants.append(participant)

            finalists = sorted(final_participants,key=lambda p:(p['games_pos']),reverse=False)

            for finalist in finalists:
                finalist_atc = {}
                finalist_gp = {}
                if finalist['games_pos'] <= 10:
                    finalist_atc['Pos'] = finalist['games_pos']
                    finalist_atc['TH'] = finalist['townhall']
                    finalist_atc['Player'] = finalist['player']
                    finalist_atc['Discord'] = "None"
                        
                    for user, account in registered_accounts.items():
                        if finalist['tag'] in list(account.values())[0]:
                            user_a = get(ctx.bot.get_all_members(),id=user)
                            finalist_atc['Discord'] = user_a
                            #remove comment for production
                            await bank.deposit_credits(user_a,clangames_atc_reward)

                    atc_recipients.append(finalist_atc)

                if len(clangames_threward) > 0 and finalist['townhall'] in clangames_threward:
                    #add finalist to gold pass winners
                    for user, account in registered_accounts.items():
                        if finalist['tag'] in list(account.values())[0]:
                            user_b = get(ctx.bot.get_all_members(),id=user)
                            if user_b not in gp_users:
                                clangames_threward.remove(finalist['townhall'])
                                finalist_gp['TH'] = finalist['townhall']
                                finalist_gp['Player'] = finalist['player']
                                finalist_gp['Discord'] = user_b
                                gp_recipients.append(finalist_gp)
                                gp_users.append(user_b)

                                shopcog_user = await shopcog.get_instance(ctx,user=user_b)
                                sm = ShopManager(ctx, None, shopcog_user)
                                await sm.add(gp_item,gp_itemdata,1)

            gp_recipients = sorted(gp_recipients,key=lambda p:(p['TH']),reverse=True)

            embed.add_field(name=f"<:logo_ATC:971050471110377472> — **ATC WINNERS** ({clangames_atc_reward} each)",
                value=f"```{tabulate(atc_recipients,headers='keys')}```"+
                    "\nAll <:logo_ATC:971050471110377472> rewards have been deposited to the respective Discord accounts. You can check your balances in <#654994554076004372>.\n\u200b",
                inline=False
                )
            embed.add_field(name="<:GoldPass:834093287106674698> — **GOLD PASS WINNERS**",
                value=f"```{tabulate(gp_recipients,headers='keys')}```"+
                "\nYour Gift Card will be added to your Discord Inventory for redemption. Check your inventory using `;inventory` in <#654994554076004372>.",
                inline=False
                )
            
            embed.add_field(name="\u200b",
                value=f"Once again, thank you everyone for participating! We hope everyone had fun competing. See you for next month's clan games!",
                inline=False
                )        
        else:
            embed = await clash_embed(
                ctx=ctx,
                title=f"<:ClanGames:834063648494190602> **CLAN GAMES RESULTS: {clangames_series_pt}** <:ClanGames:834063648494190602>",
                message="Unfortunately we didn't reach max tier on both our clans. However, thank you to everyone who participated!",
                show_author=False)
            embed.set_image(url="https://i.imgur.com/9FU4sx5.jpg")

        await self.config.CGstatus.set(False)
        return await clanAnnouncementChannel.send(embed=embed)

    @cg.command(name="leaderboard", aliases=["lb"])
    async def cg_leaderboard(self,ctx):
        
        with open(getFile('clangames'),"r") as dataFile:
            clangames_data = json.load(dataFile)

        clangames_series = await self.config.CGseries()
        #clangames_series = "2022-06"
        clangames_series_pt = datetime.datetime.strptime(f"{clangames_series}-01","%Y-%m-%d").strftime("%B %Y")

        cg_participants = clangames_data[clangames_series]

        cg_participants.sort(key=lambda p:(p['games_pts'],(p['games_pos']*-1),p['townhall']),reverse=True)
        outputTable = []
        
        table_ct = 0
        for participant in cg_participants:
            participant_table = {}
            if participant['status'] == 'participant' and table_ct < 10:
                participant_table['Pos'] = participant['games_pos']
                participant_table['TH'] = participant['townhall']
                participant_table['Player'] = participant['player']
                participant_table['Points'] = participant['games_pts']
                table_ct += 1
                outputTable.append(participant_table)

        embed = await clash_embed(
            ctx=ctx,
            title=f"<:ClanGames:834063648494190602> **ATARAXY CLAN GAMES LEADERBOARD** <:ClanGames:834063648494190602>",
            show_author=True)

        embed.add_field(name=f"{clangames_series_pt} Series",
                    value=f"```{tabulate(outputTable,headers='keys')}```")

        return await ctx.send(embed=embed)

    @commands.group(name="cp")
    async def challengepass(self,ctx):
        """Commands relating to the Ataraxy Challenge Pass."""

    @challengepass.command()
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def mypass(self,ctx):
        """Check your Pass progress and Challenge details."""
        embedpaged = []
        wait_msg = None

        inprogress = 0
        inprogress_summ = "\u200b"
        missed = 0
        missed_summ = "\u200b"
        completed = 0
        completed_summ = "\u200b"
        new = 0
        new_summ = "\u200b"
        notstarted = 0
        notstarted_summ = "\u200b"

        try:
            user_accounts = await cp_accountselect(self,ctx)
        except:
            return None
        if not user_accounts:
            return None

        wait_msg = await ctx.send(f"{ctx.author.mention}, please wait....")

        for account in user_accounts:
            cPass = challengePass(ctx,account)
            newChallenge = None
            currentChallenge = None            

            headerTitle = f"**Ataraxy Challenge Pass: {account.player}** ({account.tag})"

            if not cPass.atxChaTrack:
                headerMessage = (f"You haven't started a Challenge Pass on this account.\nTo get started, use the command `;cp start`.")  

                embed = await clash_embed(
                    ctx=ctx,
                    title=headerTitle,
                    message=headerMessage)
                notstarted += 1
                notstarted_summ += f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}\n"

            if cPass.atxChaTrack == 'war' or cPass.atxChaTrack == 'farm':
                if not cPass.atxChaActiveChall:
                    newChallenge = Challenge(player=account,track=cPass.atxChaTrack,challDict=cPass.atxChaActiveChall,commonStreak=cPass.atxChaCommonStreak,currPoints=cPass.atxChaPoints)
                    cPass.updatePass(newChallenge.challengeToJson())
                elif cPass.atxChaActiveChall:
                    currentChallenge = Challenge(player=account,track=cPass.atxChaTrack,challDict=cPass.atxChaActiveChall,commonStreak=cPass.atxChaCommonStreak,currPoints=cPass.atxChaPoints)
                    currentChallenge.updateChallenge()
                    cPass.updatePass(currentChallenge.challengeToJson())
            
                headerMessage = (f"**Your Pass Track: `{traDict[cPass.atxChaTrack]}`**"+
                                f"\n\u200b\n__Your Season Stats:__"+
                                f"\n> Pass Completion: {numerize.numerize(cPass.atxChaPoints,1)} / 10K"+
                                f"\n> Completed: {cPass.atxChaCompleted}"+
                                f"\n> Missed: {cPass.atxChaMissed}"+
                                f"\n> Trashed: {cPass.atxChaTrashed}\n\u200b")

                if newChallenge and newChallenge.challengeProgress['status'] == 'inProgress':
                    timeRemaining = newChallenge.rTime
                    timeRemaining_days,timeRemaining = divmod(timeRemaining,86400)
                    timeRemaining_hours,timeRemaining = divmod(timeRemaining,3600)
                    timeRemaining_minutes,timeRemaining = divmod(timeRemaining,60)

                    timeRemaining_text = ''
                    if timeRemaining_days > 0:
                        timeRemaining_text += f"{int(timeRemaining_days)} day(s) "
                    if timeRemaining_hours > 0:
                        timeRemaining_text += f"{int(timeRemaining_hours)} hour(s) "
                    if timeRemaining_minutes > 0:
                        timeRemaining_text += f"{int(timeRemaining_minutes)} min(s) "
                    if timeRemaining_text == '':
                        timeRemaining_text = "a few seconds "

                    embed = await clash_embed(
                        ctx=ctx,
                        title=headerTitle,
                        message=headerMessage)

                    embed.add_field(name=f"**>> YOU RECEIVED A NEW CHALLENGE! <<**",
                        value=f"```{newChallenge.challengeDesc}```"+
                            f"\n> Current Progress: {numerize.numerize(newChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(newChallenge.challengeScore,1)}"
                            f"\n> Time Remaining: {timeRemaining_text}"+
                            f"\n> Rewards: {newChallenge.challengeReward['reward']:,} {rewDict[newChallenge.challengeReward['type']]}"+
                            f"\n> Trash Cost: {newChallenge.trashCost:,} <:logo_ATC:971050471110377472>"+
                            f"\n\u200b\nTo trash this challenge, use the command `;cp trash`."+
                            f"\n\u200b\nRemember to run the `;cp mypass` command to update your stats and to complete challenges!\n\u200b",                            
                            inline=False)

                    new += 1
                    new_summ += f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}\n> `{newChallenge.challengeDesc}`\n"      

                if currentChallenge and currentChallenge.challengeProgress['status'] == 'completed':
                    timeRemaining = currentChallenge.rTime
                    timeRemaining_days,timeRemaining = divmod(timeRemaining,86400)
                    timeRemaining_hours,timeRemaining = divmod(timeRemaining,3600)
                    timeRemaining_minutes,timeRemaining = divmod(timeRemaining,60)

                    timeRemaining_text = ''
                    if timeRemaining_days > 0:
                        timeRemaining_text += f"{int(timeRemaining_days)} day(s) "
                    if timeRemaining_hours > 0:
                        timeRemaining_text += f"{int(timeRemaining_hours)} hour(s) "
                    if timeRemaining_minutes > 0:
                        timeRemaining_text += f"{int(timeRemaining_minutes)} min(s) "
                    if timeRemaining_text == '':
                        timeRemaining_text = "a few seconds "

                    embed = await clash_embed(
                        ctx=ctx,
                        title=headerTitle,
                        message=headerMessage,
                        color="success")

                    embed.add_field(name=f"**>> CHALLENGE COMPLETED! <<**",
                        value=f"```{currentChallenge.challengeDesc}```"+
                            f"\n> Current Progress: {numerize.numerize(currentChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(currentChallenge.challengeScore,1)}"
                            f"\n> Time Remaining: {timeRemaining_text}"+
                            f"\n> Rewards: {currentChallenge.challengeReward['reward']:,} {rewDict[currentChallenge.challengeReward['type']]}"+
                            f"\n\u200b\nRewards have been credited.\n*To start a new challenge, run the `;cp mypass` command again.*\n\u200b",
                        inline=False)

                    if currentChallenge.challengeReward['type'] == 'atc':
                        await bank.deposit_credits(ctx.author,currentChallenge.challengeReward['reward'])

                    completed += 1
                    completed_summ += f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}\n> `{currentChallenge.challengeDesc}`\n"

                if currentChallenge and currentChallenge.challengeProgress['status'] == 'missed':
                    embed = await clash_embed(
                        ctx=ctx,
                        title=headerTitle,
                        message=headerMessage,
                        color="fail")

                    embed.add_field(name=f"**>> YOU MISSED A CHALLENGE! <<**",
                        value=f"```{currentChallenge.challengeDesc}```"+
                            f"\n> Current Progress: {numerize.numerize(currentChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(currentChallenge.challengeScore,1)}"
                            f"\n> Time Limit: {currentChallenge.challengeDuration}"+
                            f"\n> Rewards: {currentChallenge.challengeReward['reward']:,} {rewDict[currentChallenge.challengeReward['type']]}"+
                            f"\n\u200b\nThis challenge cannot be continued.\n*To start a new challenge, run the `;cp mypass` command again.*\n\u200b",
                        inline=False)

                    missed += 1
                    missed_summ += f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}\n> `{currentChallenge.challengeDesc}`\n"          

                if currentChallenge and currentChallenge.challengeProgress['status'] == 'inProgress':
                    timeRemaining = currentChallenge.rTime
                    timeRemaining_days,timeRemaining = divmod(timeRemaining,86400)
                    timeRemaining_hours,timeRemaining = divmod(timeRemaining,3600)
                    timeRemaining_minutes,timeRemaining = divmod(timeRemaining,60)

                    timeRemaining_text = ''
                    if timeRemaining_days > 0:
                        timeRemaining_text += f"{int(timeRemaining_days)} day(s) "
                    if timeRemaining_hours > 0:
                        timeRemaining_text += f"{int(timeRemaining_hours)} hour(s) "
                    if timeRemaining_minutes > 0:
                        timeRemaining_text += f"{int(timeRemaining_minutes)} min(s) "
                    if timeRemaining_text == '':
                        timeRemaining_text = "a few seconds "

                    embed = await clash_embed(
                        ctx=ctx,
                        title=headerTitle,
                        message=headerMessage)

                    embed.add_field(name=f"**YOU'RE WORKING ON THIS CHALLENGE...**",
                        value=f"```{currentChallenge.challengeDesc}```"+
                            f"\n> Current Progress: {numerize.numerize(currentChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(currentChallenge.challengeScore,1)}"
                            f"\n> Time Remaining: {timeRemaining_text}"+
                            f"\n> Rewards: {currentChallenge.challengeReward['reward']:,} {rewDict[currentChallenge.challengeReward['type']]}"+
                            f"\n> Trash Cost: {currentChallenge.trashCost:,} <:logo_ATC:971050471110377472>"+
                            f"\n\u200b\nTo trash this challenge, use the command `;cp trash`."+
                            f"\n\u200b\nRemember to run the `;cp mypass` command to update your stats and to complete challenges!\n\u200b",
                        inline=False)

                    inprogress += 1
                    inprogress_summ += f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}\n> `{currentChallenge.challengeDesc}`\n"          

            await cPass.savePass()
            embedpaged.append(embed)

        if wait_msg:
            await wait_msg.delete()
        if len(embedpaged)>1:

            embedpagedsumm = []
            summary_embed = await clash_embed(
                                ctx=ctx,
                                title=f"Your Challenge Pass Summary",
                                message=f"In Progress: {inprogress}\u3000New: {new}\u3000Completed: {completed}\u3000Missed: {missed}\n\u200b\n")

            if new > 0:
                summary_embed.add_field(name=f"**NEW**",value=f"{new_summ}\u200b",inline=False)
            if completed > 0:
                summary_embed.add_field(name=f"**COMPLETED**",value=f"{completed_summ}\u200b",inline=False)
            if missed > 0:
                summary_embed.add_field(name=f"**MISSED**",value=f"{missed_summ}\u200b",inline=False)
            if inprogress > 0:
                summary_embed.add_field(name=f"**IN PROGRESS**",value=f"{inprogress_summ}\u200b",inline=False)
            if notstarted > 0:
                summary_embed.add_field(name=f"**NOT STARTED**",value=f"{notstarted_summ}\u200b",inline=False)
            

            embedpagedsumm.append(summary_embed)
            embedpagedsumm.extend(embedpaged)

            paginator = BotEmbedPaginator(ctx,embedpagedsumm)
            return await paginator.run()
        elif len(embedpaged)==1:
            return await ctx.send(embed=embedpaged[0])

    @challengepass.command()
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def start(self,ctx):
        """Start your Challenge Pass journey by picking a Challenge Track!"""

        eligible_accounts = {}
        completed = False
        missed = False
        wait_msg = None

        user_accounts = await cp_accountselect(self,ctx)
        if not user_accounts:
            return None

        for account in user_accounts:
            cPass = challengePass(ctx,account)

            if not cPass.atxChaTrack:
                eligible_accounts[account.tag] = {
                    "account":account,
                    "pass":cPass,
                    }
        
        if len(eligible_accounts) == 0:
            embed = await clash_embed(
                ctx=ctx,
                message=f"You don't have any accounts to start a Challenge Pass on. You need to be **Townhall 9** or higher to participate in the Challenge Pass.\n\u200b\n*Missing an account? Try adding one with `;myaccount link`.*")
            return await ctx.send(embed=embed)
        elif len(eligible_accounts) == 1:
            aKey = list(eligible_accounts.keys())[0]
            account_text = f"**{eligible_accounts[aKey]['account'].player}** ({eligible_accounts[aKey]['account'].tag})\n{th_emotes[int(eligible_accounts[aKey]['account'].homeVillage['townHall']['thLevel'])]} {eligible_accounts[aKey]['account'].homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {eligible_accounts[aKey]['account'].clan['clan_info']['name']}"
        else:
            select_accounts = []
            account_index = []
            for tag, account in eligible_accounts.items():
                account_text = f"**{account['account'].player}** ({account['account'].tag})\n{th_emotes[int(account['account'].homeVillage['townHall']['thLevel'])]} {account['account'].homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account['account'].clan['clan_info']['name']}"
                account_index.append(tag)
                select_accounts.append(account_text)

            account_selection = BotMultipleChoice(ctx,select_accounts,f"{ctx.author.display_name}, select an account to start your Challenge Pass.")
            await account_selection.run()
            if account_selection.choice == None:
                await account_selection.quit(f"{ctx.author.mention}, request cancelled.")
                return None
            else:
                ind = select_accounts.index(account_selection.choice)
                aKey = account_index[ind]
                account_text = account_selection.choice
                await account_selection.quit()

        start_account = eligible_accounts[aKey]['account']
        start_pass = eligible_accounts[aKey]['pass']

        embed = await clash_embed(
                ctx=ctx,
                message=f"You're picking a Challenge Track for the below account.\n\u200b\n\u200b{account_text}")
        account_msg = await ctx.send(embed=embed)

        trackSelect = ['farm','war']
        trackSelectText = ['**The Farmer Track**','**The Warpath**']
        trackSelection = BotMultipleChoice(ctx,trackSelectText,f"{ctx.author.display_name}, pick a Challenge Track to start your challenge journey!")
        await trackSelection.run()

        if trackSelection.choice==None:
            if wait_msg:
                await wait_msg.delete()
            return await trackSelection.quit(f"{ctx.author.mention}, request cancelled.")
        else:
            start_pass.atxChaTrack = trackSelect[trackSelectText.index(trackSelection.choice)]
            await trackSelection.quit()
            await start_pass.savePass()

            embed = await clash_embed(
                ctx=ctx,
                title=f"**Ataraxy Challenge Pass: {start_account.player}** ({start_account.tag})",
                message=f"You've chosen the **{traDict[start_pass.atxChaTrack]}**!\n\u200b\nRun `;cp mypass` to get your first challenge!")

            return await account_msg.edit(embed=embed)

    @challengepass.command()
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.user)
    async def trash(self,ctx):
        """Trash your current challenge. Only usable with an active pass."""
        
        timestamp = time.time()
        wait_msg = None

        masterDict = {}
        selectionPass = []
        selectionIndex = []
        
        user_accounts = await cp_accountselect(self,ctx)

        if not user_accounts:
            return None

        for account in user_accounts:
            cPass = challengePass(ctx,account)
            if cPass.atxChaTrack and cPass.atxChaActiveChall:
                activeChall = Challenge(player=account,track=cPass.atxChaTrack,challDict=cPass.atxChaActiveChall,commonStreak=cPass.atxChaCommonStreak,currPoints=cPass.atxChaPoints)
                masterDict[account.tag] = {
                    'account':account,
                    'pass':cPass,
                    'challenge':activeChall,
                    }
                pass_text = f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}\n> **Trash Cost: {activeChall.trashCost:,} <:logo_ATC:971050471110377472>**\n> `{activeChall.challengeDesc}`"
                selectionPass.append(pass_text)
                selectionIndex.append(account.tag)
            
        trash_selection = BotMultipleChoice(ctx,selectionPass,f"{ctx.author.display_name}, select the Challenge you'd like to trash.")
        await trash_selection.run()

        if trash_selection.choice==None:
            ctx.command.reset_cooldown(ctx)
            return await trash_selection.quit(f"{ctx.author.mention}, request cancelled.")
        else:
            selectIndex = selectionPass.index(trash_selection.choice)
            userSelection = masterDict[selectionIndex[selectIndex]]
            await trash_selection.quit()
            wait_msg = await ctx.send(f"{ctx.author.mention}, please wait...")

        userAccount = userSelection['account']
        userPass = userSelection['pass']
        userChallenge = userSelection['challenge']

        bankBalance = await bank.get_balance(ctx.author)
        if userChallenge.trashCost > bankBalance:
            embed = await clash_embed(
                ctx=ctx,
                title="Not enough money!",
                message=f"You need {userChallenge.trashCost:,} <:logo_ATC:971050471110377472> to trash this challenge.",
                color="fail")
            return await ctx.send(embed=embed)

        timeRemaining = userChallenge.rTime
        timeRemaining_days,timeRemaining = divmod(timeRemaining,86400)
        timeRemaining_hours,timeRemaining = divmod(timeRemaining,3600)
        timeRemaining_minutes,timeRemaining = divmod(timeRemaining,60)

        timeRemaining_text = ''
        if timeRemaining_days > 0:
            timeRemaining_text += f"{int(timeRemaining_days)} day(s) "
        if timeRemaining_hours > 0:
            timeRemaining_text += f"{int(timeRemaining_hours)} hour(s) "
        if timeRemaining_minutes > 0:
            timeRemaining_text += f"{int(timeRemaining_minutes)} min(s) "
        if timeRemaining_text == '':
            timeRemaining_text = "a few second(s)"

        userChallenge.updateChallenge(trash=True)
        userPass.updatePass(userChallenge.challengeToJson())
        await bank.withdraw_credits(ctx.author, userChallenge.trashCost)
        newBalance = await bank.get_balance(ctx.author)

        embed = await clash_embed(
            ctx=ctx,
            title=f"**Ataraxy Challenge Pass: {userAccount.player}** ({userAccount.tag})",
            message=f"**Your Pass Track: `{traDict[userPass.atxChaTrack]}`**"+
                    f"\n\nYou spent `{userChallenge.trashCost:,}` <:logo_ATC:971050471110377472> to trash the below challenge.\nYou have `{newBalance:,}` <:logo_ATC:971050471110377472> left.",
            color="fail")

        embed.add_field(name=f"**>> CHALLENGE TRASHED! <<**",
            value=f"```{userChallenge.challengeDesc}```"+
                f"\n> Current Progress: {numerize.numerize(userChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(userChallenge.challengeScore,0)}"
                f"\n> Time Remaining: {timeRemaining_text}"+
                f"\n> Rewards: {userChallenge.challengeReward['reward']} {rewDict[userChallenge.challengeReward['type']]}"+
                 f"\n\u200b\nThis challenge can no longer be continued. Run the `;cp mypass` command to receive a new one!\n\u200b",
            inline=False)

        if wait_msg:
            await wait_msg.delete()
        await ctx.send(embed = embed)
        return await userPass.savePass()

    @challengepass.command(name='leaderboard', aliases=['lb'])
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.guild)
    async def cp_leaderboard(self,ctx,season='current'):
        """Check the current leaderboard."""
        registered_clans = await self.config.clans()
        registered_accounts = await self.config.all_users()

        embed = await clash_embed(
            ctx=ctx,
            message=f"Fetching data... please wait.")

        init_message = await ctx.send(embed=embed)

        try:
            with open(getFile('challengepass'),"r") as dataFile:
                cpData = json.load(dataFile)
        except:
            await init_message.delete()
            return await clashdata_err(self,ctx)

        allPasses = []
        for player in list(cpData[season].keys()):
            try:
                member = Member(ctx,player)
            except:
                return await clashdata_err(self,ctx)
            if member.atxMemberStatus=='member':
                cPass = challengePass(ctx,member,season)
                allPasses.append(cPass)

        allPasses.sort(key=lambda x:(x.atxChaPoints),reverse=True)

        farm_lb = []
        farm_lb_position = 0
        war_lb = []
        war_lb_position = 0
        
        for cPass in allPasses:
            if cPass.atxChaTrack == 'farm':
                farm_lb_position += 1
                lb_pass = {
                    'Pos': farm_lb_position,
                    'Player': cPass.player,
                    'Points': f"{cPass.atxChaPoints:,}",
                    'C/M/T': f"{cPass.atxChaCompleted}/{cPass.atxChaMissed}/{cPass.atxChaTrashed}"
                    }
                farm_lb.append(lb_pass)
            if cPass.atxChaTrack == 'war':
                war_lb_position += 1
                lb_pass = {
                    'Pos': war_lb_position,
                    'Player': cPass.player,
                    'Points': f"{cPass.atxChaPoints:,}",
                    'C/M/T': f"{cPass.atxChaCompleted}/{cPass.atxChaMissed}/{cPass.atxChaTrashed}"}
                war_lb.append(lb_pass)

        embed = await clash_embed(
            ctx=ctx,
            title=f"Ataraxy Challenge Pass Leaderboard",
            message=f"*{season.capitalize()} Season* \n`C: Completed / M: Missed / T: Trashed`")

        if len(war_lb) > 0:
            embed.add_field(name=f"**THE WARPATH**",
                value=f"```{tabulate(war_lb,headers='keys')}```",
                inline=False
            )
        else:
            embed.add_field(name=f"**THE WARPATH**",
                value=f"```No players found...```",
                inline=False
            )

        if len(farm_lb) > 0:
            embed.add_field(name="**THE FARMER LIFE**",
                value=f"```{tabulate(farm_lb,headers='keys')}```",
                inline=False
            )
        else:
            embed.add_field(name="**THE FARMER LIFE**",
                value=f"```No players found...```",
                inline=False
            )
        
        return await init_message.edit(embed=embed)
    
    @commands.group(name="clan")
    async def clan_admin(self,ctx):
        """Clan-related functions."""
        
    # @clan_admin.command(name="info",aliases=["joinatx"])
    # async def get_clan_info(self, ctx):
    #     """
    #     Get information about Ataraxy Clans.
    #     """
    #     registered_clans = await self.config.clans()

    #     if len(registered_clans) == 0:
    #         embed = await clash_embed(ctx=ctx,message=f"An error occurred.")
    #         return await ctx.send(embed=embed)

    #     embedpaged = []
    #     embed = await clash_embed(ctx=ctx,
    #                                     message=f"The Ataraxy Clash family is proud to feature the below clans in our family."+
    #                                             f"\nJoin any of the below clans to be an Ataraxy member! Send us a request in-game with the password `atxftw`.")            
    #     for clan in registered_clans:
    #         try:                    
    #             clan = Clan(ctx,clan)
    #         except Clash_APIError as err:
    #             return await clashapi_err(self,ctx,err,clan)
    #         except:
    #             return await clashdata_err(self,ctx)
            
    #         if clan.recruitment['setting'] == "closed":
    #             clanStatus = 'Closed'
    #         else:
    #             clanStatus = 'Open'
            
    #         totalDonationsRcvd = 0
    #         totalDonationsSent = 0
    #         for member in clan.members:
    #             totalDonationsRcvd += member['donationsReceived']
    #             totalDonationsSent += member['donations']
    #             if clan.warInfo['publicWarLog']:
    #                 warStats = f"{clan.warInfo.get('warStats',{}).get('wins',0)}W/{clan.warInfo.get('warStats',{}).get('losses',0)}L/{clan.warInfo.get('warStats',{}).get('ties',0)}D (Streak: {clan.warInfo.get('warWinStreak',0)})"
    #             else:
    #                 warStats = f"{clan.warInfo.get('warStats',{}).get('wins',0)}W (Streak: {clan.warInfo.get('warWinStreak',0)})"
    #             embed.add_field(
    #                 name=f"**{clan.clan} ({clan.tag})**",
    #                 value=f"**Level: {clan.level}\u3000Clan Status: {clanStatus}**"
    #                     + f"\n> Members: {len(clan.members)}/50\u3000Location: {clan.locale.get('location',{}).get('name','Not specified.')} / {clan.locale.get('language',{}).get('name','Not specified.')}"
    #                     + f"\n> <:ClanWarLeagues:825752759948279848> {clan.warInfo.get('warLeague',{}).get('league',{}).get('name','Not placed.')}\u3000<:ClanWars:825753092230086708> {warStats}"
    #                     + f"\n> <:HomeTrophies:825589905651400704> {clan.gameStats['trophyScore']}\u3000<:BuilderTrophies:825713625586466816> {clan.gameStats['builderScore']}"
    #                     + f"\n> <:DonationsSent:825574412589858886> {totalDonationsSent}\u3000<:DonationsReceived:825574507045584916> {totalDonationsRcvd}"
    #                     + f"\n```{clan.description}```"
    #                     + f"\n**More Stats from Clash Of Stats**\nhttps://www.clashofstats.com/clans/{clan.tag.replace('#','')}"
    #                     + f"\n**Join in-game!**\n https://link.clashofclans.com/en?action=OpenClanProfile&tag={clan.tag.replace('#','')}"
    #                     +f"\n\u200b",
    #                 inline=False)            
    #     await ctx.send(embed=embed)

    @clan_admin.command(name="cwlrefresh")
    async def refresh_cwlroster(self,ctx):
        """Refresh the CWL Rosters."""

        embed = await clash_embed(
            ctx=ctx,
            message=f"Refreshing data... please wait.")

        init_message = await ctx.send(embed=embed)

        cwlRosterDict = {}
        registered_clans = await self.config.clans()

        for clan in registered_clans:
            clan_tag = clan
            try:
                clan = Clan(ctx,clan_tag)
            except:
                await init_message.delete()
                return await clashdata_err(self,ctx)
            
            clanRoster = {}

            for member in clan.members:
                if member['league']['name'] != 'Unranked':                    
                    try:
                        member = Member(ctx,member['tag'])
                    except:
                        await init_message.delete()
                        return await clashdata_err(self,ctx)

                    if member.atxMemberStatus == 'member' and member.atxWar['registrationStatus'] == 'Yes':
                        if clan_tag == '#CRYPVGQ0':
                            if member.homeVillage['townHall']['thLevel'] >= 13:
                                clanRoster[member.tag] = {
                                    "tag": member.tag,
                                    "player": member.player,
                                    "townHall": member.homeVillage['townHall']['thLevel'],
                                    "heroLevels": sum(member.homeVillage['heroes'].values()),
                                    "priority": 0,
                                    "totalStars": 0,
                                    }
                            else:
                                pass
                        else:
                            clanRoster[member.tag] = {
                                "tag": member.tag,
                                "player": member.player,
                                "townHall": member.homeVillage['townHall']['thLevel'],
                                "heroLevels": sum(member.homeVillage['heroes'].values()),
                                "priority": 0,
                                "totalStars": 0,
                                }

            cwlRosterDict[clan_tag] = clanRoster

        with open(getFile('cwlroster'),"w") as dataFile:
            json.dump(cwlRosterDict,dataFile,indent=2)

        embed = await clash_embed(
            ctx=ctx,
            message=f"CWL Roster refreshed.")

        return await init_message.edit(embed=embed)
    
    @clan_admin.command(name="warcc")
    async def generate_clancastle(self,ctx):
        """Generate War Clan Castle suggestions. Does not suggest Super Troops."""

        embed = await clash_embed(
            ctx=ctx,
            message=f"Fetching data... please wait.")
        init_message = await ctx.send(embed=embed)

        cwlStatus = await self.config.CWLregistration()
        all_troops = troops['elixir_troops'] + troops['dark_troops'] + troops['super_troops']
        recommendClanCastle = {
            10: [   {
                    'Lava Hound': 1,
                    'Headhunter': 1,
                    'Archer': 9,
                    },
                    {
                    'Lava Hound': 1,
                    'Headhunter': 2,
                    'Archer': 3,
                    },
                    {
                    'Lava Hound': 1,
                    'Ice Golem': 1,
                    },
                    {
                    'Super Minion': 3,
                    'Archer': 9,
                    }   ],
            8: [   {
                    'Lava Hound': 1,
                    'Headhunter': 1,
                    'Archer': 4,
                    },
                    {
                    'Super Minion':2,
                    'Headhunter':1,
                    'Archer':2,
                    },
                    {
                    'Dragon': 1,
                    'Witch': 1,
                    'Archer': 8
                    }   ],
            7: [   {
                    'Baby Dragon': 1,
                    'Witch': 2,
                    'Archer': 1
                    },
                    {
                    'Lava Hound': 1,
                    'Archer': 5
                    },
                    {
                    'Dragon': 1,
                    'Witch': 1,
                    'Archer': 3
                    }   ],
            5:  [   {  
                    'Baby Dragon': 1,
                    'Witch': 1,
                    'Archer': 8
                    },
                    {
                    'Dragon': 1,
                    'Archer': 10
                    },
                    {
                    'Lava Hound': 1
                    }   ],
            4:  [   {
                    'Baby Dragon': 1,
                    'Valkyrie': 1,
                    'Wizard': 1,
                    'Archer': 3
                    },
                    {
                    'Baby Dragon':1,
                    'Witch':1,
                    'Archer':3
                    },
                    {
                    'Dragon':1,
                    'Wizard':1,
                    'Archer':1
                    }   ],
            3:  [   {
                    'Dragon':1,
                    }   ],
            2:  [   {
                    'Ice Golem':1,
                    }
                ]
            }         
        embedpaged = []
        registered_clans = await self.config.clans()

        try:
            with open(getFile('players'),"r") as dataFile:
                playerJson = json.load(dataFile)
                playerData = playerJson['current']
        except:
            return await clashdata_err(self,ctx)

        for clan in registered_clans:
            try:
                clan = Clan(ctx,clan)
            except Clash_APIError as err:
                return await clashapi_err(self,ctx,err,clan)
            except:
                return await clashdata_err(self,ctx)

            activeWar = False            
            troopLibrary = {}
            for troop in all_troops:
                troopLibrary[troop] = 0
            
            try:
                clan.GetClassicWar()
                currentWar = clan.warInfo['classicWar']['currentWar']
            except Clash_APIError as err:
                return await clashapi_err(self,ctx,err,clan)
            except:
                return await clashdata_err(self,ctx)

            if currentWar['state'] == 'preparation':
                activeWar = True
            elif cwlStatus:
                try:
                    clan.GetWarLeagues()
                    for cwlRound in clan.warInfo['warLeague']['currentGroup']['rounds']:
                        for cwlWar in cwlRound['warTags']:
                            cwlWar = clashapi_cwl(cwlWar)
                            if cwlWar['state']=='preparation' and isinstance(cwlWar['opponent']['tag'],str) and (cwlWar['clan']['tag'] == clan.tag or cwlWar['opponent']['tag'] == clan.tag):
                                activeWar = True
                                currentWar = cwlWar
                except Clash_APIError as err:
                    return await clashapi_err(self,ctx,err,clan)
                except:
                    return await clashdata_err(self,ctx)

            if activeWar:
                participantList = []
                warTitle = f"{currentWar['clan']['name']} vs {currentWar['opponent']['name']}"
                warCCsumm = ""

                if clan.tag == currentWar['clan']['tag']:
                    clanWarInfo = currentWar['clan']
                    warParticipants = currentWar['clan']['members']
                elif clan.tag == currentWar['opponent']['tag']:
                    clanWarInfo = currentWar['opponent']
                    warParticipants = currentWar['opponent']['members']

                warParticipants.sort(key=lambda x:(x['mapPosition']))
                
                for participant in warParticipants:
                    participantData = playerData.get(participant['tag'],{})
                    ccLevel = participantData.get('clanCastleLevel',0)
                    if ccLevel > 1:
                        if ccLevel == 9:
                            ccLevel = 10
                        elif ccLevel == 6:
                            ccLevel = 7
                        ccSelect = random.choice(recommendClanCastle[ccLevel])

                        ccText = []
                        for troop, qty in ccSelect.items():
                            ccText.append(f"{troop} x{qty}")
                            troopLibrary[troop] += qty
                        participantDict = {
                            'title': f"{th_emotes[int(participant['townhallLevel'])]} **{participant['name']}** ({participant['tag']})",
                            'desc': f"{humanize_list(ccText)}",
                            }
                        participantList.append(participantDict)
                    else:
                        participantDict = {
                            'title': f"{th_emotes[int(participant['townhallLevel'])]} **{participant['name']}** ({participant['tag']})",
                            'desc': f"*No Clan Castle.*",
                            }
                        participantList.append(participantDict)

                for troop, qty in troopLibrary.items():
                    if qty > 0:
                        warCCsumm += f"> {troop}: {qty}\n"
                    
                embed = await clash_embed(
                        ctx=ctx,
                        title=warTitle,
                        show_author=True)
                embed.set_thumbnail(url=clan.badges['medium'])
                for participant in participantList:
                    embed.add_field(
                        name=participant['title'],
                        value=participant['desc'],
                        inline=False)
                embed.add_field(
                    name=f"__Troop Totals__",
                    value=warCCsumm,
                    inline=False)
                embedpaged.append(embed)

            else:
                embed = await clash_embed(
                        ctx=ctx,
                        title=clan.clan,
                        message="Did not find a War currently in preparation.",
                        show_author=True)
                embed.set_thumbnail(url=clan.badges['medium'])

        if len(embedpaged)>1:
            paginator = BotEmbedPaginator(ctx,embedpaged)
            await paginator.run()
        elif len(embedpaged)==1:
            await ctx.send(embed=embedpaged[0])
        return await init_message.delete()


    @clan_admin.group(name="members")
    async def clan_members(self,ctx):
        """Clan Member Management"""

        # if not ctx.invoked_subcommand:

        #     embed = await clash_embed(
        #         ctx=ctx,
        #         message=f"Fetching data... please wait.")
        #     init_message = await ctx.send(embed=embed)

        #     embedpaged = []

        #     registered_clans = await self.config.clans()
        #     try:
        #         with open(getFile('players'),"r") as dataFile:
        #             playerJson = json.load(dataFile)
        #             playerData = playerJson['current']
        #     except:
        #         return await clashdata_err(self,ctx)          

        #     for clan in registered_clans:

        #         embed = await clash_embed(
        #             ctx=ctx,
        #             title=f"**{clan.clan} ({clan.tag})**",
        #             message=f"**Level: {clan.level}\u3000Clan Status: {clanStatus}**"
        #                     + f"\n> Members: {len(clan.members)}/50\u3000Location: {clan.locale.get('location',{}).get('name','Not specified.')} / {clan.locale.get('language',{}).get('name','Not specified.')}"
        #                 )
        #         memberlist = []

        #         try:
        #             clan = Clan(ctx,clan)
        #         except Clash_APIError as err:
        #             return await clashapi_err(self,ctx,err,clan)
        #         except:
        #             return await clashdata_err(self,ctx)

        #         for member in clan.members:
        #             memberTable = {}
        #             try:
        #                 memberInfo = playerData[member['tag']]
        #             except:
        #                 memberInfo = {}

        #             embed.add_field(
        #                 name=f"**{member['name']}** ({member['tag']})",
        #                 value=f"{th_emotes[memberInfo.get('townHallLevel',1)]} {memberInfo.get('townHallLevel',1)}\u3000<:donated:825574412589858886> {memberInfo['donations']['sent']['season']:,}\u3000<:received:825574507045584916> {memberInfo['donations']['received']['season']:,}",
        #                 inline=False
        #                 )

        #         embedpaged.append(embed)

        #     if len(embedpaged)>1:
        #         paginator = BotEmbedPaginator(ctx,embedpaged)
        #         await paginator.run()
        #     elif len(embedpaged)==1:
        #         await ctx.send(embed=embedpaged[0])
        #     return await init_message.delete()

    @clan_members.command(name="checkactivity")
    async def activity_check(self,ctx,clan='#2PCRPUPCY',season='current'):
        """Checks for members who do not meet activity requirements."""
        #gp_shop = "Admin Store"
        #gp_item = "[R] COC Gold Pass (USD5 Gift Card)"

        embedpaged = []    

        registered_accounts = await self.config.all_users()

        try:
            with open(getFile('players'),"r") as dataFile:
                playerJson = json.load(dataFile)
                playerData = playerJson[season]
        except:
            err_embed = await clash_embed(ctx=ctx,message=f"Error retrieving player data for {season} season.",color="fail")
            return await ctx.send(embed=err_embed)

        try:
            with open(getFile('clangames'),"r") as dataFile:
                clanGamesJson = json.load(dataFile)
                clanGamesSeason = list(clanGamesJson.keys())
                clanGamesSeason = clanGamesSeason[-1]                
                clanGamesData = clanGamesJson[clanGamesSeason]
        except:
            err_embed = await clash_embed(ctx=ctx,message=f"Error retrieving clan games data for {clanGamesSeason} season.",color="fail")
            return await ctx.send(embed=err_embed)

        playerCount = 0
        playerList = []

        for player in playerData.values():

            handle = True

            if clan:
                if player['lastSeen']['currentClan'] != clan:
                    handle = False

            if handle:                    
                activityReq1 = 0
                activity1 = 'lose'
                activityReq2 = 0
                activity2 = 'lose'
                activityReq3 = 0
                activity3 = 'lose'
                activity3 = 'lose'
                activity3 = 'lose'
                if player['memberStatus'] == 'member':

                    playerLeague = 'Not Placed'                
                    try:
                        if player['leagueInfo']['leagueDetails'] != None:
                            playerLeague = player['leagueInfo']['leagueDetails']['name']
                            activity1 = 'win'
                            activityReq1 = 1
                    except:
                        pass

                    try:
                        for cg_participant in clanGamesData:
                            if cg_participant['tag'] == player['tag']:
                                cg_pts = cg_participant['games_pts']
                                if cg_pts >= 1500:
                                    activity2 = 'win'
                                    activityReq2 = 1
                    except:
                        cg_pts = 0

                    warStarsOffense = 0
                    for war in player['warLog']:
                        warStarsOffense += war['attackStars']
                            
                    if warStarsOffense >= 20:
                        activity3 = 'win'
                        activityReq3 = 1
                    elif player['clanCapital']['goldContributed']['season'] >= capitalGoldElderReq.get(player['townHallLevel'],10000):
                        activity3 = 'win'
                        activityReq3 = 1
                    elif (player['donations']['sent']['season'] + player['donations']['received']['season']) >= 3000:
                        activity3 = 'win'
                        activityReq3 = 1

                    if (activityReq1 + activityReq2 + activityReq3) < 3:

                        playerStr = (f"\n\u200b\u3000{elder_status[activity1]} Trophy League: **{playerLeague}**"
                                    + f"\n\u200b\u3000{elder_status[activity2]} Clan Games ({clanGamesSeason}): **{cg_pts:,}** / 1,500"
                                    + f"\n\u200b\u3000{elder_status[activity3]} War Stars: **{warStarsOffense}** / 20"
                                    + f"\n\u200b\u3000{elder_status[activity3]} Clan Capital: **{player['clanCapital']['goldContributed']['season']:,}** / {capitalGoldElderReq.get(player['townHallLevel'],10000):,}"
                                    + f"\n\u200b\u3000{elder_status[activity3]} Donations: **{player['donations']['sent']['season'] + player['donations']['received']['season']:,}** / 3,000\n\u200b")

                        playerDict = {
                            'name': f"**TH{player['townHallLevel']} {player['player']} ({player['tag']})**",
                            'value': playerStr,
                            }
                        playerList.append(playerDict)

        totalPlayers = len(playerList)

        while playerCount <= 10 and totalPlayers > 0:

            for player in playerList:
                totalPlayers -= 1
                playerCount += 1
        
                if playerCount == 1:
                    embed = await clash_embed(
                        ctx=ctx,
                        title="Clan Activity Report: Inactive Members",
                        message=f"Inactive Members Found: {len(playerList)}"
                        )
                embed.add_field(
                    name=f"{player['name']}",
                    value=f"{player['value']}",
                    inline=False
                    )

                if playerCount == 10:
                    embedpaged.append(embed)
                    playerCount = 0

        if len(embedpaged)>1:
            paginator = BotEmbedPaginator(ctx,embedpaged)
            await paginator.run()
        elif len(embedpaged)==1:
            await ctx.send(embed=embedpaged[0])
        return 