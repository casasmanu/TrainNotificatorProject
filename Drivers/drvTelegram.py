import telebot
import logging
logger = logging.getLogger(__name__)

# --------------------- Import Variables ----------------------- #

import __main__

#define usefull functions
def bot_send_msg(msg):
  try:
    bot = telebot.TeleBot(__main__.botToken)  
    bot.send_message(__main__.destinatary,msg)
    logger.info("message sent succesfully")
  except:
    logger.error("Problem while trying to send a msg")
  return


def getNewUsers():
 bot = telebot.TeleBot(__main__.botToken)  
 arrRawData=bot.get_updates()
 arrIds=[]
 
 try:
    for i in arrRawData:
      if(i.message!=""):
        #get important values from the msg
        userName=i.message.chat.first_name
        userId=str(i.message.from_user.id)
        #if the msg was already catched, skip to the next msg
        if(checkUserExistsInArray(arrIds,userId)):
            continue

        arrIds.append([userName,userId])
    return arrIds
 except Exception as error:
    # handle the exception
    print("An exception occurred:", error)

def checkUserExistsInArray(array,userId):
  output = False
  for i in array:
    if (i[1]==userId):
        output=True

  return output

