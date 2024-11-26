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

 
from flask import Flask, jsonify, request
import logging
import psycopg2
import time
import jwt
import json

app = Flask(__name__) 
password= "token123sgd"

@app.route('/') 
def inicio(): 
    return """

    rest API- sgd  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/> Desenvolvido por: Beatriz Fernandes (2023215703) e Matilde Rebelo (2023231257)
    """

statusCode={
    'success':200,
    'bad_request':400,
    'internal_error':500
}


def gerar_token (id_users):
    payload={
        "id": id_users,
        "tempo_expiração": time.time()+1800 #30min
    }
    token= jwt.encode(payload, password, algorithm='HS256')
    return token

def verificar_token(id_users):
    token= gerar_token(id_users)
    try:
        descodificar_payload= jwt.decode(token, password, algorithms=["HS256"])

        # Se o token for válido, retornar os dados decodificados
        return {"status": "success", "user_id": descodificar_payload["id"], "message": "Token válido"}

    except jwt.ExpiredSignatureError:
        # Se o token expirou
        return {"status": "error", "message": "Token expirado"}
    
    except jwt.InvalidTokenError:
        # Se o token é inválido
        return {"status": "error", "message": "Token inválido"}
    
@app.route("/users/", methods=['POST'])
def criar_user():
    logger.info("###              DEMO: POST /user              ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new user  ----")
    logger.debug(f'payload: {payload}')
    dadosUser={}
    for key, value in payload.items():
        dadosUser[key.lower()]= value
        
    if 'name' not in dadosUser:
        response = {'status': statusCode['bad_request'], 'message': 'name value not in payload'}
        return jsonify(response)
    if 'email' not in dadosUser:
        response = {'status': statusCode['bad_request'], 'message': 'email value not in payload'}
        return jsonify(response)
    if 'password' not in dadosUser:
        response = {'status': statusCode['bad_request'], 'message': 'password value not in payload'}
        return jsonify(response)

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO Airport (name, email, password) 
                          VALUES ( %s,   %s ,   %s )"""

    values = (payload["name"], payload["email"], payload["password"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'status': statusCode['sucess'], 'results:':'user_code'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result ={'status': statusCode['sucess'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)
    
##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    # NOTE: change the host to "db" if you are running as a Docker container
    db = psycopg2.connect(user = "projetoSGD",
                            password = "projetosgd",
                            host = "localhost", #"db",
                            port = "5432",
                            database = "companhiaarea")
    return db




##
##      Demo GET
##
## Obtain all departments, in JSON format
##
## To use it, access: 
## 
##   http://localhost:8080/departments/
##

#ver rotas available
'''@app.route("/rotas/", methods=['GET'], strict_slashes=True)
def get_available_route():
    logger.info("###              DEMO: GET /rotas              ###")
    dadosFlight= request.get_json()   

    conn = db_connection()
    cur = conn.cursor()

    #cur.execute("SELECT ndep, nome, local FROM dep")
    #rows = cur.fetchall()

    #payload = []
    logger.debug(f'Post/ available_routes-payload:{dadosFlight}')
    dados={}
    if dadosFlight:
        for key, value in dados.items():
            dados[key.lower()]=value
            
    #statement= "SELECT f.id "
    for row in rows:
        logger.debug(row)
        content = {'ndep': int(row[0]), 'nome': row[1], 'localidade': row[2]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)'''



##
##      Demo GET
##
## Obtain department with ndep <ndep>
##
## To use it, access: 
## 
##   http://localhost:8080/departments/10
##



##
##      Demo POST
##
## Add a new department in a JSON payload
##
## To use it, you need to use postman or curl: 
##
##   curl -X POST http://localhost:8080/departments/ -H "Content-Type: application/json" -d '{"localidade": "Polo II", "ndep": 69, "nome": "Seguranca"}'
##

#criar airport
@app.route("/airport/", methods=['POST'])
def add_airport():
    logger.info("###              DEMO: POST /airport              ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new airport  ----")
    logger.debug(f'payload: {payload}')
    dadosAirport={}
    for key, value in payload.items():
        dadosAirport[key.lower()]= value
        
    if 'name' not in dadosAirport:
        response = {'status': statusCode['bad_request'], 'message': 'name value not in payload'}
        return jsonify(response)
    if 'city' not in dadosAirport:
        response = {'status': statusCode['bad_request'], 'message': 'city value not in payload'}
        return jsonify(response)
    if 'country' not in dadosAirport:
        response = {'status': statusCode['bad_request'], 'message': 'country value not in payload'}
        return jsonify(response)

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO Airport (city, name, country) 
                          VALUES ( %s,   %s ,   %s )"""

    values = (payload["city"], payload["name"], payload["country"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'status': statusCode['sucess'], 'results:':'airport_code'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result ={'status': statusCode['sucess'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

#criar flight
@app.route("/flight/", methods=['POST'])
def add_flight():
    logger.info("###              DEMO: POST /flight              ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new flight  ----")
    logger.debug(f'payload: {payload}')
    dadosFlight={}
    for key, value in payload.items():
        dadosFlight[key.lower()]= value
        
    if 'departure_time' not in dadosFlight:
        response = {'status': statusCode['bad_request'], 'message': 'departure_time value not in payload'}
        return jsonify(response)
    if 'arrivel_time' not in dadosFlight:
        response = {'status': statusCode['bad_request'], 'message': 'arrivel_time value not in payload'}
        return jsonify(response)
    if 'capacity' not in dadosFlight:
        response = {'status': statusCode['bad_request'], 'message': 'capacity value not in payload'}
        return jsonify(response)
    if 'destination' not in dadosFlight:
        response = {'status': statusCode['bad_request'], 'message': 'destination value not in payload'}
        return jsonify(response)
    if 'origin' not in dadosFlight:
        response = {'status': statusCode['bad_request'], 'message': 'origin value not in payload'}
        return jsonify(response)

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO Flight (departure_time, arrivel_time, capacity, destination, origin) 
                          VALUES ( %s,   %s ,   %s,   %s ,   %s  )"""

    values = (payload["departure_time"], payload["arrivel_time"], payload["capacity"], payload["destination"], payload["origin"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'status': statusCode['sucess'], 'results:':'flight_code'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result ={'status': statusCode['sucess'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)
#criar schedule
@app.route("/schedule/", methods=['POST'])
def add_schedule():
    logger.info("###              DEMO: POST /schedule              ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new schedule  ----")
    logger.debug(f'payload: {payload}')
    dadosSchedule={}
    for key, value in payload.items():
        dadosSchedule[key.lower()]= value
        
    if 'fligth_date' not in dadosSchedule:
        response = {'status': statusCode['bad_request'], 'message': 'fligth_date value not in payload'}
        return jsonify(response)
    

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO Schedule (fligth_date) 
                          VALUES ( %s )"""

    values = (payload["fligth_date"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'status': statusCode['sucess'], 'results:':'schedule_id'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result ={'status': statusCode['sucess'], 'errors:':'errors'}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)


##
##      Demo PUT
##
## Update a department based on the a JSON payload
##
## To use it, you need to use postman or curl: 
##
##   curl -X PUT http://localhost:8080/departments/ -H "Content-Type: application/json" -d '{"ndep": 69, "localidade": "Porto"}'
##

@app.route("/departments/", methods=['PUT'])
def update_departments():
    logger.info("###              DEMO: PUT /departments              ###");   
    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()


    #if content["ndep"] is None or content["nome"] is None :
    #    return 'ndep and nome are required to update'

    if "ndep" not in content or "localidade" not in content:
        return 'ndep and localidade are required to update'


    logger.info("---- update department  ----")
    logger.info(f'content: {content}')

    # parameterized queries, good for security and performance
    statement ="""
                UPDATE dep 
                  SET local = %s
                WHERE ndep = %s"""


    values = (content["localidade"], content["ndep"])

    try:
        res = cur.execute(statement, values)
        result = f'Updated: {cur.rowcount}'
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)






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
                  "API v1.0 online: http://localhost:8080/departments/\n\n")


    
    # NOTE: change to 5000 or remove the port parameter if you are running as a Docker container
    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)