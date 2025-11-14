from random import randint
import time
import os
import redis
import json

def conectar_redis():  # conecta no banco
    print("Conectando ao banco...\n")
    return redis.Redis(
        host='10.1.69.134',
        port=6379,
        db=0
    )

def cria_sala(nome_sala):  # valida se a sala existe
    r = conectar_redis()
    chave_sala = f"sala:{nome_sala}"

    if r.exists(chave_sala):
        print(f"A sala '{nome_sala}' já existe.")
        return False

    # Cria a sala
    r.hset(chave_sala, mapping={
        "nome": nome_sala,
        "jogador1": "",
        "jogador2": ""
    })

    print(f"Sala '{nome_sala}' criada com sucesso.")
    return True

def conectar_sala(nome_sala):  # conecta na sala existente
    r = conectar_redis()
    chave_sala = f"sala:{nome_sala}"

    if r.exists(chave_sala):
        print(f"Conectado à sala '{nome_sala}'.")
        return True
    else:
        print(f"A sala '{nome_sala}' não existe.")
        return False

def criar_jogadores(nome_sala, jogador_id):
    r = conectar_redis()
    chave_sala = f"sala:{nome_sala}"

    if not r.exists(chave_sala):
        print("A sala não existe!")
        return False

    j1 = r.hget(chave_sala, "jogador1").decode()
    j2 = r.hget(chave_sala, "jogador2").decode()

    if j1 == "":
        r.hset(chave_sala, "jogador1", jogador_id)
        print(f"Jogador 1 definido: {jogador_id}")
        return 1

    elif j2 == "":
        r.hset(chave_sala, "jogador2", jogador_id)
        print(f"Jogador 2 definido: {jogador_id}")
        return 2

    else:
        print("A sala já está cheia (2 jogadores).")
        return False

def registrar_jogada(nome_sala, jogada_j1, jogada_j2):
    r = conectar_redis()
    chave_jogadas = f"sala:{nome_sala}:jogadas"

    rodada = json.dumps({
        "j1": jogada_j1,
        "j2": jogada_j2
    })

    r.rpush(chave_jogadas, rodada)

def finalizar_jogo(nome_sala):
    r = conectar_redis()
    chave_jogadas = f"sala:{nome_sala}:jogadas"
    jogadas_brutas = r.lrange(chave_jogadas, 0, -1)

    jogadas = [json.loads(j) for j in jogadas_brutas]

    print("\n===== RESULTADO FINAL =====")

    v1 = 0
    v2 = 0

    for i, rodada in enumerate(jogadas, start=1):
        j1 = rodada["j1"]
        j2 = rodada["j2"]

        print(f"Rodada {i}: Jogador1 = {j1}  x  Jogador2 = {j2}")

        if j1 == j2:
            pass
        elif (j1 == 1 and j2 == 3) or (j1 == 2 and j2 == 1) or (j1 == 3 and j2 == 2):
            v1 += 1
        else:
            v2 += 1

    print("---------------------------")
    print(f"Vitórias do Jogador 1: {v1}")
    print(f"Vitórias do Jogador 2: {v2}")

    if v1 > v2:
        print("🏆 Jogador 1 VENCEU!")
    elif v2 > v1:
        print("🏆 Jogador 2 VENCEU!")
    else:
        print("🤝 EMPATE!")

def exclui_sala(nome_sala, jogador_id):
    r = conectar_redis()
    chave_sala = f"sala:{nome_sala}"
    chave_jogadas = f"{chave_sala}:jogadas"

    # Se sala não existe
    if not r.exists(chave_sala):
        print("A sala não existe mais.")
        return False

    # Pegando o jogador1 salvo no Redis
    jogador1 = r.hget(chave_sala, "jogador1")
    jogador1 = jogador1.decode() if jogador1 else ""

    # Verificando permissão
    if jogador_id != jogador1:
        print("❌ Apenas o Jogador 1 pode excluir a sala.")
        return False

    # Jogador 1 pode excluir
    r.delete(chave_sala)
    r.delete(chave_jogadas)

    print(f"✅ Sala '{nome_sala}' excluída pelo Jogador 1.")
    return True

def front(state: int, user_credits, user_j=0, machine_j=0):
    choi = ["👊", "🖐", "✌", "??"]
    if user_j != 0:
        user_j = choi[user_j - 1]
    if machine_j != 0:
        machine_j = choi[machine_j - 1]
    os.system("cls")
    print("+-------------------------------+")
    print(f"+user_credits:{user_credits}\t\t\t+")
    print("+-------------------------------+")
    print("+        ._._.     _|.|_        +")
    if state == 0:
        print("+       (´-_-`)   [´-_-`]       +")
        print("+       \\\\  //     \\\\  //       +")
        print(f"+       [{user_j}]//|     |\\\\[{machine_j}]     +")
    elif state == 1:
        print("+       (´-_-`)   [´-_-`]       +")
        print("+        | \\\\ \\\\  // // |       +")
        print(f"+        +--\\[{user_j}][{machine_j}]/--+       +")
    elif state == 2:
        print("+       (*`_´*) 🖕[ ´-_-]       +")
        print("+     \\\\//   \\\\//  | \\_/|       +")
        print("+        +--+      |+--+|       +")
    elif state == 3:
        print("+       (-_-` )🖕 [*`_´*]       +")
        print("+       |\\_/ |  \\\\//   \\\\//     +")
        print("+        +--+      |+--+|       +")
    print("+       / || \\     / || \\       +")
    print("+_______c_|_|_'___c_|_|_'_______+")


def ui(typee: int = 1, user_credits=0):
    if typee == 1:
        while True:
            try:
                select = int(input("1) 👊\n2) 🖐\n3) ✌\nDigite sua jogada: "))
                if select > 0 and select < 4:
                    return user_credits, select
            except:
                pass
    elif typee == 2:
        print("Realize o pagamento com o QR code!")
        os.system("pause")
        return user_credits + 1, None

def anime(user_credits, user_j, machine_j):
    front(state=0, user_credits=user_credits)
    for ii in range(1, 4):
        front(state=0, user_credits=user_credits, user_j=user_j, machine_j=ii)
        time.sleep(0.5)
    for ii in range(1, 4):
        front(state=0, user_credits=user_credits, user_j=user_j, machine_j=ii)
        time.sleep(0.5)
    front(state=1, user_credits=user_credits, user_j=user_j, machine_j=machine_j)
    time.sleep(3)
    if user_j == machine_j:
        return 0
    else:
        if (user_j == 1 and machine_j == 2) or (user_j == 2 and machine_j == 3) or (user_j == 3 and machine_j == 1):
            front(state=3, user_credits=user_credits)
            time.sleep(3)
            return -1
        else:
            front(state=2, user_credits=user_credits)
            time.sleep(3)
            return 1

if __name__ == '__main__':

    print("\nDeseja criar ou se conectar a uma sala ?")
    resp = input("1 - CRIAR | 2 - CONECTAR: ")

    nome_sala = input("Digite o nome da sala: ")

    if resp == "1":
        cria_sala(nome_sala)
    else:
        conectar_sala(nome_sala)

    jogador_id = input("Digite seu nome/jogador: ")
    posicao = criar_jogadores(nome_sala, jogador_id)

    print(f"Você é o jogador {posicao}")

    # Aqui jogam até acabar créditos
    user_credits = 0
    cw = 0
    cl = 0

    while True:
        front(state=0, user_credits=user_credits)

        if user_credits > 0:
            user_credits, jogada_j1 = ui(1, user_credits)
            jogada_j2 = randint(1, 3)

            registrar_jogada(nome_sala, jogada_j1, jogada_j2)

            resul = anime(user_credits=user_credits, user_j=jogada_j1, machine_j=jogada_j2)
            user_credits += resul

        else:
            user_credits, _ = ui(2, user_credits)

        if user_credits >= 5:  # regra de fim
            break

    finalizar_jogo(nome_sala)
    exclui_sala(nome_sala, jogador_id)