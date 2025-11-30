// ========================================
// MINIMAL TRADING ASSISTANT - FRONTEND
// ========================================

let sparklineChart = null;
let currentSymbol = "NIFTY";
let interval = 5;

// Initialize on page load
window.addEventListener("load", () => {
    initSparkline();
    setupSymbolSelector();
    fetchData();
    
    // Poll every 2 seconds
    setInterval(fetchData, 2000);
});

// Initialize sparkline chart
function initSparkline() {
    const ctx = document.getElementById("sparklineChart").getContext("2d");
    
    sparklineChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: "#00c853",
                borderWidth: 2,
                fill: false,
                tension: 0.3,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

// Setup symbol selector
function setupSymbolSelector() {
    const selector = document.getElementById("symbolSelect");
    selector.addEventListener("change", (e) => {
        currentSymbol = e.target.value;
        fetchData();
    });
}

// Fetch data from backend
async function fetchData() {
    try {
        const response = await fetch(
            `http://127.0.0.1:8000/api/signal_live?symbol=${currentSymbol}&interval=${interval}&limit=100`
        );
        const data = await response.json();
        
        if (data.error) {
            console.error("API Error:", data.error);
            return;
        }
        
        updateUI(data);
    } catch (error) {
        console.error("Fetch error:", error);
    }
}

// Update all UI elements
function updateUI(data) {
    updateSignalCard(data);
    updatePrice(data);
    updateSparkline(data);
    updateMarketSummary(data);
    updateOptions(data);
    updateNews(data);
}

// Update signal card
function updateSignalCard(data) {
    const card = document.getElementById("signalCard");
    const actionEl = document.getElementById("signalAction");
    const confidenceEl = document.getElementById("signalConfidence");
    const mlEl = document.getElementById("signalML");
    const reasonsEl = document.getElementById("signalReasons");

    const label = data.final?.label || data.signal?.action || "WAIT";
    const score = typeof data.final?.score === "number" ? data.final.score : 0;
    const mlTrend = data.ml_view?.trend_label || (data.ml_predict?.trend_label || "--");
    const reasons = data.signal?.reasons || [];

    actionEl.textContent = label;

    const labelLower = label.toLowerCase();
    let actionClass = "wait";
    if (labelLower.includes("sell")) {
        actionClass = "sell";
    } else if (labelLower.includes("buy")) {
        actionClass = "buy";
    }

    card.classList.remove("buy", "sell", "wait");
    card.classList.add(actionClass);

    const confidencePct = Math.max(0, Math.min(100, Math.round(score * 100)));
    confidenceEl.textContent = `Confidence: ${confidencePct}%`;

    mlEl.textContent = `ML Trend: ${mlTrend}`;

    reasonsEl.innerHTML = "";
    const topReasons = reasons.slice(0, 3);
    if (topReasons.length > 0) {
        topReasons.forEach((reason) => {
            const li = document.createElement("li");
            li.textContent = reason;
            reasonsEl.appendChild(li);
        });
    } else {
        const li = document.createElement("li");
        li.textContent = "No specific reasons available";
        reasonsEl.appendChild(li);
    }
}

// Update price section
function updatePrice(data) {
    const priceEl = document.getElementById("priceValue");
    const trendEl = document.getElementById("priceTrend");
    
    const price = data.price || 0;
    const candles = data.candles || [];
    
    priceEl.textContent = `₹${price.toFixed(2)}`;
    
    // Determine trend from last few candles
    if (candles.length >= 2) {
        const current = candles[candles.length - 1].close;
        const previous = candles[candles.length - 2].close;
        
        if (current > previous) {
            trendEl.textContent = "↗ Uptrend";
            trendEl.className = "price-trend up";
        } else if (current < previous) {
            trendEl.textContent = "↘ Downtrend";
            trendEl.className = "price-trend down";
        } else {
            trendEl.textContent = "→ Sideways";
            trendEl.className = "price-trend";
        }
    }
}

// Update sparkline chart
function updateSparkline(data) {
    const candles = data.candles || [];
    
    if (candles.length === 0) return;
    
    // Take last 30 candles
    const last30 = candles.slice(-30);
    const closes = last30.map(c => c.close);
    const labels = last30.map((_, i) => i);
    
    // Determine color based on trend
    const firstClose = closes[0];
    const lastClose = closes[closes.length - 1];
    const color = lastClose >= firstClose ? "#00c853" : "#ff1744";
    
    sparklineChart.data.labels = labels;
    sparklineChart.data.datasets[0].data = closes;
    sparklineChart.data.datasets[0].borderColor = color;
    sparklineChart.update("none"); // No animation for smooth updates
}

// Update market summary
function updateMarketSummary(data) {
    // Market Mood
    const moodEl = document.getElementById("marketMood");
    const score = data.final?.score || 0;
    let moodText = "Neutral";
    if (score > 70) moodText = "Bullish";
    else if (score < 30) moodText = "Bearish";
    moodEl.textContent = moodText;
    moodEl.style.color = score > 70 ? "#00c853" : score < 30 ? "#ff1744" : "#ffea00";
    
    // Sector Mood
    const sectorEl = document.getElementById("sectorMood");
    const sectorScore = data.sector_view?.sector_score || 0;
    let sectorText = "Neutral";
    if (sectorScore > 60) sectorText = "Positive";
    else if (sectorScore < 40) sectorText = "Negative";
    sectorEl.textContent = sectorText;
    sectorEl.style.color = sectorScore > 60 ? "#00c853" : sectorScore < 40 ? "#ff1744" : "#ffea00";
    
    // News Sentiment
    const newsEl = document.getElementById("newsSentiment");
    const sentiment = data.news?.sentiment_summary || "Neutral";
    newsEl.textContent = sentiment;
    if (sentiment.toLowerCase().includes("positive")) {
        newsEl.style.color = "#00c853";
    } else if (sentiment.toLowerCase().includes("negative")) {
        newsEl.style.color = "#ff1744";
    } else {
        newsEl.style.color = "#ffea00";
    }
    
    // VIX
    const vixEl = document.getElementById("vixValue");
    const vix = data.vix?.value || 0;
    const vixLabel = data.vix?.label || "";
    vixEl.textContent = `${vix.toFixed(2)} (${vixLabel})`;
    if (vixLabel.toLowerCase().includes("high")) {
        vixEl.style.color = "#ff1744";
    } else if (vixLabel.toLowerCase().includes("low")) {
        vixEl.style.color = "#00c853";
    } else {
        vixEl.style.color = "#ffea00";
    }
}

// Update options summary
function updateOptions(data) {
    const options = data.options || {};
    
    // Action
    const actionEl = document.getElementById("optAction");
    actionEl.textContent = options.signal?.action || "--";
    
    // Strike
    const strikeEl = document.getElementById("optStrike");
    strikeEl.textContent = options.strike?.atm || "--";
    
    // IV
    const ivEl = document.getElementById("optIV");
    const iv = options.iv?.iv || 0;
    const ivTrend = options.iv?.trend || "";
    ivEl.textContent = `${(iv * 100).toFixed(2)}% (${ivTrend})`;
    
    // OI Sentiment
    const oiEl = document.getElementById("optOI");
    oiEl.textContent = options.oi?.sentiment || "--";
    
    // Greeks
    const greeksEl = document.getElementById("optGreeks");
    const greeks = options.greeks || {};
    greeksEl.textContent = `Δ ${greeks.delta?.toFixed(3) || "--"}, θ ${greeks.theta?.toFixed(3) || "--"}`;
}

// Update news headlines
function updateNews(data) {
    const newsList = document.getElementById("newsList");
    const headlines = data.news?.headlines || [];
    
    newsList.innerHTML = "";
    
    if (headlines.length === 0) {
        const li = document.createElement("li");
        li.textContent = "No headlines available";
        newsList.appendChild(li);
        return;
    }
    
    // Show top 5 headlines
    const top5 = headlines.slice(0, 5);
    top5.forEach(headline => {
        const li = document.createElement("li");
        li.textContent = headline;
        newsList.appendChild(li);
    });
}
