import math
from scipy.stats import norm

def bs_greeks(spot, strike, iv, days, option_type="CE"):
    if iv is None or spot is None or strike is None:
        return {"delta": None, "theta": None, "vega": None, "gamma": None}

    t = days / 365
    r = 0.06  # risk-free

    iv = iv / 100  # convert %

    try:
        d1 = (math.log(spot / strike) + (r + iv**2 / 2) * t) / (iv * math.sqrt(t))
        d2 = d1 - iv * math.sqrt(t)

        if option_type == "CE":
            delta = norm.cdf(d1)
        else:
            delta = -norm.cdf(-d1)

        gamma = norm.pdf(d1) / (spot * iv * math.sqrt(t))
        vega = spot * norm.pdf(d1) * math.sqrt(t) / 100
        theta = -(spot * norm.pdf(d1) * iv/(2*math.sqrt(t))) / 365

        return {
            "delta": round(delta, 3),
            "gamma": round(gamma, 3),
            "vega": round(vega, 3),
            "theta": round(theta, 3)
        }
    except:
        return {"delta": None, "gamma": None, "vega": None, "theta": None}
