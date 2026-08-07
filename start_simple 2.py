#!/usr/bin/env python3
"""
Упрощенный запуск для хостинга
Поддерживает только cloudflare tunnel (без ngrok)
"""
import os
import sys
import time
import json
import hmac
import hashlib
import logging
import subprocess
from threading import Thread, Lock
from urllib.parse import parse_qsl

# Минимальное логирование для экономии памяти
logging.basicConfig(
    level=logging.WARNING,  # Изменено с INFO на WARNING
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_cloudflared():
    """Автоматическая установка cloudflared"""
    try:
        import platform
        import urllib.request
        
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Определяем архитектуру
        if 'x86_64' in machine or 'amd64' in machine:
            arch = 'amd64'
        elif 'aarch64' in machine or 'arm64' in machine:
            arch = 'arm64'
        elif 'arm' in machine:
            arch = 'arm'
        else:
            arch = 'amd64'  # fallback
        
        # Определяем URL для скачивания
        if system == 'linux':
            url = f'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}'
            filename = 'cloudflared'
        elif system == 'windows':
            url = f'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-{arch}.exe'
            filename = 'cloudflared.exe'
        elif system == 'darwin':
            url = f'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-{arch}'
            filename = 'cloudflared'
        else:
            logger.error(f"❌ Неподдерживаемая ОС: {system}")
            return False
        
        logger.info(f"📥 Скачиваю cloudflared для {system}-{arch}...")
        logger.info(f"   URL: {url}")
        
        # Скачиваем
        urllib.request.urlretrieve(url, filename)
        
        # Даем права на выполнение (Linux/Mac)
        if system in ['linux', 'darwin']:
            os.chmod(filename, 0o755)
        
        logger.info(f"✅ cloudflared установлен: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка установки cloudflared: {e}")
        return False

def start_cloudflared():
    """Запускает cloudflared tunnel (БЕЗ предупреждений!)"""
    try:
        # Проверяем наличие cloudflared
        cloudflared_cmd = None
        
        # Проверяем локальный файл
        if os.path.exists('./cloudflared'):
            cloudflared_cmd = './cloudflared'
        elif os.path.exists('./cloudflared.exe'):
            cloudflared_cmd = './cloudflared.exe'
        elif os.path.exists('cloudflared'):
            cloudflared_cmd = 'cloudflared'
        elif os.path.exists('cloudflared.exe'):
            cloudflared_cmd = 'cloudflared.exe'
        else:
            # Проверяем системный cloudflared
            try:
                subprocess.run(['cloudflared', '--version'], capture_output=True, check=True, timeout=5)
                cloudflared_cmd = 'cloudflared'
            except:
                pass
        
        # Если не найден - устанавливаем
        if not cloudflared_cmd:
            if install_cloudflared():
                if os.path.exists('./cloudflared'):
                    cloudflared_cmd = './cloudflared'
                elif os.path.exists('./cloudflared.exe'):
                    cloudflared_cmd = './cloudflared.exe'
                else:
                    return None
            else:
                return None
        
        # Логи cloudflared пишем в ФАЙЛ, а не в pipe: иначе после чтения URL
        # никто pipe не читает, буфер (64КБ) забивается, cloudflared виснет и туннель отваливается (530).
        import re
        log_path = '/tmp/cloudflared.log'
        logf = open(log_path, 'w')
        # --protocol http2: на IPv6-only хостах UDP/QUIC (порт 7844) часто зарезан,
        #                   а TCP/HTTP2 проходит. --edge-ip-version 6: ходить к edge по IPv6 (IPv4 нет).
        process = subprocess.Popen(
            [cloudflared_cmd, 'tunnel', '--protocol', 'http2', '--edge-ip-version', '6',
             '--url', 'http://localhost:5000', '--no-autoupdate'],
            stdout=logf,
            stderr=subprocess.STDOUT,  # cloudflared печатает URL в stderr — тоже в файл
        )

        # Ждем URL (макс 30 секунд), читая лог-файл
        url = None
        timeout = time.time() + 30
        while time.time() < timeout:
            time.sleep(0.5)
            try:
                with open(log_path, 'r') as f:
                    content = f.read()
            except Exception:
                content = ''
            m = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', content)
            if m:
                url = m.group(0)
                break

        if url:
            print(f"✅ Tunnel: {url}")
            return url
        else:
            return None
            
    except Exception as e:
        logger.error(f"Cloudflare error: {e}")
        return None

# Пути от файла, а не от cwd: под systemd рабочий каталог может быть любым.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REVIEWS_FILE = os.path.join(BASE_DIR, 'custom_reviews.txt')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
REVIEWS_LOCK = Lock()

# Сколько завершённых сделок нужно, чтобы получить право оставить отзыв.
REQUIRED_DEALS = 2
# Сколько живёт подпись initData. Дольше суток окно держать незачем.
INIT_DATA_TTL = 24 * 60 * 60


# ---------------------------------------------------------------- личность

def _bot_token():
    try:
        from config import BOT_TOKEN
        return BOT_TOKEN
    except Exception:
        return os.environ.get('BOT_TOKEN', '')


def parse_init_data(init_data):
    """Проверяет подпись Telegram Web App. Возвращает dict user или None.

    Ник и id берём только отсюда: всё, что прислал браузер, подделывается.
    """
    if not init_data:
        return None

    token = _bot_token()
    if not token:
        logger.error('BOT_TOKEN недоступен, initData проверить нечем')
        return None

    try:
        fields = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        return None

    received = fields.pop('hash', '')
    if not received:
        return None

    secret = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()

    # Telegram считает хэш по всем полям кроме hash. В клиентах с Ed25519 есть
    # ещё поле signature, и разные версии документации то включают его в
    # строку проверки, то нет. Пробуем оба варианта: без токена не подделать ни один.
    variants = [fields]
    if 'signature' in fields:
        variants.append({k: v for k, v in fields.items() if k != 'signature'})

    for variant in variants:
        check_string = '\n'.join(f'{k}={variant[k]}' for k in sorted(variant))
        calculated = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(calculated, received):
            break
    else:
        return None

    try:
        if time.time() - int(fields.get('auth_date', 0)) > INIT_DATA_TTL:
            return None
    except (TypeError, ValueError):
        return None

    try:
        user = json.loads(fields.get('user', ''))
    except Exception:
        return None

    if not isinstance(user, dict) or not user.get('id'):
        return None
    return user


def display_name(user):
    return str(user.get('username') or user.get('first_name') or 'Guest')


def completed_deals(user_id):
    """Число завершённых сделок из users.json. Бросает RuntimeError, если файл не читается."""
    for attempt in range(3):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            break
        except FileNotFoundError:
            return 0
        except (json.JSONDecodeError, OSError):
            # app.py переписывает users.json не атомарно: можно поймать его пустым
            time.sleep(0.15)
    else:
        raise RuntimeError('users.json не читается')

    record = data.get(str(user_id)) or {}
    try:
        return int(record.get('added_deals', 0) or 0)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------- отзывы

# Поля отзыва хранятся в одну строку через "|", поэтому сам разделитель
# и переносы строк из пользовательского ввода вырезаем.
def _clean_field(value, max_len):
    text = str(value or '').replace('|', '/').replace('\n', ' ').replace('\r', ' ')
    return text.strip()[:max_len]


def read_custom_reviews(viewer_id='', viewer_name=''):
    """Отзывы, оставленные через форму, видит только их автор.

    Формат строки: ник | подарок | оценка | текст | дата | user_id
    Старые строки записаны без user_id — их автора опознаём по нику.
    """
    if not viewer_id and not viewer_name:
        return []

    if not os.path.exists(REVIEWS_FILE):
        return []

    reviews = []
    with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 4:
                continue

            try:
                rating = int(parts[2])
            except ValueError:
                continue

            owner_id = parts[5] if len(parts) > 5 else ''
            if owner_id:
                if owner_id != str(viewer_id):
                    continue
            elif not viewer_name or parts[0] != viewer_name:
                continue

            reviews.append({
                'username': parts[0],
                'gift': parts[1],
                'rating': max(1, min(5, rating)),
                'text': parts[3],
                'date': parts[4] if len(parts) > 4 and parts[4] else None,
                'isCustom': True,
            })

    return reviews


def append_custom_review(username, gift, rating, text, user_id):
    """Дописывает отзыв в custom_reviews.txt"""
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"{username} | {gift} | {rating} | {text} | {stamp} | {user_id}\n"

    with REVIEWS_LOCK:
        needs_newline = (
            os.path.exists(REVIEWS_FILE)
            and os.path.getsize(REVIEWS_FILE) > 0
            and open(REVIEWS_FILE, 'rb').read()[-1:] != b'\n'
        )
        with open(REVIEWS_FILE, 'a', encoding='utf-8') as f:
            if needs_newline:
                f.write('\n')
            f.write(line)

def start_flask(webapp_url):
    """Запускает Flask сервер (легковесный режим)"""
    os.environ['WEBAPP_URL'] = webapp_url

    try:
        from flask import Flask, send_from_directory, jsonify, request

        app = Flask(__name__, static_folder='site')
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        @app.route('/')
        def index():
            return send_from_directory('site', 'index.html')

        # Кнопка в боте ведёт на /reviewsite (без слэша) — отдаём страницу на оба варианта.
        @app.route('/reviewsite')
        @app.route('/reviewsite/')
        def reviewsite_index():
            return send_from_directory('site/reviewsite', 'index.html')

        def current_user():
            """initData приходит заголовком, а на POST может лежать и в теле."""
            raw = request.headers.get('X-Telegram-Init-Data', '')
            if not raw and request.method == 'POST':
                raw = (request.get_json(silent=True) or {}).get('initData', '')
            if not raw:
                raw = request.args.get('initData', '')
            return parse_init_data(raw)

        @app.route('/api/me')
        def whoami():
            user = current_user()
            if not user:
                return jsonify({'authorized': False, 'canReview': False,
                                'deals': 0, 'required': REQUIRED_DEALS})
            try:
                deals = completed_deals(user['id'])
            except RuntimeError:
                return jsonify({'authorized': True, 'canReview': False, 'deals': 0,
                                'required': REQUIRED_DEALS, 'error': 'unavailable'}), 503

            return jsonify({
                'authorized': True,
                'username': display_name(user),
                'deals': deals,
                'required': REQUIRED_DEALS,
                'canReview': deals >= REQUIRED_DEALS,
            })

        @app.route('/api/get-custom-reviews')
        def get_custom_reviews():
            user = current_user()
            if not user:
                return jsonify({'reviews': []})
            try:
                return jsonify({'reviews': read_custom_reviews(user['id'], display_name(user))})
            except Exception as e:
                logger.error(f"read reviews error: {e}")
                return jsonify({'reviews': []}), 500

        @app.route('/api/submit-review', methods=['POST'])
        def submit_review():
            user = current_user()
            if not user:
                return jsonify({'success': False, 'error': 'auth'}), 401

            try:
                deals = completed_deals(user['id'])
            except RuntimeError:
                return jsonify({'success': False, 'error': 'unavailable'}), 503

            if deals < REQUIRED_DEALS:
                return jsonify({'success': False, 'error': 'not_enough_deals',
                                'deals': deals, 'required': REQUIRED_DEALS}), 403

            data = request.get_json(silent=True) or {}

            # Ник берём из подписанного initData, а не из тела запроса.
            username = _clean_field(display_name(user), 64)
            gift = _clean_field(data.get('gift'), 64)
            text = _clean_field(data.get('text'), 50)

            try:
                rating = int(data.get('rating'))
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': 'bad rating'}), 400

            if not username or not gift or not text or not 1 <= rating <= 5:
                return jsonify({'success': False, 'error': 'bad payload'}), 400

            try:
                append_custom_review(username, gift, rating, text, user['id'])
            except Exception as e:
                logger.error(f"write review error: {e}")
                return jsonify({'success': False, 'error': 'write failed'}), 500

            return jsonify({'success': True})

        @app.route('/<path:path>')
        def serve_static(path):
            return send_from_directory('site', path)

        # Запуск без логов для экономии памяти
        import logging as flask_logging
        flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)

        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)

    except Exception as e:
        logger.error(f"Flask error: {e}")

def start_bot(webapp_url):
    """Запускает Telegram бота"""
    os.environ['WEBAPP_URL'] = webapp_url
    
    try:
        subprocess.run([sys.executable, 'app.py'])
    except Exception as e:
        logger.error(f"Bot error: {e}")

def main():
    print("🎯 LZMarket Bot")
    
    # Запускаем Cloudflare Tunnel
    public_url = start_cloudflared()
    
    if not public_url:
        print("❌ Tunnel failed")
        sys.exit(1)
    
    print(f"📱 URL: {public_url}\n")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=start_flask, args=(public_url,), daemon=True)
    flask_thread.start()
    
    # Ждем запуска Flask
    time.sleep(2)
    
    # Запускаем бота
    try:
        start_bot(public_url)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
