from translations import t
from ui_element import UIElement


# ROOT SCREEN
class CampaignTeamSelectUIPresenter(UIElement):
    def build_prompt(self):
        battleName = self.glom("CampaignTeamSelectUIPresenter.BattleName")
        leaderSummary = self.glom("TeamSelectBaseUIPresenter.Leader.ChampionConfigId")
        selectedChampions = self.glom_summary("TeamSelectBaseUIPresenter.SelectedChampions")
        waveCount = self.glom("TeamSelectDefaultEnemiesUIPresenter.WavesCountInt")
        enemySummary = self.glom_summary("TeamSelectDefaultEnemiesUIPresenter")
        return f"""
You are on the prebattle team selection screen. Currently selected battle is {t(battleName)}
You can check battle details by using tool: uxHelper("TeamSelectDefaultEnemiesUIPresenter")
Player has chosen {t(leaderSummary)} as leader and he has selected the following champions: {selectedChampions}.
If you need details on selected champions, use tool: uxHelper("SelectedChampions"). 
There will be {waveCount} waves in this battle. Opponents are: {enemySummary}
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

    def build_prompt(self):
        champions = [self._format_champion_all(item) for item in self.child_tree.values()]
        return f"""
Selected champions panel, here are detailed information about champions: [{", ".join(champions)}]
"""

    def build_summary(self):
        champions = [self._format_champion(item) for item in self.child_tree.values()]
        return f"[{', '.join(champions)}]"


class Leader(UIElement):
    def build_prompt(self):
        return "Leader " + t(self.glom("ChampionConfigId"), "name.titlecase")

    def build_summary(self):
        leaderId = self.glom("ChampionConfigId")
        return f"{t(leaderId, 'name.titlecase')}"


class TeamSelectDefaultEnemiesUIPresenter(UIElement):
    def _enemy_short_desc(self, enemy: dict) -> str:
        return f"Name {t(enemy.get('EnemyConfigId'), 'name.titlecase')}, Power {enemy.get('EnemyPowerInt', 'Unknown')}"

    def _enemy_long_desc(self, enemy: dict) -> str:
        return (
            f"Name {t(enemy.get('EnemyConfigId'), 'name.titlecase')}, "
            f"Power {enemy.get('EnemyPowerInt', 'Unknown')}, "
            f"Affinity {enemy.get('EnemyAffinityName', 'Unknown')}, "
            f"Rarity {enemy.get('EnemyRarityName', 'Unknown')}, "
            f"Class {enemy.get('EnemyClassName', 'Unknown')}, "
            f"Faction {enemy.get('EnemyFactionName', 'Unknown')}"
        )

    def build_prompt(self):
        waves = self.child_tree.get("Waves", {})
        if not waves:
            return "No enemy waves"

        wave_summaries = []
        for wave in waves.values():
            enemies = wave.get("Enemies", {})
            if not enemies:
                continue
            enemy_summaries = [self._enemy_long_desc(enemy) for enemy in enemies.values()]
            wave_summaries.append(f"Wave: [{', '.join(enemy_summaries)}]")

        return f"Enemies: {', '.join(wave_summaries)}"

    def build_summary(self):
        # get enemy waves from child tree (dict)
        waves = self.child_tree.get("Waves", {})
        if not waves:
            return "No enemy waves"
        wave_summaries = []
        for wave in waves.values():
            enemies = wave.get("Enemies", {})
            if not enemies:
                continue
            enemy_summaries = [self._enemy_short_desc(enemy) for enemy in enemies.values()]
            wave_summaries.append(f"Wave: [{', '.join(enemy_summaries)}]")
        return f"Enemies: {', '.join(wave_summaries)}"
