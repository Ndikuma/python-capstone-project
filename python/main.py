from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import time

RPC_URL = "http://alice:password@127.0.0.1:18443"


def get_wallet(client, wallet_name):
    wallet_dirs = client.listwalletdir()["wallets"]
    wallet_exists = any(w["name"] == wallet_name for w in wallet_dirs)

    if not wallet_exists:
        print(f"Creating wallet '{wallet_name}'...")
        client.createwallet(wallet_name)

    loaded_wallets = client.listwallets()
    if wallet_name not in loaded_wallets:
        print(f"Loading wallet '{wallet_name}'...")
        client.loadwallet(wallet_name)

    return AuthServiceProxy(f"{RPC_URL}/wallet/{wallet_name}")


def main():
    try:
        print("Connecting to Bitcoin node...")

        client = AuthServiceProxy(RPC_URL)

        print("Blockchain Info:")
        print(client.getblockchaininfo())

        miner = get_wallet(client, "Miner")
        trader = get_wallet(client, "Trader")

        block_count = client.getblockcount()
        print(f"Current block count: {block_count}")

        miner_address = miner.getnewaddress()

        if block_count < 101:
            blocks_needed = 101 - block_count
            print(f"Mining {blocks_needed} blocks...")
            client.generatetoaddress(blocks_needed, miner_address)

        miner_balance = miner.getbalance()
        print(f"Miner balance: {miner_balance}")

        trader_address = trader.getnewaddress()
        print(f"Trader address: {trader_address}")

        print("Sending 20 BTC...")
        txid = miner.sendtoaddress(trader_address, 20)

        print(f"TXID: {txid}")

        time.sleep(1)

        print("Mining confirmation block...")
        client.generatetoaddress(1, miner_address)

        time.sleep(1)

        tx = miner.gettransaction(txid)

        block_hash = tx["blockhash"]
        block_height = tx["blockheight"]

        raw_tx = client.getrawtransaction(txid)
        decoded_tx = client.decoderawtransaction(raw_tx)

        print("Transaction confirmed")
        print(f"Block hash: {block_hash}")
        print(f"Block height: {block_height}")

        # TODO:
        # Write exactly what test.spec.ts expects here.
        with open("out.txt", "w") as f:
            f.write(txid + "\n")
            f.write(block_hash + "\n")
            f.write(str(block_height) + "\n")

        print("out.txt created")

    except JSONRPCException as e:
        print(f"RPC Error: {e.error}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()