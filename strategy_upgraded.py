import Algofox
from kite_trade import *
import pyotp
import pandas as pd
import json
import traceback
import time
from datetime import datetime, timedelta
import time as sleep_time
from Algofox import *
import pandas_ta as ta


def write_to_order_logs(message):
    with open('OrderLog.txt', 'a') as file:  # Open the file in append mode
        file.write(message + '\n')


def delete_file_contents(file_name):
    try:
        # Open the file in write mode, which truncates it (deletes contents)
        with open(file_name, 'w') as file:
            file.truncate(0)
        print(f"Contents of {file_name} have been deleted.")
    except FileNotFoundError:
        print(f"File {file_name} not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def get_zerodha_credentials():
    delete_file_contents("OrderLog.txt")
    credentials = {}
    try:
        df = pd.read_csv('ZerodhaCredentials.csv')
        for index, row in df.iterrows():
            title = row['Title']
            value = row['Value']
            credentials[title] = value
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return credentials


credentials_dict = get_zerodha_credentials()

user_id = credentials_dict.get('ZerodhaUserId')  # Login Id
password = credentials_dict.get('ZerodhaPassword')  # Login password
fakey = credentials_dict.get('Zerodha2fa')

mode = credentials_dict.get('MODE')
expiery = credentials_dict.get('monthlyexp')
stoploss = credentials_dict.get('Stoploss')
takeprofit = credentials_dict.get('Target')
strategytag = credentials_dict.get('StrategyTag')
tslstep = credentials_dict.get('TSLStep')
tslmove = credentials_dict.get('TSLMove')
strattime = credentials_dict.get('StartTime')
stoptime = credentials_dict.get('Stoptime')
Algofoxid = credentials_dict.get('Algofoxid')
Algofoxpassword = credentials_dict.get('Algofoxpassword')
role = credentials_dict.get('role')
url = credentials_dict.get('algofoxurl')
ordertype = credentials_dict.get('ordertype')
createurl(url)

monthlyexp_str = credentials_dict.get('monthlyexp')
monthlyexp_al = datetime.strptime(monthlyexp_str, "%d-%m-%Y")
monthlyexp_al = monthlyexp_al.strftime("%d%b%Y")

supertrend_period = credentials_dict.get('supertrend_period')
supertrend_multiplier = credentials_dict.get('supertrend_multiplier')

monthlyexp = credentials_dict.get('monthlyexp')

monthlyexp = datetime.strptime(monthlyexp, "%d-%m-%Y")
monthlyexp = monthlyexp.strftime("%Y-%m-%d")
otmbuffer = credentials_dict.get('otmbuffer')
otmbuffer = float(otmbuffer)
Signal_dict = {}

twofa = pyotp.TOTP(fakey)
twofa = twofa.now()

enctoken = get_enctoken(user_id, password, twofa)

kite = KiteApp(enctoken=enctoken)
instruments = kite.instruments("NFO")

df = pd.DataFrame(instruments)
df.to_csv("Instruments.csv")
loginresult = login_algpfox(username=Algofoxid, password=Algofoxpassword, role=role)

if loginresult != 200:
    print(
        "Algofoz credential wrong, shutdown down Trde Copier, please provide correct details and run again otherwise program will not work correctly ...")
    time.sleep(10000)


def extract_and_save_symbols(input_file, output_file):
    try:
        df = pd.read_csv(input_file)
        unique_symbols = df['name'].unique()
        symbols_df = pd.DataFrame({'nfotradingsymbol': unique_symbols})
        symbols_df.to_csv(output_file, index=False)
        print(f"Unique symbols extracted and saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


def extract_and_save_symbols_nfo(input_file, output_file):
    try:

        monthlyexp = credentials_dict.get('monthlyexp')
        monthlyexp = datetime.strptime(monthlyexp, "%d-%m-%Y")
        monthlyexp = monthlyexp.strftime("%Y-%m-%d")
        df = pd.read_csv(input_file)
        filtered_df = df[(df['expiry'] == monthlyexp) & (df['instrument_type'] == 'FUT')]
        unique_symbols_df = filtered_df.drop_duplicates(subset=['name'], keep='first')
        symbols_df = pd.DataFrame({
            'nfotradingsymbol': unique_symbols_df['name'],
            'tradingsymbol': unique_symbols_df['tradingsymbol']
        })
        symbols_df.to_csv(output_file, index=False)
        print(f"Unique symbols extracted and saved to {output_file}")


    except Exception as e:

        traceback.print_exc()


# extract_and_save_symbols_nfo(input_file="Instruments.csv", output_file="UniqueInstrumentsnfo.csv")

def Get_Ohlc():
    global mode

    df = pd.read_csv("UniqueInstruments.csv")
    df["OPEN"] = None
    df["HIGH"] = None
    df["LOW"] = None
    for index, row in df.iterrows():
        symbol = row['nfotradingsymbol']
        try:
            if symbol == "NIFTY" or symbol == "BANKNIFTY":
                if symbol == "NIFTY":
                    res = kite.quote(["NSE:NIFTY 50"])['NSE:NIFTY 50']['ohlc']
                if symbol == "BANKNIFTY":
                    res = kite.quote(["NSE:NIFTY BANK"])['NSE:NIFTY BANK']['ohlc']
            else:

                res = kite.quote(f"NSE:{symbol}")[f"NSE:{symbol}"]['ohlc']

            # Update the DataFrame with open, high, low values
            df.at[index, 'OPEN'] = res['open']
            df.at[index, 'HIGH'] = res['high']
            df.at[index, 'LOW'] = res['low']

            # Save the updated DataFrame to CSV
        except KeyError:
            print(f"Skipping symbol {symbol}. OHLC data not available.")

    filtered_df = df[(df["OPEN"] == df["HIGH"]) | (df["OPEN"] == df["LOW"])]

    # Save the filtered DataFrame to CSV
    filtered_df.to_csv("UpdatedInstruments.csv", index=False)


def Get_Ohlc_nfo():
    global mode

    df = pd.read_csv("UniqueInstrumentsnfo.csv")
    df["OPEN"] = None
    df["HIGH"] = None
    df["LOW"] = None
    for index, row in df.iterrows():
        symbol = row['tradingsymbol']
        try:
            if symbol == "NIFTY" or symbol == "BANKNIFTY":
                if symbol == "NIFTY":
                    res = kite.quote(["NFO:NIFTY 50"])['NFO:NIFTY 50']
                if symbol == "BANKNIFTY":
                    res = kite.quote(["NFO:NIFTY BANK"])['NFO:NIFTY BANK']
            else:

                res = kite.quote(f"NFO:{symbol}")[f"NFO:{symbol}"]['ohlc']

            # Update the DataFrame with open, high, low values
            df.at[index, 'OPEN'] = res['open']
            df.at[index, 'HIGH'] = res['high']
            df.at[index, 'LOW'] = res['low']

            # Save the updated DataFrame to CSV
        except KeyError:
            print(f"Skipping symbol {symbol}. OHLC data not available.")

    filtered_df = df[(df["OPEN"] == df["HIGH"]) | (df["OPEN"] == df["LOW"])]

    # Save the filtered DataFrame to CSV
    filtered_df.to_csv("UpdatedInstrumentsnfo.csv", index=False)


# Get_Ohlc_nfo()

filtered_dfs = {}


def get_atm_otm_detail():
    global filtered_dfs, monthlyexp
    df = pd.read_csv("UpdatedInstruments.csv")
    pf = pd.read_csv("Instruments.csv")
    unique_symbols = df["nfotradingsymbol"].unique()
    try:
        monthlyexp = credentials_dict.get('monthlyexp')
        monthlyexp = datetime.strptime(monthlyexp, "%d-%m-%Y")
        monthlyexp = monthlyexp.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error while processing monthly expiration date: {e}")
        return  # You can return or handle the error as needed

    for symbol in unique_symbols:
        try:
            current_symbol_df = df[df["nfotradingsymbol"] == symbol]
            current_pf_filtered = pf[
                (pf["name"] == symbol) & (pf["expiry"] == monthlyexp) & (pf["instrument_type"] == "CE")]

            if not current_pf_filtered.empty:
                current_pf_filtered["strike_diff"] = abs(
                    current_pf_filtered["strike"] - current_symbol_df["OPEN"].values[0])

                min_diff_row = current_pf_filtered.loc[current_pf_filtered['strike_diff'].idxmin()]
                min_diff_idx = current_pf_filtered.index.get_loc(min_diff_row.name)
                selected_rows = current_pf_filtered.iloc[
                                max(min_diff_idx - 2, 0):min(min_diff_idx + 3, len(current_pf_filtered))]

                current_pf_filtered = selected_rows.copy()

                current_pf_filtered = current_pf_filtered[["tradingsymbol", "strike", "strike_diff", "lot_size"]]

                filtered_dfs[symbol] = {
                    'df': current_symbol_df,
                    'pf_filtered': current_pf_filtered
                }
        except Exception as e:
            print(f"Error while processing symbol {symbol}: {e}")
            continue


def get_atm_otm_detail_nfo():
    global filtered_dfs, monthlyexp
    df = pd.read_csv("UpdatedInstrumentsnfo.csv")
    pf = pd.read_csv("Instruments.csv")
    unique_symbols = df["nfotradingsymbol"].unique()
    try:
        monthlyexp = credentials_dict.get('monthlyexp')
        monthlyexp = datetime.strptime(monthlyexp, "%d-%m-%Y")
        monthlyexp = monthlyexp.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error while processing monthly expiration date: {e}")
        return  # You can return or handle the error as needed

    for symbol in unique_symbols:
        try:
            current_symbol_df = df[df["nfotradingsymbol"] == symbol]

            current_pf_filtered = pf[
                (pf["name"] == symbol) & (pf["expiry"] == monthlyexp) & (pf["instrument_type"] == "CE")]

            if not current_pf_filtered.empty:
                current_pf_filtered["strike_diff"] = abs(
                    current_pf_filtered["strike"] - current_symbol_df["OPEN"].values[0])

                min_diff_row = current_pf_filtered.loc[current_pf_filtered['strike_diff'].idxmin()]
                min_diff_idx = current_pf_filtered.index.get_loc(min_diff_row.name)

                selected_rows = current_pf_filtered.iloc[
                                max(min_diff_idx - 2, 0):min(min_diff_idx + 3, len(current_pf_filtered))]
                if len(selected_rows) >= 5:
                    current_pf_filtered = selected_rows.copy()
                    current_pf_filtered = current_pf_filtered[["tradingsymbol", "strike", "strike_diff", "lot_size"]]

                    filtered_dfs[symbol] = {
                        'df': current_symbol_df,
                        'pf_filtered': current_pf_filtered
                    }
        except Exception as e:
            print(f"Error while processing symbol {symbol}: {e}")
            continue


# get_atm_otm_detail_nfo()

def condition_order_placement():
    global mode, expiery, otmbuffer, ordertype, filtered_dfs, stoploss, takeprofit, strategytag, tslstep, tslmove, Signal_dict, Algofoxid, Algofoxpassword, role, monthlyexp_al
    try:
        ordertype = credentials_dict.get('ordertype')
        otmbuffer = float(credentials_dict.get('otmbuffer'))
        Algofoxid = credentials_dict.get('Algofoxid')
        Algofoxpassword = credentials_dict.get('Algofoxpassword')
        role = credentials_dict.get('role')
        stoploss = credentials_dict.get('Stoploss')
        takeprofit = credentials_dict.get('Target')
        strategytag = credentials_dict.get('StrategyTag')
        tslstep = credentials_dict.get('TSLStep')
        tslmove = credentials_dict.get('TSLMove')
        otm_ce1 = None
        otm_ce2 = None
        otm_pe1 = None
        otm_pe2 = None
        otm_pe2_O = None
        otm_pe2_L = None
        otm_pe1_O = None
        otm_pe1_L = None
        otm_ce2_O = None
        otm_ce2_L = None
        otm_ce1_O = None
        otm_ce1_L = None
        ce_atm_O = None
        ce_atm_H = None
        ce_atm_L = None
        pe_atm_O = None
        pe_atm_H = None
        pe_atm_L = None
        ce_atm_symbol = None
        expiery = datetime.strptime(expiery, '%d-%m-%Y')
        expiery = expiery.strftime('%Y-%m-%d')
        # expiery="2023-09-23"
        expiery = datetime.strptime(expiery, "%Y-%m-%d")
        expiery = expiery.strftime("%y%b").upper()

        if mode == "NSE":
            df = pd.read_csv("UpdatedInstruments.csv")
            unique_symbols = df["nfotradingsymbol"].unique()
            # unique_tradingsymbols = df["tradingsymbol"].unique()
            # symbol_map = {symbol: trading_symbol for symbol, trading_symbol in
            #               zip(unique_symbols, unique_tradingsymbols)}

        if mode == "NFO":
            df = pd.read_csv("UpdatedInstrumentsnfo.csv")
            unique_symbols = df["nfotradingsymbol"].unique()
            unique_tradingsymbols = df["tradingsymbol"].unique()
            symbol_map = {symbol: trading_symbol for symbol, trading_symbol in
                          zip(unique_symbols, unique_tradingsymbols)}

        for symbol in unique_symbols:
            try:
                current_symbol_df = df[df["nfotradingsymbol"] == symbol]
                print(f"Check Trades for @ {symbol}")
                if symbol in filtered_dfs:
                    pf_filtered = filtered_dfs[symbol]['pf_filtered']
                    min_diff_row = pf_filtered.loc[pf_filtered['strike_diff'].idxmin()]
                    atm_strike = min_diff_row['strike']
                    lot = min_diff_row['lot_size']
                    if atm_strike % 1 == 0:
                        atm_strike = int(atm_strike)

                    sorted_strikes = sorted(pf_filtered['strike'])

                    atm_index = sorted_strikes.index(atm_strike)

                    if atm_index >= 0 and atm_index < len(sorted_strikes):
                        otm_ce_strike1 = sorted_strikes[atm_index + 1]

                    if otm_ce_strike1 % 1 == 0:
                        otm_ce_strike1 = int(otm_ce_strike1)

                    if atm_index >= 0 and atm_index < len(sorted_strikes):
                        otm_ce_strike2 = sorted_strikes[atm_index + 2]

                    if otm_ce_strike2 % 1 == 0:
                        otm_ce_strike2 = int(otm_ce_strike2)

                    if atm_index >= 0 and atm_index < len(sorted_strikes):
                        otm_pe_strike1 = sorted_strikes[atm_index - 2]

                    if otm_pe_strike1 % 1 == 0:
                        otm_pe_strike1 = int(otm_pe_strike1)
                    if atm_index >= 0 and atm_index < len(sorted_strikes):
                        otm_pe_strike2 = sorted_strikes[atm_index - 3]

                    if otm_pe_strike2 % 1 == 0:
                        otm_pe_strike2 = int(otm_pe_strike2)

                    ce_atm_symbol = f"{symbol}{expiery}{atm_strike}CE"
                    # print(kite.quote(f"NFO:{ce_atm_symbol}")[f"NFO:{ce_atm_symbol}"]['ohlc'])
                    res = kite.quote(f"NFO:{ce_atm_symbol}")[f"NFO:{ce_atm_symbol}"]['ohlc']
                    ce_atm_O = res['open']
                    ce_atm_H = res['high']
                    ce_atm_L = res['low']
                    ce_atm_C = res['close']

                    pe_atm_symbol = f"{symbol}{expiery}{atm_strike}PE"
                    res = kite.quote(f"NFO:{pe_atm_symbol}")[f"NFO:{pe_atm_symbol}"]['ohlc']
                    pe_atm_O = res['open']
                    pe_atm_H = res['high']
                    pe_atm_L = res['low']
                    pe_atm_C = res['close']

                    otm_ce_symbol1 = f"{symbol}{expiery}{otm_ce_strike1}CE"
                    print(otm_ce_symbol1)
                    res = kite.quote(f"NFO:{otm_ce_symbol1}")[f"NFO:{otm_ce_symbol1}"]['ohlc']
                    otm_ce1_O = res['open']
                    otm_ce1_H = res['high']
                    otm_ce1_L = res['low']
                    otm_ce1_C = res['close']

                    otm_ce_symbol2 = f"{symbol}{expiery}{otm_ce_strike2}CE"
                    res = kite.quote(f"NFO:{otm_ce_symbol2}")[f"NFO:{otm_ce_symbol2}"]['ohlc']
                    otm_ce2_O = res['open']
                    otm_ce2_H = res['high']
                    otm_ce2_L = res['low']
                    otm_ce2_C = res['close']

                    otm_pe_symbol1 = f"{symbol}{expiery}{otm_pe_strike1}PE"

                    res = kite.quote(f"NFO:{otm_pe_symbol1}")[f"NFO:{otm_pe_symbol1}"]['ohlc']

                    otm_pe1_O = res['open']
                    otm_pe1_H = res['high']
                    otm_pe1_L = res['low']
                    otm_pe1_C = res['close']

                    otm_pe_symbol2 = f"{symbol}{expiery}{otm_pe_strike2}PE"
                    res = kite.quote(f"NFO:{otm_pe_symbol2}")[f"NFO:{otm_pe_symbol2}"]['ohlc']
                    otm_pe2_O = res['open']
                    otm_pe2_H = res['high']
                    otm_pe2_L = res['low']
                    otm_pe2_C = res['close']
                condition1_met = any((current_symbol_df["OPEN"] == current_symbol_df["HIGH"]) & (
                            current_symbol_df["OPEN"] != current_symbol_df["LOW"]))

                # Condition 2: OPEN == LOW
                condition2_met = any((current_symbol_df["OPEN"] == current_symbol_df["LOW"]) & (
                            current_symbol_df["OPEN"] != current_symbol_df["HIGH"]))

                if condition1_met:
                    if ce_atm_O == ce_atm_H and pe_atm_O == pe_atm_L and ce_atm_O != ce_atm_L and pe_atm_O != pe_atm_H:
                        otm_pe1_open_up, otm_pe1_open_down = calculate_percentage_values(otm_pe1_O, otmbuffer)
                        otm_pe2_open_up, otm_pe2_open_down = calculate_percentage_values(otm_pe2_O, otmbuffer)

                        if otm_pe1_L >= otm_pe1_open_down and otm_pe1_L <= otm_pe1_open_up and otm_pe2_L >= otm_pe2_open_down and otm_pe2_L <= otm_pe2_open_up:
                            current_time = datetime.now()
                            timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

                            script_ltp = kite.quote(f"NFO:{pe_atm_symbol}")[f"NFO:{pe_atm_symbol}"]

                            depth_info = script_ltp.get('depth', {})
                            buy_details = depth_info.get('buy', [])
                            first_buy_price = None
                            if buy_details:
                                first_buy_price = buy_details[0].get('price')
                                script_ltp = first_buy_price
                            # print("script_ltp:", script_ltp)
                            tp = (float(takeprofit) / 100) * float(script_ltp)
                            tp = script_ltp + tp
                            sl = pe_atm_O
                            tslstep_val = (float(tslstep) / 100) * float(script_ltp)
                            tslstep_val = script_ltp + tslstep_val
                            tslmove_val = (float(tslmove) / 100) * float(script_ltp)
                            tslmove_val = sl + tslmove_val
                            if mode == 'NSE':
                                NFOSYM_value = "NULL"
                            else:
                                NFOSYM_value = symbol_map.get(symbol)

                            trade_details = {
                                "Sym": symbol,
                                "NFOSYM":NFOSYM_value,
                                "exp": expiery,
                                "atm_strike": atm_strike,
                                "Contracttype": "PE",
                                "lotsize": lot,
                                "Target": tp,
                                "Stop": sl,
                                "tslstep_val": tslstep_val,
                                "tslmove_val": tslmove_val,
                                "t": True,
                                "s": True,
                                "strategy_mode": mode,
                                "symext":  None,
                                "flip": 0,
                            }

                            algofox_symbol = f"{trade_details['Sym']}|{monthlyexp_al}|{trade_details['atm_strike']}|{trade_details['Contracttype']}"
                            s = f"{trade_details['Sym']}{trade_details['exp']}{trade_details['atm_strike']}{trade_details['Contracttype']}"
                            Algofox.Buy_order_algofox(symbol=algofox_symbol, quantity=trade_details['lotsize'],
                                                      instrumentType="OPTSTK", direction="BUY",
                                                      product="MIS", strategy=strategytag, order_typ=ordertype,
                                                      price=float(script_ltp),
                                                      username=Algofoxid, password=Algofoxpassword, role=role)
                            timestamp = datetime.now()
                            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                            orderlog = f"{timestamp} Buy order executed for {s} for lotsize= {lot} @ {script_ltp} ,Target ={tp} And Stoploss ={sl}, Condition met = Open is equal to High "
                            write_to_order_logs(orderlog)
                            print(orderlog)
                            Signal_dict[pe_atm_symbol] = trade_details

                if condition2_met:
                    if ce_atm_O == ce_atm_L and pe_atm_O == pe_atm_H and ce_atm_O != ce_atm_H and pe_atm_O != pe_atm_L:
                        otm_ce1_open_up, otm_ce1_open_down = calculate_percentage_values(otm_ce1_O, otmbuffer)
                        otm_ce2_open_up, otm_ce2_open_down = calculate_percentage_values(otm_ce2_O, otmbuffer)
                        if otm_ce1_L >= otm_ce1_open_down and otm_ce1_L <= otm_ce1_open_up and otm_ce2_L >= otm_ce2_open_down and otm_ce2_L <= otm_ce2_open_up:
                            current_time = datetime.now()
                            timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

                            script_ltp = kite.quote(f"NFO:{ce_atm_symbol}")[f"NFO:{ce_atm_symbol}"]

                            depth_info = script_ltp.get('depth', {})
                            buy_details = depth_info.get('buy', [])
                            first_buy_price = None
                            if buy_details:
                                first_buy_price = buy_details[0].get('price')
                                script_ltp = first_buy_price
                            print("script_ltp:", script_ltp)
                            tp = (float(takeprofit) / 100) * float(script_ltp)
                            tp = script_ltp + tp
                            sl = ce_atm_O
                            tslstep_val = (float(tslstep) / 100) * float(script_ltp)
                            tslstep_val = script_ltp + tslstep_val
                            tslmove_val = (float(tslmove) / 100) * float(script_ltp)
                            tslmove_val = sl + tslmove_val
                            if mode == 'NSE':
                                NFOSYM_value = "NULL"
                            else:
                                NFOSYM_value = symbol_map.get(symbol)

                            trade_details = {
                                "Sym": symbol,
                                "NFOSYM":NFOSYM_value,
                                "exp": expiery,
                                "atm_strike": atm_strike,
                                "Contracttype": "CE",
                                "lotsize": lot,
                                "Target": tp,
                                "Stop": sl,
                                "tslstep_val": tslstep_val,
                                "tslmove_val": tslmove_val,
                                "t": True,
                                "s": True,
                                "strategy_mode": mode,
                                "flip":0,
                                "symext": None
                            }

                            algofox_symbol = f"{trade_details['Sym']}|{monthlyexp_al}|{trade_details['atm_strike']}|{trade_details['Contracttype']}"

                            s = f"{trade_details['Sym']}{trade_details['exp']}{trade_details['atm_strike']}{trade_details['Contracttype']}"

                            Algofox.Buy_order_algofox(symbol=algofox_symbol, quantity=trade_details['lotsize'],
                                                      instrumentType="OPTSTK",
                                                      direction="BUY",
                                                      product="MIS", strategy=strategytag, order_typ=ordertype,
                                                      price=float(script_ltp),
                                                      username=Algofoxid, password=Algofoxpassword, role=role)

                            timestamp = datetime.now()
                            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                            orderlog = f"{timestamp} Buy order executed for {s} for lotsize= {lot} @ {script_ltp} ,Target ={tp} And Stoploss ={sl}, Condition met = Open is equal to Low "
                            write_to_order_logs(orderlog)
                            print(orderlog)
                            Signal_dict[ce_atm_symbol] = trade_details

            except Exception as e:
                # Handle the exception for the current stock
                traceback.print_exc()
                continue  # Continue to the next stock
    except Exception as e:
        traceback.print_exc()
        return
    print("Signal_dict= ", Signal_dict)


def convert_to_human_readable(df):
    df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df


def get_instrument_token (Sym):
    df=pd.read_csv("Instruments.csv")
    matching_row = df[df["tradingsymbol"] == Sym]
    if not matching_row.empty:
        return matching_row.iloc[0]["instrument_token"]
    else:
        return None




def get_historical_data(Token , sym, supertrend_period , supertrend_multiplier):
    try:
        from_datetime = datetime.now() - timedelta(days=5)  # From last 1 day
        to_datetime = datetime.now()
        res = kite.historical_data(instrument_token=Token, from_date=from_datetime, to_date=to_datetime,
                                   interval="2minute", continuous=False, oi=True)
        price_data = pd.DataFrame(res)
        price_data = convert_to_human_readable(pd.DataFrame(res))
        price_data["SYMBOL"] = sym
        price_data['date'] = pd.to_datetime(price_data['date'])
        colname = f'SUPERT_{int(supertrend_period)}_{float(supertrend_multiplier)}'
        colname2 = f'SUPERTd_{int(supertrend_period)}_{float(supertrend_multiplier)}'

        price_data["Supertrend Values"] = ta.supertrend(high=price_data['high'], low=price_data['low'], close=price_data['close'], length=int(supertrend_period),
                                                multiplier=float(supertrend_multiplier))[colname]
        price_data["Supertrend Signal"] = ta.supertrend(high=price_data['high'], low=price_data['low'], close=price_data['close'], length=int(supertrend_period),
                                                multiplier=float(supertrend_multiplier))[colname2]

        return price_data

    except (IndexError, KeyError) as e:
        print(f"Error: {e}")


def ATM_CE_AND_PE_SYMBOL(ltp,symbol):
    global monthlyexp
    try:
        monthlyexp = credentials_dict.get('monthlyexp')
        monthlyexp = datetime.strptime(monthlyexp, "%d-%m-%Y")
        monthlyexp = monthlyexp.strftime("%Y-%m-%d")
        pf = pd.read_csv("Instruments.csv")
        filtered_df = pf[(pf['expiry'] == monthlyexp) & (pf['instrument_type'] == 'CE') & (pf["name"]==symbol)]
        if not filtered_df.empty:
            filtered_df["strike_diff"] = abs(
                filtered_df["strike"] - ltp)
            min_diff_row = filtered_df.loc[filtered_df['strike_diff'].idxmin()]
        strike=int(min_diff_row["strike"])

        cesymname=min_diff_row["tradingsymbol"]
        pesymname = cesymname.rsplit('CE', 1)[0] + 'PE'
        return cesymname,pesymname

    except Exception as e:
        print(f"ATM_CE_AND_PE_COMBIMED error : {str(e)}")
def ATM_CE_AND_PE(ltp,symbol):
    global monthlyexp
    try:
        monthlyexp = credentials_dict.get('monthlyexp')
        monthlyexp = datetime.strptime(monthlyexp, "%d-%m-%Y")
        monthlyexp = monthlyexp.strftime("%Y-%m-%d")
        pf = pd.read_csv("Instruments.csv")
        filtered_df = pf[(pf['expiry'] == monthlyexp) & (pf['instrument_type'] == 'CE') & (pf["name"]==symbol)]
        if not filtered_df.empty:
            filtered_df["strike_diff"] = abs(
                filtered_df["strike"] - ltp)
            min_diff_row = filtered_df.loc[filtered_df['strike_diff'].idxmin()]
        strike=int(min_diff_row["strike"])

        cesymname=min_diff_row["tradingsymbol"]
        pesymname = cesymname.rsplit('CE', 1)[0] + 'PE'
        return strike


    except Exception as e:
        print(f"ATM_CE_AND_PE_COMBIMED error : {str(e)}")


flip=0
supertrendbuy = False
supertrendsell = False
def supertrend_sl(Signal_dict):
    global supertrend_period,supertrend_multiplier,monthlyexp_al,flip,supertrendbuy,supertrendsell

    for symbol, data in Signal_dict.items():

        if data.get('strategy_mode') == "NFO":
            print(f"Supertrend calculation started for { data.get('NFOSYM')} ")
            instoken = get_instrument_token(data.get('NFOSYM'))
            DATAFRAME=get_historical_data(instoken, data.get('NFOSYM'), supertrend_period, supertrend_multiplier)
            last_supertrend_signal = DATAFRAME['Supertrend Signal'].iloc[-1]
            second_last_supertrend_signal = DATAFRAME['Supertrend Signal'].iloc[-2]
            third_last_supertrend_signal = DATAFRAME['Supertrend Signal'].iloc[-3]
            print("Supertrend 2nd :", second_last_supertrend_signal)
            print("Supertrend 3rd :", third_last_supertrend_signal)

        #      buy flip
            if third_last_supertrend_signal == -1 and second_last_supertrend_signal == 1 and data.get('flip') <= 1 and supertrendbuy==False:

                supertrendbuy=True
                supertrendsell = False
                scriptltp = kite.quote(f"NFO:{data.get('NFOSYM')}")[f"NFO:{data.get('NFOSYM')}"]
                algofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{data.get('atm_strike')}|{data.get('Contracttype')}"
                Algofox.Sell_order_algofox(symbol=algofox_symbol, quantity=int(data.get('lotsize', None)), instrumentType="OPTSTK",
                                           direction="SELL",
                                           product="MIS", strategy=strategytag, order_typ=ordertype,
                                           price=0,
                                           username=Algofoxid, password=Algofoxpassword, role=role)

                ltp = kite.quote(f"NFO:{data.get('NFOSYM')}")[f"NFO:{data.get('NFOSYM')}"]
                ltp = ltp['depth']['buy'][0]['price']
                print("ltp: ", ltp)
                print("NFOSYM: ", data.get('NFOSYM'))
                cesymname, pesymname = ATM_CE_AND_PE_SYMBOL(ltp, data.get('Sym'))
                print("cesymname: ", cesymname)
                strike = ATM_CE_AND_PE(ltp, data.get('Sym'))
                data['atm_strike']=strike
                newalgofox_symbol=f"{data.get('Sym')}|{monthlyexp_al}|{strike}|CE"
                celtp=kite.quote(f"NFO:{cesymname}")[f"NFO:{cesymname}"]
                celtp = celtp['depth']['buy'][0]['price']
                if data['flip']==1:
                    Algofox.Buy_order_algofox(symbol=newalgofox_symbol, quantity=int(data.get('lotsize', None)),
                                               instrumentType="OPTSTK",
                                               direction="BUY",
                                               product="MIS", strategy=strategytag, order_typ=ordertype,
                                               price=celtp,
                                               username=Algofoxid, password=Algofoxpassword, role=role)
                data['flip'] += 1
                # close previous trade
                # calculate latest atm
                #  send order
                # ce lena h
                data['atm_strike'] = strike
                data['Contracttype'] = "CE"
                print(f"Supertrend flipped buy {symbol} ")

                timestamp = datetime.now()
                timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                orderlog = f"{timestamp} Supertrend flipped buy @ {symbol} @ {celtp} "
                write_to_order_logs(orderlog)




        #      sell flip
            if third_last_supertrend_signal == 1 and second_last_supertrend_signal == -1 and data.get('flip') <= 1 and supertrendsell == False:

                supertrendbuy =  False
                supertrendsell = True
                print(f"Supertrend flipped buy {symbol} ")
                # pe lena h
                algofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{data.get('atm_strike')}|{data.get('Contracttype')}"
                Algofox.Sell_order_algofox(symbol=algofox_symbol, quantity=int(data.get('lotsize', None)),
                                           instrumentType="OPTSTK",
                                           direction="SELL",
                                           product="MIS", strategy=strategytag, order_typ=ordertype,
                                           price=0,
                                           username=Algofoxid, password=Algofoxpassword, role=role)

                ltp = kite.quote(f"NFO:{data.get('NFOSYM')}")[f"NFO:{data.get('NFOSYM')}"]
                ltp=ltp['depth']['buy'][0]['price']
                print("ltp: ", ltp)
                print("NFOSYM: ", data.get('NFOSYM'))
                cesymname, pesymname = ATM_CE_AND_PE_SYMBOL(ltp, data.get('Sym'))
                print("cesymname: ", cesymname)
                strike = ATM_CE_AND_PE(ltp, data.get('Sym'))
                data['atm_strike'] = strike
                newalgofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{strike}|PE"
                peltp = kite.quote(f"NFO:{pesymname}")[f"NFO:{pesymname}"]
                peltp = peltp['depth']['buy'][0]['price']
                if data['flip']==1:
                    Algofox.Buy_order_algofox(symbol=newalgofox_symbol, quantity=int(data.get('lotsize', None)),
                                              instrumentType="OPTSTK",
                                              direction="BUY",
                                              product="MIS", strategy=strategytag, order_typ=ordertype,
                                              price=peltp,
                                              username=Algofoxid, password=Algofoxpassword, role=role)

                data['flip'] += 1
                data['atm_strike'] = strike
                data['Contracttype'] = "PE"
                timestamp = datetime.now()
                timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                orderlog = f"{timestamp} Supertrend flipped sell @ {symbol} @ {peltp}"
                write_to_order_logs(orderlog)




        if data.get('strategy_mode') == "NSE":
            print(f"Supertrend calculation started for {data.get('Sym')} ")
            instoken = get_instrument_token(data.get('Sym'))

            DATAFRAME=get_historical_data(instoken, data.get("Sym"), supertrend_period, supertrend_multiplier)
            last_supertrend_signal = DATAFRAME['Supertrend Signal'].iloc[-1]
            second_last_supertrend_signal = DATAFRAME['Supertrend Signal'].iloc[-2]
            third_last_supertrend_signal = DATAFRAME['Supertrend Signal'].iloc[-3]
            #      buy flip
            if third_last_supertrend_signal == -1 and second_last_supertrend_signal == 1 and data.get('flip') <= 2:
                data['flip'] += 1
                scriptltp = kite.quote(f"NSE:{data.get('Sym')}")[f"NSE:{data.get('Sym')}"]
                print(f"Supertrend flipped buy {data.get('Sym')} ")
                algofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{data.get('atm_strike')}|{data.get('Contracttype')}"
                Algofox.Sell_order_algofox(symbol=algofox_symbol, quantity=int(data.get('lotsize', None)),
                                           instrumentType="OPTSTK",
                                           direction="SELL",
                                           product="MIS", strategy=strategytag, order_typ=ordertype,
                                           price=float(scriptltp),
                                           username=Algofoxid, password=Algofoxpassword, role=role)

                ltp = kite.quote(f"NSE:{data.get('Sym')}")[f"NSE:{data.get('Sym')}"]
                cesymname, pesymname = ATM_CE_AND_PE_SYMBOL(ltp, data.get('Sym'))
                strike = ATM_CE_AND_PE(ltp, data.get('Sym'))
                newalgofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{strike}|CE"
                Algofox.Buy_order_algofox(symbol=newalgofox_symbol, quantity=int(data.get('lotsize', None)),
                                          instrumentType="OPTSTK",
                                          direction="BUY",
                                          product="MIS", strategy=strategytag, order_typ=ordertype,
                                          price=kite.quote(f"NFO:{cesymname}")[f"NFO:{cesymname}"],
                                          username=Algofoxid, password=Algofoxpassword, role=role)
                data['atm_strike'] = strike
                data['Contracttype'] = "CE"
                timestamp = datetime.now()
                timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                orderlog = f"{timestamp} Supertrend flipped buy @ {symbol} @ {kite.quote(f'NFO:{cesymname}')[f'NFO:{cesymname}']} "
                write_to_order_logs(orderlog)
            #      sell flip
            if third_last_supertrend_signal == 1 and second_last_supertrend_signal == -1 and data.get('flip') <= 2:
                data['flip'] += 1
                print(f"Supertrend flipped buy {symbol} ")
                # pe lena h
                algofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{data.get('atm_strike')}|{data.get('Contracttype')}"
                Algofox.Sell_order_algofox(symbol=algofox_symbol, quantity=int(data.get('lotsize', None)),
                                           instrumentType="OPTSTK",
                                           direction="SELL",
                                           product="MIS", strategy=strategytag, order_typ=ordertype,
                                           price=float(scriptltp),
                                           username=Algofoxid, password=Algofoxpassword, role=role)

                ltp = kite.quote(f"NSE:{data.get('Sym')}")[f"NSE:{data.get('Sym')}"]
                cesymname, pesymname = ATM_CE_AND_PE_SYMBOL(ltp, data.get('Sym'))
                strike = ATM_CE_AND_PE(ltp, data.get('Sym'))
                newalgofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{strike}|PE"
                Algofox.Buy_order_algofox(symbol=newalgofox_symbol, quantity=int(data.get('lotsize', None)),
                                          instrumentType="OPTSTK",
                                          direction="BUY",
                                          product="MIS", strategy=strategytag, order_typ=ordertype,
                                          price=kite.quote(f"NFO:{pesymname}")[f"NFO:{pesymname}"],
                                          username=Algofoxid, password=Algofoxpassword, role=role)
                data['atm_strike'] = strike
                data['Contracttype'] = "PE"
                timestamp = datetime.now()
                timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                orderlog = f"{timestamp} Supertrend flipped sell @ {symbol} @ {kite.quote(f'NFO:{pesymname}')[f'NFO:{pesymname}']} "
                write_to_order_logs(orderlog)





def tp_sl():
    global Signal_dict, monthlyexp_al

    for symbol, data in Signal_dict.items():
        symbol = symbol
        target_value = float(data.get('Target', None))
        stop_value = float(data.get('Stop', None))
        tslstep_val = float(data.get('tslstep_val', None))
        tslmove_val = float(data.get('tslmove_val', None))
        lotsize = int(data.get('lotsize', None))
        t = bool(data.get('t', None))
        s = bool(data.get('s', None))
        symsym = f"{data.get('Sym')}{data.get('exp')}{data.get('atm_strike')}{data.get('Contracttype')}"

        algofox_symbol = f"{data.get('Sym')}|{monthlyexp_al}|{data.get('atm_strike')}|{data.get('Contracttype')}"

        try:
            scriptltp = kite.quote(f"NFO:{symbol}")[f"NFO:{symbol}"]
            depth_info = scriptltp.get('depth', {})
            buy_details = depth_info.get('buy', [])
            first_buy_price = None
            if buy_details:
                first_buy_price = buy_details[0].get('price')
                scriptltp = first_buy_price

            # print(f"Checking Stoploss and Takeprofit for {symbol}")

            if t == True and s == True:
                if scriptltp >= target_value and target_value > 0 and t == True:
                    t = False
                    Signal_dict[symbol]['t'] = t  # Assign the updated t value
                    print(f"Take profit executed @ {symbol} @ {scriptltp}")
                    Algofox.Sell_order_algofox(symbol=algofox_symbol, quantity=lotsize, instrumentType="OPTSTK",
                                               direction="SELL",
                                               product="MIS", strategy=strategytag, order_typ=ordertype,
                                               price=float(scriptltp),
                                               username=Algofoxid, password=Algofoxpassword, role=role)

                    timestamp = datetime.now()
                    timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                    orderlog = f"{timestamp} Take profit executed for symbol @ {symbol} @ {scriptltp} "
                    write_to_order_logs(orderlog)

                if scriptltp <= stop_value and stop_value > 0 and s == True:
                    s = False
                    Signal_dict[symbol]['s'] = s
                    print(f"Stoploss executed @ {symbol} @ {scriptltp}")
                    Algofox.Sell_order_algofox(symbol=algofox_symbol, quantity=lotsize, instrumentType="OPTSTK",
                                               direction="SELL",
                                               product="MIS", strategy=strategytag, order_typ=ordertype,
                                               price=float(scriptltp),
                                               username=Algofoxid, password=Algofoxpassword, role=role)

                    timestamp = datetime.now()
                    timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                    orderlog = f"{timestamp} Stoploss executed for symbol @ {symbol} @ {scriptltp}"
                    write_to_order_logs(orderlog)
        except TypeError as e:
            print(f"TypeError occurred: {e}")
        # You can add any error handling logic here, or simply continue without further processing
        pass  # To ensure the code continues execution even if the error occurs







def calculate_percentage_values(value, percentage):
    up_value = value * (1 + percentage)
    down_value = value * (1 - percentage)
    return up_value, down_value


def mainstrategy():
    global strattime, stoptime,Signal_dict
    strattime = credentials_dict.get('StartTime')
    stoptime = credentials_dict.get('Stoptime')

    start_time = datetime.strptime(strattime, '%H:%M').time()
    stop_time = datetime.strptime(stoptime, '%H:%M').time()
    functions_executed = False

    while True:
        now = datetime.now().time()

        # Check if it's the start time and functions haven't been executed yet
        if now >= start_time and now < stop_time and not functions_executed:
            if mode == "NSE":
                extract_and_save_symbols(input_file="Instruments.csv", output_file="UniqueInstruments.csv")
                Get_Ohlc()
                get_atm_otm_detail()
                condition_order_placement()
                functions_executed = True

            if mode == "NFO":
                extract_and_save_symbols_nfo(input_file="Instruments.csv", output_file="UniqueInstrumentsnfo.csv")
                Get_Ohlc_nfo()
                get_atm_otm_detail_nfo()
                condition_order_placement()
                functions_executed = True

        # Check if it's past the stop time
        if now >= start_time and functions_executed == True:
            # Rest of the code runs every second
            tp_sl()
            supertrend_sl(Signal_dict)
            sleep_time.sleep(1)


mainstrategy()












