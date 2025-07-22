from translations import t
from ui_element import UIElement


# ROOT SCREEN
class CampaignTeamSelectUIPresenter(UIElement):
    def build_prompt(self):
        battleName = self.glom("CampaignTeamSelectUIPresenter.BattleName")
        leaderSummary = self.glom("TeamSelectBaseUIPresenter.Leader.ChampionConfigId")
        selectedChampions = self.glom_summary(
            "TeamSelectBaseUIPresenter.SelectedChampions"
        ).build_summary()

        return f"""
You are on the prebattle team selection screen. Currently selected battle is {t(battleName)}
You can check battle details by using tool: uxHelper("TeamSelectDefaultEnemiesUIPresenter")
Player has chosen {t(leaderSummary)} as leader and he has selected the following champions: {selectedChampions}.
If you need details on selected champions, use tool: uxHelper("SelectedChampions")
"""

    def build_summary(self, data, parser):
        return f"""
You are on the prebattle team selection screen. Currently selected battle is {self.glom("CampaignTeamSelectUIPresenter.BattleName", default="Unknown")}
"""


class TeamSelectBaseUIPresenter(UIElement):
    def build_prompt(self):
        return "Team Select Base! This is prompt!"

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

    def build_prompt(self):
        champions = [
            self._format_champion_all(item) for item in self.child_tree.values()
        ]
        return f"""
Selected champions panel, here are detailed information about champions: [{", ".join(champions)}]
"""
    def build_summary(self):
        champions = [
            f"{t(item.get('ChampionConfigId', 'name.titlecase'))} (Power: {item.get('ChampionPowerInt', 'Unknown')})"
            for item in self.child_tree.values()
        ]
        return f"[{', '.join(champions)}]"


class Leader(UIElement):
    def build_prompt(self):
        return "Leader: " + t(self.glom("ChampionConfigId"), "name.titlecase")

    def build_summary(self):
        leaderId = self.glom("ChampionConfigId")
        return f"{t(leaderId, 'name.titlecase')}"
