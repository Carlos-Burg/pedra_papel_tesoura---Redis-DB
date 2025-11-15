from random import randint
import time
import os
import redis
import json

def conectar_redis():  # conecta no banco
    # Retire o print em produção se quiser
    return redis.Redis(
        host='localhost',
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
    r.hset(chave_sala, "nome", nome_sala)
    r.hset(chave_sala, "jogador1", "")
    r.hset(chave_sala, "jogador2", "")

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

    # ler com segurança
    raw_j1 = r.hget(chave_sala, "jogador1")
    raw_j2 = r.hget(chave_sala, "jogador2")
    j1 = raw_j1.decode() if raw_j1 else ""
    j2 = raw_j2.decode() if raw_j2 else ""

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

def registrar_jogada_individual(nome_sala, jogador_num, jogada):
    """Registra apenas a jogada do jogador (chave única por jogador)."""
    r = conectar_redis()
    chave = f"sala:{nome_sala}:jogada_j{jogador_num}"
    # Salva como string (int também funciona), sem expiração
    r.set(chave, int(jogada))

def esperar_jogada_oponente(nome_sala, jogador_num): 
    """Bloqueia até que a chave do adversário exista e retorne o valor."""
    r = conectar_redis()
    outro = 2 if jogador_num == 1 else 1
    chave_oponente = f"sala:{nome_sala}:jogada_j{outro}"

    print("Aguardando o outro jogador jogar...")

    while True:
        jogada = r.get(chave_oponente)
        if jogada:
            try:
                return int(jogada)
            except ValueError:
                # se por algum motivo não for int, tenta converter
                return int(jogada.decode() if isinstance(jogada, bytes) else jogada)
        time.sleep(0.3)

def registrar_jogada(nome_sala, jogada_j1, jogada_j2):
    """Registra no histórico (lista) a rodada completa."""
    r = conectar_redis()
    chave_jogadas = f"sala:{nome_sala}:jogadas"

    rodada = json.dumps({
        "j1": int(jogada_j1),
        "j2": int(jogada_j2)
    })

    r.rpush(chave_jogadas, rodada)

def limpar_jogadas(nome_sala):
    """Limpa as chaves de jogada para a próxima rodada."""
    r = conectar_redis()
    r.delete(f"sala:{nome_sala}:jogada_j1")
    r.delete(f"sala:{nome_sala}:jogada_j2")

def finalizar_jogo(nome_sala):
    r = conectar_redis()
    chave_jogadas = f"sala:{nome_sala}:jogadas"
    jogadas_brutas = r.lrange(chave_jogadas, 0, -1)

    # se não houver jogadas, mostra mensagem
    if not jogadas_brutas:
        print("\nNenhuma rodada registrada.")
        return

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

def front(state: int, user_credits, user_j=0, machine_j=0):
    choi = ["👊", "🖐", "✌", "??"]
    if user_j != 0:
        user_j = choi[user_j - 1]
    if machine_j != 0:
        machine_j = choi[machine_j - 1]
    # limpa tela (Windows usa cls, outros usam clear)
    try:
        os.system("cls")
    except:
        os.system("clear")
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
                if 1 <= select <= 3:
                    return user_credits, select
            except:
                pass
    elif typee == 2:
        print("Realize o pagamento com o QR code!")
        os.system("pause")
        return user_credits + 1, None

def anime(user_credits, user_j, machine_j):
    # Animação simplificada: mostra jogadas e decide vencedor localmente
    front(state=0, user_credits=user_credits)
    for ii in range(1, 4):
        front(state=0, user_credits=user_credits, user_j=user_j, machine_j=ii)
        time.sleep(0.5)
    for ii in range(1, 4):
        front(state=0, user_credits=user_credits, user_j=user_j, machine_j=ii)
        time.sleep(0.5)
    front(state=1, user_credits=user_credits, user_j=user_j, machine_j=machine_j)
    time.sleep(1.2)
    if user_j == machine_j:
        print("\nEmpate!")
        return 0
    else:
        # condição de vitória do usuário (1 vence 3, 2 vence 1, 3 vence 2)
        if (user_j == 1 and machine_j == 3) or (user_j == 2 and machine_j == 1) or (user_j == 3 and machine_j == 2):
            print("\nVocê venceu esta rodada!")
            return 1
        else:
            print("\nVocê perdeu esta rodada!")
            return -1

if __name__ == '__main__':

    # LOOP PARA CRIAR / CONECTAR A SALA CORRETAMENTE
    while True:
        print("\nDeseja criar ou se conectar a uma sala ?")
        resp = input("1 - CRIAR | 2 - CONECTAR: ").strip()

        nome_sala = input("Digite o nome da sala: ").strip()

        if resp == "1":
            if cria_sala(nome_sala):
                break
            else:
                print("\n❌ A sala já existe! Tente novamente.\n")

        elif resp == "2":
            if conectar_sala(nome_sala):
                break
            else:
                print("\n❌ A sala não existe! Tente novamente.\n")

        else:
            print("\nOpção inválida. Tente novamente.\n")

    # Definindo jogador (loop até conseguir entrar)
    while True:
        jogador_id = input("Digite seu nome/jogador: ").strip()
        posicao = criar_jogadores(nome_sala, jogador_id)
        if posicao:
            break
        else:
            print("Não foi possível entrar na sala. Tente outro nome ou sala.\n")

    print(f"Você é o jogador {posicao}")

    # Limpa jogadas antigas de rodadas passadas (safety)
    r = conectar_redis()
    r.delete(f"sala:{nome_sala}:jogada_j1")
    r.delete(f"sala:{nome_sala}:jogada_j2")

    # Aqui jogam até acabar créditos
    user_credits = 0

    while True:
        front(state=0, user_credits=user_credits)

        if user_credits > 0:
            # --- MULTIPLAYER FLOW ---
            # Jogador faz sua jogada
            user_credits, minha_jogada = ui(1, user_credits)

            # Registra apenas a sua jogada no Redis
            registrar_jogada_individual(nome_sala, posicao, minha_jogada)

            # Espera a jogada do oponente (bloqueante)
            jogada_oponente = esperar_jogada_oponente(nome_sala, posicao)

            # Ordena j1/j2 para salvar histórico corretamente
            if posicao == 1:
                j1 = minha_jogada
                j2 = jogada_oponente
            else:
                j1 = jogada_oponente
                j2 = minha_jogada

            # Registra a rodada no histórico (lista)
            registrar_jogada(nome_sala, j1, j2)

            # Executa animação/resultado localmente
            resultado = anime(user_credits=user_credits, user_j=minha_jogada, machine_j=jogada_oponente)
            user_credits += resultado

            # Limpa chaves de jogada para próxima rodada
            limpar_jogadas(nome_sala)

        else:
            # Comprar crédito (ou ganhar de outra forma)
            user_credits, _ = ui(2, user_credits)

        # Condição de término
        if user_credits >= 5:
            print("\n💰 Você atingiu o máximo de créditos! Fim da partida.\n")
            break
            
    # Finaliza e limpa sala (apenas jogador 1 pode excluir)
    finalizar_jogo(nome_sala)