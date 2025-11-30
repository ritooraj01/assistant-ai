def choose_strike(spot, strikes):
    atm = min(strikes, key=lambda x: abs(x - spot))

    # ATM + 1 strike
    otm_call = atm + 50
    otm_put = atm - 50

    return {
        "atm": atm,
        "otm_call": otm_call,
        "otm_put": otm_put
    }
