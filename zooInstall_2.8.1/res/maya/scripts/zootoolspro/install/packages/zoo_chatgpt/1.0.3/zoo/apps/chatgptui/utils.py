import os, openai
from zoo.apps.chatgptui import constants


def hasApiKey():
    currentGlobalKey = os.getenv(constants.OPENAI_ENV)
    return currentGlobalKey is not None and openai.api_key is not None

def validateKey(key):
    try:
        openai.api_key = key
        openai.Model.list()
    except openai.error.AuthenticationError:
        openai.api_key = None
        return False
    return True


def setAPIkey(key):
    openai.api_key = key
    os.environ[constants.OPENAI_ENV] = key

def setApiKeyIfFound():
    """Sets the openai api key if it's found in the environment variables as `ZOO_OPENAI_KEY`

    :rtype: bool
    """
    currentGlobalKey = os.getenv(constants.OPENAI_ENV)
    if currentGlobalKey is not None:
        openai.api_key = currentGlobalKey
        return True
    return False
