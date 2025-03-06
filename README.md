# lucky_miner_log

Uses websockets to connect to a lucky miner (sha256 miner) and show real time data.

$ python3 luckylogs.py

Uptime: 00h 29m 46s    Pool: public-pool.io:21496    Power: 14.36w    Temp: 48C    Hashrate: 455.52 GH/s    Total shares: 52    Best diff ever: 2.05G                       
Best diff: 94.06M    Last diff: 73.53K    Pool diff: 4.10K    Shares: 31    Hashrate: 463.03 GH/s    Current session: 00h 19m 38s

Generates luckyminer.*.log files, use tail and regex like

tail -f "$(ls -1tRh | head -n 2 | grep luckyminer)" -n 100000 | grep -E "Nonce difficulty [0-9]{6,}"

to search for best difficulties.
