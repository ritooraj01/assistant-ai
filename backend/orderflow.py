# backend/orderflow.py

def classify_orderflow(ce: dict, pe: dict):
    """
    Use CE/PE OI & change in OI to classify order flow type:
      - Long buildup
      - Short buildup (writing)
      - Long unwinding
      - Short covering
    """
    ce_oi = ce.get("openInterest", 0) or 0
    pe_oi = pe.get("openInterest", 0) or 0
    ce_chg = ce.get("changeinOpenInterest", 0) or 0
    pe_chg = pe.get("changeinOpenInterest", 0) or 0

    ce_vol = ce.get("totalTradedVolume", 0) or 0
    pe_vol = pe.get("totalTradedVolume", 0) or 0

    flow = []
    score = 0.0

    # Very basic classification
    if ce_chg > 0 and ce_vol > 0:
        flow.append("CE long buildup or writing (depends on price trend).")
        score += 0.5

    if ce_chg < 0 and ce_vol > 0:
        flow.append("CE long unwinding / short covering.")
        score -= 0.3

    if pe_chg > 0 and pe_vol > 0:
        flow.append("PE long buildup or writing (depends on price trend).")
        score -= 0.5

    if pe_chg < 0 and pe_vol > 0:
        flow.append("PE long unwinding / short covering.")
        score += 0.3

    ce_dom = ce_oi > pe_oi
    if ce_dom:
        flow.append("Calls have higher OI than puts.")
        score += 0.2
    else:
        flow.append("Puts have higher OI than calls.")
        score -= 0.2

    return {
        "flows": flow,
        "score": round(score, 2),
        "ce_oi": ce_oi,
        "pe_oi": pe_oi,
        "ce_chg": ce_chg,
        "pe_chg": pe_chg
    }
