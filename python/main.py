from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import time

RPC_URL = "http://alice:password@127.0.0.1:18443"


def get_wallet(client, wallet_name):
    wallets = [w["name"] for w in client.listwalletdir()["wallets"]]

    if wallet_name not in wallets:
        print(f"Creating wallet '{wallet_name}'...")
        client.createwallet(wallet_name)

    if wallet_name not in client.listwallets():
        print(f"Loading wallet '{wallet_name}'...")
        client.loadwallet(wallet_name)

    return AuthServiceProxy(f"{RPC_URL}/wallet/{wallet_name}")


def get_address(script_pub_key):
    if "address" in script_pub_key:
        return script_pub_key["address"]

    if "addresses" in script_pub_key:
        return script_pub_key["addresses"][0]

    return ""


def main():
    try:
        print("Connecting to Bitcoin node...")

        client = AuthServiceProxy(RPC_URL)

        miner = get_wallet(client, "Miner")
        trader = get_wallet(client, "Trader")

        block_count = client.getblockcount()
        print(f"Current block count: {block_count}")

        # Miner address
        miner_reward_address = miner.getnewaddress()

        # Need 101 blocks so coinbase reward becomes spendable
        if block_count < 101:
            blocks_needed = 101 - block_count
            print(f"Mining {blocks_needed} blocks...")
            client.generatetoaddress(blocks_needed, miner_reward_address)

        print(f"Miner balance: {miner.getbalance()} BTC")

        # Trader receiving address
        trader_address = trader.getnewaddress()
        print(f"Trader address: {trader_address}")

        # Send 20 BTC
        print("Sending 20 BTC...")
        txid = miner.sendtoaddress(trader_address, 20)

        print(f"Transaction ID: {txid}")

        # Confirm transaction
        print("Mining confirmation block...")
        client.generatetoaddress(1, miner_reward_address)

        time.sleep(1)

        # Wallet transaction details
        tx = miner.gettransaction(txid)

        block_height = tx["blockheight"]
        block_hash = tx["blockhash"]
        fee = tx["fee"]

        # Decode transaction
        raw_tx = tx["hex"]
        decoded_tx = client.decoderawtransaction(raw_tx)

        # Input details
        vin = decoded_tx["vin"][0]

        prev_tx = client.getrawtransaction(vin["txid"], True)
        prev_vout = prev_tx["vout"][vin["vout"]]

        miner_input_address = get_address(prev_vout["scriptPubKey"])
        miner_input_amount = prev_vout["value"]

        # Output details
        trader_output_address = ""
        trader_output_amount = 0

        miner_change_address = ""
        miner_change_amount = 0

        for vout in decoded_tx["vout"]:
            address = get_address(vout["scriptPubKey"])

            if address == trader_address:
                trader_output_address = address
                trader_output_amount = vout["value"]
            else:
                miner_change_address = address
                miner_change_amount = vout["value"]

        # Write required output
        with open("out.txt", "w") as f:
            f.write(f"{txid}\n")
            f.write(f"{miner_input_address}\n")
            f.write(f"{miner_input_amount}\n")
            f.write(f"{trader_output_address}\n")
            f.write(f"{trader_output_amount}\n")
            f.write(f"{miner_change_address}\n")
            f.write(f"{miner_change_amount}\n")
            f.write(f"{fee}\n")
            f.write(f"{block_height}\n")
            f.write(f"{block_hash}\n")

        print("out.txt created successfully")

        print("\n=== Summary ===")
        print(f"TXID: {txid}")
        print(f"Miner Input: {miner_input_address} ({miner_input_amount} BTC)")
        print(f"Trader Output: {trader_output_address} ({trader_output_amount} BTC)")
        print(f"Miner Change: {miner_change_address} ({miner_change_amount} BTC)")
        print(f"Fee: {fee} BTC")
        print(f"Block Height: {block_height}")
        print(f"Block Hash: {block_hash}")

    except JSONRPCException as e:
        print(f"RPC Error: {e.error}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()