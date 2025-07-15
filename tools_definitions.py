from tools.db_rag_get_champion_details import db_rag_get_champion_details
from tools.db_rag_get_boss_details import db_rag_get_boss_details
from tools.db_rag_get_mechanic_details import db_rag_get_mechanic_details
from tools.db_rag_get_gameplay_details import db_rag_get_gameplay_details
from tools.db_rag_get_general_knowledge import db_rag_get_general_knowledge
from tools.db_rag_get_location_details import db_rag_get_location_details
from tools.db_rag_get_battle_details import db_rag_get_battle_details
from tools.db_get_ux_details import db_get_ux_details
from tools.db_get_champions_list import db_get_champions_list
from tools.db_get_screen_context_help import db_get_screen_context_help
from tools.db_rag_get_smalltalk import db_rag_get_smalltalk


# Import PostgreSQL database tool functions
from tools.db_get_champion_details import db_get_champion_details
from tools.db_get_champion_details_byid import db_get_champion_details_byid
from tools.db_get_battle_details import db_get_battle_details
from tools.db_get_battle_details_byid import db_get_battle_details_byid

# Import lore report tool function
from tools.db_get_lore_details import db_get_lore_details

# Import new PostgreSQL functions with trait filtering
from tools.db_find_strongest_champions import db_find_strongest_champions
from tools.db_find_champions_stronger_than import db_find_champions_stronger_than
from tools.db_get_champions_by_traits import db_get_champions_by_traits
from tools.db_compare_champions import db_compare_champions
from tools.db_find_champions import db_find_champions





from tools_functions import T3RNTool


TOOLS = [
    T3RNTool(
        name="db_get_champions_list",
        function=db_get_champions_list,
        description= 'Get complete list of all available champions',
        system_prompt="""

""",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        }
    )
]

















