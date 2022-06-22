from numerize import numerize
#from atxcoc.resources.coc_resources import clashapi_player, clashapi_clan, clashapi_pverify, clashapi_leagueinfo, clashapi_cwl
from coc_resources import Clash_ClassError, Clash_NotMember, StatTooHigh, Clan, Player, PlayerVerify, Member, challengePass, Challenge, getTroops, getFile, clashJsonLock, clashapi_player, clashapi_clan, clashapi_pverify, clashapi_leagueinfo, clashapi_cwl
import asyncio
import requests
import sys
import os
import json
import datetime
import time
import pytz
import random

async def dataRefresh():
    with open(getFile('configdir'),"r") as configFile:
        configData = json.load(configFile)

    with open(getFile('seasons'),"r") as seasonsFile:
        seasonsData = json.load(seasonsFile)

    registered_clans = configData['828462461169696778']['GLOBAL']['clans']
    cg_status = configData['828462461169696778']['GLOBAL']['CGstatus']
    cg_series = configData['828462461169696778']['GLOBAL']['CGseries']

    print(f"Clan Games Status: {cg_status}")
    print(f"Clan Games Series: {cg_series}")

    #update new season
    new_season_id = []
    seasons_api = clashapi_leagueinfo(29000022,2)
    for season in seasons_api['items']:
        if season['id'] not in seasonsData['seasons']:
            new_season_id.append(season['id'])

    if len(new_season_id) > 0:
        if len(new_season_id) != 1:
            sys.exit("Error with season handling.")
    
        seasonsData['seasons'].extend(new_season_id)
        with open(getFile('seasons'),"w") as seasonsFile:
            json.dump(seasonsData,seasonsFile,indent=2)
    
        async with clashJsonLock('member'):
            with open(getFile('players'),"r") as dataFile:
                current_data = json.load(dataFile)
                current_data[new_season_id[0]] = current_data['current']
                current_data['current'] = {}
            with open(getFile('players'),"w") as dataFile:
                json.dump(current_data,dataFile,indent=2)

        async with clashJsonLock('war'):
            with open(getFile('warlog'),"r") as dataFile:
                current_data = json.load(dataFile)
                current_data[new_season_id[0]] = current_data['current']
                current_data['current'] = {}
            with open(getFile('warlog'),"w") as dataFile:
                json.dump(current_data,dataFile,indent=2)

        async with clashJsonLock('challengepass'):
            with open(getFile('challengepass'),"r") as dataFile:
                current_data = json.load(dataFile)
                current_data[new_season_id[0]] = current_data['current']
                current_data['current'] = {}
            with open(getFile('challengepass'),"w") as dataFile:
                json.dump(current_data,dataFile,indent=2)

    with open(getFile('players'),"r") as dataFile:
        current_members = list(json.load(dataFile)['current'].keys())

    clan_members = []

    for clan in registered_clans:        
        clan = Clan(ctx=None,clan_tag=clan)
        clan.GetClassicWar()
        clan.GetWarLeagues()
        print(f"Clan initialized: {clan.tag}")

        for member in clan.members:
            clan_members.append(member['tag'])

        new_members = [member for member in clan_members if member not in current_members]

        print(f"Checking for new members: {clan.tag}")

        for player in new_members:
            player = Member(ctx=None,player_tag=player)
            current_members.append(player.tag)
            print(f"New Member: {player.tag} {player.player}")
            player.newMember()
            await player.saveData(force=True)

        print(f"New members updated: {clan.tag}")
        
        await clan.ClanWarUpdate()
        print(f"War update complete: {clan.tag}")


    print(f"Initializing member update.")

    for player in current_members:
        player = Member(ctx=None,player_tag=player)

        if player.atxMemberStatus == 'member':
            if player.tag not in clan_members:
                print(f"Player Left: {player.tag} {player.player}")
                #cPass = challengePass(ctx=None,member=player)
                #if cPass.atxChaTrack and cPass.atxChaActiveChall:
                #    trashChallenge = Challenge(player=player,track=cPass.atxChaTrack,challDict=cPass.atxChaActiveChall,commonStreak=cPass.atxChaCommonStreak)
                #    trashChallenge.updateChallenge(trash=True)
                #    cPass.updatePass(trashChallenge.challengeToJson())
                #    cPass.atxChaPoints = cPass.atxChaPoints - (cPass.atxChaPoints * 0.25)
                #    await cPass.savePass()

                player.inactivateMember()
                await player.saveData(force=True)                    
                if cg_status:
                    await player.updateClanGames(cg_series,"remove")                    
            else:
                player.updateStats()
                await player.saveData()
                if cg_status:
                    await player.updateClanGames(cg_series,"update")

        if player.atxMemberStatus == 'pastMember' and player.tag in clan_members:
            print(f"New Member: {player.tag} {player.player}")
            player.newMember()
            await player.saveData(force=True)
    
    print(f"Ataraxy member update complete.")

if __name__ == "__main__":
    print(f"Initalizing...")
    asyncio.run(dataRefresh())