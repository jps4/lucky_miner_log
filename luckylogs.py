import asyncio
import websockets
import re
import signal
import sys
import time
import requests
from datetime import datetime

def sigint_signal(sig, frame):
    print("")
    print(f"{datetime.now()}: Ctrl+C, exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_signal)

current_diff_pattern = re.compile(r"asic_result: Nonce difficulty (\d+\.?\d*) of (\d+\.?\d*)")

def print_data(data, lucky_info):
    # data1 = f"Wifi status: {lucky_info['wifiStatus']}"
    data1 = f"Uptime: {human_readable_timediff(lucky_info['uptimeSeconds'])}"
    data1 += f"    Pool: {lucky_info['stratumURL']}:{lucky_info['stratumPort']}"
    data1 += f"    Power: {human_readable_diff(lucky_info['power'])}w"
    data1 += f"    Temp: {lucky_info['temp']}C"
    data1 += f"    Hashrate: {human_readable_hashrate(lucky_info['hashRate']*10**9)}"
    data1 += f"    Total shares: {lucky_info['sharesAccepted']}"
    data1 += f"    Best diff ever: {lucky_info['bestDiff']}                       \n"

    hashrate = calculate_hashrate(data['current_shares'], data['pool_diff'], data['current_pool_diff_session'])
    data2 = f"Best diff: {human_readable_diff(data['best_diff'])}"
    data2 += f"    Last diff: {human_readable_diff(data['last_diff'])}"
    data2 += f"    Pool diff: {human_readable_diff(data['pool_diff'])}"
    data2 += f"    Shares: {data['shares']}"
    data2 += f"    Hashrate: {human_readable_hashrate(hashrate)}"
    data2 += f"    Current session: {human_readable_timediff(data['current_session'])}                       \n"

    sys.stdout.write("\033[F\033[F")
    sys.stdout.write("\033[K\033[K")
    sys.stdout.write(data1)
    sys.stdout.write(data2)
    sys.stdout.flush()


def human_readable_hashrate(hashrate):
    '''Returns a human readable representation of hashrate.'''

    if hashrate < 1000:
        return '%.2f H/s' % hashrate
    if hashrate < 1000000:
        return '%.2f kH/s' % (hashrate / 1000)
    if hashrate < 1000000000:
        return '%.2f MH/s' % (hashrate / 1000000)

    return '%.2f GH/s' % (hashrate / 1000000000)

def human_readable_diff(diff):
    '''Returns a human readable representation of hashrate.'''

    if diff < 1000:
        return '%.2f' % diff
    if diff < 1000000:
        return '%.2fK' % (diff / 1000)
    if diff < 1000000000:
        return '%.2fM' % (diff / 1000000)

    return '%.2fG' % (diff / 1000000000)

def human_readable_timediff(secs):
    hours = int(secs // 3600)
    mins = int((secs % 3600) // 60)
    secs = int(secs % 60)

    return f"{hours:02d}h {mins:02d}m {secs:02d}s"


def update_session(start_time, start_time_change_pool_diff, best_session) -> dict:
    end_time = time.time()
    if end_time - start_time > best_session:
        best_session = end_time - start_time

    return {
        'current_session': end_time - start_time,
        'current_pool_diff_session': end_time - start_time_change_pool_diff,
        'best_session': best_session
    }

def calculate_hashrate(shares, pool_diff, time_t):
    # calculate hashrate for current pool_diff in one second:
    # print(f"\n\n\nshares: {shares}, pool_diff: {pool_diff}, time: {time_t}")
    return pool_diff * 2**32 * shares / time_t

def update_lucky_info(url: str) -> dict:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {}

async def get_logs():
    ip = "192.168.1.80"
    url_websocket = f"ws://{ip}/api/ws"
    lucky_info_url =f"http://{ip}/api/system/info"
    data = {
        'best_diff': 0.0,
        'best_session': 0.0,
        'shares': 0
    }
    lucky_info = update_lucky_info(lucky_info_url)

    start_time = time.time()

    with open(f"luckyminer.{time.time()}.log", 'w') as lucky_log:
        while True:
            data = { **data,
                'current_session': 0.0,
                'current_shares': 0,
                'pool_diff': 1000.0,
                'current_pool_diff_session': 0.0
            }

            print("")
            print("")

            try:
                async with websockets.connect(url_websocket) as websocket:
                    # print(f"Conectado al WebSocket en {url_websocket}")
                    
                    start_time_change_pool_diff = time.time()
                    try:
                        while True:
                            message = await websocket.recv()
                            lucky_log.write(message)
                            found_diff = current_diff_pattern.search(message)
                            if found_diff:
                                data['last_diff'] = float(found_diff.group(1))
                                if data['last_diff'] > data['best_diff']:
                                    data['best_diff'] = data['last_diff']
                                if float(found_diff.group(2)) != data['pool_diff']:
                                    data['pool_diff'] = float(found_diff.group(2))
                                    data['current_shares'] = 0
                                    start_time_change_pool_diff = time.time()
                                if data['last_diff'] > data['pool_diff']:
                                    data['shares'] += 1
                                    data['current_shares'] += 1

                                    lucky_info = {**lucky_info, **update_lucky_info(lucky_info_url)}

                            data = { **data, **update_session(start_time, start_time_change_pool_diff, data['best_session'])}
                            print_data(data, lucky_info)
                    except KeyboardInterrupt:
                        await websocket.close()
                        raise
            except websockets.ConnectionClosed as e:
                pass
            except KeyboardInterrupt:
                print("Ctrl+C, exiting...")
            except Exception as e:
                pass



asyncio.get_event_loop().run_until_complete(get_logs())

