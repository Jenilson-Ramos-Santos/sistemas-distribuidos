import os
import json
import threading
import time
import requests
import random
from fastapi import FastAPI, Response, status
from uvicorn import Config, Server
from pydantic import BaseModel, StrictStr


app = FastAPI()


class Resolver(BaseModel):
    operacao: StrictStr
    argumetos: dict


class Info(BaseModel):
    server_name: StrictStr
    server_endpoint: StrictStr
    descricao: StrictStr
    versao: StrictStr
    Status: StrictStr
    tipo_de_eleicao_ativa: StrictStr


class Peer(BaseModel):
    id: StrictStr
    nome: StrictStr
    url: StrictStr


class RecursoGetDelete(BaseModel):
    codigo_de_acesso: StrictStr


class RecursoPut(BaseModel):
    codigo_de_acesso: StrictStr
    valor: int


class Eleicao(BaseModel):
    id: StrictStr
    dados: list


class Coordenador(BaseModel):
    coordenador: StrictStr
    id_eleicao: StrictStr


# Métodos para Eleição do Coordenador
###################################################################################################


@app.get('/coordenador', status_code=200)
def get_coordenador():
    with open('eleicao.json', 'r', encoding='utf8') as json_file:
        dado = json.load(json_file)

    return {'coordenador': dado['coordenador'], 'coordenador_atual': dado['coordenador_atual']}


@app.get('/eleicao', status_code=200)
def get_eleicao():
    with open('eleicao.json', 'r', encoding='utf8') as json_file:
        dado_eleicao = json.load(json_file)

    with open('info.json', 'r', encoding='utf8') as json_file:
        dado_info = json.load(json_file)

    return {'tipo_de_eleicao_ativa': dado_info['tipo_de_eleicao_ativa'],
            'eleicoes_em_andamento': dado_eleicao['eleicoes_em_andamento']}


@app.post('/eleicao', status_code=200)
def post_eleicao(eleicao: Eleicao, response: Response):
    eleicao = eleicao.dict()

    with open('info.json', 'r', encoding='utf8') as json_file:
        info = json.load(json_file)

    if info['status'] == 'online':
        if info['tipo_de_eleicao_ativa'] == 'valentao':
            valentao(eleicao['id'])
        else:
            anel(eleicao)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST


@app.post('/eleicao/coordenador', status_code=200)
def post_coordenador(coordenador: Coordenador, response: Response):
    with open('info.json', 'r', encoding='utf8') as json_file:
        info = json.load(json_file)

    if info['status'] == 'online':
        with open('eleicao.json', 'r', encoding='utf8') as json_file:
            dado = json.load(json_file)

        coordenador = coordenador.dict()
        if coordenador['coordenador'] == '201810665':
            dado['coordenador'] = True
        else:
            dado['coordenador'] = False
        dado['coordenador_atual'] = coordenador['coordenador']
        dado['id_eleicao'] = coordenador['id_eleicao']

        with open('eleicao.json', 'w', encoding='utf8') as json_file:
            json.dump(dado, json_file, indent=2)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST


# Métodos de Get
###################################################################################################


@app.get('/info', status_code=200)
def get_info():
    with open('info.json', 'r', encoding='utf8') as json_file:
        dados = json.load(json_file)

    return dados


@app.get('/peers', status_code=200)
def get_peers():
    with open('dados.json', 'r', encoding='utf8') as json_file:
        dados = json.load(json_file)

    return dados


@app.get('/peers/{id_peer}', status_code=200)
def get_peers_by_id(id_peer: str, response: Response):
    with open('dados.json', 'r') as json_file:
        dados = json.load(json_file)

    for dado in dados:
        if dado['id'] == id_peer:
            return dado

    response.status_code = status.HTTP_404_NOT_FOUND


@app.get('/recurso', status_code=401)
def get_recurso(codigo: RecursoGetDelete, response: Response):
    with open('recurso.json', 'r', encoding='utf8') as json_file:
        dado = json.load(json_file)

    codigo = codigo.dict()
    if codigo['codigo_de_acesso'] == dado['codigo_de_acesso'] and dado['tempo_de_expiracao'] > int(time()):
        response.status_code = status.HTTP_200_OK
        return {'valor': float(dado['valor'])}


# Métodos Post
###################################################################################################


@app.post('/resolver', status_code=200)
def post_resolver(resolve: Resolver, response: Response):
    with open('dados.json', 'r', encoding='utf8') as json_file:
        dados = json.load(json_file)

    resolve = resolve.dict()
    for dado in dados:
        if dado['nome'] == resolve['argumetos']['nome']:
            return {'nome': dado['nome'], 'url': dado['url']}

    response.status_code = status.HTTP_404_NOT_FOUND


@app.post('/peers', status_code=400)
def post_peers(peer: Peer, response: Response):
    with open('dados.json', 'r', encoding='utf8') as json_file:
        peers = json.load(json_file)

    peer = peer.dict()
    for dado in peers:
        print(dado)
        print(peer)
        if dado['id'] == peer['id'] or dado['nome'] == peer['nome']:
            response.status_code = status.HTTP_409_CONFLICT
            return

    peers.append(peer)
    with open('dados.json', 'w', encoding='utf8') as json_file:
        json.dump(peers, json_file, indent=2)

    response.status_code = status.HTTP_200_OK


@app.post('/recurso', status_code=409)
def post_recurso(response: Response):
    with open('recurso.json', 'r', encoding='utf8') as json_file:
        dado = json.load(json_file)

    if dado['tempo_de_expiracao'] < int(time()):
        codigo = 'codigo_unico_' + str(random.random())
        validade = int(time()) + 5

        dado['codigo_de_acesso'] = codigo
        dado['tempo_de_expiracao'] = validade
        with open('recurso.json', 'w', encoding='utf8') as json_file:
            json.dump(dado, json_file, indent=2)

        response.status_code = status.HTTP_200_OK
        return {'codigo_de_acesso': codigo, 'validade': str(validade)}


# Métodos Put
###################################################################################################


@app.put('/info', status_code=400)
def put_info(info: Info, response: Response):
    with open('info.json', 'w', encoding='utf8') as json_file:
        json.dump(info.dict(), json_file, indent=2)

    response.status_code = status.HTTP_200_OK


@app.put('/peers/{id_peer}', status_code=400)
def put_peers(id_peer: str, peer: Peer, response: Response):
    with open('dados.json', 'r', encoding='utf8') as json_file:
        peers = json.load(json_file)

    peer = peer.dict()
    for dado in peers:
        if dado['id'] == id_peer:
            peers.remove(dado)
            peers.append(peer)
            with open('dados.json', 'w', encoding='utf8') as json_file:
                json.dump(peers, json_file, indent=2)
            response.status_code = status.HTTP_200_OK
            return peer

    response.status_code = status.HTTP_404_NOT_FOUND


@app.put('/recurso', status_code=401)
def put_recurso(recurso: RecursoPut, response: Response):
    with open('recurso.json', 'r', encoding='utf8') as json_file:
        dado = json.load(json_file)

    recurso = recurso.dict()
    if recurso['codigo_de_acesso'] == dado['codigo_de_acesso']:
        dado['valor'] = recurso['valor']

        with open('recurso.json', 'w', encoding='utf8') as json_file:
            json.dump(dado, json_file, indent=2)

        response.status_code = status.HTTP_200_OK


# Métodos Delete
###################################################################################################


@app.delete('/peers/{id_peer}', status_code=200)
def delete_peers(id_peer: str, response: Response):
    with open('dados.json', 'r', encoding='utf8') as json_file:
        peers = json.load(json_file)

    for dado in peers:
        if dado['id'] == id_peer:
            peers.remove(dado)
            with open('dados.json', 'w', encoding='utf8') as json_file:
                json.dump(peers, json_file, indent=2)
            return

    response.status_code = status.HTTP_404_NOT_FOUND


@app.delete('/recurso', status_code=410)
def delete_recurso(codigo: RecursoGetDelete, response: Response):
    with open('recurso.json', 'r', encoding='utf8') as json_file:
        dado = json.load(json_file)

    codigo = codigo.dict()
    if codigo['codigo_de_acesso'] == dado['codigo_de_acesso'] and dado['tempo_de_expiracao'] > int(time()):
        dado['codigo_de_acesso'] = ''
        dado['tempo_de_expiracao'] = 0

        with open('recurso.json', 'w', encoding='utf8') as json_file:
            json.dump(dado, json_file, indent=2)

        response.status_code = status.HTTP_200_OK


def main():
    threading.Thread(target=checa_coordenador, ).start()

    # Configuração para rodar localmente
    # config = Config(app=app, host='127.0.0.1', port=int(8000), debug=True)

    # Configuração para rodar no Heroku
    config = Config(app=app, host='0.0.0.0', port=os.environ.get('PORT'), debug=True)

    server = Server(config=config)
    server.run()


# Métodos para Eleição
###################################################################################################


def checa_coordenador():
    while True:
        with open('eleicao.json', 'r', encoding='utf8') as json_file:
            dado = json.load(json_file)

        with open('dados.json', 'r', encoding='utf8') as json_file:
            peers = json.load(json_file)

        i = 0
        while i < len(peers):
            if peers[i]['id'] == dado['coordenador_atual']:
                request = requests.get(peers[i]['url'] + "info")
                if request.status_code == 200 and request.json()['status'] == 'offline':
                    time.sleep(random.randint(5, 10))
                    request = requests.get(peers[i]['url'] + "info")
                    if request.status_code == 200 and request.json()['status'] == 'offline':
                        iniciar_eleicao()
                break
            i = i + 1
        time.sleep(2)


def iniciar_eleicao():
    with open('info.json', 'r', encoding='utf8') as json_file:
        dado = json.load(json_file)

    if dado['tipo_de_eleicao_ativa'] == 'valentao':
        valentao()
    else:
        anel({'id': '', 'dados': ['']})


def valentao(id_eleicao=''):
    with open('dados.json', 'r', encoding='utf8') as json_file:
        dados = json.load(json_file)

    if id_eleicao == '':
        id_eleicao = str(random.randint(1, 100))

    minha_forca = '201810665'
    lista = list()
    for dado in dados:
        if int(dado['id']) > int(minha_forca):
            lista.append(dado['id'])

    lider = True
    for peer in lista:
        resposta = requests.post(peer['url'] + 'eleicao',
                                 data=json.dumps({'id': id_eleicao, 'dados': []}))
        if resposta.status_code == 200:
            lider = False

    if lider:
        for dado in dados:
            requests.post(dado['url'] + 'eleicao/coordenador',
                          data=json.dumps({'coordenador': minha_forca, 'id_eleicao': id_eleicao}))

        with open('eleicao.json', 'r', encoding='utf8') as json_file:
            eleicao = json.load(json_file)

        eleicao['coordenador'] = True
        eleicao['coordenador_atual'] = minha_forca
        eleicao['id_eleicao'] = id_eleicao

        with open('eleicao.json', 'w', encoding='utf8') as json_file:
            json.dump(eleicao, json_file, indent=2)


def anel(eleicao: Eleicao):
    with open('dados.json', 'r', encoding='utf8') as json_file:
        dados = json.load(json_file)

    maior = '201810665'
    menor = '201810665'
    url_maior = ""
    url_menor = ""
    for dado in dados:
        if int(dado['id']) > 201810665:
            if int(dado['id']) < int(maior) or maior == '201810665':
                maior = dado['id']
                url_maior = dado['url']
        if int(dado['id']) < int(menor):
            menor = dado['id']
            url_menor = dado['url']

    if maior == '201810665':
        prox = url_menor
    else:
        prox = url_maior
    print("cheguei")
    if eleicao['id'] == '':
        requests.post(prox + 'eleicao',
                      data=json.dumps({'id': str(random.randint(1, 100)), 'dados': ['201810665']}))
    else:
        if eleicao['dados'][0] == '201810665':
            for dado in dados:
                requests.post(dado['url'] + 'eleicao/coordenador',
                              data=json.dumps({'coordenador': '201810665', 'id_eleicao': eleicao['id']}))

            with open('eleicao.json', 'r', encoding='utf8') as json_file:
                dado = json.load(json_file)

            dado['coordenador'] = True
            dado['coordenador_atual'] = '201810665'
            dado['id_eleicao'] = eleicao['id']

            with open('eleicao.json', 'w', encoding='utf8') as json_file:
                json.dump(dado, json_file, indent=2)
        else:
            if int(eleicao['dados'][0]) > 201810665:
                requests.post(prox + 'eleicao',
                              data=json.dumps(eleicao))
            else:
                requests.post(prox + 'eleicao',
                              data=json.dumps({'id': eleicao['id'], 'dados': ['201810665']}))


if __name__ == '__main__':
    main()
