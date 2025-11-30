// ====================================================================
// GLOBAL VARIABLES
// ====================================================================

// TradingView Lightweight Charts
let chart = null;
let candleSeries = null;
let volumeSeries = null;
let ema21Series = null;
let ema50Series = null;
let supertrendSeries = null;
let markers = [];

let ws = null;
let currentInterval = 5;  // default 5m

function buildApiUrl() {
    return `http://127.0.0.1:8000/api/signal_live?symbol=NIFTY&interval=${currentInterval}&limit=80`;
}

// ====================================================================
// CHART INITIALIZATION
// ====================================================================

function initAdvancedChart() {
    const container = document.getElementById('advancedChart');
    
    // Check if TradingView library loaded
    if (typeof LightweightCharts === 'undefined') {
        console.error("TradingView Lightweight Charts library not loaded!");
        container.innerHTML = '<div style="color: red; padding: 20px;">Chart library failed to load. Check your internet connection.</div>';
        return;
    }
    
    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 400,
        layout: {
            background: { color: "#1e1e1e" },
            textColor: "#ffffff"
        },
        grid: {
            vertLines: { color: "#232323" },
            horzLines: { color: "#232323" }
        },
        timeScale: {
            timeVisible: true,
            secondsVisible: false
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal
        }
    });

    // Candlestick series
    candleSeries = chart.addCandlestickSeries({
        upColor: "#26a69a",
        downColor: "#ef5350",
        borderVisible: false,
        wickDownColor: "#ef5350",
        wickUpColor: "#26a69a"
    });

    // Volume series
    volumeSeries = chart.addHistogramSeries({
        priceFormat: { type: "volume" },
        color: "#4e6aff",
        priceScaleId: "",
        scaleMargins: {
            top: 0.8,
            bottom: 0,
        },
    });

    // EMA 21 series
    ema21Series = chart.addLineSeries({
        color: "#ffcc00",
        lineWidth: 2,
        title: "EMA 21"
    });

    // EMA 50 series
    ema50Series = chart.addLineSeries({
        color: "#ff77aa",
        lineWidth: 2,
        title: "EMA 50"
    });

    // Supertrend series
    supertrendSeries = chart.addLineSeries({
        color: "#00ff99",
        lineWidth: 2,
        title: "Supertrend"
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        chart.applyOptions({ width: container.clientWidth });
    });
}

function updateAdvancedChart(candles, series) {
    if (!candles || candles.length === 0) return;
    if (!chart) return;

    // Format candlestick data
    const formattedCandles = candles.map(c => ({
        time: Math.floor(c.start_ts),
        open: parseFloat(c.open),
        high: parseFloat(c.high),
        low: parseFloat(c.low),
        close: parseFloat(c.close)
    }));

    candleSeries.setData(formattedCandles);

    // Volume data (color by candle direction)
    const volumes = candles.map(c => ({
        time: Math.floor(c.start_ts),
        value: c.volume || 1000,
        color: c.close >= c.open ? "#26a69a80" : "#ef535080" // Semi-transparent
    }));
    volumeSeries.setData(volumes);

    // EMA 21 series
    if (series?.ema21 && series.ema21.length > 0) {
        const ema21Data = series.ema21
            .map((v, i) => ({
                time: formattedCandles[i].time,
                value: parseFloat(v)
            }))
            .filter(d => d.value && !isNaN(d.value));
        
        if (ema21Data.length > 0) {
            ema21Series.setData(ema21Data);
        }
    }

    // EMA 50 series
    if (series?.ema50 && series.ema50.length > 0) {
        const ema50Data = series.ema50
            .map((v, i) => ({
                time: formattedCandles[i].time,
                value: parseFloat(v)
            }))
            .filter(d => d.value && !isNaN(d.value));
        
        if (ema50Data.length > 0) {
            ema50Series.setData(ema50Data);
        }
    }

    // Supertrend series
    if (series?.supertrend && series.supertrend.length > 0) {
        const supertrendData = series.supertrend
            .map((v, i) => ({
                time: formattedCandles[i].time,
                value: parseFloat(v)
            }))
            .filter(d => d.value && !isNaN(d.value));
        
        if (supertrendData.length > 0) {
            supertrendSeries.setData(supertrendData);
        }
    }

    // Apply markers for buy/sell signals
    if (markers.length > 0) {
        candleSeries.setMarkers(markers);
    }

    // Fit content to visible range
    chart.timeScale().fitContent();
}

// ====================================================================
// SIGNAL CARD
// ====================================================================

function updateSignalCard(signal) {
    const card = document.getElementById("signalCard");
    const actionEl = document.getElementById("signalAction");
    const confEl = document.getElementById("signalConfidence");
    const reasonsList = document.getElementById("signalReasons");

    const action = signal.action || "WAIT";
    const conf = signal.confidence || 0;

    card.classList.remove("signal-buy", "signal-sell", "signal-wait");

    if (action === "BUY") card.classList.add("signal-buy");
    else if (action === "SELL") card.classList.add("signal-sell");
    else card.classList.add("signal-wait");

    actionEl.innerText = `Signal: ${action}`;
    confEl.innerText = `Confidence: ${Math.round(conf * 100)}%`;

    reasonsList.innerHTML = "";
    (signal.reasons || []).slice(0, 6).forEach(r => {
        const li = document.createElement("li");
        li.innerText = r;
        reasonsList.appendChild(li);
    });
}

// ====================================================================
// ML PREDICTIONS (GRADIENT BARS)
// ====================================================================

function updateML(ml) {
    if (!ml) {
        ["ml1Bar","ml3Bar","ml5Bar"].forEach(id => {
            document.getElementById(id).style.width = "0%";
        });
        ["ml1Value","ml3Value","ml5Value"].forEach(id => {
            document.getElementById(id).innerText = "--";
        });
        document.getElementById("mlTrend").innerText = "--";
        return;
    }

    const p1 = ml.next_1_up || 0;
    const p3 = ml.next_3_up || 0;
    const p5 = ml.next_5_up || 0;

    setMlBar("ml1Bar", "ml1Value", p1);
    setMlBar("ml3Bar", "ml3Value", p3);
    setMlBar("ml5Bar", "ml5Value", p5);

    // If backend also returns ml_view, we'll set trend here in refreshAll / WS
}

function setMlBar(barId, textId, prob) {
    const bar = document.getElementById(barId);
    const txt = document.getElementById(textId);

    const pct = Math.round(prob * 100);
    bar.style.width = `${pct}%`;
    txt.innerText = `${pct}%`;
}

// ====================================================================
// MARKET MOOD
// ====================================================================

function updateMarketMood(score) {
    const box = document.getElementById("mood-box");
    const val = document.getElementById("mood-score");
    const lbl = document.getElementById("mood-label");

    if (score === undefined || score === null) {
        val.innerText = "--";
        lbl.innerText = "No data";
        box.style.background = "#1a1f27";
        return;
    }

    val.innerText = score;

    if (score > 70) {
        lbl.innerText = "Bullish";
        box.style.background = "#0d3d16";
    } else if (score > 55) {
        lbl.innerText = "Positive";
        box.style.background = "#1c5420";
    } else if (score > 45) {
        lbl.innerText = "Neutral";
        box.style.background = "#5d5d5d";
    } else if (score > 30) {
        lbl.innerText = "Negative";
        box.style.background = "#5a1f1f";
    } else {
        lbl.innerText = "Bearish";
        box.style.background = "#3b0e0e";
    }
}

// ====================================================================
// GLOBAL CUES
// ====================================================================

function updateGlobal(globalObj) {
    const g = id => document.getElementById(id);

    if (!globalObj) {
        g("gift").innerText = "--";
        g("nasdaq").innerText = "--";
        g("crude").innerText = "--";
        g("usdinr").innerText = "--";
        return;
    }

    // globalObj may be { data: {...}, score, comments } or plain data
    const data = globalObj.data || globalObj;

    const formatEntry = (entry) => {
        if (!entry || entry.last === null || entry.change_pct === null) return "--";
        const last = entry.last;
        const chg = entry.change_pct;
        const sign = chg >= 0 ? "+" : "";
        return `${last.toFixed(2)} (${sign}${chg.toFixed(2)}%)`;
    };

    const nifty = data.nifty_spot || data.nifty;
    const nas = data.nasdaq;
    const crd = data.crude;
    const fx = data.usdinr;

    g("gift").innerText = formatEntry(nifty);
    g("nasdaq").innerText = formatEntry(nas);
    g("crude").innerText = formatEntry(crd);
    g("usdinr").innerText = formatEntry(fx);
}

// ====================================================================
// NEWS
// ====================================================================

function updateNews(news) {
    const list = document.getElementById("newsList");
    const scoreEl = document.getElementById("news-score");

    list.innerHTML = "";

    if (!news) {
        scoreEl.innerText = "No news";
        return;
    }

    const headlines = news.headlines || [];
    headlines.slice(0, 6).forEach(h => {
        const li = document.createElement("li");
        li.innerText = h;
        list.appendChild(li);
    });

    scoreEl.innerText = news.sentiment_summary || "Mixed / Neutral";
}

// ====================================================================
// SECTOR MOOD (derived from sector_view)
// ====================================================================

function updateSectorMood(sectorView) {
    const el = document.getElementById("sector-mood");
    if (!sectorView) {
        el.innerText = "--";
        el.style.color = "#ffffff";
        return;
    }

    const s = sectorView.sector_score || 0; // -1..1
    const score01 = (s + 1) / 2;
    const score100 = Math.round(score01 * 100);

    let label = "Neutral sector";
    if (score01 > 0.7) label = "Strong sector support";
    else if (score01 > 0.55) label = "Sector mildly supportive";
    else if (score01 < 0.3) label = "Sector strongly against";
    else if (score01 < 0.45) label = "Sector mildly against";

    el.innerText = `${label} (${score100}%)`;

    if (score01 > 0.6) el.style.color = "#69ff6b";
    else if (score01 < 0.4) el.style.color = "#ff6b6b";
    else el.style.color = "#fff56b";
}

// ====================================================================
// FII / DII
// ====================================================================

function updateFII(fii) {
    const el = document.getElementById("fii-text");
    if (!fii) {
        el.innerText = "--";
        return;
    }

    // We only have score, label, comments
    const label = fii.label || "Unknown";
    const comments = fii.comments || [];

    el.innerText = label + (comments[0] ? ` – ${comments[0]}` : "");

    if (fii.score > 0.3) el.style.color = "#6cff7a";
    else if (fii.score < -0.3) el.style.color = "#ff6b6b";
    else el.style.color = "#ffffff";
}

// ====================================================================
// VIX
// ====================================================================

function updateVIX(vixObj) {
    const el = document.getElementById("vix-text");
    if (!vixObj) {
        el.innerText = "--";
        return;
    }

    const v = vixObj.value;
    const label = vixObj.label || "";

    if (v == null) {
        el.innerText = label;
        el.style.color = "#ffffff";
        return;
    }

    el.innerText = `${v.toFixed(2)} (${label})`;

    if (v < 13) el.style.color = "#6cff7a";
    else if (v < 18) el.style.color = "#fff56b";
    else el.style.color = "#ff6b6b";
}

// ====================================================================
// MARKET REGIME
// ====================================================================

function updateRegime(regime) {
    const labelEl = document.getElementById("regimeLabel");
    const statsEl = document.getElementById("regimeStats");

    if (!regime) {
        labelEl.innerText = "--";
        statsEl.innerText = "ATR: --, BB: --";
        return;
    }

    labelEl.innerText = regime.label || "--";
    statsEl.innerText = `ATR: ${regime.atr_pct}% | BBW: ${regime.bb_pct}%`;

    const box = document.getElementById("regime-box");
    if (regime.label && regime.label.includes("Trending")) {
        box.style.background = "#0d3d16";
    } else if (regime.label && regime.label.includes("High Volatility")) {
        box.style.background = "#5a1f1f";
    } else if (regime.label && regime.label.includes("Dead")) {
        box.style.background = "#333333";
    } else {
        box.style.background = "#1a1f27";
    }
}

// ====================================================================
// REVERSAL SIGNALS
// ====================================================================

function updateReversals(list, prob) {
    const probEl = document.getElementById("rev-prob");
    probEl.innerText = `Reversal Chance: ${prob != null ? Math.round(prob * 100) + "%" : "--"}`;
    

    const box = document.getElementById("rev-list");
    box.innerHTML = "";

    if (!list || list.length === 0) {
        const li = document.createElement("li");
        li.innerText = "No strong reversal signals.";
        box.appendChild(li);
        return;
    }

    list.forEach(msg => {
        const li = document.createElement("li");
        li.innerText = msg;
        box.appendChild(li);
    });
}

// ====================================================================
// OPTIONS PANEL
// ====================================================================

function updateOptions(options) {
    const summaryEl = document.getElementById("optSummary");
    const strikeEl = document.getElementById("optStrike");
    const ivEl = document.getElementById("optIV");
    const oiEl = document.getElementById("optOI");
    const deltaEl = document.getElementById("optDelta");
    const thetaEl = document.getElementById("optTheta");
    const vegaEl = document.getElementById("optVega");
    const expMoveEl = document.getElementById("optExpMove");
    const sltEl = document.getElementById("optSLTarget");
    const flowEl = document.getElementById("optFlow");
    const reasonsList = document.getElementById("optReasons");

    const box = document.getElementById("option-box");
    box.classList.remove("opt-buy", "opt-put", "opt-avoid");

    // Handle errors or missing data
    if (!options) {
        summaryEl.innerText = "No options data.";
        strikeEl.innerText = "--";
        ivEl.innerText = "--";
        oiEl.innerText = "--";
        deltaEl.innerText = "--";
        thetaEl.innerText = "--";
        vegaEl.innerText = "--";
        expMoveEl.innerText = "--";
        sltEl.innerText = "--";
        flowEl.innerText = "--";
        reasonsList.innerHTML = "";
        return;
    }

    // Check for error field
    if (options.error) {
        summaryEl.innerText = options.error;
        strikeEl.innerText = "--";
        ivEl.innerText = "--";
        oiEl.innerText = "--";
        deltaEl.innerText = "--";
        thetaEl.innerText = "--";
        vegaEl.innerText = "--";
        expMoveEl.innerText = "--";
        sltEl.innerText = "--";
        flowEl.innerText = "--";
        reasonsList.innerHTML = "";
        return;
    }

    // Check if signal exists
    if (!options.signal) {
        summaryEl.innerText = "Options signal unavailable.";
        strikeEl.innerText = "--";
        ivEl.innerText = "--";
        oiEl.innerText = "--";
        deltaEl.innerText = "--";
        thetaEl.innerText = "--";
        vegaEl.innerText = "--";
        reasonsList.innerHTML = "";
        return;
    }

    const sig = options.signal;
    const strikeInfo = options.strike || {};
    const ivInfo = options.iv || {};
    const oiInfo = options.oi || {};
    const greeks = options.greeks || {};

    // Summary line
    const action = sig.action || "AVOID";
    const conf = sig.confidence || 0;
    summaryEl.innerText = `${action} (${conf}%)`;

    if (action.includes("CALL")) {
        box.classList.add("opt-buy");
    } else if (action.includes("PUT")) {
        box.classList.add("opt-put");
    } else {
        box.classList.add("opt-avoid");
    }

    // Strike info
    const atm = strikeInfo.atm != null ? strikeInfo.atm : "--";
    const otmC = strikeInfo.otm_call != null ? strikeInfo.otm_call : "--";
    const otmP = strikeInfo.otm_put != null ? strikeInfo.otm_put : "--";
    strikeEl.innerText = `ATM ${atm} | CE OTM ${otmC} | PE OTM ${otmP}`;

    // IV info
    if (ivInfo.iv != null) {
        const ivVal = Number(ivInfo.iv);
        const trend = ivInfo.trend || "flat";
        ivEl.innerText = `${ivVal.toFixed(2)}% (${trend})`;
    } else {
        ivEl.innerText = "--";
    }

    // OI info
    const ceChg = oiInfo.ce_chg != null ? oiInfo.ce_chg : "--";
    const peChg = oiInfo.pe_chg != null ? oiInfo.pe_chg : "--";
    const sentiment = oiInfo.sentiment || "neutral";
    oiEl.innerText = `ΔCE OI: ${ceChg}, ΔPE OI: ${peChg}, ${sentiment}`;

    // Greeks
    if (greeks.delta != null) {
        deltaEl.innerText = greeks.delta;
        thetaEl.innerText = greeks.theta;
        vegaEl.innerText = greeks.vega;
    } else {
        deltaEl.innerText = "--";
        thetaEl.innerText = "--";
        vegaEl.innerText = "--";
    }

    // Expected Move
    const em = options.exp_move || null;
    if (em && em.expected_move_pts != null) {
        expMoveEl.innerText = `${em.expected_move_pts} pts (ATR ${em.atr_pct}%)`;
        sltEl.innerText = `SL ${em.sl_pts} pts / Target ${em.target_pts} pts (RR ${em.rr}x)`;
    } else {
        expMoveEl.innerText = "--";
        sltEl.innerText = "--";
    }

    // Order Flow
    const of = options.order_flow || null;
    if (of && of.flows && of.flows.length > 0) {
        flowEl.innerText = of.flows[0] || "Mixed";
    } else {
        flowEl.innerText = "--";
    }

    // Reasons
    reasonsList.innerHTML = "";
    (sig.reasons || []).slice(0, 5).forEach(r => {
        const li = document.createElement("li");
        li.innerText = r;
        reasonsList.appendChild(li);
    });
}


// ====================================================================
// MAIN REFRESH FUNCTION
// ====================================================================

async function refreshAll() {
    try {
        console.log("Fetching from:", buildApiUrl());
        const res = await fetch(buildApiUrl());
        console.log("Response status:", res.status);
        const data = await res.json();
        console.log("Data received:", data);

        if (data.error) {
            document.getElementById("priceBox").innerText = "Error: " + data.error;
            return;
        }

        // PRICE
        document.getElementById("priceBox").innerText = `${data.symbol || "NIFTY"}: ${data.price}`;

        // GENERATE BUY/SELL MARKERS
        if (data.signal && data.candles && data.candles.length > 0) {
            const lastCandle = data.candles[data.candles.length - 1];
            const action = data.signal.action || "WAIT";
            
            // Clear old markers and add new ones
            markers = [];
            
            if (action.includes("BUY")) {
                markers.push({
                    time: Math.floor(lastCandle.start_ts),
                    position: 'belowBar',
                    color: '#00ff99',
                    shape: 'arrowUp',
                    text: 'BUY'
                });
            } else if (action.includes("SELL")) {
                markers.push({
                    time: Math.floor(lastCandle.start_ts),
                    position: 'aboveBar',
                    color: '#ff3333',
                    shape: 'arrowDown',
                    text: 'SELL'
                });
            }
        }

        // CHART
        updateAdvancedChart(data.candles || [], data.series || {});

        // SIGNAL
        updateSignalCard(data.signal || {});

        // ML
        updateML(data.ml_predict || null);
        
        // ML TREND LABEL (from ml_view)
        if (data.ml_view && data.ml_view.trend_label) {
            document.getElementById("mlTrend").innerText = data.ml_view.trend_label;
        }

        // MARKET REGIME
        updateRegime(data.regime || null);

        // MARKET MOOD
        updateMarketMood(data.market_mood);

        // GLOBAL
        updateGlobal(data.global || null);

        // FII / DII
        updateFII(data.fii_dii || null);

        // VIX
        updateVIX(data.vix || null);

        // NEWS
        updateNews(data.news || null);

        // SECTOR
        updateSectorMood(data.sector_view || null);

        // OPTIONS
        updateOptions(data.options || null);

        // REVERSALS (with reversal probability)
        updateReversals(data.reversal_signals || null, data.reversal_prob || null);

    } catch (err) {
        console.error("Fetch error:", err);
        document.getElementById("priceBox").innerText = "Network error: " + err.message;
    }
}

// ====================================================================
// TIMEFRAME BUTTONS
// ====================================================================

function setupTimeframeControls() {
    const btns = document.querySelectorAll(".tf-btn");
    console.log("Found timeframe buttons:", btns.length);
    btns.forEach(btn => {
        btn.addEventListener("click", () => {
            console.log("Timeframe button clicked:", btn.dataset.interval);
            btns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const val = parseInt(btn.dataset.interval, 10);
            if (!isNaN(val)) {
                currentInterval = val;
                
                // Refresh data immediately
                refreshAll();
                
                // Restart WebSocket with new timeframe
                if (ws) {
                    reconnectAttempt = true;  // Prevent auto-reconnect
                    ws.close();  // Close old socket
                }
                setTimeout(() => {
                    startWebSocket();  // Open new one with updated interval
                }, 100);
            }
        });
    });
}

// ====================================================================
// INIT
// ====================================================================


let reconnectAttempt = false;

function startWebSocket() {
    const url = `ws://127.0.0.1:8000/ws/live?symbol=NIFTY&interval=${currentInterval}`;
    ws = new WebSocket(url);
    reconnectAttempt = false;

    ws.onopen = () => {
        console.log("WebSocket connected.");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateFromWebSocket(data);
    };

    ws.onclose = () => {
        console.log("WebSocket closed.");
        // Only auto-reconnect if it wasn't a manual close
        if (!reconnectAttempt) {
            console.log("Reconnecting in 2 seconds...");
            reconnectAttempt = true;
            setTimeout(startWebSocket, 2000);
        }
    };

    ws.onerror = (err) => {
        console.log("WebSocket error:", err);
    };
}

function updateFromWebSocket(data) {
    // replicate update logic from refreshAll
    document.getElementById("priceBox").innerText = `${data.symbol}: ${data.price}`;
    
    // Generate markers for WebSocket updates
    if (data.signal && data.candles && data.candles.length > 0) {
        const lastCandle = data.candles[data.candles.length - 1];
        const action = data.signal.action || "WAIT";
        
        markers = [];
        
        if (action.includes("BUY")) {
            markers.push({
                time: Math.floor(lastCandle.start_ts),
                position: 'belowBar',
                color: '#00ff99',
                shape: 'arrowUp',
                text: 'BUY'
            });
        } else if (action.includes("SELL")) {
            markers.push({
                time: Math.floor(lastCandle.start_ts),
                position: 'aboveBar',
                color: '#ff3333',
                shape: 'arrowDown',
                text: 'SELL'
            });
        }
    }
    
    updateAdvancedChart(data.candles || [], data.series || {});
    updateSignalCard(data.signal);
    updateML(data.ml_predict);
    
    // ML TREND LABEL (from ml_view)
    if (data.ml_view && data.ml_view.trend_label) {
        document.getElementById("mlTrend").innerText = data.ml_view.trend_label;
    }
    
    // MARKET REGIME
    updateRegime(data.regime || null);
    
    updateMarketMood(data.market_mood);
    updateGlobal(data.global_cues);
    updateNews(data.news);
    updateFII(data.fii_dii);
    updateVIX(data.vix);
    
    // REVERSALS with probability
    updateReversals(data.reversal_signals || null, data.reversal_prob || null);
    
    // OPTIONS
    updateOptions(data.options || null);
}

window.addEventListener("load", () => {
    initAdvancedChart();
    setupTimeframeControls();
    
    // Initial load with REST API
    refreshAll();
    
    // Then start WebSocket for live updates
    setTimeout(() => {
        startWebSocket();
    }, 500);
});

