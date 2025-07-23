from ..translations import t
from ..ui_element import UIElement, safe_output


# ROOT SCREEN
class CampaignTeamSelectUIPresenter(UIElement):
    @safe_output("Campaign Team Select screen prompt is not available")
    def build_prompt(self):
        battleName = self.glom("CampaignTeamSelectUIPresenter.BattleName")
        leaderSummary = self.glom("TeamSelectBaseUIPresenter.Leader.ChampionConfigId")
        selectedChampions = self.glom_summary("TeamSelectBaseUIPresenter.SelectedChampions")
        waveCount = self.glom("TeamSelectDefaultEnemiesUIPresenter.WavesCountInt")
        return f"""
You are on the prebattle team selection screen. Currently selected battle is {t(battleName)}
You can check battle details by using tool: uxHelper("TeamSelectDefaultEnemiesUIPresenter")
Player has chosen {t(leaderSummary)} as leader and he has selected the following champions: {selectedChampions}.
If you need details on selected champions, use tool: uxHelper("SelectedChampions"). 
There will be {waveCount} waves in this battle. Call uxHelper("TeamSelectDefaultEnemiesUIPresenter") to get more details about enemies.
User can start battle by using button in the middle of the screen. 
"""

    def build_summary(self, data, parser):
        return f"""
You are on the prebattle team selection screen. Currently selected battle is {self.glom("CampaignTeamSelectUIPresenter.BattleName")}
"""


class TeamSelectBaseUIPresenter(UIElement):
    def build_prompt(self):
        return ""

    def build_summary(self):
        return ""


class SelectedChampions(UIElement):
    def _format_champion_all(self, item: dict) -> str:
        return (
            f"Name: {t(item.get('ChampionConfigId'), 'name.titlecase')}, "
            f"Stars: {item.get('ChampionStarsInt', 'Unknown')}, "
            f"Level: {item.get('ChampionLevelInt', 'Unknown')}/{item.get('ChampionMaxLevelInt', 'Unknown')}, "
            f"Power: {item.get('ChampionPowerInt', 'Unknown')}, "
            f"Affinity: {item.get('ChampionAffinityName', 'Unknown')}, "
            f"Rarity: {item.get('ChampionRarityName', 'Unknown')}, "
            f"Class: {item.get('ChampionClassName', 'Unknown')}, "
            f"Faction: {item.get('ChampionFactionName', 'Unknown')}"
        )

    def _format_champion(self, item: dict) -> str:
        return (
            f"{t(item.get('ChampionConfigId'), 'name.titlecase')} "
            f"(Stars {item.get('ChampionStarsInt', 'Unknown')}, "
            f"Power {item.get('ChampionPowerInt', 'Unknown')})"
        )

    @safe_output("Selected champions panel, here are detailed information about. Information is not available.")
    def build_prompt(self):
        champions = [self._format_champion_all(item) for item in self.child_tree.values()]
        return f"""
Selected champions panel, here are detailed information about champions: [{", ".join(champions)}]
"""

    @safe_output("Selected champions not available")
    def build_summary(self):
        champions = [self._format_champion(item) for item in self.child_tree.values()]
        return f"[{', '.join(champions)}]"


class Leader(UIElement):
    @safe_output("Leader information is not available")
    def build_prompt(self):
        return "Leader " + t(self.glom("ChampionConfigId"), "name.titlecase")

    @safe_output("Leader information is not available")
    def build_summary(self):
        leaderId = self.glom("ChampionConfigId")
        return f"{t(leaderId, 'name.titlecase')}"


class TeamSelectDefaultEnemiesUIPresenter(UIElement):
    def _enemy_short_desc(self, enemy: dict) -> str:
        return f"Name {self._name(enemy.get('EnemyConfigId'))}, Power {enemy.get('EnemyPowerInt', 'Unknown')}"

    def _enemy_long_desc(self, enemy: dict) -> str:
        return (
            f"Name {self._name(enemy.get('EnemyConfigId'))}, "
            f"Power {enemy.get('EnemyPowerInt', 'Unknown')}, "
            f"Affinity {enemy.get('EnemyAffinityName', 'Unknown')}, "
            f"Rarity {enemy.get('EnemyRarityName', 'Unknown')}, "
            f"Class {enemy.get('EnemyClassName', 'Unknown')}, "
            f"Faction {enemy.get('EnemyFactionName', 'Unknown')}"
        )

    # TODO
    # Parsing strage mob id into name key.
    def _name(self, id: str | None) -> str | None:
        if not id:
            return None

        return t(".".join(id.split(".")[1:-2]), "name.titlecase")

    @safe_output("Enemy waves information is not available")
    def build_prompt(self):
        waves = self.child_tree.get("EnemyWaves", {})
        if not waves:
            return "No enemy waves found."
        wave_descriptions = []
        for wave_name, wave_list in waves.items():
            enemies_in_wave = [self._enemy_long_desc(enemy) for enemy in wave_list]
            wave_descriptions.append(f"* {wave_name}: {', '.join(enemies_in_wave)}\n")
        return f"""In this battle, user will face the following Waves and Enemies:
{"".join(wave_descriptions)}"""

    @safe_output("Enemy waves information is not available")
    def build_summary(self):
        # get enemy waves from child tree (dict)
        waves = self.child_tree.get("EnemyWaves", {})
        if not waves:
            return "No enemy waves found."
        wave_descriptions = []
        for wave_name, wave_list in waves.items():
            enemies_in_wave = [self._enemy_short_desc(enemy) for enemy in wave_list]
            wave_descriptions.append(f"* {wave_name} Enemies: {', '.join(enemies_in_wave)}\n")

        return f"{''.join(wave_descriptions)}"


# todo AvailableChampions


class LobbyMainUIPresenter(UIElement):
    @safe_output("Lobby main screen prompt is not available")
    def build_prompt(self):
        return """
You are on the main lobby screen. You can access various game features from here.
Encourage user to explore the game, ask about mechanics, information.
There are three buttons on the bottom:
- Champions
- Quests
- BATTLE - big yellow button that will allow user to start the game.
"""

    @safe_output("Lobby main screen summary is not available")
    def build_summary(self):
        return ""


# TODO Write description for this screen
# ROOT SCREEN
class ChampionEquipmentPanelPresenter(UIElement):
    @safe_output("Champion Equipment screen prompt is not available")
    def build_prompt(self):
        champSummary = self.glom_summary("ChampionMainPanelPresenter")
        return f"""
You are on the Champion Equipment screen. Here you can manage your champion's equipment.
User currently is looking at:
{champSummary}
You can use uxHelper("ChampionEquipmentPanelPresenter") to get more details this champion.
If user asks about mechanics, stats, abilities System recommends to use databases and tools.
"""

    @safe_output("Champion Equipment screen summary is not available")
    def build_summary(self):
        champSummary = self.glom_summary("ChampionMainPanelPresenter")
        return f"""Champion Equipment screen summary:
{champSummary}
"""


class ChampionMainPanelPresenter(UIElement):
    @safe_output("Champion Main Panel prompt is not available")
    def build_prompt(self):
        champName = t(self.glom("ChampionConfigId"), "name.titlecase")
        champStars = self.glom("ChampionStarsInt")
        champLevel = self.glom("ChampionLevelInt")
        champMaxLevel = self.glom("ChampionMaxLevelInt")
        champPower = self.glom("ChampionPowerInt")
        champAffinity = self.glom("ChampionAffinityName")
        champRarity = self.glom("ChampionRarityName")
        champClass = self.glom("ChampionClassName")
        champFaction = self.glom("ChampionFactionName")
        champStats = self.glom("ChampionStats")
        isLocked = self.glom("IsChampionLocked")

        return f"""This is ChampionMainPanelPresenter,
User currently can see the following champion:
- Name: {champName}
- Stars: {champStars}
- Level: {champLevel}/{champMaxLevel}
- Power: {champPower}
- Affinity: {champAffinity}
- Rarity: {champRarity}
- Class: {champClass}
- Faction: {champFaction}
- Locked: {"Yes" if isLocked else "No"}
Stats:
- Attack: {champStats.get("AttackInt", "Unknown")}
- Defense: {champStats.get("DefenseInt", "Unknown")}
- Health: {champStats.get("HealthInt", "Unknown")}
- Resistance: {champStats.get("ResistanceInt", "Unknown")}
- Accuracy: {champStats.get("AccuracyInt", "Unknown")}
- Critical Rate: {champStats.get("CriticalRateFloat", "Unknown")}
- Critical Damage: {champStats.get("CriticalDamageFloat", "Unknown")}
- Speed: {champStats.get("SpeedInt", "Unknown")}
- Mana: {champStats.get("ManaInt", "Unknown")}
"""

    @safe_output("Champion Main Panel summary is not available")
    def build_summary(self):
        champName = t(self.glom("ChampionConfigId"), "name.titlecase")
        champPower = self.glom("ChampionPowerInt")
        champStars = self.glom("ChampionStarsInt")
        champLevel = self.glom("ChampionLevelInt")
        champMaxLevel = self.glom("ChampionMaxLevelInt")
        isLocked = self.glom("IsChampionLocked")
        return (
            f"""Champion: {champName} (Power {champPower}, Stars {champStars}, Level {champLevel}/{champMaxLevel}) {"(Locked)" if isLocked else ""}"""
        )
