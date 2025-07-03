#!/usr/bin/env python3
"""
GCS Tool: Compare Characters
Compare two or more characters side by side with comprehensive analysis
"""

import json
import logging
from db_gcs import execute_query

# Logger
logger = logging.getLogger("GCS Compare Characters")


def gcs_compare_characters(character_names: list, detailed: bool = True) -> str:
    """
    Compare two or more characters with comprehensive analysis including stats, abilities, and recommendations.
    
    Args:
        character_names: List of character names to compare (minimum 2 required)
        detailed: Boolean flag for detailed analysis (default: True)
        
    Returns:
        str: JSON formatted comparison analysis of the characters
    """
    try:
        # Validate input
        if not character_names or len(character_names) < 2:
            return json.dumps({
                "status": "error",
                "message": "At least 2 character names are required for comparison",
                "characters": [],
                "internal_info": {
                    "function_name": "gcs_compare_characters",
                    "parameters": {"character_names": character_names, "detailed": detailed}
                }
            })
        
        characters = []
        not_found = []
        
        # Find each character using fuzzy search
        for name in character_names:
            char_query = """
            SELECT ge.id, ge.name, ge.entity_type, ge.rarity, ge.affinity, ge.class_type, 
                   ge.series, ge.faction,
                   es.attack, es.defense, es.health, es.speed,
                   (es.attack + es.defense + es.health) as total_power
            FROM game_entities ge
            JOIN entity_stats es ON ge.id = es.entity_id
            WHERE LOWER(ge.name) LIKE ?
            ORDER BY ge.entity_type, (es.attack + es.defense + es.health) DESC
            LIMIT 1
            """
            
            char_result = execute_query(char_query, (f'%{name.lower()}%',))
            
            if char_result:
                character = char_result[0]
                
                # Get abilities for this character
                abilities_query = """
                SELECT ea.ability_slot, a.name as ability_name, ea.ability_level, a.max_level
                FROM entity_abilities ea
                JOIN abilities a ON ea.ability_id = a.id
                WHERE ea.entity_id = ?
                ORDER BY
                    CASE ea.ability_slot
                        WHEN 'basic' THEN 1
                        WHEN 'special' THEN 2
                        WHEN 'passive' THEN 3
                        WHEN 'leader' THEN 4
                    END
                """
                abilities = execute_query(abilities_query, (character['id'],))
                
                # Get traits for this character
                traits_query = """
                SELECT trait_category, trait_value
                FROM entity_traits
                WHERE entity_id = ?
                ORDER BY trait_category
                """
                traits = execute_query(traits_query, (character['id'],))
                
                # Add abilities and traits to character data
                character['abilities'] = abilities
                character['traits'] = traits
                
                characters.append(character)
            else:
                not_found.append(name)
        
        if not characters:
            return json.dumps({
                "status": "error",
                "message": f"None of the provided characters were found: {', '.join(character_names)}",
                "characters": [],
                "not_found": character_names,
                "internal_info": {
                    "function_name": "gcs_compare_characters",
                    "parameters": {"character_names": character_names, "detailed": detailed}
                }
            })
        
        # Perform comparison analysis
        comparison_analysis = _perform_comparison_analysis(characters)
        
        # Create formatted comparison for LLM presentation
        formatted_comparison = _format_comparison_for_llm(characters, comparison_analysis)
        
        # Generate recommendations
        recommendations = _generate_recommendations(characters, comparison_analysis)
        
        # Create summary
        summary = _create_comparison_summary(characters, comparison_analysis)
        
        return json.dumps({
            "status": "success",
            "message": f"Successfully compared {len(characters)} characters",
            "characters": characters,
            "found_count": len(characters),
            "not_found": not_found,
            "stat_comparison": comparison_analysis['stat_comparison'],
            "power_analysis": comparison_analysis['power_analysis'],
            "role_analysis": comparison_analysis['role_analysis'],
            "ability_comparison": comparison_analysis['ability_comparison'],
            "recommendations": recommendations,
            "summary": summary,
            "formatted_comparison": formatted_comparison,
            "internal_info": {
                "function_name": "gcs_compare_characters",
                "parameters": {"character_names": character_names, "detailed": detailed}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in gcs_compare_characters: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error comparing characters: {str(e)}",
            "characters": [],
            "internal_info": {
                "function_name": "gcs_compare_characters",
                "parameters": {"character_names": character_names, "detailed": detailed}
            }
        })


def _perform_comparison_analysis(characters: list) -> dict:
    """Perform comprehensive comparison analysis."""
    stats_to_compare = ['attack', 'defense', 'health', 'speed', 'total_power']
    
    # Stat comparison
    stat_comparison = {}
    for stat in stats_to_compare:
        values = [(char['name'], char[stat]) for char in characters]
        values.sort(key=lambda x: x[1], reverse=True)
        
        highest = values[0]
        lowest = values[-1]
        difference = highest[1] - lowest[1]
        
        stat_comparison[stat] = {
            'highest': highest,
            'lowest': lowest,
            'difference': difference,
            'ranking': values
        }
    
    # Power analysis
    powers = [char['total_power'] for char in characters]
    avg_power = sum(powers) / len(powers)
    power_spread = max(powers) - min(powers)
    power_gap_percentage = (power_spread / avg_power * 100) if avg_power > 0 else 0
    
    most_powerful = max(characters, key=lambda x: x['total_power'])
    least_powerful = min(characters, key=lambda x: x['total_power'])
    
    power_analysis = {
        'average_power': round(avg_power, 1),
        'power_spread': power_spread,
        'most_powerful': most_powerful,
        'least_powerful': least_powerful,
        'power_gap_percentage': round(power_gap_percentage, 1)
    }
    
    # Role analysis
    role_analysis = {}
    for char in characters:
        total_power = char['total_power']
        if total_power > 0:
            attack_ratio = (char['attack'] / total_power) * 100
            defense_ratio = (char['defense'] / total_power) * 100
            health_ratio = (char['health'] / total_power) * 100
            
            # Determine role
            if attack_ratio > 40:
                role = "Damage Dealer"
            elif defense_ratio > 35 or health_ratio > 35:
                role = "Tank/Support"
            else:
                role = "Balanced"
            
            role_analysis[char['name']] = {
                'role': role,
                'attack_ratio': round(attack_ratio, 1),
                'defense_ratio': round(defense_ratio, 1),
                'health_ratio': round(health_ratio, 1)
            }
    
    # Ability comparison
    ability_comparison = {}
    for char in characters:
        abilities = {}
        for ability in char['abilities']:
            slot = ability['ability_slot']
            upgrade_potential = ability['max_level'] - ability['ability_level']
            abilities[slot] = {
                'name': ability['ability_name'],
                'level': ability['ability_level'],
                'max_level': ability['max_level'],
                'upgrade_potential': upgrade_potential
            }
        ability_comparison[char['name']] = abilities
    
    return {
        'stat_comparison': stat_comparison,
        'power_analysis': power_analysis,
        'role_analysis': role_analysis,
        'ability_comparison': ability_comparison
    }


def _format_comparison_for_llm(characters: list, analysis: dict) -> str:
    """Format comparison data for LLM presentation - simple format."""
    lines = []
    
    # Character summary
    char_names = [char['name'] for char in characters]
    lines.append(f"Comparing {len(characters)} characters: {', '.join(char_names)}")
    lines.append("")
    
    # Power ranking
    power_ranking = analysis['stat_comparison']['total_power']['ranking']
    most_powerful = power_ranking[0]
    least_powerful = power_ranking[-1]
    power_gap = analysis['power_analysis']['power_gap_percentage']
    
    lines.append(f"Power ranking: {most_powerful[0]} ({most_powerful[1]}) is strongest")
    if len(characters) > 2:
        for i, (name, power) in enumerate(power_ranking[1:-1], 2):
            lines.append(f"{i}. {name} ({power})")
    lines.append(f"Weakest: {least_powerful[0]} ({least_powerful[1]})")
    lines.append(f"Power gap: {power_gap:.1f}%")
    lines.append("")
    
    # Role summary
    roles = []
    for name, role_data in analysis['role_analysis'].items():
        roles.append(f"{name} ({role_data['role']})")
    lines.append(f"Team roles: {', '.join(roles)}")
    lines.append("")
    
    return "\n".join(lines)


def _generate_recommendations(characters: list, analysis: dict) -> list:
    """Generate intelligent recommendations based on comparison."""
    recommendations = []
    
    # Power gap analysis
    power_gap = analysis['power_analysis']['power_gap_percentage']
    if power_gap > 30:
        most_powerful = analysis['power_analysis']['most_powerful']['name']
        least_powerful = analysis['power_analysis']['least_powerful']['name']
        recommendations.append(f"Large power gap detected ({power_gap:.1f}%). Consider investing in {least_powerful} to balance with {most_powerful}.")
    
    # Role diversity analysis
    roles = [role_data['role'] for role_data in analysis['role_analysis'].values()]
    unique_roles = set(roles)
    if len(unique_roles) < len(characters):
        recommendations.append("Characters have overlapping roles. Consider diversifying your team composition.")
    else:
        recommendations.append("Good role diversity! This team covers different tactical roles.")
    
    # Rarity analysis
    legendary_chars = [char['name'] for char in characters if char.get('rarity') == 'legendary']
    if legendary_chars:
        recommendations.append(f"Legendary characters detected: {', '.join(legendary_chars)}. These are excellent long-term investments.")
    
    # Affinity synergy
    affinities = [char.get('affinity') for char in characters if char.get('affinity')]
    affinity_counts = {}
    for affinity in affinities:
        affinity_counts[affinity] = affinity_counts.get(affinity, 0) + 1
    
    synergy_affinities = [affinity for affinity, count in affinity_counts.items() if count >= 2]
    if synergy_affinities:
        recommendations.append(f"Affinity synergy potential: {', '.join(synergy_affinities)} affinity characters can work well together.")
    
    # Ability upgrade potential
    for char in characters:
        abilities = analysis['ability_comparison'].get(char['name'], {})
        upgradeable = [slot for slot, data in abilities.items() if data.get('upgrade_potential', 0) > 0]
        if upgradeable:
            recommendations.append(f"{char['name']} has upgrade potential in: {', '.join(upgradeable)} abilities.")
    
    return recommendations


def _create_comparison_summary(characters: list, analysis: dict) -> str:
    """Create a concise summary of the comparison."""
    char_names = [char['name'] for char in characters]
    most_powerful = analysis['power_analysis']['most_powerful']['name']
    power_gap = analysis['power_analysis']['power_gap_percentage']
    
    roles = list(set([role_data['role'] for role_data in analysis['role_analysis'].values()]))
    
    summary = f"Compared {len(characters)} characters: {', '.join(char_names)}. "
    summary += f"{most_powerful} is the strongest. "
    summary += f"Power gap: {power_gap:.1f}%. "
    summary += f"Roles covered: {', '.join(roles)}."
    
    return summary