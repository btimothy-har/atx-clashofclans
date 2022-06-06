from numerize import numerize
import asyncio
import requests
import sys
import os
import json
import datetime
import time
import pytz
import random

cogdir = os.path.dirname(__file__)

with open(os.path.join(cogdir,'data_resources.json'),'r') as dataResourceFile:
    dataResource = json.load(dataResourceFile)
    dataFiles = dataResource['dataFiles']
    apiKeys = dataResource['apiKeys']
    serverIDs = dataResource['serverIDs']

troops = {
    'elixir_troops':["Barbarian","Archer","Giant","Goblin","Wall Breaker","Balloon","Wizard","Healer","Dragon","P.E.K.K.A","Baby Dragon","Miner","Electro Dragon","Yeti"],
    'dark_troops':["Minion","Hog Rider","Valkyrie","Golem","Witch","Lava Hound","Bowler","Ice Golem","Headhunter"],
    'siege_machines':["Wall Wrecker", "Battle Blimp", "Stone Slammer", "Siege Barracks", "Log Launcher"],
    'hero_pets':["L.A.S.S.I", "Electro Owl", "Mighty Yak", "Unicorn"],
    'super_troops':["Super Barbarian","Super Archer","Super Giant","Sneaky Goblin","Super Wall Breaker","Rocket Balloon","Super Wizard","Super Dragon","Inferno Dragon","Super Minion","Super Valkyrie","Super Witch","Ice Hound","Super Bowler"],
    'elixir_spells':["Lightning Spell","Healing Spell","Rage Spell","Jump Spell","Freeze Spell","Clone Spell","Invisibility Spell"],
    'dark_spells':["Poison Spell","Earthquake Spell","Haste Spell","Skeleton Spell","Bat Spell"]
    }

maxHomeLevels = {
    1:[0,0,0],
    2:[3,0,0],
    3:[8,0,0],
    4:[12,0,0],
    5:[17,4,0],
    6:[22,7,0],
    7:[36,12,5],
    8:[56,19,10],
    9:[77,30,60],
    10:[99,48,80],
    11:[124,59,120],
    12:[160,67,170],
    13:[191,73,225],
    14:[245,75,245]
    }

clan_roles = {
    "leader":"Leader",
    "coLeader":"Co-Leader",
    "admin":"Elder",
    "member":"Member",
    "None":None
}

fileLocks = {
    'member': asyncio.Lock(),
    'war': asyncio.Lock(),
    'cwl': asyncio.Lock(),
    'clangames': asyncio.Lock(),
    'challengepass': asyncio.Lock()
    }

api_url = apiKeys['Url']
api_key = apiKeys['Key']
a_header = {'Accept':'application/json','authorization':'Bearer '+api_key}

error_definitions = {
    400:'Incorrect parameters were provided',
    403:'Authentication error. Please verify the API Key being used.',
    404:'Information was not found for this clan/player.',
    429:'Request limits exceeded. Please try again later.',
    500:'Unknown error occurred.',
    503:'Clash of Clans API is currently under maintenance.',
    504:'Request timed out.'
    } 

class Clash_APIError(Exception):
    def __init__(self,error_code,end_point):
        self.error_code = error_code
        self.error_description = error_definitions.get(error_code,'Unknown API error.')
        self.end_point = end_point
        
    def __str__(self):
        return f"Clash API Error Code [{self.error_code}]: {self.error_description}. Attempted end point: {self.end_point}"

def getTroops(cat):
    if cat not in list(troops.keys()):
        return None
    return troops[cat]

def getMaxTroops(townhall):
    return maxHomeLevels[townhall]

def getFile(cat):
    if cat not in list(dataFiles.keys()):
        return None
    return dataFiles[cat]

def getServerID(cat):
    if cat not in list(serverIDs.keys()):
        return None
    return serverIDs[cat]

def clashJsonLock(locktype):
    if locktype not in list(fileLocks.keys()):
        fileLocks[locktype] = asyncio.Lock()
    return fileLocks[locktype]

def api_return(request,result):
    if result.status_code == 200:
        return result.json()
    else:
        raise Clash_APIError(error_code=result.status_code,end_point=request)

def clashapi_player(player_tag):
    api_request = f"{api_url}/players/%23{player_tag.upper().replace('#','').replace('O','0')}"
    api_result = requests.get(api_request,headers=a_header)
    return api_return(api_request,api_result)

def clashapi_pverify(p_tag,p_token):
    api_request = f"{api_url}/players/%23{p_tag.upper().replace('#','').replace('O','0')}/verifytoken"
    api_result = requests.post(api_request,json={"token":p_token},headers=a_header)
    return api_return(api_request,api_result)

def clashapi_clan(clan_tag,req_id=0):
    fc_tag = clan_tag.upper().replace('#','').replace('O','0')
    api_request = {
        #Get clan information
        0:f"{api_url}/clans/%23{fc_tag}",
        #Get clan members
        1:f"{api_url}/clans/%23{fc_tag}/members",
        #Get clan war log
        2:f"{api_url}/clans/%23{fc_tag}/warlog?limit=30",
        #Get clan current war
        3:f"{api_url}/clans/%23{fc_tag}/currentwar",
        #Get CWL group information
        4:f"{api_url}/clans/%23{fc_tag}/currentwar/leaguegroup"
        }
    api_result = requests.get(api_request[req_id],headers=a_header)
    return api_return(api_request[req_id],api_result)

def clashapi_cwl(w_tag):
    api_request = f"{api_url}/clanwarleagues/wars/%23{w_tag.upper().replace('#','').replace('O','0')}"
    api_result = requests.get(api_request,headers=a_header)
    return api_return(api_request,api_result)

def clashapi_leagueinfo(league_id=29000022,req_id=0):
    api_request = {
        #List all leagues
        0:f"{api_url}/leagues",
        #Get league information
        1:f"{api_url}/leagues/{league_id}",
        #Get league seasons
        2:f"{api_url}/leagues/{league_id}/seasons"
        }
    api_result = requests.get(api_request[req_id],headers=a_header)
    return api_return(api_request,api_result)
    
class Clash_ClassError(Exception):
    def __init__(self):
        self.message = "An API error ocurred when attempting to retrieve data from the Clash API."
    def __str__(self):
        return f"Clash API Error. Please refer to admin logs."

class Clash_NotMember(Exception):
    def __init__(self):
        self.message = "This player is not a current member of Ataraxy."
    def __str__(self):
        return f"This player is not a current member of Ataraxy."

class StatTooHigh(Exception):
    def __init__(self):
        self.message = "Achievement Stat in COC has hit maximum."
    def __str__(self):
        return f"Achievement Stat in COC has hit maximum."

class Clan:
    def __init__(self,ctx,clan_tag):
        tag = clan_tag.upper().replace('#','').replace('O','0')
        
        #check if is valid playertag:
        try:
            api_clan = clashapi_clan(tag,0)
        except:
            raise Clash_ClassError
        else:
            self.tag = api_clan['tag']
            self.clan = api_clan['name']
            self.badges = api_clan.get('badgeUrls',None)
            self.description = api_clan.get('description',None)
            self.level = api_clan.get('clanLevel',0)
            self.locale = {
                "location": api_clan.get('location',{"id":"","name":"","isCountry":""}),
                "language": api_clan.get('chatLanguage',{"id":"","name":"","languageCode":""})
                }
            self.recruitment = {
                "setting": api_clan['type'],
                "requirements": {
                    "townHall": api_clan.get('requiredTownhallLevel',0),
                    "homeTrophies": api_clan.get('requiredTrophies',0),
                    "builderTrophies": api_clan.get('requiredVersusTrophies',0),
                    }
                }
            self.gameStats = {
                "trophyScore": api_clan.get('clanPoints',0),
                "builderScore": api_clan.get('clanVersusPoints',0),
            }
            self.warInfo = {
                "publicWarLog": api_clan['isWarLogPublic'],
                "warFrequency": api_clan.get('warFrequency',None),
                "warWinStreak": api_clan.get('warWinStreak',None),
                "warStats": {
                    "wins": api_clan.get('warWins',0),
                    "ties": api_clan.get('warTies',0),
                    "losses": api_clan.get('warLosses',0),
                    },
                "classicWar": {
                    "currentWar": {},
                    "warLog": []
                    },
                "warLeague": {
                    "league": api_clan.get('warLeague',{}),
                    "currentGroup": {}
                    },
                }
            self.members = api_clan.get('memberList',[])

    def GetClassicWar(self):
        try:
            api_clanWarLog = clashapi_clan(self.tag,2)
        except:
            api_clanWarLog = {}
        try:
            api_clanCurrentWar = clashapi_clan(self.tag,3)
        except:
            api_clanCurrentWar = {}
        self.warInfo['classicWar']['currentWar'] = api_clanCurrentWar
        self.warInfo['classicWar']['warLog'] = api_clanWarLog.get('items',[])

    def GetWarLeagues(self):
        try:
            api_clanWarLeague = clashapi_clan(self.tag,4)
        except:
            api_clanWarLeague = {}
        self.warInfo['warLeague']['currentGroup'] = api_clanWarLeague

    async def ClanWarUpdate(self):
        self.GetClassicWar()
        self.GetWarLeagues()
        warCount = 0
        warUpdates = []
        cwlWarProgress = []
        try:
            if self.warInfo['classicWar']['currentWar']['state']=='warEnded' and isinstance(self.warInfo['classicWar']['currentWar']['opponent']['tag'],str):
                self.warInfo['classicWar']['currentWar']['warType'] = 'classic'
                warUpdates.append(self.warInfo['classicWar']['currentWar'])
        except:
            pass
        try:
            for cwlRound in self.warInfo['warLeague']['currentGroup']['rounds']:
                for cwlWar in cwlRound['warTags']:
                    cwlWar = clashapi_cwl(cwlWar)
                    if cwlWar['state']=='warEnded' and isinstance(cwlWar['opponent']['tag'],str) and (cwlWar['clan']['tag'] == self.tag or cwlWar['opponent']['tag'] == self.tag):
                        cwlWar['warType'] = 'cwl'
                        warUpdates.append(cwlWar)
        except:
            pass

        if len(warUpdates) >= 1:
            for war in warUpdates:
                warContinue = True
                if self.tag == war['opponent']['tag']:
                    clanPos = 'opponent'
                    oppoPos = 'clan'
                else:                                
                    clanPos = 'clan'
                    oppoPos = 'opponent'

                try:
                    with open(getFile('warlog'),"r") as dataFile:
                        warLog = json.load(dataFile)

                except:
                    warLog = {
                        "current": {
                            self.tag: []
                            }
                        }

                for season, clanLogs in list(warLog.items()):
                    for clanW, logs in list(clanLogs.items()):
                        if clanW == self.tag:
                            for warRecord in logs:
                                if war[oppoPos]['tag'] == warRecord['opponent']['tag'] and war['endTime'] == warRecord['endTime']:
                                    warContinue = False

                if warContinue:
                    warCount += 1
                    if war[clanPos]['stars'] > war[oppoPos]['stars']:
                        warResult = "win"
                    elif war[clanPos]['stars'] < war[oppoPos]['stars']:
                        warResult = "lose"
                    else:
                        if war[clanPos]['destructionPercentage'] > war[oppoPos]['destructionPercentage']:
                            warResult = "win"
                        elif war[clanPos]['destructionPercentage'] < war[oppoPos]['destructionPercentage']:
                            warResult = "lose"
                        else:
                            warResult = "tie"
                    try:
                        warLog['current'][self.tag] = warLog['current'][self.tag]
                    except KeyError:
                        warLog['current'][self.tag] = []
                    finally:
                        newWarLog = {
                            "wartype": war['warType'],
                            "warSize": war['teamSize'],
                            "opponent": {
                                "tag": war[oppoPos]['tag'],
                                "name": war[oppoPos]['name']
                                },
                            "results": {
                                "result": warResult,
                                "attackStars": war[clanPos]['stars'],
                                "attackDestruction": war[clanPos]['destructionPercentage'],
                                "defenseStars": war[oppoPos]['stars'],
                                "defenseDestruction": war[oppoPos]['destructionPercentage']
                                },
                            "startTime": war['startTime'],
                            "endTime": war['endTime']
                            }
                        warLog['current'][self.tag].append(newWarLog)

                    for participant in war[clanPos]['members']:
                        warAttacks = {"classic":2,"cwl":1}
                        attackedTHs = []
                        player = Member(self,participant['tag'])

                        participantStats = {
                            "warResult": warResult,
                            "attackStars":0,
                            "attackDestruction":0,
                            "defenseStars":participant.get('bestOpponentAttack',{}).get('stars',0),
                            "defenseDestruction":participant.get('bestOpponentAttack',{}).get('destructionPercentage',0),
                            "attacks":len(participant.get('attacks',[])),
                            "missedAttacks":warAttacks[war['warType']] - len(participant.get('attacks',[])),
                            "attackedTHs": []
                            }

                        for opponent in war[oppoPos]['members']:
                            if opponent['opponentAttacks'] > 0:
                                if opponent['bestOpponentAttack']['attackerTag'] == participant['tag']:
                                    participantStats['attackStars'] += opponent['bestOpponentAttack']['stars']
                                    participantStats['attackDestruction'] += opponent['bestOpponentAttack']['destructionPercentage']
                                    attackedTHs.append(opponent['townhallLevel'])

                        participantStats['attackedTHs'] = attackedTHs

                        await player.updateWar(war,clanPos,oppoPos,participantStats)
                        if war['warType'] == 'cwl':
                            await player.saveCwlData(self.tag)

                    async with clashJsonLock('war'):
                        with open(getFile('warlog'),"w") as dataFile:
                            json.dump(warLog,dataFile,indent=2)
        return warCount

class Player():
    #class to gather and compile stats for players from API
    def __init__(self,ctx,player_tag):
        tag = player_tag.upper().replace('#','').replace('O','0')
        self.ctx = ctx        
        #check if is valid playertag:
        try:
            api_player = clashapi_player(tag)
        except:
            raise Clash_ClassError
        else:
            if api_player['townHallLevel'] >= 12:
                townhall_text = f"**{api_player['townHallLevel']}**-{api_player['townHallWeaponLevel']}"
            else:
                townhall_text = f"**{api_player['townHallLevel']}**"

            #build troop list
            elixirTroops = []
            darkTroops = []
            siegeMachines = []
            heroPets = []
            superTroops = []        
            builderTroops = []
            for troop in api_player['troops']:
                if troop['village'] == 'home':
                    if troop['name'] in getTroops('elixir_troops'):
                        elixirTroops.append(troop)
                    if troop['name'] in getTroops('dark_troops'):
                        darkTroops.append(troop)
                    if troop['name'] in getTroops('siege_machines'):
                        siegeMachines.append(troop)
                    if troop['name'] in getTroops('hero_pets'):
                        heroPets.append(troop)
                    if troop['name'] in getTroops('super_troops'):
                        superTroops.append(troop)                  
                if troop['village'] == 'builderBase':
                    builderTroops.append(troop)

            #build spell list
            elixirSpells = []
            darkSpells = []
            for spell in api_player['spells']:
                if spell['name'] in getTroops('elixir_spells'):
                    elixirSpells.append(spell)
                if spell['name'] in getTroops('dark_spells'):
                    darkSpells.append(spell)

            #build hero list
            barbarianKing = 0
            archerQueen = 0
            grandWarden = 0
            royalChampion = 0
            battleMachine = 0
            for hero in api_player['heroes']:
                if hero['name'] == 'Barbarian King':
                    barbarianKing = hero['level']
                if hero['name'] == 'Archer Queen':
                    archerQueen = hero['level']
                if hero['name'] == 'Grand Warden':
                    grandWarden = hero['level']
                if hero['name'] == 'Royal Champion':
                    royalChampion = hero['level']
                if hero['name'] == 'Battle Machine':
                    battleMachine = hero['level']

            #build achievement list
            homeAchievements = []
            builderAchievements = []
            for achievement in api_player['achievements']:
                if achievement['village'] == 'home':
                    homeAchievements.append(achievement)
                if achievement['village'] == 'builderBase':
                    builderAchievements.append(achievement)

            self.timestamp = time.time()
            self.tag = api_player['tag']
            self.player = api_player['name']
            self.exp = api_player['expLevel']
            self.clan = {
                'clan_info': api_player.get('clan',"No Clan"),
                'role': clan_roles[api_player.get('role',"None")],
                'donations': api_player.get('donations',0),
                'donationsRcvd': api_player.get('donationsReceived',0)
                }
            self.homeVillage = {
                'warPreference': api_player.get('warPreference',"out"),
                "townHall": {
                    'discordText': townhall_text,
                    'thLevel': api_player['townHallLevel'],
                    'thWeapon': api_player.get('townHallWeaponLevel',None)
                    },
                "league": {
                    "attacksWon": api_player['attackWins'],
                    "defensesWon": api_player['defenseWins'],
                    "trophies": api_player.get('trophies',0),
                    "bestTrophies": api_player.get('bestTrophies',0),
                    "leagueDetails": api_player.get('league',None),
                    "legendLeague": api_player.get('legendStatistics',None)
                    },
                "heroes": {
                    "barbarianKing": barbarianKing,
                    "archerQueen": archerQueen,
                    "grandWarden": grandWarden,
                    "royalChampion": royalChampion
                    },
                "troops": {
                    "elixirTroops": elixirTroops,
                    "darkTroops": darkTroops,
                    "siegeMachines": siegeMachines,
                    "pets": heroPets,
                    "superTroops": superTroops,
                    },
                "spells": {
                    "elixirSpells": elixirSpells,
                    "darkSpells": darkSpells
                    },
                "achievements": homeAchievements,
                }
            self.builderBase = {
                "builderHall": api_player.get('builderHallLevel',None),
                "league": {
                    "trophies": api_player.get('versusTrophies',0),
                    "bestTrophies": api_player.get('bestVersusTrophies',0),
                    },
                "heroes": {
                    "battleMachine": battleMachine,
                    },
                "troops": builderTroops,
                "achievements": builderAchievements
                }

class PlayerVerify(Player):
    def __init__(self,ctx,player_tag,api_token):
        self.ctx = ctx
        Player.__init__(self,self.ctx,player_tag)

        try:
            api_verify = clashapi_pverify(self.tag,api_token)
        except:
            raise Clash_ClassError
        else:
            self.verifyTag = api_verify.get('tag',"")
            self.verifyToken = api_verify.get('token',"")
            self.verifyStatus = api_verify.get('status',"")

class Member(Player):
    #class to gather and compile stats from ATX Json
    def __init__(self,ctx,player_tag):
        self.ctx = ctx
        Player.__init__(self,self.ctx,player_tag)
        
        with open(getFile('players'),"r") as dataFile:
            playerJson = json.load(dataFile)
        
        try:
            playerJsonExtract = playerJson['current'][self.tag]
        except:
            self.atxMemberStatus = "notFound"
            self.atxRank = "none"
            self.atxLastUpdated = time.time()
            self.atxLastSeen = {
                "clans": [],
                "timer": 0,
                }
            self.atxDonations = {
                "received": {
                    "season": 0,
                    "lastUpdate": 0
                },
                "sent": {
                    "season": 0,
                    "lastUpdate": 0
                    }
                }
            self.atxLoot = {
                "gold": {
                    "season": 0,
                    "lastUpdate": 0
                    },
                "elixir": {
                    "season": 0,
                    "lastUpdate": 0
                    },
                "darkElixir": {
                    "season": 0,
                    "lastUpdate": 0
                    }
                }
            self.atxClanCapital = {
                "goldContributed": {
                    "season": 0,
                    "lastUpdate": 0
                    },
                "goldLooted": {
                    "season": 0,
                    "lastUpdate": 0
                    }
                }
            self.atxWar = {
                "registrationStatus": "No",
                "warPriority": 0,
                "cwlStars": 0,
                "warStars": 0,
                "missedAttacks": 0
                }
            self.atxWarLog = []
        else:
            self.atxMemberStatus = playerJsonExtract.get('memberStatus','notFound')
            self.atxRank = playerJsonExtract.get('rank','none')
            self.atxLastUpdated = playerJsonExtract.get('lastUpdated',0)
            self.atxLastSeen = playerJsonExtract.get('lastSeen',{"clans":[],"timer":0})
            self.atxDonations = playerJsonExtract.get('donations',{"received": {"season": 0,"lastUpdate": 0},"sent": {"season": 0,"lastUpdate": 0}})
            self.atxLoot = playerJsonExtract.get('loot',{"gold": {"season": 0,"lastUpdate": 0},"elixir": {"season": 0,"lastUpdate": 0},"darkElixir": {"season": 0,"lastUpdate": 0}})
            self.atxClanCapital = playerJsonExtract.get('clanCapital',{"goldContributed": {"season": 0,"lastUpdate": 0},"goldLooted": {"season": 0, "lastUpdate": 0}})
            self.atxWar = playerJsonExtract.get('war',{"registrationStatus": "No","warPriority": 0,"cwlStars": 0,"warStars": 0,"missedAttacks": 0})
            self.atxWarLog = playerJsonExtract.get('warLog',[])

    def updateStats(self):
        #only update stats for members
        if self.atxMemberStatus=='member':
            if self.clan['clan_info']['tag'] not in self.atxLastSeen['clans']:
                self.atxLastSeen["clans"].append(self.clan['clan_info']['tag'])
            self.atxLastSeen['timer'] += (self.timestamp - self.atxLastUpdated)

            if self.clan['role']=='Leader' or self.clan['role']=='Co-Leader':
                self.atxRank = 'Leader'
            elif self.atxRank=='Elder':
                self.atxRank = 'Elder'
            else:
                self.atxRank = 'none'

            for achievement in self.homeVillage['achievements']:
                if achievement['name'] == "Gold Grab":
                    gold_total = achievement['value']
                if achievement['name'] == "Elixir Escapade": 
                    elixir_total = achievement['value']
                if achievement['name'] == "Heroic Heist":
                    darkelixir_total = achievement['value']
                if achievement['name'] == "Most Valuable Clanmate":
                    capitalgold_contributed_total = achievement['value']
                if achievement['name'] == "Aggressive Capitalism":
                    capitalgold_looted_total = achievement['value']

            if self.clan['donationsRcvd'] >= self.atxDonations['received']['lastUpdate']:
                newDonationsRcvd = self.clan['donationsRcvd'] - self.atxDonations['received']['lastUpdate']
            else:
                newDonationsRcvd = self.clan['donationsRcvd']

            if self.clan['donations'] >= self.atxDonations['sent']['lastUpdate']:
                newDonationsSent = self.clan['donations'] - self.atxDonations['sent']['lastUpdate']
            else:
                newDonationsSent = self.clan['donations']

            self.atxDonations['received']['season'] += newDonationsRcvd
            self.atxDonations['received']['lastUpdate'] = self.clan['donationsRcvd']
            self.atxDonations['sent']['season'] += newDonationsSent
            self.atxDonations['sent']['lastUpdate'] = self.clan['donations']

            self.atxLoot['gold']['season'] += gold_total - self.atxLoot['gold']['lastUpdate']
            self.atxLoot['gold']['lastUpdate'] = gold_total

            self.atxLoot['elixir']['season'] += elixir_total - self.atxLoot['elixir']['lastUpdate']
            self.atxLoot['elixir']['lastUpdate'] = elixir_total
        
            self.atxLoot['darkElixir']['season'] += darkelixir_total - self.atxLoot['darkElixir']['lastUpdate']
            self.atxLoot['darkElixir']['lastUpdate'] = darkelixir_total

            self.atxClanCapital['goldContributed']['season'] += capitalgold_contributed_total - self.atxClanCapital['goldContributed']['lastUpdate']
            self.atxClanCapital['goldContributed']['lastUpdate'] = capitalgold_contributed_total

            self.atxClanCapital['goldLooted']['season'] += capitalgold_looted_total - self.atxClanCapital['goldLooted']['lastUpdate']
            self.atxClanCapital['goldLooted']['lastUpdate'] = capitalgold_looted_total

            if self.homeVillage['warPreference'] == "in":
                self.atxWar['registrationStatus'] = "Yes"
            else:
                self.atxWar['registrationStatus'] = "No"

    def newMember(self):
        for achievement in self.homeVillage['achievements']:
            if achievement['name'] == "Gold Grab":
                gold_total = achievement['value']
            if achievement['name'] == "Elixir Escapade": 
                elixir_total = achievement['value']
            if achievement['name'] == "Heroic Heist":
                darkelixir_total = achievement['value']
            if achievement['name'] == "Most Valuable Clanmate":
                capitalgold_contributed_total = achievement['value']
            if achievement['name'] == "Aggressive Capitalism":
                capitalgold_looted_total = achievement['value']

        #reset these to 0 as COC resets donation counts to 0 when someone changes clans
        self.atxDonations['received']['lastUpdate'] = 0
        self.atxDonations['sent']['lastUpdate'] = 0

        #set new baselines for loot totals
        self.atxLoot['gold']['lastUpdate'] = gold_total
        self.atxLoot['elixir']['lastUpdate'] = elixir_total
        self.atxLoot['darkElixir']['lastUpdate'] = darkelixir_total
        self.atxClanCapital['goldContributed']['lastUpdate'] = capitalgold_contributed_total
        self.atxClanCapital['goldLooted']['lastUpdate'] = capitalgold_looted_total

        self.atxMemberStatus = 'member'
        self.updateStats()

    def inactivateMember(self):
        self.atxMemberStatus = 'pastMember'

    async def updateWar(self,war,clanPos,oppoPos,stats):
        logData = {
            "warType": war['warType'],
            "result": stats['warResult'],
            "clan": {
                "tag": war[clanPos]['tag'],
                "name": war[clanPos]['name']
                },
            "opponent": {
                "tag": war[oppoPos]['tag'],
                "name": war[oppoPos]['name']
                },
            "attackStars": stats['attackStars'],
            "attackDestruction": stats['attackDestruction'],
            "defenseStars": stats['defenseStars'],
            "defenseDestruction": stats['defenseDestruction'],
            "missedAttacks": stats['missedAttacks'],
            }

        if war['warType'] == 'cwl':
            self.getCWLstats(logData['clan']['tag'])
            priorityChange = 0-3
            if stats['warResult'] == 'win':
                priorityChange += 0
            else:
                priorityChange -= 1
            if stats['missedAttacks'] == 0:
                priorityChange += 1
            if stats['attackStars'] >= 2:
                if stats['attackStars'] == 2:
                    priorityChange += 1
                if stats['attackStars'] == 3:
                    priorityChange += 2
                priorityChange += (int(max(stats['attackedTHs'])) - int(self.homeVillage['townHall']['thLevel']))

            self.atxWar['cwlStars'] += (stats['attackStars']-stats['defenseStars'])
            self.atxCwlPriority += priorityChange
            self.atxCwlTotalStars += stats['attackStars']
            #self.atxCwlWarLog.append(logData)

        else:
            priorityChange = 0
            #if self.clan['role']=='Elder' and stats['warResult']=='win':
            #    priorityChange += 1
            if stats['warResult']=='win':
                priorityChange += 1
            else:
                priorityChange -= 1
            if stats['attackStars'] >= 3:
                priorityChange += 1
            if stats['attackStars'] >= 6:
                priorityChange += 1
            if stats['missedAttacks'] >= 1:
                priorityChange -= 3

            self.atxWar['warPriority'] += priorityChange
            self.atxWar['warStars'] += (stats['attackStars']-stats['defenseStars'])
        
        self.atxWar['missedAttacks'] += stats['missedAttacks']           
        self.atxWarLog.append(logData)     
        await self.saveData(force=True)

    async def updateClanGames(self,clan,series,action):
        async with clashJsonLock('clangames'):
            with open(getFile('clangames'),"r") as dataFile:
                jsonData = json.load(dataFile)

            if action=="remove":
            #if departing member, disqualify from clangames
                for participant in jsonData[series][clan.tag]:
                    if participant['tag'] == self.tag:
                        participant['status'] = "disqualified"
                        return 1
                return 0

            if action=="update":
                leaderboard = []
                for participant in jsonData[series][clan.tag]:
                    leaderboard.append(participant['games_pos'])

                last_rank = max(leaderboard)

                for participant in jsonData[series][clan.tag]:
                    if participant['tag'] == self.tag and participant['games_pos'] == 0:
                        for achievement in self.homeVillage['achievements']:
                            if achievement['name'] == "Games Champion":
                                new_games_pts = achievement['value']

                        if (new_games_pts - participant['init_pts']) >= 4000:
                            participant['games_pts'] = 4000
                            participant['games_pos'] = last_rank + 1
                            last_rank += 1
                        else:
                            participant['games_pts'] = new_games_pts - participant['init_pts']
                        return 1
                return 0

            with open(getFile('clangames'),"w") as dataFile:
                return json.dump(jsonData,dataFile,indent=2)

    async def saveData(self,force=False):
        if not force and (self.atxLastUpdated + 180) > time.time(): #if save is called within 5mins after the last update, don't save
            return
        async with clashJsonLock('member'):
            #if timestamp data is more than 3mins old. we call this within the lock so that refreshed data immediately gets pushed to json.
            if (self.timestamp + 180) < time.time(): 
                self.__init__(self.ctx,self.tag)
                self.updateStats()
            with open(getFile('players'),"r") as dataFile:
                jsonData = json.load(dataFile)
            jsonData['current'][self.tag] = {
                "tag": self.tag,
                "player": self.player,
                "memberStatus": self.atxMemberStatus,
                "rank": self.atxRank,
                "lastUpdated": self.timestamp,
                "lastSeen": self.atxLastSeen,
                "donations": self.atxDonations,
                "loot": self.atxLoot,
                "clanCapital": self.atxClanCapital,
                "war": self.atxWar,
                "warLog": self.atxWarLog,
                }
            with open(getFile('players'),"w") as dataFile:
                return json.dump(jsonData,dataFile,indent=2)

    def getCWLstats(self,cwlClan):
        try:
            with open(getFile('cwlroster'),"r") as dataFile:
                cwlData = json.load(dataFile)
            cwlPlayer = cwlData[cwlClan][self.tag]
        except:
            self.atxCwlOrder = 0
            self.atxCwlPriority = 0
            self.atxCwlTotalStars = 0
            #self.atxCwlWars = 0
            #self.atxCwlWarLog = []
        else:
            self.atxCwlOrder = cwlPlayer['regOrder']
            self.atxCwlPriority = cwlPlayer['priority']
            self.atxCwlTotalStars = cwlPlayer['totalStars']
            #self.atxCwlWars = len(cwlData['warLog'])
            #self.atxCwlWarLog = cwlData['warLog']

    async def saveCwlData(self,cwlClan):
        async with clashJsonLock('cwl'):
            try:
                with open(getFile('cwlroster'),"r") as dataFile:
                    cwlData = json.load(dataFile)
            except:
                cwlData = {}

            try:
                cwlClanData = cwlData[cwlClan]
            except KeyError:
                cwlData = {cwlClan: {} }

            cwlData[cwlClan][self.tag] = {
                'tag': self.tag,
                'player': self.player,
                'regOrder': self.atxCwlOrder,
                'priority': self.atxCwlPriority,
                'totalStars': self.atxCwlTotalStars,
                #'warLog': self.atxCwlWarLog
                }
            with open(getFile('cwlroster'),"w") as dataFile:
                json.dump(cwlData,dataFile,indent=2)

class challengePass():
    #separate class for the Challenge Pass, exclusive to members only.
    def __init__(self,ctx,member,season):
        self.ctx = ctx
        self.memberStatus = member.atxMemberStatus
        self.tag = member.tag
        self.player = member.player
        self.season = season

        if self.memberStatus != 'member':
            raise Clash_NotMember
    
        try:
            with open(getFile('challengepass'),"r") as dataFile:
                challengeJson = json.load(dataFile)
        except FileNotFoundError:
            init_data = {}
            init_data['current'] = {}
            with open(getFile('challengepass'),"w") as dataFile:
                json.dump(init_data,dataFile,indent=2)
        
        try:
            challengeJson[self.season][self.tag]
        except:
            self.atxChaTrack = ""
            self.atxChaPoints = 0
            self.atxChaCompleted = 0
            self.atxChaMissed = 0
            self.atxChaTrashed = 0
            self.atxChaCommonStreak = 0
            self.atxChaActiveChall = None
            self.atxChaCompletedChalls = []
        else:
            self.atxChaTrack = challengeJson[self.season][self.tag]['track']
            self.atxChaPoints = challengeJson[self.season][self.tag]['totalPoints']
            self.atxChaCompleted = challengeJson[self.season][self.tag]['completed']
            self.atxChaMissed = challengeJson[self.season][self.tag]['missed']
            self.atxChaTrashed = challengeJson[self.season][self.tag]['trashed']
            self.atxChaCommonStreak = challengeJson[self.season][self.tag]['commonStreak']
            self.atxChaActiveChall = challengeJson[self.season][self.tag]['activeChallenge']
            self.atxChaCompletedChalls = challengeJson[self.season][self.tag]['completedChallenges']

    def updatePass(self,activeChallenge):
        if activeChallenge['progress']['status'] == 'completed':
            if activeChallenge['reward']['type'] == 'challengePoints':
                self.atxChaPoints += activeChallenge['reward']['reward']
                self.atxChaCommonStreak = 0
            if activeChallenge['reward']['type'] != 'challengePoints':
                self.atxChaCommonStreak += 1
            self.atxChaCompleted += 1
            self.atxChaCompletedChalls.append(activeChallenge)
            self.atxChaActiveChall = None

        if activeChallenge['progress']['status'] == 'missed':
            if activeChallenge['reward']['type'] != 'challengePoints':
                self.atxChaCommonStreak += 0
            self.atxChaMissed += 1
            self.atxChaCompletedChalls.append(activeChallenge)
            self.atxChaActiveChall = None

        if activeChallenge['progress']['status'] == 'trashed':
            if activeChallenge['reward']['type'] != 'challengePoints':
                self.atxChaCommonStreak += 0
            self.atxChaTrashed += 1
            self.atxChaCompletedChalls.append(activeChallenge)
            self.atxChaActiveChall = None

        if activeChallenge['progress']['status'] == 'inProgress':
            self.atxChaActiveChall = activeChallenge

    async def savePass(self):
        if self.season=='current':
            async with clashJsonLock('challengepass'):
                with open(getFile('challengepass'),"r") as dataFile:
                    challengeJson = json.load(dataFile)
                challengeJson['current'][self.tag] = {
                    "tag": self.tag,
                    "player": self.player,
                    "track":self.atxChaTrack,
                    "totalPoints":self.atxChaPoints,
                    "completed":self.atxChaCompleted,
                    "missed":self.atxChaMissed,
                    "trashed":self.atxChaTrashed,
                    "commonStreak": self.atxChaCommonStreak,
                    "activeChallenge":self.atxChaActiveChall,
                    "completedChallenges":self.atxChaCompletedChalls,
                    }
                with open(getFile('challengepass'),"w") as dataFile:
                    return json.dump(challengeJson,dataFile,indent=2)

class Challenge():
    #This represents a challenge for the Ataraxy Pass
    def __init__(self,player,track,challDict=None,commonStreak=0):
        self.member = player
        self.challengeTrack = track

        if challDict==None:
            self.generateChallenge(commonStreak)
        else:
            self.challengeTask = challDict['task']
            self.challengeTarget = challDict['target']
            self.challengeDuration = challDict['duration']
            self.challengeScore = challDict['targetScore']
            self.challengeDesc = challDict['desc']
            self.challengeReward = challDict['reward']
            self.challengeProgress = challDict['progress']              

    def generateChallenge(self,commonStreak):
        commonStreak2 = commonStreak
        player = self.member
        generateTime = time.time()
        #trackWar = ['trophies','defenses','townhall','victories','troopBoost','warStars']
        trackWar = ['trophies','defenses','victories','troopBoost','warStars']
        trackFarm = ['lootElixir', 'lootGold', 'lootDarkElixir','seasonChallenges','obstacles','warTreasury']
        trackCommon = ['donations','request','destroyTarget','heroUpgrade','troopUpgrade']

        challengePointReward = range(300,500)

        durationMultiplier = {
            1: 1,
            2: 1.5,
            3: 2,
            4: 3,
            5: 4,
            6: 7,
            7: 10
            }    

        if self.challengeTrack == 'war':
            self.challengeTask = random.choice(trackWar)
        elif self.challengeTrack == 'farm':
            self.challengeTask = random.choice(trackFarm)

        if commonStreak2 < 3:
            commonChance = random.choice(range(1,10))
            if commonChance >= 7:
                self.challengeTask = random.choice(trackCommon)   

        try:
            if self.challengeTask == 'trophies':
                baseScore = 150
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Earn {self.challengeScore} trophies in Multiplayer Battles."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': player.homeVillage['league']['trophies']
                    }

            if self.challengeTask == 'defenses':
                baseScore = 1
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Win {self.challengeScore} defenses in Multiplayer Battles."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Unbreakable':
                        initStat = achievement['value']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    }

            if self.challengeTask == 'townhall':
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Humiliator':
                        initStat = achievement['value']
                baseScore = 3
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Destroy {self.challengeScore} enemy townhalls in Multiplayer Battles."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }            
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    }

            if self.challengeTask == 'victories':
                baseScore = 5
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Win {self.challengeScore} attacks in Multiplayer Battles."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Conqueror':
                        initStat = achievement['value']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    }

            if self.challengeTask == 'troopBoost':
                baseScore = 1
                availableDurations = [3,6]
                self.challengeDuration = random.choice(availableDurations)
                if round(durationMultiplier[self.challengeDuration]*baseScore) > 4:
                    self.challengeScore = 4
                else:
                    self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Boost Troops to their Super version {self.challengeScore} times."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Superb Work':
                        initStat = achievement['value']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    }

            if self.challengeTask == 'warStars':
                baseScore = 2
                availableDurations = [2,4,6]
                self.challengeDuration = random.choice(availableDurations)
                if self.challengeDuration == 2:
                    self.challengeScore = 2
                if self.challengeDuration == 4:
                    self.challengeScore = 5
                if self.challengeDuration == 6:
                    self.challengeScore = 8            
                self.challengeDesc = f"Earn {self.challengeScore} stars in Clan Wars. Stars lost on defense count against your total."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': player.atxWar['warStars'] + player.atxWar['cwlStars']
                    }              

            if self.challengeTask == 'lootElixir':
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Elixir Escapade':
                        initStat = achievement['value']
                if initStat > (2000000000 - 50000000):
                    raise StatTooHigh
                baseScore = 1000000
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Loot {numerize.numerize(self.challengeScore,1)} Elixir from your enemies! Don't forget to spend it..."
                self.challengeReward = {
                    'reward':round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': player.atxLoot['elixir']['season']
                    }

            if self.challengeTask == 'lootGold':
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Gold Grab' and achievement['value'] < (2000000000 - 50000000):
                        initStat = achievement['value']
                if initStat > (2000000000 - 50000000):
                    raise StatTooHigh
                baseScore = 1000000
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Loot {numerize.numerize(self.challengeScore,1)} Gold from your enemies! Don't forget to spend it..."
                self.challengeReward = {
                    'reward':round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': player.atxLoot['gold']['season']
                    }

            if self.challengeTask == 'lootDarkElixir':
                baseScore = 20000
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Loot {numerize.numerize(self.challengeScore,1)} Dark Elixir from your enemies! Don't forget to spend it..."
                self.challengeReward = {
                    'reward':round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': player.atxLoot['darkElixir']['season']
                    }            

            if self.challengeTask == 'seasonChallenges':
                baseScore = 60
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Complete {self.challengeScore} points worth of challenges in the Season Pass."
                self.challengeReward = {
                    'reward':round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Well Seasoned':
                        initStat = achievement['value']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    } 
            
            if self.challengeTask == 'obstacles':
                baseScore = 10
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Clear {self.challengeScore} obstacles from either your Home Village or Builder Base."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Nice and Tidy':
                        initStat = achievement['value']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    }            

            if self.challengeTask == 'warTreasury':
                baseScore = 500000
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Collect {numerize.numerize(self.challengeScore,1)} Gold from your Treasury."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'challengePoints'
                    }
                for achievement in player.homeVillage['achievements']:
                    if achievement['name'] == 'Clan War Wealth':
                        initStat = achievement['value']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    }            

            if self.challengeTask == 'donations':
                baseScore = 100
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Donate {self.challengeScore} troops/spells/siege machines to your clan mates."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'atc'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': player.atxDonations['sent']['season']
                    }

            if self.challengeTask == 'request':
                baseScore = 100
                availableDurations = [1,2,3,4,5,6,7]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Receive {self.challengeScore} troops/spells/siege machines from your clan mates."
                self.challengeReward = {
                    'reward': round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'atc'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': player.atxDonations['received']['season']
                    }

            if self.challengeTask == 'destroyTarget':
                baseScore = 3
                availableDurations = [1,2,3,4,5,6,7]
                availableTargets = ['Walls','Builder Huts','Mortars','X-Bows','Inferno Towers','Eagle Artilleries','Scattershots']
                self.challengeDuration = random.choice(availableDurations)
                self.challengeTarget = random.choice(availableTargets)
                if self.challengeTarget == 'Walls':
                    self.challengeScore = (round(durationMultiplier[self.challengeDuration]*baseScore))*50
                else:
                    self.challengeScore = (round(durationMultiplier[self.challengeDuration]*baseScore))
                self.challengeDesc = f"Destroy {self.challengeScore} {self.challengeTarget} in Multiplayer Battles."
                self.challengeReward = {
                    'reward':round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type': 'atc'
                    }
                for achievement in player.homeVillage['achievements']:
                    if self.challengeTarget == 'Builder Huts' and achievement['name'] == 'Union Buster':
                        initStat = achievement['value']
                    if self.challengeTarget == 'Mortars' and achievement['name'] == 'Mortar Mauler':
                        initStat = achievement['value']
                    if self.challengeTarget == 'X-Bows' and achievement['name'] == 'X-Bow Exterminator':
                        initStat = achievement['value']
                    if self.challengeTarget == 'Inferno Towers' and achievement['name'] == 'Firefighter':
                        initStat = achievement['value']
                    if self.challengeTarget == 'Eagle Artilleries' and achievement['name'] == 'Anti-Artillery':
                        initStat = achievement['value']
                    if self.challengeTarget == 'Scattershots' and achievement['name'] == 'Shattered and Scattered':
                        initStat = achievement['value']
                    if self.challengeTarget == 'Walls' and achievement['name'] == 'Wall Buster':
                        initStat = achievement['value']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': initStat
                    }            

            if self.challengeTask == 'heroUpgrade':
                baseScore = 1
                availableDurations = [3,5]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(durationMultiplier[self.challengeDuration]*baseScore)
                self.challengeDesc = f"Upgrade your heroes by {self.challengeScore} level(s)."
                self.challengeReward = {
                    'reward':round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type':'atc'
                    }
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': sum(player.homeVillage['heroes'].values())
                    }  

            if self.challengeTask == 'troopUpgrade':
                totalLevel = 0
                baseScore = 1
                availableDurations = [3]
                self.challengeDuration = random.choice(availableDurations)
                self.challengeScore = round(1*baseScore)
                self.challengeDesc = f"Upgrade your troops and/or spells by {self.challengeScore} level(s)."
                self.challengeReward = {
                    'reward':round(durationMultiplier[self.challengeDuration]*round(random.choice(challengePointReward)/10)*10),
                    'type':'atc'
                    }
                for labTroop in player.homeVillage['troops']['elixirTroops']+player.homeVillage['troops']['darkTroops']+player.homeVillage['troops']['siegeMachines']+player.homeVillage['troops']['pets']+player.homeVillage['spells']['elixirSpells']+player.homeVillage['spells']['darkSpells']:
                    totalLevel += labTroop['level']
                self.challengeProgress = {
                    'status': 'inProgress',
                    'startTime': generateTime,
                    'completedTime': 0,
                    'currentScore': 0,
                    'initStat': totalLevel
                    }

            if self.challengeTask != 'destroyTarget':
                self.challengeTarget = None
        except:
            self.generateChallenge(commonStreak2)

    def updateChallenge(self,trash=False):
        updateTime = time.time()
        player = self.member

        if updateTime > (self.challengeProgress['startTime'] + (self.challengeDuration * 86400)):
            self.challengeProgress['status'] = "missed"
            self.challengeProgress['completedTime'] = updateTime
            return

        if self.challengeTask == 'trophies':
            newStat = player.homeVillage['league']['trophies']

        if self.challengeTask == 'defenses':
            for achievement in player.homeVillage['achievements']:
                if achievement['name'] == 'Unbreakable':
                    newStat = achievement['value']

        if self.challengeTask == 'townhall':
            for achievement in player.homeVillage['achievements']:
                if achievement['name'] == 'Humiliator':
                    newStat = achievement['value']            

        if self.challengeTask == 'victories':
            for achievement in player.homeVillage['achievements']:
                if achievement['name'] == 'Conqueror':
                    newStat = achievement['value']

        if self.challengeTask == 'troopBoost':
            for achievement in player.homeVillage['achievements']:
                if achievement['name'] == 'Superb Work':
                    newStat = achievement['value']

        if self.challengeTask == 'warStars':
            newStat = player.atxWar['warStars'] + player.atxWar['cwlStars']

        if self.challengeTask == 'lootElixir':
            newStat = player.atxLoot['elixir']['season']

        if self.challengeTask == 'lootGold':
            newStat = player.atxLoot['gold']['season']

        if self.challengeTask == 'lootDarkElixir':
            newStat = player.atxLoot['darkElixir']['season']

        if self.challengeTask == 'seasonChallenges':
            for achievement in player.homeVillage['achievements']:
                if achievement['name'] == 'Well Seasoned':
                    newStat = achievement['value']
        
        if self.challengeTask == 'obstacles':
            for achievement in player.homeVillage['achievements']:
                if achievement['name'] == 'Nice and Tidy':
                    newStat = achievement['value']

        if self.challengeTask == 'warTreasury':
            for achievement in player.homeVillage['achievements']:
                if achievement['name'] == 'Clan War Wealth':
                    newStat = achievement['value']            

        if self.challengeTask == 'donations':
            newStat = player.atxDonations['sent']['season']

        if self.challengeTask == 'request':
            newStat = player.atxDonations['received']['season']

        if self.challengeTask == 'destroyTarget':
            for achievement in player.homeVillage['achievements']:
                if self.challengeTarget == 'Builder Huts' and achievement['name'] == 'Union Buster':
                    newStat = achievement['value']
                if self.challengeTarget == 'Mortars' and achievement['name'] == 'Mortar Mauler':
                    newStat = achievement['value']
                if self.challengeTarget == 'X-Bows' and achievement['name'] == 'X-Bow Exterminator':
                    newStat = achievement['value']
                if self.challengeTarget == 'Inferno Towers' and achievement['name'] == 'Firefighter':
                    newStat = achievement['value']
                if self.challengeTarget == 'Eagle Artilleries' and achievement['name'] == 'Anti-Artillery':
                    newStat = achievement['value']
                if self.challengeTarget == 'Scattershots' and achievement['name'] == 'Shattered and Scattered':
                    newStat = achievement['value']
                if self.challengeTarget == 'Walls' and achievement['name'] == 'Wall Buster':
                    newStat = achievement['value']

        if self.challengeTask == 'heroUpgrade':
            newStat = sum(player.homeVillage['heroes'].values())

        if self.challengeTask == 'troopUpgrade':
            totalLevel = 0
            for labTroop in player.homeVillage['troops']['elixirTroops']+player.homeVillage['troops']['darkTroops']+player.homeVillage['troops']['siegeMachines']+player.homeVillage['troops']['pets']+player.homeVillage['spells']['elixirSpells']+player.homeVillage['spells']['darkSpells']:
                totalLevel += labTroop['level']
            newStat = totalLevel

        self.challengeProgress['currentScore'] = newStat-self.challengeProgress['initStat']

        if trash:
            self.challengeProgress['status'] = "trashed"
            self.challengeProgress['completedTime'] = updateTime
            return

        if self.challengeProgress['currentScore'] >= self.challengeScore:
            self.challengeProgress['status'] = "completed"
            self.challengeProgress['completedTime'] = updateTime
            return

    def challengeToJson(self):
        retDictionary = {
            'task': self.challengeTask,
            'target': self.challengeTarget,
            'duration': self.challengeDuration,
            'targetScore': self.challengeScore,
            'reward': self.challengeReward,
            'desc': self.challengeDesc,
            'progress': self.challengeProgress
            }
        return retDictionary