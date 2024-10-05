import json
import logging
logger = logging.getLogger(__name__)

# function to read config data from a config.json file and 
# return the values in a dictionary

def readConfigFile(path:str)->dict[str,str]:
    with open(path) as f:
        data = json.load(f)

    config_output= {
    "api_key": data["api_key"],
    "city":data["city"],
    "bot_token":data["bot_token"]
    }
    logger.info("config map correctly loaded")

    return config_output


