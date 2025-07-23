#!/usr/bin/env python3
"""
PostgreSQL Database Tool: Compare Champions
Compare two or more champions side by side with comprehensive analysis
"""

import logging

from db_postgres import execute_query

# Logger
logger = logging.getLogger("ChampionsComparator")


def db_compare_champions(champion_names: list, detailed: bool = True) -> dict:
    """
    Compare two or more champions with comprehensive analysis including stats, traits, and recommendations.

    Args:
        champion_names: List of champion names to compare (minimum 2 required, max 5)
        detailed: Boolean flag for detailed analysis (default: True)

    Returns:
        str: JSON formatted comparison analysis of the champions
    """
    try:
        # Validate input
        if not champion_names or len(champion_names) < 2:
            return {
                "status": "error",
                "message": "At least 2 champion names are required for comparison",
                "champions": [],
                "internal_info": {
                    "function_name": "db_compare_champions",
                    "parameters": {
                        "champion_names": champion_names,
                        "detailed": detailed,
                    },
                },
            }

        if len(champion_names) > 5:
            return {
                "status": "error",
                "message": "Maximum 5 champions can be compared at once",
                "champions": [],
                "internal_info": {
                    "function_name": "db_compare_champions",
                    "parameters": {
                        "champion_names": champion_names,
                        "detailed": detailed,
                    },
                },
            }

        champions = []
        not_found = []

        # Find each champion using fuzzy search
        for name in champion_names:
            char_query = """
            SELECT ct.id, ct.champion_name, ct.rarity, ct.affinity, ct.class, ct.faction,
                   ct.era, ct.fighting_style, ct.race, ct.side_of_force,
                   cs.attack, cs.defense, cs.health, cs.speed, cs.accuracy, cs.resistance,
                   cs.critical_rate, cs.critical_damage, cs.mana,
                   (cs.attack + cs.defense + cs.health) as total_power
            FROM champion_traits ct
            JOIN champion_stats cs ON ct.champion_name = cs.champion_name
            WHERE ct.champion_name ILIKE %s
            ORDER BY (cs.attack + cs.defense + cs.health) DESC
            LIMIT 1
            """

            char_result = execute_query(char_query, (f"%{name}%",))

            if char_result:
                champion = char_result[0]
                champions.append(champion)
            else:
                not_found.append(name)

        if not champions:
            return {
                "status": "success",
                "message": f"None of the provided champions were found: {', '.join(champion_names)}",
                "champions": [],
                "not_found": champion_names,
                "found_count": 0,
                "comparison_summary": "No champions found to compare.",
                "llm_instruction": f"No champions found matching: {', '.join(champion_names)}. Please check the champion names and try again.",
                "internal_info": {
                    "function_name": "db_compare_champions",
                    "parameters": {
                        "champion_names": champion_names,
                        "detailed": detailed,
                    },
                },
            }

        if len(champions) < 2:
            found_names = [c["champion_name"] for c in champions]
            return {
                "status": "success",
                "message": f"Only found {len(champions)} champion(s), need at least 2 for comparison",
                "champions": champions,
                "not_found": not_found,
                "found_count": len(champions),
                "comparison_summary": f"Found: {', '.join(found_names)}. Missing: {', '.join(not_found)}",
                "llm_instruction": f"Only found {len(champions)} champion(s): {', '.join(found_names)}. Need at least 2 champions for comparison. Missing: {', '.join(not_found)}",
                "internal_info": {
                    "function_name": "db_compare_champions",
                    "parameters": {
                        "champion_names": champion_names,
                        "detailed": detailed,
                    },
                },
            }

        # Perform comparison analysis
        comparison_analysis = _perform_comparison_analysis(champions)

        # Create formatted comparison for LLM presentation
        formatted_comparison = _format_comparison_for_llm(champions, comparison_analysis)

        # Generate recommendations
        recommendations = _generate_recommendations(champions, comparison_analysis)

        # Create summary
        summary = _create_comparison_summary(champions, comparison_analysis)

        found_names = [c["champion_name"] for c in champions]

        return {
            "status": "success",
            "message": f"Successfully compared {len(champions)} champions",
            "champions": champions,
            "found_count": len(champions),
            "not_found": not_found,
            "stat_comparison": comparison_analysis["stat_comparison"],
            "power_analysis": comparison_analysis["power_analysis"],
            "role_analysis": comparison_analysis["role_analysis"],
            "trait_comparison": comparison_analysis["trait_comparison"],
            "recommendations": recommendations,
            "summary": summary,
            "formatted_comparison": formatted_comparison,
            "llm_instruction": f"Present comparison of {len(champions)} champions ({', '.join(found_names)}):\n\n{formatted_comparison}\n\nThen provide analysis and recommendations.",
            "internal_info": {
                "function_name": "db_compare_champions",
                "parameters": {"champion_names": champion_names, "detailed": detailed},
            },
        }

    except Exception as e:
        logger.error(f"Error in db_compare_champions: {str(e)}")
        return {
            "status": "error",
            "message": f"Error comparing champions: {str(e)}",
            "champions": [],
            "internal_info": {
                "function_name": "db_compare_champions",
                "parameters": {"champion_names": champion_names, "detailed": detailed},
            },
        }


def _perform_comparison_analysis(champions: list) -> dict:
    """Perform comprehensive comparison analysis."""
    stats_to_compare = [
        "attack",
        "defense",
        "health",
        "speed",
        "total_power",
        "accuracy",
        "resistance",
        "critical_rate",
        "critical_damage",
        "mana",
    ]

    # Stat comparison
    stat_comparison = {}
    for stat in stats_to_compare:
        values = [(char["champion_name"], char[stat]) for char in champions]
        values.sort(key=lambda x: x[1], reverse=True)

        highest = values[0]
        lowest = values[-1]
        difference = highest[1] - lowest[1]

        stat_comparison[stat] = {
            "highest": highest,
            "lowest": lowest,
            "difference": difference,
            "ranking": values,
        }

    # Power analysis
    powers = [char["total_power"] for char in champions]
    avg_power = sum(powers) / len(powers)
    power_spread = max(powers) - min(powers)
    power_gap_percentage = (power_spread / avg_power * 100) if avg_power > 0 else 0

    most_powerful = max(champions, key=lambda x: x["total_power"])
    least_powerful = min(champions, key=lambda x: x["total_power"])

    power_analysis = {
        "average_power": round(avg_power, 1),
        "power_spread": power_spread,
        "most_powerful": {
            "name": most_powerful["champion_name"],
            "power": most_powerful["total_power"],
        },
        "least_powerful": {
            "name": least_powerful["champion_name"],
            "power": least_powerful["total_power"],
        },
        "power_gap_percentage": round(power_gap_percentage, 1),
    }

    # Role analysis
    role_analysis = {}
    for char in champions:
        total_power = char["total_power"]
        if total_power > 0:
            attack_ratio = (char["attack"] / total_power) * 100
            defense_ratio = (char["defense"] / total_power) * 100
            health_ratio = (char["health"] / total_power) * 100

            # Determine role based on class and stats
            class_role = char["class"]
            if attack_ratio > 40:
                stat_role = "Damage Dealer"
            elif health_ratio > 50:
                stat_role = "Tank"
            elif defense_ratio > 30:
                stat_role = "Defender"
            else:
                stat_role = "Balanced"

            role_analysis[char["champion_name"]] = {
                "class": class_role,
                "stat_role": stat_role,
                "attack_ratio": round(attack_ratio, 1),
                "defense_ratio": round(defense_ratio, 1),
                "health_ratio": round(health_ratio, 1),
                "fighting_style": char["fighting_style"],
            }

    # Trait comparison
    trait_comparison = {
        "rarity": {},
        "affinity": {},
        "faction": {},
        "era": {},
        "side_of_force": {},
        "race": {},
    }

    for char in champions:
        name = char["champion_name"]
        trait_comparison["rarity"][name] = char["rarity"]
        trait_comparison["affinity"][name] = char["affinity"]
        trait_comparison["faction"][name] = char["faction"]
        trait_comparison["era"][name] = char["era"]
        trait_comparison["side_of_force"][name] = char["side_of_force"]
        trait_comparison["race"][name] = char["race"]

    return {
        "stat_comparison": stat_comparison,
        "power_analysis": power_analysis,
        "role_analysis": role_analysis,
        "trait_comparison": trait_comparison,
    }


def _format_comparison_for_llm(champions: list, analysis: dict) -> str:
    """Format comparison for LLM presentation - mobile-friendly format without markdown tables."""
    lines = []

    # Header
    champion_names = [c["champion_name"] for c in champions]
    lines.append(f"COMPARISON: {' vs '.join(champion_names)}")
    lines.append("")

    # Individual champion stats in compact format
    lines.append("CHAMPION STATS:")
    for i, char in enumerate(champions, 1):
        lines.append(f"{i}. {char['champion_name']}")
        lines.append(f"   Power: {char['total_power']} (Attack: {char['attack']}, Defense: {char['defense']}, Health: {char['health']})")
        lines.append(f"   Speed: {char['speed']} | {char['rarity']} {char['affinity']} {char['class']}")
        lines.append(f"   Style: {char['fighting_style']} | Faction: {char['faction']}")
        lines.append("")

    # Power ranking in simple format
    power_ranking = sorted(champions, key=lambda x: x["total_power"], reverse=True)
    lines.append("POWER RANKING:")
    for i, char in enumerate(power_ranking, 1):
        power_diff = ""
        if i > 1:
            prev_power = power_ranking[i - 2]["total_power"]
            diff = prev_power - char["total_power"]
            power_diff = f" (-{diff})"
        lines.append(f"{i}. {char['champion_name']}: {char['total_power']} power{power_diff}")

    lines.append("")

    # Key differences in readable format
    lines.append("KEY DIFFERENCES:")
    strongest = max(champions, key=lambda x: x["total_power"])
    fastest = max(champions, key=lambda x: x["speed"])
    highest_attack = max(champions, key=lambda x: x["attack"])
    tankiest = max(champions, key=lambda x: x["health"])

    lines.append(f"• Strongest: {strongest['champion_name']} ({strongest['total_power']} power)")
    lines.append(f"• Fastest: {fastest['champion_name']} ({fastest['speed']} speed)")
    lines.append(f"• Highest Attack: {highest_attack['champion_name']} ({highest_attack['attack']} attack)")
    lines.append(f"• Most Health: {tankiest['champion_name']} ({tankiest['health']} health)")

    return "\n".join(lines)


def _generate_recommendations(champions: list, analysis: dict) -> dict:
    """Generate recommendations based on comparison."""
    most_powerful = analysis["power_analysis"]["most_powerful"]

    # General recommendations
    recommendations = {
        "strongest_overall": f"{most_powerful['name']} with {most_powerful['power']} total power",
        "best_for_roles": {},
        "synergies": [],
        "usage_scenarios": {},
    }

    # Role-specific recommendations
    attackers = [c for c in champions if c["class"] == "ATTACKER"]
    defenders = [c for c in champions if c["class"] == "DEFENDER"]
    supports = [c for c in champions if c["class"] == "SUPPORT"]

    if attackers:
        best_attacker = max(attackers, key=lambda x: x["attack"])
        recommendations["best_for_roles"]["damage"] = best_attacker["champion_name"]

    if defenders:
        best_defender = max(defenders, key=lambda x: x["defense"] + x["health"])
        recommendations["best_for_roles"]["defense"] = best_defender["champion_name"]

    if supports:
        best_support = max(supports, key=lambda x: x["total_power"])
        recommendations["best_for_roles"]["support"] = best_support["champion_name"]

    # Affinity synergies
    affinities = {}
    for char in champions:
        affinity = char["affinity"]
        if affinity not in affinities:
            affinities[affinity] = []
        affinities[affinity].append(char["champion_name"])

    for affinity, chars in affinities.items():
        if len(chars) > 1:
            recommendations["synergies"].append(f"{affinity} synergy: {', '.join(chars)}")

    # Usage scenarios
    fastest = max(champions, key=lambda x: x["speed"])
    tankiest = max(champions, key=lambda x: x["health"])
    highest_attack = max(champions, key=lambda x: x["attack"])

    recommendations["usage_scenarios"] = {
        "speed_missions": fastest["champion_name"],
        "survival_content": tankiest["champion_name"],
        "burst_damage": highest_attack["champion_name"],
    }

    return recommendations


def _create_comparison_summary(champions: list, analysis: dict) -> str:
    """Create a summary of the comparison."""
    champion_names = [c["champion_name"] for c in champions]
    most_powerful = analysis["power_analysis"]["most_powerful"]
    power_gap = analysis["power_analysis"]["power_gap_percentage"]

    summary_parts = [
        f"Compared {len(champions)} champions: {', '.join(champion_names)}",
        f"Strongest: {most_powerful['name']} ({most_powerful['power']} power)",
        f"Power gap: {power_gap}%",
    ]

    # Add role diversity
    classes = set(c["class"] for c in champions)
    if len(classes) > 1:
        summary_parts.append(f"Role diversity: {', '.join(classes)}")

    return ". ".join(summary_parts)
