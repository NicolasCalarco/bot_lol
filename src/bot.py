import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from config.auth import  token_telegram , token_riot, db_server, db_database, db_username, db_password
import psycopg2
import http
import urllib3
import json
http = urllib3.PoolManager()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, edu crack!")




async def add(update, context):
    if context.args:
        print(context.args)
        name = context.args[0]
        print(name)
        chat_id_telegram = update.effective_chat.id
        print(chat_id_telegram)
        #capturar el error si no existe el name
        summoner = riot().get_summoner_by_name(name)
        if summoner is not None:
            id_riot = summoner['id']
            logging.info(id_riot)
            account_id_riot = summoner['accountId']
            logging.info(account_id_riot)
            puuid_riot = summoner['puuid']
            logging.info(puuid_riot)
            name_riot = summoner['name']
            logging.info(name_riot)
            lolcito = db.get_lolcito(name_riot,chat_id_telegram)
            if lolcito :
               await context.bot.send_message(chat_id=update.effective_chat.id, text="El lolcito ya existe")
            else:
                db.insert_data_lolcito(name, chat_id_telegram, id_riot, account_id_riot, puuid_riot, name_riot, True)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="El lolcito se agrego correctamente")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Verificar nombre de cuenta")


async def list(update, context):
    chat_id_telegram = update.effective_chat.id
    lolcitos = db.get_lolcitos_by_chat_id_telegram(chat_id_telegram)
    if lolcitos:
        logging.info(lolcitos)
        for lolcito in lolcitos:
            
            logging.info(lolcito[0])
            name_lolcito = db.get_lolcito(lolcito[0],chat_id_telegram)
            logging.info(name_lolcito)
            
            await context.bot.send_message(chat_id=update.effective_chat.id, text=name_lolcito[0][0])
            logging.info("Se envio correctamente")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No hay lolcitos")


async def delete(update, context):
    chat_id_telegram = update.effective_chat.id
    if context.args:
        name = context.args[0]
        lolcito = db.verificar_lolcito(name,chat_id_telegram)
        logging.info(lolcito[0][0])
        if lolcito[0][0] >0:
            db.delete_lolcito(name,chat_id_telegram)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="El lolcito se elimino correctamente")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="El lolcito no existe")


#crear funcion para consultar el ranking actual de un lolcito por su id_riot en la api de riot
async def rank(update, context):
    chat_id_telegram = update.effective_chat.id
    lolcitos = db.get_lolcitos_by_chat_id_telegram(chat_id_telegram)
    logging.info(lolcitos)
    if lolcitos:
        for lolcito in lolcitos:
            logging.info(lolcito[0])
            stats_lolcito = riot().get_stats(lolcito[0])
            logging.info(stats_lolcito)
            #separar la información por tipo de queueType y guardar en variables tier , rank, lp, wins, losses
            for stats in stats_lolcito:
                if stats['queueType'] == "RANKED_SOLO_5x5":
                    Name = stats['summonerName']
                    tier = stats['tier']
                    rank = stats['rank']
                    lp = stats['leaguePoints']
                    wins = stats['wins']
                    losses = stats['losses']
                    #mostrar porcentaje de victorias solo dos decimales

                    pVictorias = str(round((wins/(wins+losses))*100,2))+' %'
                    logging.info(Name)
                    logging.info(tier)
                    logging.info(rank)
                    logging.info(lp)
                    logging.info(wins)
                    logging.info(losses)
                    logging.info(pVictorias)

                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Cuenta:  "+Name+"\nSolo/Duo: \n Tier: " + tier + " " + rank + " " + str(lp) + " LP \n Wins: " + str(wins) + " Losses: " + str(losses) + "\n Porcentaje de victorias: " + str(pVictorias))
                    
                elif stats['queueType'] == "RANKED_FLEX_SR":
                    Name = stats['summonerName']
                    tier = stats['tier']
                    rank = stats['rank']
                    lp = stats['leaguePoints']
                    wins = stats['wins']
                    losses = stats['losses']
                    pVictorias = str(round((wins/(wins+losses))*100,2))+' %'
                    logging.info(tier)
                    logging.info(rank)
                    logging.info(lp)
                    logging.info(wins)
                    logging.info(losses)

                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Cuenta:  "+Name+"\nFlex: \n Tier: " + tier + " " + rank + " " + str(lp) + " LP \n Wins: " + str(wins) + " Losses: " + str(losses) + "\n Porcentaje de victorias: " + str(pVictorias))
                else:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="Unranked")

    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No hay lolcitos")

async def help(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Comandos: \n /add [nombre de cuenta] -Agrega al listado de cuentas. \n /list -Muestra el listado de cuentas agregadas.\n /delete [nombre de cuenta] -Elimina una cuenta del listado.\n /rank  -Muestra el ranking de cada cuenta \n /help")
class db:
    def __init__(self):
        self.cnxn = psycopg2.connect(
            host=db_server,
            database=db_database,
            user=db_username,
            password=db_password
        )
        self.cursor = self.cnxn.cursor()
        self.create_table()

    def execute(self, query):
        self.cursor.execute(query)
        self.cnxn.commit()

    def fetch(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()
    

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS lolcito (
        id serial PRIMARY KEY,
        name varchar(255),
        chat_id_telegram varchar(255),
        id_riot varchar(100),
        account_id_riot varchar(100), 
        puuid_riot varchar(100),
        name_riot varchar(50) , 
        online boolean,
        cantidad_partidas int,
        cant_victorias int, 
        last_update TIMESTAMP default NOW())
        """
        self.execute(query)


    def insert_data_lolcito(self, name, chat_id_telegram,id_riot, account_id_riot, puuid_riot, name_riot, online):
        query = f"INSERT INTO lolcito (name, chat_id_telegram,id_riot, account_id_riot, puuid_riot, name_riot, online) VALUES ('{name}', '{chat_id_telegram}','{id_riot}', '{account_id_riot}', '{puuid_riot}', '{name_riot}', {online})"
        logging.info(query)
        self.execute(query)
        logging.info("Se inserto correctamente")

    #traer todos los registros de un chat_id_telegram
    def get_lolcitos_by_chat_id_telegram(self, chat_id_telegram):
        query = f"SELECT id_riot FROM lolcito WHERE chat_id_telegram = '{chat_id_telegram}'"
        return self.fetch(query)


    #crear funcion para traer un solo registro de la tabla lolcito con el name_riot
    def get_lolcito(self, name_riot, chat_id_telegram):

        query = f"SELECT name FROM lolcito WHERE id_riot = '{name_riot}' AND chat_id_telegram = '{chat_id_telegram}'"
        logging.info(query)
        return self.fetch(query)    
    
    def verificar_lolcito(self, name, chat_id_telegram):
        query = f"SELECT count(name) FROM lolcito WHERE name = '{name}' AND chat_id_telegram = '{chat_id_telegram}'"
        logging.info(query)
        return self.fetch(query)
        
        

    #crear funcion para traer todos los registros de la tabla lolcito
    def get_lolcitos(self):
        query = "SELECT * FROM lolcito"
        return self.fetch(query)

    #crear funcion para actualizar el registro , id_riot, account_id_riot, puuid_riot, name_riot, online
    def update_lolcito(self, id_riot, account_id_riot, puuid_riot, name_riot, online, name):
        query = f"UPDATE lolcito SET id_riot = '{id_riot}', account_id_riot = '{account_id_riot}', puuid_riot = '{puuid_riot}', name_riot = '{name_riot}', online = '{online}' WHERE name = '{name}'"
        self.execute(query)
    
    #crear funcion para actualizar el totalizador de victorias de un summoner
    def update_lolcito_victorias(self, cant_victorias, account_id_riot):
        query = f"UPDATE lolcito SET cant_victorias = '{cant_victorias}' WHERE name = '{account_id_riot}'"
        self.execute(query)

    #crear funcion para eliminar el registro de la tabla lolcito
    def delete_lolcito(self, name, chat_id_telegram):
        query = f"DELETE FROM lolcito WHERE name = '{name}' and chat_id_telegram = '{chat_id_telegram}'"
        logging.info(query)
        self.execute(query)
        logging.info("Se elimino correctamente")

class riot:
    
    def __init__(self):
       
        self.api_key = token_riot

    def get_summoner_by_name(self, name):
        #manejo de errores
        try:
            url = f"https://la2.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}?api_key={self.api_key}"
            r = http.request('GET', url)
            return json.loads(r.data.decode('utf-8'))
        except:
            return None
            

    
#crear funcion para consultar las partidas de un summoner
    def get_match_list(self, summoner_id):
        try:
            url = f"https://la2.api.riotgames.com/lol/match/v4/matchlists/by-account/{summoner_id}?api_key={self.api_key}"
            r = http.request('GET', url)
            return json.loads(r.data.decode('utf-8'))
        except:
            return None
            
#crear funcion para consultar los datos de una partida
    def get_match(self, match_id):
        try:
            url = f"https://la2.api.riotgames.com/lol/match/v4/matches/{match_id}?api_key={self.api_key}"
            r = http.request('GET', url)
            return json.loads(r.data.decode('utf-8'))
        except:
            return None
    def get_stats(self,id_riot):
        try:
            url = f"https://la2.api.riotgames.com/lol/league/v4/entries/by-summoner/{id_riot}?api_key={self.api_key}"
            r = http.request('GET', url)
            return json.loads(r.data.decode('utf-8'))
        except:
            return None

      
    


if __name__ == '__main__':
    application = ApplicationBuilder().token(token_telegram).build()
    db = db()
    db.create_table()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    add_handler = CommandHandler('add', add)
    application.add_handler(add_handler)

    list_handler = CommandHandler('list', list)
    application.add_handler(list_handler)

    delete_handler = CommandHandler('delete', delete)
    application.add_handler(delete_handler)

    ranking_handler = CommandHandler('rank', rank)
    application.add_handler(ranking_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    application.run_polling()

