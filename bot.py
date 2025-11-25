# turbopost.py - 512 vídeos ALEATÓRIOS + 18 copys + NUNCA MAIS CAI (ReadTimeout PROOF)
import os
import time
import threading
import random
from datetime import datetime, timedelta
import pandas as pd
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================== CONFIGURAÇÕES =====================
BOT_TOKEN = os.getenv('8479231276:AAFu1wDzJG3c8BkLfhH_QBAjp-kZXoMouFc', '8479231276:AAFu1wDzJG3c8BkLfhH_QBAjp-kZXoMouFc')
GRUPO_DESTINO = -1002941003438
EXCEL_PATH = 'db.xlsx'
PASTA_MIDIA = 'midia'
TOTAL_VIDEOS = 512
TOTAL_COPYS = 18
# =====================================================

bot = TeleBot(BOT_TOKEN, parse_mode='HTML')  # HTML pra links e negrito
running = False
lock = threading.Lock()

# Índices dos vídeos (aleatórios)
indices_videos = list(range(1, TOTAL_VIDEOS + 1))
random.shuffle(indices_videos)
proximo_video = 0

# 18 copys únicas
copys_18 = []

HORARIOS = ['00:00','01:00','02:00','03:00','04:00','05:00','06:00','07:00','08:00',
            '10:00','12:00','14:00','16:00','18:00','20:00','22:00']

def carregar_18_copys():
    global copys_18
    try:
        df = pd.read_excel(EXCEL_PATH)
        copys_18 = []
        for i in range(min(TOTAL_COPYS, len(df))):
            row = df.iloc[i]
            msg = str(row.get('mensagem', '')).strip()
            msg_link = str(row.get('mensagem.1', '')).strip() if 'mensagem.1' in row and pd.notna(row.get('mensagem.1')) else ""
            texto = msg + (f"\n\n{msg_link}" if msg_link else "") + "\n\nMELHORES VAZADOS"
            if texto.strip():
                copys_18.append(texto)
        if not copys_18:
            copys_18 = [f"Vídeo insano #{i+1}\n\nMELHORES VAZADOS" for i in range(18)]
        print(f"Carregadas {len(copys_18)} copys únicas")
    except Exception as e:
        print(f"Erro ao carregar copys: {e}")
        copys_18 = [f"Vídeo top #{i+1}\n\nMELHORES VAZADOS" for i in range(18)]

def pegar_copy_aleatoria():
    return random.choice(copys_18)

def postar():
    global proximo_video, running
    with lock:
        if not running or proximo_video >= TOTAL_VIDEOS:
            if proximo_video >= TOTAL_VIDEOS:
                print("\nTODOS OS 512 VÍDEOS POSTADOS!")
                running = False
            return False
        indice_excel = indices_videos[proximo_video]
        proximo_video += 1

    try:
        df = pd.read_excel(EXCEL_PATH)
        row = df.iloc[indice_excel - 1]

        # Caminho do vídeo
        midia_nome = row.get('midia')
        if midia_nome and pd.notna(midia_nome):
            midia_path = midia_nome if os.path.isabs(midia_nome) else os.path.join(PASTA_MIDIA, midia_nome)
        else:
            midia_path = os.path.join(PASTA_MIDIA, f"video ({indice_excel}).mp4")

        if not os.path.exists(midia_path):
            print(f"Vídeo não encontrado: {midia_path}")
            return True

        caption = pegar_copy_aleatoria()
        markup = None
        if pd.notna(row.get('botao_texto_1')) and pd.notna(row.get('botao_url_1')):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(row['botao_texto_1'], url=row['botao_url_1']))
            if pd.notna(row.get('botao_texto_2')) and pd.notna(row.get('botao_url_2')):
                markup.add(InlineKeyboardButton(row['botao_texto_2'], url=row['botao_url_2']))

        grupo = row.get('grupo') if pd.notna(row.get('grupo')) else GRUPO_DESTINO

        with open(midia_path, 'rb') as video:
            bot.send_video(grupo, video, caption=caption, reply_markup=markup, timeout=120)

        print(f"Post [{proximo_video}/512] → Linha {indice_excel} | Copy #{copys_18.index(caption) % 18 + 1}")
        return True

    except Exception as e:
        print(f"Erro ao postar linha {indice_excel}: {e}")
        return True

def agendar():
    global running
    print("Agendador iniciado!")
    while running:
        with lock:
            if proximo_video >= TOTAL_VIDEOS: break

        agora = datetime.now()
        post_feito = False
        for h in HORARIOS:
            hora, minuto = map(int, h.split(':'))
            proxima = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            if proxima > agora:
                delay = int((proxima - agora).total_seconds())
                print(f"Próximo post: {proxima.strftime('%H:%M')} (em {delay//60} min)")
                for _ in range(delay):
                    if not running: return
                    time.sleep(1)
                if running:
                    postar()
                    post_feito = True
                break

        if not post_feito:
            primeiro = HORARIOS[0]
            h, m = map(int, primeiro.split(':'))
            amanha = (agora + timedelta(days=1)).replace(hour=h, minute=m, second=0, microsecond=0)
            delay = int((amanha - agora).total_seconds())
            for _ in range(delay):
                if not running: return
                time.sleep(1)
            if running: postar()

# ==================== COMANDOS ====================
@bot.message_handler(commands=['postar'])
def start_posting(message):
    global running
    with lock:
        if running: 
            bot.reply_to(message, "Já está rodando!")
            return
        running = True

    bot.reply_to(message, "BOT LIGADO E INDESTRUTÍVEL!\n\n"
                          "512 vídeos aleatórios\n"
                          "18 copys variadas\n"
                          "16 posts/dia\n"
                          "Nunca mais cai por timeout")

    threading.Thread(target=postar, daemon=True).start()
    time.sleep(2)
    threading.Thread(target=agendar, daemon=True).start()

@bot.message_handler(commands=['stop', 'parar'])
def stop(message):
    global running
    with lock: running = False
    bot.reply_to(message, f"BOT PARADO\nPostados: {proximo_video}/512")

@bot.message_handler(commands=['reiniciar'])
def reiniciar(message):
    global indices_videos, proximo_video, running
    with lock:
        if running:
            bot.reply_to(message, "Pare com /stop primeiro")
            return
        indices_videos = list(range(1, TOTAL_VIDEOS + 1))
        random.shuffle(indices_videos)
        proximo_video = 0
        carregar_18_copys()
    bot.reply_to(message, "REINICIADO!\nNova ordem aleatória\n18 copys recarregadas\nUse /postar")

@bot.message_handler(commands=['status'])
def status(message):
    with lock:
        bot.reply_to(message, f"Status: {'RODANDO' if running else 'PARADO'}\n"
                              f"Postados: {proximo_video}/512\n"
                              f"Copys ativas: {len(copys_18)}")

# ==================== LOOP INDESTRUTÍVEL (NUNCA MAIS CAI) ====================
if __name__ == '__main__':
    print("TurboPost 2025 - INDESTRUTÍVEL (ReadTimeout = IMPOSSÍVEL)")
    if not os.path.exists(EXCEL_PATH):
        print(f"{EXCEL_PATH} não encontrado!"); exit(1)
    if not os.path.exists(PASTA_MIDIA):
        print(f"Pasta '{PASTA_MIDIA}' não encontrada!"); exit(1)

    carregar_18_copys()
    print("Bot 100% pronto - Envie /postar no privado")

    # LOOP QUE REINICIA AUTOMATICAMENTE PRA SEMPRE
    while True:
        try:
            bot.polling(
                none_stop=True,
                interval=1,
                timeout=90,          # Timeout alto
                long_polling_timeout=90,
                allowed_updates=["message", "callback_query"]
            )
        except Exception as e:
            print(f"Erro de conexão: {e}")
            print("Reiniciando bot em 10 segundos...")
            time.sleep(10)  # Espera e tenta de novo pra sempre