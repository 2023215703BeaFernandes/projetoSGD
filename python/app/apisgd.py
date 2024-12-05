##
## =============================================
## ======== Sistema de Gestão de Dados =========
## ============== LECD  2024/2025 ==============
## =============================================
## =================== Demo ====================
## =============================================
## =============================================
## === Department of Informatics Engineering ===
## =========== University of Coimbra ===========
## =============================================
##
## Authors: 
##   José D'Abruzzo Pereira <josep@dei.uc.pt>
##   Gonçalo Carvalho <gcarvalho@dei.uc.pt>
##   University of Coimbra


'''
How to run?
$ python3 -m venv proj_sgd_env
$ source proj_sgd_env/bin/activate
$ pip3 install flask
$ pip3 install jwt
$ pip3 install psycopg2-binary
$ python3 apisgd.py
--> Ctrl+C to stop
$ deactivate
'''

import flask
import logging
import psycopg2
import time
import jwt
import json
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import traceback


app = flask.Flask(__name__) 
password_token= "token123sgd"

statusCode = {
        'success': 200,
        'bad request': 400,
        'unauthorized': 401,
        'not_found': 404,
        'forbidden': 403,
        'internal_error': 500
    }
##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    # NOTE: change the host to "db" if you are running as a Docker container
    db = psycopg2.connect(user = "postgres",
                            password = "projetosgd",
                            host = "localhost", #"db",
                            port = "5432",
                            database = "projetosgd")
    return db




@app.route('/') 
def inicio(): 
    return """

    rest API- sgd  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/> Desenvolvido por: Beatriz Fernandes (2023215703) 
    """

def gerar_token (id_users):
    payload={
        "id": id_users,
        "tempo_expiração": time.time()+1800 #30min
    }
    token= jwt.encode(payload, password_token, algorithm='HS256')
    return token

def gerar_seats(capacity):
    colunas=6
    filas= capacity//colunas
    lugares=[]
    for fila in range (1,filas+1):
        for coluna in range(1,colunas+1):
            lugar= str(fila)+ chr(64+coluna)
            lugares.append(lugar)
    return lugares
    
def verificar_token():
    token= flask.request.headers.get('Authorization') #Temos de explicar isto
    if not token:
        return flask.jsonify({'status': statusCode['unauthorized'], 'message': 'token não encontrado'}),401
    try:
        if token.startswith("Bearer"):
            token = token[7:]
        payload= jwt.decode(token,password_token, algorithms='HS256' )

        if payload["tempo_expiração"] < time.time():
            return flask.jsonify({'status': statusCode['unauthorized'], 'message': 'tempo expirado'}),401
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return flask.jsonify({'status': statusCode['unauthorized'], 'message': 'tempo expirado'}),401
    except jwt.InvalidTokenError:
        return flask.jsonify({'status': statusCode['unauthorized'], 'message': 'token inválido'}),401

def verificar_admin():
    payload= verificar_token()
    if isinstance(payload, tuple):      #antes tinha dict  #verifica se é um erro(resposta JSON)
        return payload
    
    users_id_users = payload["id"]
    
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM administrator WHERE users_id_users=%s", (users_id_users,))
    row=cur.fetchone()
    if row and row[0]>0:
        return payload
    else:
        return flask.jsonify({"status": statusCode['forbidden'], "message": "Acesso restrito aos administradores"}), 403

def verificar_member():
    resultado= verificar_token()
    if isinstance(resultado, tuple):  
        return resultado
    conn= db_connection()
    cur=conn.cursor()
    users_id_users=resultado["id_users"] 
    cur.execute("SELECT * FROM member WHERE users_id_users=%s", (users_id_users,))
    row= cur.fetchone
    if row:
        return {"status": "success", "message": "Membro da crew válido"}
    else:
        return {"status": "error", "message": "Membro da crew inválido"}
    
def verificar_passenger():
    resultado= verificar_token
    if isinstance(resultado, tuple):  
        return resultado
    conn= db_connection()
    cur=conn.cursor()
    users_id_users=resultado["id_users"]
    cur.execute("SELECT * FROM passenger WHERE users_id_users=%s", (users_id_users,))
    row= cur.fetchone
    if row:
        return {"status": "success", "message": "Passenger válido"}
    else:
        return {"status": "error", "message": "Passenger inválido"}   
     
def verificar(payload, necessario):
    for chave in necessario:
        if chave not in payload:
            response={'status': statusCode['bad request'], 'message': f'{chave} tem de estar no payload'}
            return flask.jsonify(response)
    return None


##
##      Demo GET
##
## Obtain all users, in JSON format
##
## To use it, access: 
## 
##   http://localhost:8080/users/
##

@app.route("/check_seats", methods=['GET']) 
def available_seat():            #quantidade de lugares disponiveis em um determinado voo
    logger.info("###              DEMO: GET /check_seats            ###");   
    payload = flask.request.get_json()

    logger.info("---- lugares disponíveis  ----")
    logger.debug(f'payload: {payload}')
    lugares={}
    for key, value in payload.items():
        lugares[key.lower()]= value
        
    if 'flight_code' not in lugares:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'flight_code value não está no payload'})

    if 'id_schedule' not in lugares:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'id_schedule value não está no payload'})
    
    flight_code= lugares['flight_code']  
    id_schedule= lugares['id_schedule']
    conn = db_connection()
    cur = conn.cursor()
    
    #ver o id_fligth que corresponde ao fligth_code
    cur.execute("SELECT id_fligth FROM fligth WHERE flight_code = %s", (flight_code,))
    fligth= cur.fetchone()
    if not fligth:
        return flask.jsonify({'status': statusCode['not_found'], 'message': 'voo não encontrado'})
    id_flight= fligth[0]
    
    #vemos se o schedule desse id
    cur.execute("SELECT id_schedule FROM schedule WHERE fligth_id_fligth = %s AND id_schedule = %s", (id_flight, id_schedule))
    schedule = cur.fetchone()
    if not schedule:
        return flask.jsonify({'status':statusCode['not_found'], 'message': 'schedule não foi encontrado para esse voo especifico'})
    
    #lugares disponiveis
    cur.execute("SELECT ts.seat_id_seat FROM ticket_seat AS ts JOIN schedule AS s ON s.fligth_id_fligth=%s WHERE ts.seat_availability= TRUE AND s.id_schedule=%s", (id_flight, id_schedule))
    resultado= cur.fetchall()
    lugares_disponiveis=[]
    for row in resultado:
        lugares_disponiveis.append(row[0])
    conn.close ()
    return flask.jsonify({'status': statusCode['success'], 'errors': None, 'results':lugares_disponiveis})

@app.route("/check_routes", methods=['GET']) 
def available_routes():
    logger.info("###              DEMO: GET /check_routes            ###");
    payload= flask.request.get_json()
    
    logger.info("---- rotas disponíveis  ----")
    logger.debug(f'payload: {payload}')
    rotas={}
    for key, value in payload.items():
        rotas[key.lower()]= value
    
    if 'origin_airport' not in rotas:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'origin_airport não está no payload'})

    if 'destination_airport' not in rotas:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'destination_airport não está no payload'})
    
    origin_airport= rotas['origin_airport']  
    destination_airport= rotas['destination_airport']
    
    conn= db_connection()
    cur= conn.cursor()
    
    cur.execute("SELECT id_fligth, flight_code, airport_id_airport= %s AND airport_id_airport1=%s FROM fligth", (origin_airport, destination_airport))
    rows= cur.fetchall()
    resultado=[]
    if not rows:
            return flask.jsonify({'status': statusCode['not_found'], 'message': 'Nenhuma rota encontrada para os aeroportos fornecidos'})
    if rows:
        for row in rows:
            id_fligth= row[0]
            flight_code= row[1]
    cur.execute("SELECT * FROM schedule WHERE fligth_id_fligth= %s",(id_fligth,))
    resultados_schedule=[]
    schedules= cur.fetchall()
    for schedule in schedules:
        dados={"id_schedule": schedule[0],"fligth_date":schedule[1], "administrator_users_id_users": schedule[2], "crew_id_crew":schedule[3], "fligth_id_fligth":schedule[4]}
        resultados_schedule.append(dados)
    
    resultado.append({"origin_airport":origin_airport, "destination_airport":destination_airport,"flight_code":flight_code, "schedules":resultados_schedule})
    conn.close()
    return flask.jsonify({'status': statusCode['success'], 'errors': None, 'results':resultado})
 


##
##      Demo GET
##
## Obtain department with ndep <ndep>
##
## To use it, access: 
## 
##   http://localhost:8080/departments/10
##

@app.route("/topDestinations/<n>", methods=['GET']) 
def get_n_destinations(n):
    logger.info("###              DEMO: GET /topDestinations/<n>              ###");   
    logger.debug(f'n: {n}')

    conn = db_connection()
    cur = conn.cursor()
    n= int(n)
    results=[]
    try:
        cur.execute("SELECT fligth.airport_id_airport1 AS destination_airport, COUNT(schedule.id_schedule) AS number_flights FROM fligth JOIN schedule ON fligth.id_fligth= schedule.fligth_id_fligth where fligth.departure_time>= DATE_TRUNC ('month', CURRENT_DATE)- INTERVAL '12 months' GROUP BY fligth.airport_id_airport1 ORDER BY number_flights DESC")   
        rows= cur.fetchall()
        for row in rows[:n]:
            destination_airport = row[0]
            number_flights = row[1]
            results.append({"destination_airport": destination_airport, "number_flights": number_flights})

            response= {'status': statusCode['success'], 'results': results}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response ={'status': statusCode['internal_error'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)   
   
@app.route("/topRoutes/<n>", methods=['GET']) 
def get_n_routes(n):
    logger.info("###              DEMO: GET /topRoutes/<n>              ###");   
    logger.debug(f'n: {n}')

    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT TO_CHAR(fligth.departure_time, 'Month_YYYY') AS month, fligth.id_fligth AS flight_id, COUNT(ticket_seat.id_tickets) AS total_passengers FROM ticket_seat JOIN booking ON ticket_seat.booking_id_booking = booking.id_booking JOIN schedule ON booking.schedule_id_schedule = schedule.id_schedule JOIN fligth ON schedule.fligth_id_fligth = fligth.id_fligth WHERE ticket_seat.seat_availability = FALSE AND fligth.departure_time >= CURRENT_DATE - INTERVAL '12 months' GROUP BY TO_CHAR(fligth.departure_time, 'Month_YYYY'), fligth.id_fligth ORDER BY month DESC, total_passengers DESC")
        rows= cur.fetchall()
        results={}
        for row in rows:
            month= row[0]
            flight_id= row[1]
            total_passengers= row[2]
            if month not in results:
                results[month]= []
                results[month].append({"flight_id": flight_id, "total_passengers": total_passengers})

        response= []
        for month, fligths in results.items():
            voos= fligths[:n] #limito o numero d voos retornados a n
            dados_mes= {"month": month, "topN": voos}
            response.append(dados_mes)
        
        result={'status': statusCode['success'], 'result': response}
    except (Exception, psycopg2.DatabaseError) as error:
        result= {'status': statusCode['internal_error'], 'errors:':str(error)}
    finally:
        cur.close()
        conn.close()
    return flask.jsonify(result)

##
##      Demo POST
##
## Add a new department in a JSON payload
##
## To use it, you need to use postman or curl: 
##
##   curl -X POST http://localhost:8080/departments/ -H "Content-Type: application/json" -d '{"localidade": "Polo II", "ndep": 69, "nome": "Seguranca"}'
##

@app.route("/fligth/", methods=['POST'])  
def criar_flight():
    logger.info("###              DEMO: POST /flight              ###");   
   
    payload=verificar_admin()
    if isinstance(payload, tuple):   #verifica se é uma resposta JSON de erro
        return payload
    id_admin= payload['id']

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new flight  ----")
    payload= flask.request.get_json()
    logger.debug(f'payload: {payload}')
    dadosFlight={}
    for key, value in payload.items():
        dadosFlight[key.lower()]= value
        
    required_fields = ['departure_time', 'arrivel_time', 'capacity', 'origin', 'destination', 'flight_code']
    for field in required_fields:
        if field not in dadosFlight:
            response = {'status': statusCode['bad request'], 'message': f'{field} value not in payload'}
            return flask.jsonify(response)
    
    # Verifica se o flight_code já existe
    cur.execute("SELECT flight_code FROM fligth WHERE flight_code = %s", (dadosFlight["flight_code"],))
    verificarVoo = cur.fetchone()
    if verificarVoo is not None:
        response = {'status': statusCode['conflict'], 'message': 'flight_code já existe, escolha outro.'}
        return flask.jsonify(response) 
      
    #dá-nos o id do aeroporto de origem   
    cur.execute("SELECT id_airport FROM airport WHERE name = %s", (dadosFlight["origin"],))
    origin_row = cur.fetchone()
    if origin_row is None:
        response = {'status': statusCode['bad request'], 'message': 'aeroporto de origem não encontrado'}
        return flask.jsonify(response)
    else:
        logger.debug(f'origin_row: {origin_row}')
        origin_id = origin_row[0]  # ID do aeroporto de origem

    #dá-nos o id do aeroporto de chegada  
    cur.execute("SELECT id_airport FROM airport WHERE name = %s", (dadosFlight["destination"],))
    destination_row = cur.fetchone()
    if destination_row is None:
        response = {'status': statusCode['bad request'], 'message': 'aeroporto de destino não encontrado'}
        return flask.jsonify(response)
    else:
        logger.debug(f'origin_row: {destination_row}')
        destination_id = destination_row[0]  # ID do aeroporto de destino

    try:
        capacity= int(dadosFlight["capacity"])
        seats= gerar_seats(capacity)
        logger.debug(f'Assentos gerados: {seats}')
    except ValueError as e:
        response= {'status': statusCode['bad request'], 'message': 'não foram criados lugares'}
        return flask.jsonify(response)


    # parameterized queries, good for security and performance
    statement = "INSERT INTO fligth (departure_time, arrivel_time, capacity, flight_code, airport_id_airport, airport_id_airport1, administrator_users_id_users) VALUES ( %s, %s, %s, %s, %s, %s, %s )"  

    values = (dadosFlight["departure_time"],dadosFlight["arrivel_time"],dadosFlight["capacity"],dadosFlight["flight_code"],origin_id,destination_id,id_admin)  
    try:
        cur.execute(statement, values)
        conn.commit()
        result = {'status': statusCode['success'], 'results:':dadosFlight['flight_code']}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result ={'status': statusCode['success'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(result)

@app.route("/schedule/", methods=['POST']) 
def criar_schedule():   
    logger.info("###              DEMO: POST /schedule              ###");   
    
    payload=verificar_admin()
    if isinstance(payload, tuple):   #verifica se é uma resposta JSON de erro
        return payload
    
    id_admin= payload['id']
    

    conn = db_connection()
    cur = conn.cursor()
    payload = flask.request.get_json()
    logger.info("---- new schedule  ----")
    logger.debug(f'payload: {payload}')
    for key, value in payload.items():
        payload[key.lower()]= value
        
    if 'fligth_date' not in payload:
        response = {'status': statusCode['bad request'], 'message': 'fligth_date value not in payload'}
        return flask.jsonify(response)
    if 'fligth_code' not in payload:
        response = {'status': statusCode['bad request'], 'message': 'fligth_code value not in payload'}
        return flask.jsonify(response)
    
    #vai guardar o id do voo em questão
    cur.execute("SELECT id_fligth,departure_time FROM fligth WHERE flight_code = %s", (payload['fligth_code'],))
    resultado= cur.fetchone()
    if resultado is None:
        return flask.jsonify({'status': 'not_found', 'message': 'flight_code not found'})
    id_fligth, departure_time= resultado
    
    #compara se as datas sao iguais
    if payload['fligth_date'] != str(departure_time.date()):  # Comparação apenas da data
        return flask.jsonify({'status': 'bad request', 'message': 'fligth_date nao corresponde a data deste voo'})
    
    
    #ver se já existe um horario
    cur.execute("SELECT COUNT(*) FROM schedule WHERE fligth_id_fligth= %s AND fligth_date= %s", (id_fligth, payload['fligth_date']))
    if cur.fetchone()[0]>0:
        return flask.jsonify({'status': 'bad request', 'message': 'schedule já existe'})
    
    #escolher a crew
    cur.execute("SELECT id_crew FROM crew WHERE id_crew NOT IN (SELECT id_crew FROM schedule WHERE fligth_date=%s)", (payload['fligth_date'],))
    resultado_crew= cur.fetchone()
    if resultado_crew is None:
        return flask.jsonify({'status': 'bad request', 'message': 'crew não encontrada'})
    id_crew= resultado_crew[0]
        
    # parameterized queries, good for security and performance
    statement = "INSERT INTO schedule (fligth_date, administrator_users_id_users, crew_id_crew, fligth_id_fligth) VALUES ( %s, %s, %s, %s)"

    values = (payload["fligth_date"],id_admin, id_crew, id_fligth)

    try:
        cur.execute(statement, values)
        conn.commit()
        result = {'status': statusCode['success'], 'results:':'schedule_id'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result ={'status': statusCode['success'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(result)

@app.route("/admin/", methods=['POST']) 
def criar_administrator():
    logger.info("###              DEMO: POST /admin/create              ###");
    
    payload=verificar_admin()
    if isinstance(payload, tuple):   
        return payload
    
    payload = flask.request.get_json()
    resultado_user= criar_user()
    resultado_user_json = resultado_user.get_json()
    if resultado_user_json['status'] != statusCode['success']:
        return resultado_user_json

    conn = db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id_users FROM users WHERE name = %s AND email = %s AND password = %s", 
                    (payload['name'], payload['email'], payload['password']))
        id_users= cur.fetchone()
        
        cur.execute("INSERT INTO administrator (users_id_users) VALUES (%s)", (id_users[0],))
        conn.commit()
        return {'status': statusCode['success'], 'message': 'Administrador criado com sucesso.'}

    except Exception as e:
        logger.error(e)
        return {'status': statusCode['internal_error'], 'message': 'Erro ao criar administrador.'},500
    
    finally:
        if conn is not None:
            conn.close()
            
@app.route("/passenger/", methods=['POST'])
def criar_passenger():
    logger.info("###              DEMO: POST /passenger/create              ###");
    payload= flask.request.get_json()
    resultado_user= criar_user()
    resultado_user_json = resultado_user.get_json()
    if resultado_user_json['status'] != statusCode['success']:
        return resultado_user_json
    conn= db_connection()
    cur= conn.cursor()
    try:
        cur.execute("SELECT id_users FROM users WHERE name = %s AND email = %s AND password = %s", 
                    (payload['name'], payload['email'], payload['password']))
        id_user= cur.fetchone()
        
        cur.execute("INSERT INTO passenger (users_id_users) VALUES (%s)", (id_user[0],))
        conn.commit()
        return {'status': statusCode['success'], 'message': 'Passageiro criado com sucesso.'}

    except Exception as e:
        logger.error(e)
        return {'status': statusCode['internal_error'], 'message': 'Erro ao criar passageiro.'}
    
    finally:
        if conn is not None:
            conn.close()
 
@app.route("/member/", methods=['POST'])
def criar_member():
    logger.info("###              DEMO: POST /member/create              ###");
    payload= flask.request.get_json()
    resultado_user= criar_user()
    resultado_user_json = resultado_user.get_json()
    if resultado_user_json['status'] != statusCode['success']:
        return resultado_user_json
    conn= db_connection()
    cur= conn.cursor()
    try:
        cur.execute("SELECT id_users FROM users WHERE name = %s AND email = %s AND password = %s", 
                    (payload['name'], payload['email'], payload['password']))
        id_user= cur.fetchone()
        
        cur.execute("INSERT INTO member (users_id_users) VALUES (%s)", (id_user[0],))
        conn.commit()
        return {'status': statusCode['success'], 'message': 'Membro da crew criado com sucesso.'}

    except Exception as e:
        logger.error(e)
        return {'status': statusCode['internal_error'], 'message': 'Erro ao criar membro da crew.'}
    
    finally:
        if conn is not None:
            conn.close()

@app.route("/users/", methods=['POST']) 
def criar_user():
    logger.info("###              DEMO: POST /user              ###");   
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new user  ----")
    logger.debug(f'payload: {payload}')
    dadosUser={}
    for key, value in payload.items():
        dadosUser[key.lower()]= value
        
    if 'name' not in dadosUser:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'name value not in payload'})

    if 'email' not in dadosUser:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'email value not in payload'})
    if 'password' not in dadosUser:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'password value not in payload'})


    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO users (name, email, password) 
                          VALUES ( %s,   %s ,   %s )"""

    values = (payload["name"], payload["email"], payload["password"])

    try:
        cur.execute(statement, values)
        conn.commit()
        response = {'status': statusCode['success'], 'results:':'user_code'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response ={'status': statusCode['error'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route("/airport/", methods=['POST'])   
def criar_airport():
    logger.info("###              DEMO: POST /airport/create              ###");
    
    payload=verificar_admin()
    if isinstance(payload, tuple):  
        return payload
    admin_id = payload["id"]
    payload = flask.request.get_json()  
    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new airport  ----")
    logger.debug(f'payload: {payload}')
    dadosAirport={}
    for key, value in payload.items():
        dadosAirport[key.lower()]= value
    
    if 'city' not in dadosAirport:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'city value not in payload'})
    if 'name' not in dadosAirport:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'name value not in payload'})
    if 'country' not in dadosAirport:
        return flask.jsonify(response = {'status': statusCode['bad request'], 'message': 'country value not in payload'})
    
    try:
        cur.execute("SELECT COUNT(*) FROM airport WHERE city = %s AND name = %s AND country = %s", 
            (payload["city"], payload["name"], payload["country"]))
        count = cur.fetchone()[0]
        if count > 0:
            return flask.jsonify({'status': statusCode['bad request'], 'message': 'Aeroporto já existe.'}), statusCode['bad request']
        
        cur.execute("INSERT INTO airport (city, name, country, administrator_users_id_users) VALUES ( %s,   %s ,   %s ,   %s )", (payload["city"], payload["name"], payload["country"], admin_id))
        conn.commit()
        response = {'status': statusCode['success'], 'results:':'airport_code'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response ={'status': statusCode['error'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)            

@app.route("/crew/", methods=['POST'])       #VERIFICAR SE ESSES ID EXISTEM NO MEMBER
def criar_crew():
    logger.info("###              DEMO: POST /crew/create              ###");
    payload= verificar_admin()
    if isinstance(payload, tuple):   #verifica se é o payload é um tuple
        return payload
    
    id_admin= payload['id'] 
    
    payload= flask.request.get_json()
    logger.info("---- Creating Crew ----")
    logger.debug(f'Payload: {payload}')  #nós vamos mandar 2 listas de id de members que ja foram criados, mas uma lista de flight_attendants e outra de pilots
    if "flight_attendants" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'flight_attendants value not in payload'})
    if "pilots" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'pilots value not in payload'})

    flight_attendants = payload.get('flight_attendants', [])
    pilots = payload.get('pilots', [])

    conn= db_connection()
    cur= conn.cursor()
    try:
        cur.execute("INSERT INTO crew (administrator_users_id_users) VALUES (%s)", (id_admin,))
        cur.execute("SELECT * FROM crew WHERE administrator_users_id_users = %s", (id_admin,))
        crews= cur.fetchall() #vai dar as crews todas
        ultima= crews[-1] #vai a ultima que foi inserida
        crew_id = ultima[0]  # Obtém o ID da nova crew
        conn.commit()
        
        for id_member in flight_attendants:
            cur.execute("SELECT COUNT(*) FROM member WHERE users_id_users = %s", (id_member,))
            if cur.fetchone()[0] == 0:
                return {'status': 400, 'message': f'O membro {id_member} não existe na tabela member.'}
            
            cur.execute(
                "INSERT INTO flight_attendant (crew_id_crew, member_users_id_users) VALUES (%s, %s)",
                (crew_id, id_member)
            )
            
        for id_member in pilots:
            cur.execute("SELECT COUNT(*) FROM member WHERE users_id_users = %s", (id_member,))
            if cur.fetchone()[0] == 0:
                return {'status': 400, 'message': f'O membro {id_member} não existe na tabela member.'}
            
            cur.execute(
                "INSERT INTO pilot (crew_id_crew, member_users_id_users) VALUES (%s, %s)",
                (crew_id, id_member)
            )
            
        conn.commit()
        response = {'status': 200, 'message': 'Crew criada com sucesso.', 'crew_id': crew_id}
    except Exception as e:
        logger.error(f"Erro ao criar crew: {e}")
        response = {'status': 500, 'message': f'Erro ao criar crew: {str(e)}'}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route("/criarbooking/", methods=['POST'])  
def criar_booking():
    payload= flask.request.get_json()
    logger.info("---- Creating booking ----")
    logger.debug(f'Payload: {payload}')  
    
    if "numbertickets" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'numbertickets value not in payload'})
    if "seat_id" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'id_passengers value not in payload'})
    if "typeluggage" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'typeluggage value not in payload'})
    if "id_schedule" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'id_schedule value not in payload'})
    if "fligth_code" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'fligth_code value not in payload'})
    if "id_passengers" not in payload:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'id_passengers value not in payload'})

    numbertickets = payload['numbertickets']
    seat_id = payload['seat_id']
    typeluggage = payload['typeluggage']
    id_schedule = payload['id_schedule']
    fligth_code = payload['fligth_code']
    id_passengers = payload['id_passengers']
    
    if len(seat_id)!= numbertickets or len(id_passengers)!= numbertickets:
        return flask.jsonify({'status': statusCode['bad request'], 'message': 'deve corresponde tudo'})
    
    conn= db_connection()
    cur= conn.cursor()
    
    try:
        #schedule existe ou nao
        logger.debug(f"Checking if schedule {id_schedule} exists")
        cur.execute("SELECT id_schedule FROM schedule WHERE id_schedule = %s", (id_schedule,))
        resultado= cur.fetchone()
        if resultado is None:
            return flask.jsonify({'status': 'not found', 'message': 'id_schedule not found'})
        schedule= resultado[0]
        
        #ver se o voo existe e a sua capacidade
        logger.debug(f"Checking if flight {fligth_code} exists and its capacity")
        cur.execute("SELECT capacity FROM fligth WHERE flight_code= %s", (fligth_code,))
        resultado= cur.fetchone()
        if resultado is None:
            return flask.jsonify({'status': statusCode['not found'], 'message': 'voo nao encontrado'})
        capacity= resultado[0]
        
        #ver se existe o schedule e se o voo consegue levar mais pesssoas
        logger.debug(f"Checking if the flight has available capacity for {numbertickets} passengers")
        cur.execute("SELECT COUNT (*) FROM booking WHERE schedule_id_schedule=%s",(id_schedule,))
        resultado= cur.fetchone()
        if resultado is None:
            return flask.jsonify({'status': statusCode['not found'], 'message': 'schedule não identificado'})
        numero= resultado[0]
        if numero+ numbertickets>= capacity:
            return flask.jsonify({'status': statusCode['internal_error'], 'message': 'voo lotado'})

        #cria a reserva
        logger.debug(f"Inserting booking with {numbertickets} tickets")
        cur.execute("INSERT INTO booking (numbertickets, type_luggage, schedule_id_schedule) VALUES (%s, %s,%s)", (numbertickets, typeluggage, schedule))
        conn.commit()
        
        #ultimo id d utima reserva
        cur.execute("SELECT id_booking FROM booking WHERE schedule_id_schedule=%s ORDER BY id_booking DESC limit 1",(id_schedule,))
        resultado= cur.fetchone()
        if resultado is None:
            return flask.jsonify({'status': statusCode['not found'], 'message': 'erro para o id_booking'})
        id_booking= resultado[0]
        
        #atualiza para false o lugar
        logger.debug(f"Assigning seats and passengers to the booking")
        for i in range(numbertickets):
            seat_id_val= seat_id[i]
            passenger_id= id_passengers[i]
            cur.execute("UPDATE ticket_seat SET booking_id_booking=%s, seat_availability= false WHERE seat_id_seat = %s", (id_booking, seat_id_val))
            cur.execute("SELECT * FROM booking_passenger WHERE booking_id_booking=%s AND passenger_users_id_users=%s", (id_booking, passenger_id))
            resultado= cur.fetchone()
            if resultado is None:
                logger.warning(f"Passenger {passenger_id} is already associated with booking {id_booking}. Skipping insertion.")
                continue
            cur.execute("INSERT INTO booking_passenger(booking_id_booking, passenger_users_id_users) VALUES (%s, %s)", (id_booking, passenger_id))
       
        return flask.jsonify({'status': statusCode['success'], 'results': id_schedule})
    except Exception as e:
        logger.error(f'Error creating booking: {str(e)}')
        return flask.jsonify({'status': statusCode['internal_error'], 'message': str(e)})
    finally:
        if conn is not None:
            conn.close()
        
      
##
##      Demo PUT
##s
## Update a department based on the a JSON payload
##
## To use it, you need to use postman or curl: 
##
##   curl -X PUT http://localhost:8080/departments/ -H "Content-Type: application/json" -d '{"ndep": 69, "localidade": "Porto"}'
##


@app.route('/login', methods=['PUT'])
def login():
    logger.info("###              DEMO: PUT /users            ###")
    conn = db_connection()
    cur = conn.cursor()


    try:
        payload = flask.request.get_json()
        name = payload.get('name')
        password = payload.get('password')

        if not name or not password:
            return flask.jsonify({"error": "Name and password are required"}), statusCode['bad_request']

        # Check if user exists
        cur.execute("SELECT * FROM users WHERE name = %s", (name,))
        rows = cur.fetchall()
        if len(rows) == 0:
            return flask.jsonify({"error": "User not found"}), statusCode['not_found']

        row = rows[0]
        stored_password = row[3]  # Assuming 'password' column exists in the `users` table.

        # Verify password (if stored as a hashed value, use a hashing library like bcrypt or hashlib to compare)
        if stored_password != password:
            return flask.jsonify({"error": "Invalid password"}), statusCode['unauthorized']

        # Login successful
        token= gerar_token(id_users=row[0])
        return flask.jsonify({
            "message": "Login successful", 
            "user_id": row[0],
            "token": token       # Inclui o token JWT
        }), statusCode['success']
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return flask.jsonify({"error": "Internal server error"}), statusCode['internal_error']

    finally:
        cur.close()
        conn.close()





##########################################################
## MAIN
##########################################################
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
                              # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    time.sleep(1) # just to let the DB start before this print :-)


    logger.info("\n---------------------------------------------------------------\n" + 
                  "API v1.0 online: http://localhost:8080/")


    
    # NOTE: change to 5000 or remove the port parameter if you are running as a Docker container
    app.run(host="127.0.0.1", port=8080, debug=True, threaded=True)
    
