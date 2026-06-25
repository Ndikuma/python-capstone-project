from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
import time

# Node access params
RPC_URL = "http://alice:password@127.0.0.1:18443"

def create_or_load_wallet(client, wallet_name):
    # Check if wallet exists
    wallets = client.listwalletdir()["wallets"]
    wallet_exists = any(w["name"] == wallet_name for w in wallets)

    if not wallet_exists:
        print(f"Creating wallet '{wallet_name}'...")
        client.createwallet(wallet_name)
    else:
        # Load only if not already loaded
        loaded_wallets = client.listwallets()

        if wallet_name not in loaded_wallets:
            print(f"Loading wallet '{wallet_name}'...")
            client.loadwallet(wallet_name)
        else:
            print(f"Wallet '{wallet_name}' already loaded.")

    return AuthServiceProxy(f"{RPC_URL}/wallet/{wallet_name}")

def main():
    try:
        # General client for non-wallet-specific commands
        client = AuthServiceProxy(RPC_URL)

        # Get blockchain info
        blockchain_info = client.getblockchaininfo()
        print("Blockchain Info:", blockchain_info)

        # Create/Load the wallets, named 'Miner' and 'Trader'
        miner_wallet = create_or_load_wallet(client, "Miner")
        trader_wallet = create_or_load_wallet(client, "Trader")

        # Get initial balances
        miner_initial_balance = miner_wallet.getbalance()
        trader_initial_balance = trader_wallet.getbalance()
        print(f"Miner initial balance: {miner_initial_balance} BTC")
        print(f"Trader initial balance: {trader_initial_balance} BTC")

        # Generate spendable balances in the Miner wallet
        # Need to mine 101 blocks to get spendable coins (first 100 blocks are coinbase maturity)
        # plus some extra to have enough balance
        miner_address = miner_wallet.getnewaddress()
        
        # Check current block count
        current_blocks = client.getblockcount()
        print(f"Current block count: {current_blocks}")
        
        # Generate blocks to get spendable balance
        # We need at least 101 blocks for coinbase maturity + some extra for balance
        blocks_to_mine = 101 - (current_blocks % 101) + 50 if current_blocks < 101 else 150
        if current_blocks < 101:
            blocks_to_mine = 151 - current_blocks
        else:
            blocks_to_mine = 150  # Generate some extra blocks for balance
            
        print(f"Mining {blocks_to_mine} blocks...")
        client.generatetoaddress(blocks_to_mine, miner_address)
        
        # Wait for blocks to be processed
        time.sleep(1)
        
        # Get updated balance
        miner_balance = miner_wallet.getbalance()
        print(f"Miner balance after mining: {miner_balance} BTC")

        # Generate a new address for Trader
        trader_address = trader_wallet.getnewaddress()
        print(f"Trader new address: {trader_address}")

        # Send 20 BTC from Miner to Trader
        print("Sending 20 BTC from Miner to Trader...")
        txid = miner_wallet.sendtoaddress(trader_address, 20)
        print(f"Transaction ID: {txid}")

        # Check the transaction in the mempool
        time.sleep(1)  # Give time for transaction to propagate
        mempool = client.getrawmempool()
        print(f"Transaction in mempool: {txid in mempool}")
        
        if txid in mempool:
            # Get mempool entry details
            mempool_entry = client.getmempoolentry(txid)
            print(f"Mempool entry: {mempool_entry}")

        # Mine 1 block to confirm the transaction
        print("Mining 1 block to confirm transaction...")
        client.generatetoaddress(1, miner_address)
        time.sleep(1)

        # Extract all required transaction details
        # Get the transaction details from the wallet
        tx_details = miner_wallet.gettransaction(txid)
        
        # Get raw transaction
        raw_tx = client.getrawtransaction(txid)
        
        # Decode raw transaction
        decoded_tx = client.decoderawtransaction(raw_tx)
        
        # Get transaction confirmation details
        tx_info = client.gettransaction(txid)
        
        # Get block containing the transaction
        block_hash = tx_info.get('blockhash')
        block_info = client.getblock(block_hash) if block_hash else None
        
        # Get transaction receipt from block
        tx_receipt = None
        if block_hash:
            block_tx = client.getblock(block_hash, 2)  # Verbosity level 2 for full transaction details
            for tx in block_tx['tx']:
                if tx['txid'] == txid:
                    tx_receipt = tx
                    break

        # Prepare data for output
        output_data = {
            "blockchain_info": blockchain_info,
            "miner_balance": miner_balance,
            "trader_balance": trader_wallet.getbalance(),
            "trader_address": trader_address,
            "transaction_id": txid,
            "transaction_details": tx_details,
            "decoded_transaction": decoded_tx,
            "mempool_entry": mempool_entry if txid in mempool else None,
            "block_hash": block_hash,
            "block_info": block_info,
            "transaction_receipt": tx_receipt,
            "raw_transaction": raw_tx,
            "mempool_status": txid in mempool,
            "final_miner_balance": miner_wallet.getbalance(),
            "final_trader_balance": trader_wallet.getbalance()
        }

        # Write the data to ../out.txt in JSON format
        with open('../out.txt', 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print("Data successfully written to ../out.txt")
        
        # Print summary
        print("\n=== Transaction Summary ===")
        print(f"Transaction ID: {txid}")
        print(f"From (Miner): {miner_address}")
        print(f"To (Trader): {trader_address}")
        print(f"Amount: 20 BTC")
        print(f"Confirmed in block: {block_hash}")
        print(f"Final Miner balance: {output_data['final_miner_balance']} BTC")
        print(f"Final Trader balance: {output_data['final_trader_balance']} BTC")
        print("===========================\n")

    except JSONRPCException as e:
        print(f"JSONRPC Error occurred: {e}")
        print(f"Error details: {e.error}")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()