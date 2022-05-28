from redbot.core import Config, commands, bank
from numerize import numerize
from .coc_resources import Clash_ClassError, Clash_NotMember, StatTooHigh, Clan, Player, PlayerVerify, Member, challengePass, Challenge, getTroops, getFile, getServerID, clashJsonLock, clashapi_player, clashapi_clan, clashapi_pverify, clashapi_leagueinfo, clashapi_cwl, getMaxTroops
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
    async def clans(self,ctx,clan_tag=None):
        """Set clans to be included as part of the Ataraxy family."""        
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
                    except Clash_ClassError:
                        exc_embed = await clash_embed(ctx=ctx,message=f"I couldn't find a clan with this tag. Please check the tag is valid or try again later.\n\nYou provided: **{clan}**")
                        await ctx.send(embed=exc_embed)
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
            except Clash_ClassError:
                embed = await clash_embed(ctx=ctx,message=f"I couldn't find a clan with this tag. Please check the tag is valid or try again later.\n\nYou provided: **{clan_tag}**")
                await ctx.send(embed=embed)
                raise Clash_ClassError
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
    
    @cocadmin.command()
    @commands.is_owner()
    async def updateelders(self,ctx):
        """Updates Eldership status based on the last closed season."""
        lastSeason = None
        newelders = []
        elders_gp = []
        registered_accounts = await self.config.all_users()

        try:
            with open(getFile('seasons'),"r") as dataFile:
                seasonJson = json.load(dataFile)
                #lastSeason = seasonJson['seasons'][-1]
                lastSeason = 'current'
        except:
            exc_embed = await clash_embed(ctx=ctx,message=f"Error retrieving season information.")
            return await ctx.send(embed=exc_embed)

        if not lastSeason:
            exc_embed = await clash_embed(ctx=ctx,message=f"Last Season was not found.")
            return await ctx.send(embed=exc_embed)

        try:
            with open(getFile('players'),"r") as dataFile:
                playerJson = json.load(dataFile)
                playerData = playerJson[lastSeason]
        except:
            exc_embed = await clash_embed(ctx=ctx,message=f"Error retrieving player data for {lastSeason} season.")
            return await ctx.send(embed=exc_embed)

        for playerLastSeason in playerData.values():
            promoteElder = False

            if playerLastSeason['memberStatus'] == 'member':
                #if int(playerLastSeason['lastSeen']['timer']/86400) >= 20:
                if True:
                    if (playerLastSeason['war']['cwlStars'] + playerLastSeason['war']['warStars']) >= 5:
                        promoteElder = True
                    if playerLastSeason['donations']['sent']['season'] >= 1000:
                        promoteElder = True
                    if playerLastSeason['clanCapital']['goldContributed']['season'] >= 20000:
                        promoteElder = True

                if promoteElder:
                    try:                    
                        playerCurrent = Member(ctx,playerLastSeason['tag'])
                    except Clash_ClassError:
                        embed = await clash_embed(ctx=ctx,
                            message=f"Could not find this tag: {playerLastSeason['tag']}.")
                        await ctx.send(embed=embed)
                        raise Clash_ClassError

                    if playerCurrent.atxMemberStatus=='member' and playerCurrent.atxRank!='Leader':
                        playerCurrent.atxRank = "Elder"
                        #playerCurrent.saveData()

                        for user, account in registered_accounts.items():
                            if playerCurrent.tag in list(account.values())[0] and user not in elders_gp:
                                elders_gp.append(user)
                        newelders.append(playerCurrent)

        elder_announcement = f"Once again, a Clash season comes and goes. With that, we are pleased to announce our Ataraxy Elders for the new season! Congratulations to everyone for an amazing season.\n\u3000"

        for e in newelders:
            elder_announcement += f"\n\u3000{e.tag} **{e.player}**"

        gp_announcement = f"The following members are also eligible to claim a Gold Pass for the upcoming Clash season! Instructions will be provided soon.\n\u3000"

        for u in elders_gp:
            gp_announcement += f"\n\u3000<@{u}>"

        #discord_atxserver = getServerID(atxserver)
        #announcement_server = ctx.bot.get_guild(discord_atxserver)
        #announcement_channel = discord.utils.get(announcement_server.channels,id=719170006230761532)
        #announcement_ping = get(announcement_server.roles,name="COC-Clan Wars")

        embed = await clash_embed(
            ctx=ctx,
            title=f"<:logo_ATX_circle:975063153798946917>\u3000**NEW ATARAXY ELDERS**\u3000<:logo_ATX_circle:975063153798946917>",
            message=elder_announcement + "\n----------------------------------------",
            show_author=False)

        if len(elders_gp) > 0:
            embed.add_field(
                name=f"**<:GoldPass:834093287106674698> GOLD PASS REWARDS**",
                value=gp_announcement,
                inline=False)

        return await ctx.send(embed=embed)


    @commands.group(name="myprofile", autohelp=False)
    async def profile(self,ctx):
        """Shows your Ataraxy Clash profile.
        Use `;myprofile link` to add/remove accounts."""

        if not ctx.invoked_subcommand:
            registered_accounts = await self.config.user(ctx.author).players()

            embed = await clash_embed(
                ctx=ctx,
                message=f"You've linked the below Clash of Clans accounts.\nTo add/remove an account use `;myprofile link`."
                )
            for account in registered_accounts:
                try:                    
                    player = Player(ctx,account)
                except Clash_ClassError:
                    exc_embed = await clash_embed(ctx=ctx,message=f"I couldn't find a player with this tag. Please check the tag is valid or try again later.\n\nYou provided: **{clan}**")
                    await ctx.send(embed=exc_embed)
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

    @profile.command(name="link")
    async def link(self,ctx,player_tag,api_token):
        """Add/remove COC accounts from your Ataraxy profile.
        To get an API token, head in-game:
        - Go to **Settings --> More Settings**
        - Scroll down to find **API Token**
        - Tap the **Show** button to get your token"""

        registered_accounts = await self.config.user(ctx.author).players()
        try:
            player = PlayerVerify(ctx,player_tag,api_token)
        except Clash_ClassError:
            exc_embed = await clash_embed(ctx=ctx,message=f"I couldn't find a player with this tag. Please check the tag is valid or try again later.\n\nYou provided: **{clan}**")
            await ctx.send(embed=exc_embed)
            raise Clash_ClassError
        else:
            if player.verifyStatus != "ok":
                embed = await clash_embed(
                    ctx=ctx,
                    title="Verification Error!",
                    message="An error occured while verifying this player. The API token provided may be invalid.",
                    color="fail")
                return await ctx.send(embed=embed)
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
                    return await ctx.send(embed=embed)

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
                        return await ctx.send(embed=embed)
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
                        return await ctx.send(embed=embed)

    @commands.command(name="joinatx",aliases=["atxclans"])
    async def joining_info(self, ctx):
        """
        Find an Ataraxy clan!
        """
        registered_clans = await self.config.clans()

        if len(registered_clans) == 0:
            embed = await clash_embed(ctx=ctx,message=f"An error occurred.")
            return await ctx.send(embed=embed)

        else:
            embedpaged = []

            embed = await clash_embed(ctx=ctx,
                                        message=f"The Ataraxy Clash family is proud to feature the below clans in our family."+
                                                f"\nJoin any of the below clans to be an Ataraxy member! Send us a request in-game with the password `i love atx`.")

            for clan in registered_clans:
                try:                    
                    clan = Clan(ctx,clan)
                except Clash_ClassError:
                    pass
                else:
                    if clan.recruitment['setting'] == "closed":
                        clanStatus = 'Closed'
                    else:
                        clanStatus = 'Open'

                    totalDonationsRcvd = 0
                    totalDonationsSent = 0

                    for member in clan.members:
                        totalDonationsRcvd += member['donationsReceived']
                        totalDonationsSent += member['donations']

                    if clan.warInfo['publicWarLog']:
                        warStats = f"{clan.warInfo.get('warStats',{}).get('wins',0)}W/{clan.warInfo.get('warStats',{}).get('losses',0)}L/{clan.warInfo.get('warStats',{}).get('ties',0)}D (Streak: {clan.warInfo.get('warWinStreak',0)})"
                    else:
                        warStats = f"{clan.warInfo.get('warStats',{}).get('wins',0)}W (Streak: {clan.warInfo.get('warWinStreak',0)})"

                    embed.add_field(
                        name=f"**{clan.clan} ({clan.tag})**",
                        value=f"**Level: {clan.level}\u3000Clan Status: {clanStatus}**"
                            + f"\nMembers: {len(clan.members)}/50\u3000Location: {clan.locale.get('location',{}).get('name','Not specified.')} / {clan.locale.get('language',{}).get('name','Not specified.')}"
                            + f"\n<:ClanWarLeagues:825752759948279848> {clan.warInfo.get('warLeague',{}).get('league',{}).get('name','Not placed.')}\u3000<:ClanWars:825753092230086708> {warStats}"
                            + f"\n<:HomeTrophies:825589905651400704> {clan.gameStats['trophyScore']}\u3000<:BuilderTrophies:825713625586466816> {clan.gameStats['builderScore']}"
                            + f"\n<:DonationsSent:825574412589858886> {totalDonationsSent}\u3000<:DonationsReceived:825574507045584916> {totalDonationsRcvd}"
                            + f"\n```{clan.description}```"
                            + f"\n**Join in-game!**\n https://link.clashofclans.com/en?action=OpenClanProfile&tag={clan.tag.replace('#','')}"
                            +f"\n--------------------\n\u3000",
                        inline=False
                        )                    
            
            await ctx.send(embed=embed)

    @commands.command(name="getbase")
    async def get_base(self, ctx):
        """
        Get a War Base. Only usable by Members.
        """
        embedpaged = []
        is_member = False

        for account in await self.config.user(ctx.author).players():
            player = Member(ctx,account)
            if player.atxMemberStatus == 'member':
                is_member = True

        if is_member:
            try:
                with open(getFile('warbases'),"r") as dataFile:
                    warBases = json.load(dataFile)
            except:
                embed = await clash_embed(ctx=ctx,
                    message=f"Couldn't find any bases. Please contact admin.",
                    color="fail"
                    )
                return await ctx.send(embed=embed)

            base_types = ['TH14 - CWL','TH14 - War','TH14 - Legends','TH13','TH12','TH11','TH10']

            baseSelect = BotMultipleChoice(ctx,base_types,"Select a Base Type.")
            await baseSelect.run()

            if baseSelect.choice==None:
                return await baseSelect.quit(f"{ctx.author.mention}, Selection Stopped.")
            
            #await ctx.send("test")
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
        Gets information about a Clash of Clans player. Will display member stats for Ataraxy family members.
        If no tag is provided, it will return information on all your linked accounts. Link accounts with `;profile link`.
        """
        action_tags = []
        if player_tag==None:
            for account in await self.config.user(ctx.author).players():
                action_tags.append(account)
        else:
            action_tags.append(player_tag)
        if len(action_tags) == 0:
            embed = await clash_embed(ctx=ctx,
                message=f"You need to provide a tag when running this command, or link a Clash of Clans account to your Discord profile.\n\nRun `;profile link` to start the linking process.",
                color="fail"
                )
            return await ctx.send(embed=embed)
        else:
            embedpaged = []
            for action_tag in action_tags:                
                try:                    
                    player = Member(ctx,action_tag)
                except Clash_ClassError:
                    embed = await clash_embed(ctx=ctx,
                        message=f"I couldn't find a player with this tag. Please check the tag is valid or try again later.\n\nYou provided: {action_tag}")
                    await ctx.send(embed=embed)
                    raise Clash_ClassError
                else:
                    try:
                        clan_description = f"{player.clan['role']} of **[{player.clan['clan_info']['name']}](https://www.clashofstats.com/clans/{player.clan['clan_info']['tag'].replace('#','')})**"
                    except:
                        clan_description = "No Clan"

                    memberStatus = ''
                    if player.atxMemberStatus == 'member':
                        memberStatus = f"**Member of Ataraxy <:logo_ATX_circle:975063153798946917>**\n"
                    if player.atxRank != 'none':
                        memberStatus = f"\u3000**{player.atxRank} of Ataraxy <:logo_ATX_circle:975063153798946917>**\n"

                    embed = await clash_embed(ctx=ctx,
                        title=f"{player.player} ({player.tag})",
                        message=f"{memberStatus}<:Exp:825654249475932170> {player.exp}\u3000<:Clan:825654825509322752> {clan_description}",
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

                        for achievement in player.homeVillage['achievements']:
                            if achievement['name'] == "Gold Grab" and achievement['value']>=2000000000:
                                lootGold = "max"                                    
                            if achievement['name'] == "Elixir Escapade" and achievement['value']>=2000000000: 
                                lootElixir = "max"                                    
                            if achievement['name'] == "Heroic Heist" and achievement['value']>=2000000000:
                                lootDarkElixir = "max"                               

                        embed.add_field(
                            name=f"**Current Season with Ataraxy**",
                                value=
                                    f":stopwatch: Last updated: {lastseen_text}ago"+
                                    #f"\n:calendar: {int(player.atxLastSeen['timer']/86400)} days spent in Ataraxy Clans"+
                                    "\n**Donations**"+
                                    f"\n<:donated:825574412589858886> {player.atxDonations['sent']['season']}\u3000<:received:825574507045584916> {player.atxDonations['received']['season']}"+
                                    "\n**Loot**"+
                                    f"\n<:gold:825613041198039130> {lootGold}\u3000<:elixir:825612858271596554> {lootElixir}\u3000<:darkelixir:825640568973033502> {lootDarkElixir}"+
                                    "\n**Clan Capital**"+
                                    f"\n<:CC_CapitalGoldContributed:971012592057339954> {clanCapitalGold}"+                                    
                                    "\n**War Registration**"+
                                    f"\n<:ClanWars:825753092230086708> {player.atxWar['registrationStatus']}\u3000<:Ataraxy:828126720925499402> {player.atxWar['warPriority']}"+
                                    "\n**War Performance**"+
                                    f"\n<:TotalWars:827845123596746773> {len(player.atxWarLog)}\u3000<:TotalStars:825756777844178944> {player.atxWar['warStars']+player.atxWar['cwlStars']}\u3000<:MissedHits:825755234412396575> {player.atxWar['missedAttacks']}"+
                                    "\n\u200b",
                                inline=False)

                        if len(player.atxWarLog)>0:
                            latest_wars = ''

                            for clan in player.atxLastSeen['clans']:
                                war_ct = 0
                                for war in player.atxWarLog[::-1][0:3]:
                                    if clan == war['clan']['tag']:
                                        war_ct += 1
                                        clan_name = war['clan']['name']                                        
                                        war_header = f"**{war_description[war['warType']]} vs {war['opponent']['name']}**\u3000{war_result[war['result']]}"
                                        war_attacks = f"\n\u3000<:Attack:828103854814003211>\u3000<:TotalStars:825756777844178944> {war['attackStars']}\u3000:fire: {int(war['attackDestruction'])}%\u3000<:MissedHits:825755234412396575> {war['missedAttacks']}"
                                        war_defense = f"\n\u3000<:Defense:828103708956819467>\u3000<:TotalStars:825756777844178944> {war['defenseStars']}\u3000:fire: {int(war['defenseDestruction'])}%\n\u200b"
                                        latest_wars += war_header + war_attacks + war_defense
                                
                                if war_ct > 0:
                                    embed.add_field(
                                        name=f"**Recent Wars in {clan_name}**",
                                        value=latest_wars+"\u200b",
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

    @war.command(name="log")
    async def player_warlog(self, ctx):
        """[Members-only] Displays your Ataraxy War Log for your accounts."""
        action_tags = []
        for account in await self.config.user(ctx.author).players():
            action_tags.append(account)
        
        if len(action_tags) == 0:
            embed = await clash_embed(ctx=ctx,
                message=f"You need to link a Clash of Clans account to your Discord profile to use this command.\n\nRun `;profile link` to start the linking process.",
                color="fail"
                )
            return await ctx.send(embed=embed)
        else:
            embedpaged = []
            for action_tag in action_tags:                
                try:                    
                    player = Member(ctx,action_tag)
                except Clash_ClassError:
                    embed = await clash_embed(ctx=ctx,
                        message=f"I couldn't find a player with this tag. Please check the tag is valid or try again later.\n\nYou provided: {action_tag}")
                    await ctx.send(embed=embed)
                    raise Clash_ClassError
                else:                 
                    if player.atxMemberStatus=="member":
                        if len(player.atxWarLog)>0:

                            embed = await clash_embed(ctx=ctx,
                                title=f"{player.player} ({player.tag})",
                                message=f"\n<:TotalWars:827845123596746773> {len(player.atxWarLog)}\u3000<:TotalStars:825756777844178944> {player.atxWar['warStars']+player.atxWar['cwlStars']}\u3000<:MissedHits:825755234412396575> {player.atxWar['missedAttacks']}",
                                show_author=True)            
                            try:
                                embed.set_thumbnail(url=player.homeVillage['league']['leagueDetails']['iconUrls']['medium'])
                            except:
                                pass

                            for clan in player.atxLastSeen['clans']:
                                win_count = 0
                                lost_count = 0
                                draw_count = 0
                                war_log = []                                
                        
                                for war in player.atxWarLog[::-1]:

                                    if clan == war['clan']['tag']:
                                        war_text = {}
                                        clan_name = war['clan']['name']

                                        if war['result']=="win":
                                            win_count+=1
                                        elif war['result']=="lose":
                                            lost_count+=1
                                        else:
                                            draw_count+=1

                                        war_text['title'] = f"**{war_description[war['warType']]} vs {war['opponent']['name']}**\u3000{war_result[war['result']]}"
                                        war_attacks = f"> \u3000<:Attack:828103854814003211>\u3000<:TotalStars:825756777844178944> {war['attackStars']}\u3000:fire: {int(war['attackDestruction'])}%\u3000<:MissedHits:825755234412396575> {war['missedAttacks']}"
                                        war_defense = f"\n> \u3000<:Defense:828103708956819467>\u3000<:TotalStars:825756777844178944> {war['defenseStars']}\u3000:fire: {int(war['defenseDestruction'])}%"
                                        war_text['text'] = war_attacks + war_defense

                                        war_log.append(war_text)

                                embed.add_field(
                                    name=f"**War Log in {clan_name}**",
                                    value=f"Won {win_count}\u3000Lost {lost_count}\u3000Tied {draw_count}",
                                        inline=False)

                                for war in war_log:
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
        
        #get watched clans
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
                await warTypeSelect.quit()
                warRosterType = warTypeSelect.choice
        else:
            warRosterType = "Clan Wars"

        embed = await clash_embed(
            ctx=ctx,
            message=f"Fetching data... please wait.")
        init_message = await ctx.send(embed=embed)

        if warRosterType == "Clan Wars":
            for clan in registered_clans:
                war_roster = []
                clan = Clan(ctx,clan)

                for member in clan.members:
                    member = Member(ctx,member['tag'])
                    if member.atxWar['registrationStatus'] == 'Yes' and member.homeVillage['league']['leagueDetails'] != None and member.atxWar['missedAttacks'] < 6:
                        war_roster.append(member)
            
                #sort by war priority
                war_roster.sort(key=lambda x:(x.atxWar['warPriority'],x.homeVillage['townHall']['thLevel'],(x.atxDonations['sent']['season']+x.atxDonations['received']['season'])),reverse=True)

                #determine eligible war size
                war_size = len(war_roster) - (len(war_roster) % 5)

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
            try:
                with open(getFile('cwlroster'),"r") as dataFile:
                    cwlData = json.load(dataFile)
            except:
                return await cwlRegistration.quit(f"{ctx.author.mention} an unknown error occurred, please try again later.")

            rosterA = []
            rosterB = []
            rosteralt = []

            for tag, data in cwlData.items():
                member = Member(ctx,tag)
                if member.atxMemberStatus == 'member':
                    if data['townHall'] == 14 or data['townHall'] == 13:
                        rosterA.append(data)
                        rosteralt.append(data)
                    if data['townHall'] == 12 or data['townHall'] == 11 or data['townHall'] == 10 or data['townHall'] == 9:
                        rosterB.append(data)
                        rosteralt.append(data)

            if len(rosterA) >= 15 and len(rosterB) >=15:
                rosterA_count = 0
                rosterA.sort(key=lambda x:(x['priority'],(x['regOrder']*-1)), reverse=True)
                rosterA_embed = await clash_embed(
                    ctx=ctx,
                    title=f"CWL Roster for Master League",
                    message=f"Roster Size: {len(rosterA)}")
                for participant in rosterA:
                    rosterA_count += 1

                    if rosterA_count <= 15:
                        rosterA_embed.add_field(
                            name=f"**{rosterA_count}**\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} TH{participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)
                    if rosterA_count > 15:
                        rosterA_embed.add_field(
                            name=f"**SUB**\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} TH{participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)

                rosterB_count = 1
                rosterB.sort(key=lambda x:(x['priority'],(x['regOrder']*-1)), reverse=True)
                rosterB_embed = await clash_embed(
                    ctx=ctx,
                    title=f"CWL Roster for Cystal League",
                    message=f"Roster Size: {len(rosterB)}")

                rosterB_embed.add_field(
                    name=f"**1** Reserved",
                    value=f"*Reserved for Clan Donation Account",
                    inline=False)

                for participant in rosterB:
                    rosterB_count += 1
                    if rosterB_count <= 14:
                        rosterB_embed.add_field(
                            name=f"**{rosterA_count}**\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} TH{participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)
                    if rosterB_count > 14:
                        rosterB_embed.add_field(
                            name=f"**SUB**\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} TH{participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)
                embedpaged.append(rosterA_embed)
                embedpaged.append(rosterB_embed)
            
            else:
                rosteralt_count = 0
                rosteralt_TH14 = 2
                rosteralt_TH13 = 2 #4
                rosteralt_TH12 = 3 #7
                rosteralt_TH11 = 3 #10
                rosteralt_TH10 = 3 #13
                rosteralt_TH9 = 2 #15

                rosteralt.sort(key=lambda x:(x['priority'],(x['regOrder']*-1)), reverse=True)

                rosteralt_embed = await clash_embed(
                    ctx=ctx,
                    title=f"Combined CWL Roster",
                    message=f"Roster Size: {len(rosteralt)}")

                for participant in rosteralt:
                    include = False
                    if rosteralt_TH14 > 0 and participant['townHall'] == 14:
                        rosteralt_TH14 -= 1
                        rosteralt_count += 1
                        include = True
                    if rosteralt_TH13 > 0 and participant['townHall'] == 13:
                        rosteralt_TH13 -= 1
                        rosteralt_count += 1
                        include = True
                    if rosteralt_TH12 > 0 and participant['townHall'] == 12:
                        rosteralt_TH12 -= 1
                        rosteralt_count += 1
                        include = True
                    if rosteralt_TH11 > 0 and participant['townHall'] == 11:
                        rosteralt_TH11 -= 1
                        rosteralt_count += 1
                        include = True
                    if rosteralt_TH10 > 0 and participant['townHall'] == 10:
                        rosteralt_TH10 -= 1
                        rosteralt_count += 1
                        include = True
                    if rosteralt_TH9 > 0 and participant['townHall'] == 9:
                        rosteralt_TH9 -= 1
                        rosteralt_count += 1
                        include = True

                    if include:
                        rosteralt_embed.add_field(
                            name=f"**{rosteralt_count}**\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} TH{participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)
                    if not include:
                        rosteralt_embed.add_field(
                            name=f"**SUB**\u3000{participant['player']} ({participant['tag']})",
                            value=f"{th_emotes[int(participant['townHall'])]} TH{participant['townHall']}\u3000<:Ataraxy:828126720925499402> Priority: {participant['priority']}",
                            inline=False)
                embedpaged.append(rosteralt_embed)

        await init_message.delete()
        if len(embedpaged)>1:
            paginator = BotEmbedPaginator(ctx,embedpaged)
            return await paginator.run()
        elif len(embedpaged)==1:
            return await ctx.send(embed=embedpaged[0])

    @war.command(name="cwlopen")
    @commands.is_owner()
    async def cwl_initiate(self,ctx):
        """Opens up CWL for registration."""

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
            for clan in registered_clans:
                cwlData[clan] = {}
            with open(getFile('cwlroster'),"w") as dataFile:
                json.dump(cwlData,dataFile,indent=2)

        if ctx.guild.id == clanServer.id:
            roster_role = get(ctx.guild.roles,name="COC-CWL Roster")
            for member in roster_role.members:
                member.remove_roles(roster_role)

        await self.config.CWLregistration.set(True)
        await ctx.send(f"{ctx.author.mention} CWL is now open.")       

        embed = await clash_embed(
            ctx=ctx,
            title=f":trophy: **CLAN WAR LEAGUES** :trophy:",
            message=f"The next Clan War Leagues are starting soon! Registration is now open for the next **__4 DAYS__**.\n\n**Do be sure to pay attention to the below instructions.**\n\u200b",
            show_author=False)

        embed.set_image(url="https://i.imgur.com/RpEB4I0.jpg")

        embed.add_field(name=":newspaper2: — **REQUIREMENTS**",
            value=f"Prior to registration, your village must:"+
                f"\n> - Be in our in-game clan. If you are not in the clan, please request to join."+
                f"\n> - Linked to our <@828462461169696778> bot. Link your account by using `;help cocset player` in <#803655289034375178>."+
                f"\n\nYou must also meet all of the below requirements:"+
                "\n> 1) Be **Townhall 9** or higher.",
                inline=False
                )
        embed.add_field(name=":black_nib: — **REGISTRATION**",
            value=f"Use the command `;war cwlregister` in <#805105007120744469> to register for CWL. **Note that registrations cannot be cancelled.**"+
                f"\n\nWe will aim to fill 2 CWL rosters this season:"+
                f"\n\u3000> #CRYPVGQ0 SoulTakers (Master League): TH13 - TH14"+
                f"\n\u3000> #2PCRPUPCY Ataraxy (Crystal League): TH9 - TH12"+
                f"\n\nIf there are insufficient participants for two rosters, we will ensure equal participation is made available in one roster."+
                f"\nYou can check the current registration with the command `;war roster`. Your Townhall level will be taken as of your registration.",
                inline=False
                )
        embed.add_field(name=":crossed_swords: — **CWL PRIORITY SYSTEM**",
            value=f"CWL Priority is separate from regular War priority. CWL Priority will be used to determine bonuses and participation:"+
                f"\n\u200b- Participate in War: `-3`"+
                f"\n\u200b- Use your Attack: `+1`"+
                f"\n\u200b- Earn 2 Stars: `+1`"+
                f"\n\u200b- Earn 3 Stars: `+2`"+
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
    async def cwl_close(self,ctx):

        clanServer_ID = await self.config.clanServerID()
        clanServer = ctx.bot.get_guild(clanServer_ID)

        clanChannel_ID = await self.config.clanChannelID()
        clanAnnouncementChannel = discord.utils.get(clanServer.channels,id=clanChannel_ID)

        await self.config.CWLregistration.set(False)
        return await clanAnnouncementChannel.send(content=f"CWL registration is now closed.")

    @war.command(name='cwlregister')
    #@commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def cwl_register(self,ctx):
        """Register for CWL, during the respective registration window. You need to be at least TH10 to participate in CWL."""

        registered_clans = await self.config.clans()
        cwlStatus = await self.config.CWLregistration()
        linked_accounts = await self.config.user(ctx.author).players()
        select_accounts = []

        if not cwlStatus:
            return await ctx.send(f"{ctx.author.mention}, CWL registration is currently not open.")
        
        if len(linked_accounts)==0:
            embed = await clash_embed(
                ctx=ctx,
                title="No accounts available.",
                message="Link your Clash of Clans account using `;cocset player` to be able to register for CWL.",
                color="fail")
            return await ctx.send(embed=embed)

        try:
            with open(getFile('cwlroster'),"r") as dataFile:
                cwlData = json.load(dataFile)
        except:
            cwlData = {}
    
        user_accounts = []
        for account in linked_accounts:
            account = Member(ctx,account)
            if account.atxMemberStatus == 'member' and account.clan['clan_info']['tag'] in registered_clans and account.tag not in list(cwlData.keys()) and account.homeVillage['townHall']['thLevel'] >=9:
                user_accounts.append(account)

        user_accounts.sort(key=lambda x:(x.homeVillage['townHall']['thLevel']),reverse=True)

        for account in user_accounts:
            account_text = f"{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000**{account.player}** ({account.tag})\n<:Clan:825654825509322752> {account.clan['clan_info']['name']}"
            select_accounts.append(account_text)

        if len(select_accounts)==0:
            embed = await clash_embed(
                ctx=ctx,
                title="No eligible CWL accounts.",
                message="You have no accounts currently eligible for CWL. Note that you need to be at least TH9 to participate in CWL.",
                color="fail")
            return await ctx.send(embed=embed)

        cwlRegistration = BotMultipleChoice(ctx,select_accounts,"Select an account to register for CWL.")
        await cwlRegistration.run()

        if cwlRegistration.choice==None:
            return await cwlRegistration.quit(f"{ctx.author.mention}, registration has been cancelled.")
        else:
            account_index = select_accounts.index(cwlRegistration.choice)
            registered_account = user_accounts[account_index]

            try:
                currentOrder = len(list(cwlData.keys()))

                cwlData[registered_account.tag] = {
                    'tag': registered_account.tag,
                    'player': registered_account.player,
                    'regOrder':currentOrder+1,
                    'townHall':registered_account.homeVillage['townHall']['thLevel'],
                    'priority':0,
                    'totalStars':0,
                    'warLog':[]
                    }
            except:
                return await cwlRegistration.quit(f"{ctx.author.mention} an unknown error occurred, please try again later.")
                
            try:
                async with clashJsonLock('cwl'):
                    with open(getFile('cwlroster'),"w") as dataFile:
                        json.dump(cwlData,dataFile,indent=2)
            except:
                return await ctx.send(f"{ctx.author.mention} an error occurred when saving your registration. Please try again later.")

            if ctx.guild.id == discord_atxserver:
                roster_role = get(ctx.guild.roles,name="COC-CWL Roster")
                await ctx.author.add_roles(roster_role)
            return await cwlRegistration.quit(f"{ctx.author.mention}, **{registered_account.tag} {registered_account.player}** has been registered for the upcoming CWL.")

    @commands.group(name="cg")
    async def cg(self,ctx):
        """Commands to manage Clan Games."""

    @cg.command(name="initiate")
    @commands.is_owner()
    async def cg_initiate(self,ctx,th_select):

        discord_atxserver = getServerID(atxserver)

        registered_clans = await self.config.clans()
        cg_status = await self.config.CGstatus()

        if ctx.guild.id != discord_atxserver:
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

        for clan in registered_clans:
            clan_data = []
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

                clan_data.append(member_data)

            clangames_data[clangames_series][clan.tag] = clan_data

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

        announcement_server = ctx.bot.get_guild(discord_atxserver)
        announcement_channel = discord.utils.get(announcement_server.channels,id=719170006230761532)
        announcement_ping = get(announcement_server.roles,name="COC-Clan Games")

        embed = await clash_embed(
            ctx=ctx,
            title=f"<:ClanGames:834063648494190602> **CLAN GAMES: {clangames_series_pt}** <:ClanGames:834063648494190602>",
            message=f"It's that time again - the next Clan Games are about to start. Pull up your sleeves and get ready to rumble!\n\u200b",
            show_author=False)

        embed.set_image(url="https://i.imgur.com/9FU4sx5.jpg")

        embed.add_field(name="<:Gem:834064925243998279> — **REWARDS**",
            value=f"In addition to the in-game rewards, Ataraxy members stand to win:"+
                f"\n> - First **10** players who reach 4,000 points will receive **2000 <:logo_ATC:732967299853582366> each**."+
                f"\n> \u200b\n> - First player from the below TH levels to reach 4,000 points will receive a **Gold Pass (USD5 Gift Card) each**.\n> \u3000\u3000**{th_reward_message}**\n\u200b",
                inline=False
                )
        embed.add_field(name="<:WarPriority:828126720925499402> — **RULES & REGULATIONS**",
            value=f"\n> 1) Your Clash of Clans account has to be linked to our <@828462461169696778> bot to be eligible for Rewards. Refer to <#803655289034375178> for details."+
                f"\n> \u200b\n> 2) In the event of ineligibility, Gold Pass rewards will be bumped to the next eligible winner. ATC rewards __will not__ be bumped."+
                f"\n> \u200b\n> 3) Only players in our in-game clans __as of__ this announcement are eligible for Rewards. You will be __disqualified__ if you leave our clan at any point during the games."+
                f"\n> \u200b\n> 4) ATC rewards can be won multiple times from multiple Clash accounts. All other rewards can only be won __once__ per Discord user."+
                f"\n> \u200b\n> 5) For purposes of Gold Pass rewards, your Townhall level is taken __as of__ this announcement.",
                inline=False
                )
        embed.add_field(name="\u200b",
            value=f"**All the best comrades!**\n\nFor any enquiries, refer them to any of the COC Leaders: <@624366408989540392>, <@350992430897692682>, or <@644530507505336330>.",
                inline=False
                )
        await announcement_channel.send(embed=embed)

    @cg.command(name="close")
    @commands.is_owner()
    async def cg_close(self,ctx):

        discord_atxserver = getServerID(atxserver)

        if ctx.guild.id != discord_atxserver:
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

        announcement_server = ctx.bot.get_guild(discord_atxserver)
        announcement_channel = discord.utils.get(announcement_server.channels,id=719170006230761532)
        announcement_ping = get(announcement_server.roles,name="COC-Clan Games")

        embed = await clash_embed(
            ctx=ctx,
            title=f"<:ClanGames:834063648494190602> **CLAN GAMES RESULTS: {clangames_series_pt}** <:ClanGames:834063648494190602>",
            message="Thank you to everyone who participated in Clan Games! Without further delay, here are the results...\n\u200b",
            show_author=False)
        embed.set_image(url="https://i.imgur.com/9FU4sx5.jpg")

        for clan in registered_clans:
            clan = Clan(ctx,clan)

            final_participants = []
            atc_recipients = []
            gp_recipients = []
            gp_ping = []

            for participant in clangames_data[clangames_series][clan.tag]:
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

                if len(clangames_threward) > 0:
                    if finalist['townhall'] in clangames_threward:
                        #add finalist to gold pass winners
                        for user, account in registered_accounts.items():
                            if finalist['tag'] in list(account.values())[0]:
                                user_b = get(ctx.bot.get_all_members(),id=user)
                                if user_b not in gp_ping:
                                    clangames_threward.remove(finalist['townhall'])

                                    finalist_gp['TH'] = finalist['townhall']
                                    finalist_gp['Player'] = finalist['player']
                                    finalist_gp['Discord'] = user_b
                                    gp_recipients.append(finalist_gp)
                                    gp_ping.append(user_b)

            gp_recipients = sorted(gp_recipients,key=lambda p:(p['TH']),reverse=True)

            #embed.add_field(name=f"**Results for {api_response['tag']} {api_response['name']}**",
            #    value=f"\u200b",
            #    inline=False
            #    )

            embed.add_field(name=f"<:logo_ATC:732967299853582366> — **ATC WINNERS** ({clangames_atc_reward} each)",
                value=f"```{tabulate(atc_recipients,headers='keys')}```"+
                    "\nAll <:logo_ATC:732967299853582366> rewards have been deposited to the respective Discord accounts. You can check your balances in <#654994554076004372>.\n\u200b",
                inline=False
                )
            embed.add_field(name="<:GoldPass:834093287106674698> — **GOLD PASS WINNERS**",
                value=f"```{tabulate(gp_recipients,headers='keys')}```"+
                "\nPlease DM <@644530507505336330> to claim your Gift Card!",
                inline=False
                )
        
        embed.add_field(name="\u200b",
                value=f"Once again, thank you everyone for participating! We hope everyone had fun competing. See you for next month's clan games!",
                inline=False
                )

        await self.config.CGstatus.set(False)
        return await announcement_channel.send(content=f"{announcement_ping.mention}",embed=embed)

    @commands.group(name="challenge")
    async def challengepass(self,ctx):
        """Commands relating to the Ataraxy Challenge Pass."""

    @challengepass.command()
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def mypass(self,ctx):
        """Check your Pass progress and Challenge details."""
        linked_accounts = await self.config.user(ctx.author).players()
        traDict = {'farm': 'The Farmer Track', 'war': 'The Warpath'}
        rewDict = {'challengePoints': 'Challenge Pass Points', 'atc': '<:logo_ATC:732967299853582366>'}

        if len(linked_accounts)==0:
            embed = await clash_embed(
                ctx=ctx,
                title="No accounts available.",
                message="Link your Clash of Clans account using `;cocset player` to be able to participate in the Ataraxy Challenge Pass.",
                color="fail")
            return await ctx.send(embed=embed)    
    
        user_accounts = []
        for account in linked_accounts:
            account = Member(ctx,account)
            if account.atxMemberStatus == 'member' and account.homeVillage['townHall']['thLevel'] >= 9:
                user_accounts.append(account)

        user_accounts.sort(key=lambda x:(x.homeVillage['townHall']['thLevel']),reverse=True)

        select_accounts = []
        for account in user_accounts:
            account_text = f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}"
            select_accounts.append(account_text)

        if len(select_accounts)==0:
            embed = await clash_embed(
                ctx=ctx,
                title="No eligible accounts.",
                message="You have no accounts eligible for the Ataraxy Challenge Pass. To be eligible, you need to be a member of our Clan and at least Townhall 9 or above.",
                color="fail")
            return await ctx.send(embed=embed)

        if len(select_accounts) > 1:
            pass_selection = BotMultipleChoice(ctx,select_accounts,"Select an account to view your Challenge Pass.")
            await pass_selection.run()

            if pass_selection.choice==None:
                return await pass_selection.quit(f"{ctx.author.mention}, request timed out.")
            else:
                account_index = select_accounts.index(pass_selection.choice)
                selected_account = user_accounts[account_index]

                await pass_selection.quit(f"{ctx.author.mention}, please wait...")
        else:
            selected_account = user_accounts[0]            

        cPass = challengePass(ctx,selected_account)

        if not cPass.atxChaTrack:
            trackSelect = ['farm','war']
            trackSelectText = ['**The Farmer Track**: The top 5 farmers get awarded a Gold Pass each.','**The Warpath**: Our battle-hardened warriors get accorded Eldership and have access to exclusive base builds for war.']
            trackSelection = BotMultipleChoice(ctx,trackSelectText,"You haven't chosen a Pass track on this account.\nPick one to start your challenge journey!")
            await trackSelection.run()

            if trackSelection.choice==None:
                return await pass_selection.quit(f"{ctx.author.mention}, request timed out.")
            else:
                cPass.atxChaTrack = trackSelect[trackSelectText.index(trackSelection.choice)]
                await trackSelection.quit(f"{ctx.author.mention}, you've chosen the **{traDict[cPass.atxChaTrack]}**.")

        newChallenge = None
        currentChallenge = None

        if cPass.atxChaTrack == 'war' or cPass.atxChaTrack == 'farm':
            if not cPass.atxChaActiveChall:
                newChallenge = Challenge(player=selected_account,track=cPass.atxChaTrack,challDict=cPass.atxChaActiveChall,commonStreak=cPass.atxChaCommonStreak)
                cPass.updatePass(newChallenge.challengeToJson())

            elif cPass.atxChaActiveChall:
                currentChallenge = Challenge(player=selected_account,track=cPass.atxChaTrack,challDict=cPass.atxChaActiveChall,commonStreak=cPass.atxChaCommonStreak)
                currentChallenge.updateChallenge()
                cPass.updatePass(currentChallenge.challengeToJson())

            embed = await clash_embed(
                ctx=ctx,
                title=f"**Ataraxy Challenge Pass: {selected_account.player}** ({selected_account.tag})",
                message=f"**Your Pass Track: `{traDict[cPass.atxChaTrack]}`**"+
                        f"\n\u200b\n__Your Season Stats:__"+
                        f"\n> Pass Completion: {numerize.numerize(cPass.atxChaPoints,1)} / 10K"+
                        f"\n> Completed: {cPass.atxChaCompleted}"+
                        f"\n> Missed: {cPass.atxChaMissed}"+
                        f"\n> Trashed: {cPass.atxChaTrashed}\n\u200b")                

            if newChallenge and newChallenge.challengeProgress['status'] == 'inProgress':
                timeRemaining = (newChallenge.challengeProgress['startTime'] + (newChallenge.challengeDuration*86400)) - time.time()
                trashCost = round((timeRemaining / 3600)*30)
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

                embed.add_field(name=f"**>> YOU RECEIVED A NEW CHALLENGE! <<**",
                    value=f"```{newChallenge.challengeDesc}```"+
                        f"\n> Current Progress: {numerize.numerize(newChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(newChallenge.challengeScore,1)}"
                        f"\n> Time Remaining: {timeRemaining_text}"+
                        f"\n> Rewards: {newChallenge.challengeReward['reward']} {rewDict[newChallenge.challengeReward['type']]}"+
                        f"\n> Trash Cost: {trashCost} <:logo_ATC:732967299853582366>"+
                        f"\n\u200b\nRemember to run the `;challenge mypass` command to update your stats and to complete challenges!\n\u200b",                            
                        inline=False)                    

            if currentChallenge and currentChallenge.challengeProgress['status'] == 'completed':
                timeRemaining = (currentChallenge.challengeProgress['startTime'] + (currentChallenge.challengeDuration*86400)) - time.time()
                trashCost = round((timeRemaining / 3600)*30)
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

                embed.add_field(name=f"**>> CHALLENGE COMPLETED! <<**",
                    value=f"```{currentChallenge.challengeDesc}```"+
                        f"\n> Current Progress: {numerize.numerize(currentChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(currentChallenge.challengeScore,1)}"
                        f"\n> Time Remaining: {timeRemaining_text}"+
                        f"\n> Rewards: {currentChallenge.challengeReward['reward']} {rewDict[currentChallenge.challengeReward['type']]}"+
                        f"\n\u200b\nRewards have been credited.\n*To start a new challenge, run the `;challenge mypass` command again.*\n\u200b",
                    inline=False)

                if currentChallenge.challengeReward['type'] == 'atc':
                    await bank.deposit_credits(ctx.author,currentChallenge.challengeReward['reward'])

            if currentChallenge and currentChallenge.challengeProgress['status'] == 'missed':
                embed.add_field(name=f"**>> YOU MISSED A CHALLENGE! <<**",
                    value=f"```{currentChallenge.challengeDesc}```"+
                        f"\n> Current Progress: {numerize.numerize(currentChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(currentChallenge.challengeScore,1)}"
                        f"\n> Time Limit: {currentChallenge.challengeDuration}"+
                        f"\n> Rewards: {currentChallenge.challengeReward['reward']} {rewDict[currentChallenge.challengeReward['type']]}"+
                        f"\n\u200b\nThis challenge cannot be continued.\n*To start a new challenge, run the `;challenge mypass` command again.*\n\u200b",
                    inline=False)

            if currentChallenge and currentChallenge.challengeProgress['status'] == 'inProgress':
                timeRemaining = (currentChallenge.challengeProgress['startTime'] + (currentChallenge.challengeDuration*86400)) - time.time()
                trashCost = round((timeRemaining / 3600)*30)
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

                embed.add_field(name=f"**YOU'RE WORKING ON THIS CHALLENGE...**",
                    value=f"```{currentChallenge.challengeDesc}```"+
                        f"\n> Current Progress: {numerize.numerize(currentChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(currentChallenge.challengeScore,1)}"
                        f"\n> Time Remaining: {timeRemaining_text}"+
                        f"\n> Rewards: {currentChallenge.challengeReward['reward']} {rewDict[currentChallenge.challengeReward['type']]}"+
                        f"\n> Trash Cost: {trashCost} <:logo_ATC:732967299853582366>"+
                        f"\n\u200b\nRemember to run the `;challenge mypass` command to update your stats and to complete challenges!\n\u200b",
                    inline=False)

            await ctx.send(embed = embed)
            return await cPass.savePass()     

    @challengepass.command()
    async def trash(self,ctx):
        """Trash my current challenge. Only usable with an active pass."""
        linked_accounts = await self.config.user(ctx.author).players()
        traDict = {'farm': 'The Farmer Track', 'war': 'The Warpath'}
        rewDict = {'challengePoints': 'Challenge Pass Points', 'atc': '<:logo_ATC:732967299853582366>'}

        if len(linked_accounts)==0:
            embed = await clash_embed(
                ctx=ctx,
                title="No accounts available.",
                message="Link your Clash of Clans account using `;cocset player` to be able to participate in the Ataraxy Challenge Pass.",
                color="fail")
            return await ctx.send(embed=embed)    
    
        user_accounts = []
        for account in linked_accounts:
            account = Member(ctx,account)
            if account.atxMemberStatus == 'member' and account.homeVillage['townHall']['thLevel'] >= 9:
                user_accounts.append(account)

        user_accounts.sort(key=lambda x:(x.homeVillage['townHall']['thLevel']),reverse=True)

        select_accounts = []
        for account in user_accounts:
            account_text = f"**{account.player}** ({account.tag})\n{th_emotes[int(account.homeVillage['townHall']['thLevel'])]} {account.homeVillage['townHall']['discordText']}\u3000<:Clan:825654825509322752> {account.clan['clan_info']['name']}"
            select_accounts.append(account_text)

        if len(select_accounts)==0:
            embed = await clash_embed(
                ctx=ctx,
                title="No eligible accounts.",
                message="You have no accounts eligible for the Ataraxy Challenge Pass. To be eligible, you need to be a member of our Clan and at least Townhall 9 or above.",
                color="fail")
            return await ctx.send(embed=embed)

        pass_selection = BotMultipleChoice(ctx,select_accounts,"Select an account you wish to trash a Challenge.")
        await pass_selection.run()

        if pass_selection.choice==None:
            return await pass_selection.quit(f"{ctx.author.mention}, request timed out.")
        else:
            account_index = select_accounts.index(pass_selection.choice)
            selected_account = user_accounts[account_index]

            await pass_selection.quit(f"{ctx.author.mention}, please wait...")

            cPass = challengePass(ctx,selected_account)
            if not cPass.atxChaTrack:
                embed = await clash_embed(
                    ctx=ctx,
                    title="No active Challenge Pass.",
                    message="This account doesn't have an active Challenge Pass. Run the command `;challenge mypass` to start one!",
                    color="fail")
                return await ctx.send(embed=embed)

            if cPass.atxChaTrack and not cPass.atxChaActiveChall:
                embed = await clash_embed(
                    ctx=ctx,
                    title="No active Challenges.",
                    message="You aren't working on any Challenges! Run the command `;challenge mypass` to start one!",
                    color="fail")
                return await ctx.send(embed=embed)

            if cPass.atxChaTrack and cPass.atxChaActiveChall:
                trashChallenge = Challenge(player=selected_account,track=cPass.atxChaTrack,challDict=cPass.atxChaActiveChall,commonStreak=cPass.atxChaCommonStreak)

                timeRemaining = (trashChallenge.challengeProgress['startTime'] + (trashChallenge.challengeDuration*86400)) - time.time()
                trashCost = round((timeRemaining / 3600)*30)
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
                    timeRemaining_text = "a few second(s) "

                bankBalance = await bank.get_balance(ctx.author)
                if trashCost > bankBalance:
                    embed = await clash_embed(
                        ctx=ctx,
                        title="Not enough money!",
                        message=f"You need {trashCost} <:logo_ATC:732967299853582366> to trash this challenge.",
                        color="fail")
                    return await ctx.send(embed=embed)

                trashChallenge.updateChallenge(trash=True)
                cPass.updatePass(trashChallenge.challengeToJson())

                await bank.withdraw_credits(ctx.author, trashCost)

                embed = await clash_embed(
                    ctx=ctx,
                    title=f"**Ataraxy Challenge Pass: {selected_account.player}** ({selected_account.tag})",
                    message=f"**Your Pass Track: `{traDict[cPass.atxChaTrack]}`**"+
                        f"\n\nYou spent {trashCost} <:logo_ATC:732967299853582366> to trash the below challenge.",
                    color="fail")

                embed.add_field(name=f"**>> CHALLENGE TRASHED! <<**",
                    value=f"```{trashChallenge.challengeDesc}```"+
                        f"\n> Current Progress: {numerize.numerize(trashChallenge.challengeProgress['currentScore'],1)} / {numerize.numerize(trashChallenge.challengeScore,0)}"
                        f"\n> Time Remaining: {timeRemaining_text}"+
                        f"\n> Rewards: {trashChallenge.challengeReward['reward']} {rewDict[trashChallenge.challengeReward['type']]}"+
                        f"\n\u200b\nThis challenge can no longer be continued. Run the `;challenge mypass` command to receive a new one!\n\u200b",
                    inline=False)

                await ctx.send(embed = embed)
                return await cPass.savePass()

    @challengepass.command(name='leaderboard', aliases=['lb'])
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.guild)
    async def cp_leaderboard(self,ctx,season="current"):
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
            return await ctx.send(f"{ctx.author.mention} an unknown error occurred, please try again later.")

        allPasses = []
        for clan in registered_clans:            
            clan = Clan(ctx,clan)
            for member in clan.members:
                try:
                    member = Member(ctx,member['tag'])
                    cPass = challengePass(ctx,member,season)
                except:
                    pass
                else:
                    if cPass.atxChaTrack:
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
                    'Points': cPass.atxChaPoints,
                    'C/M/T': f"{cPass.atxChaCompleted}/{cPass.atxChaMissed}/{cPass.atxChaTrashed}"
                    }
                farm_lb.append(lb_pass)
            if cPass.atxChaTrack == 'war':
                war_lb_position += 1
                lb_pass = {
                    'Pos': war_lb_position,
                    'Player': cPass.player,
                    'Points': cPass.atxChaPoints,
                    'C/M/T': f"{cPass.atxChaCompleted}/{cPass.atxChaMissed}/{cPass.atxChaTrashed}"}
                war_lb.append(lb_pass)

        embed = await clash_embed(
            ctx=ctx,
            title=f"Ataraxy Challenge Pass Leaderboard",
            message=f"Season: {season}\n*C: Completed / M: Missed / T: Trashed*")

        embed.add_field(name=f"**THE WARPATH**",
            value=f"```{tabulate(war_lb,headers='keys')}```",
            inline=False
            )
        embed.add_field(name="**THE FARMER LIFE**",
            value=f"```{tabulate(farm_lb,headers='keys')}```",
            inline=False
            )
        await ctx.send(embed=embed)
        return await init_message.delete()
    
    #@commands.command(name="clan")
    #async def atxclans(self, ctx, arg):
    #    """This does stuff!"""
    #    # Your code will go here
        
    #    api = "https://api.clashofclans.com/v1"
    #    header = {'Accept':'application/json','authorization':'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImE3NjBhZTVmLTMzNTUtNDdjMS1hYjk3LWNkNjQxM2ZmNDg5ZCIsImlhdCI6MTYxNjUwNTA3OCwic3ViIjoiZGV2ZWxvcGVyLzVlM2I2NDc1LTI5YzktNWFjNy1jZjA1LTcwZDAwYTRhNDI4NCIsInNjb3BlcyI6WyJjbGFzaCJdLCJsaW1pdHMiOlt7InRpZXIiOiJkZXZlbG9wZXIvc2lsdmVyIiwidHlwZSI6InRocm90dGxpbmcifSx7ImNpZHJzIjpbIjguNi44LjE5NCJdLCJ0eXBlIjoiY2xpZW50In1dfQ.lHLbwkVvuvFtsoJg9TCKMRbQCmUPf-V1mO4i1DrJGADPAP4HrGkaBI5PX-oPJqxVoVX8rKumT33GfDSBAJFPHw'}
        
    #    api_data = requests.get(api + "/clans/" + "%23" + arg,headers=header).json()
    #    clan_name = api_data['name']
        
    #    await ctx.send("this clan is {}".format(clan_name))