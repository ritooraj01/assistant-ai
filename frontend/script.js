// ====================================================================
// PROFESSIONAL TRADING DASHBOARD - MOBILE FRIENDLY
// ====================================================================

let currentInterval = 5;
let chart = null;
let candleSeries = null;
let ema21Series = null;
let ema50Series = null;
let supertrendSeries = null;
let currentSymbol = 'NIFTY'; // Default symbol
let niftyHistory = []; // Store NIFTY price history for mini chart
let lastRefreshTime = 0; // Track last API call time
let refreshCount = 0; // Count refreshes for throttling expensive calls
let lastDataFeedUpdate = Date.now(); // Heartbeat for data feed monitoring
let heartbeatInterval = null; // Heartbeat check interval

// ====================================================================
// INITIALIZE
// ====================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀🚀🚀 APPLICATION STARTING - NEW VERSION 2.0 🚀🚀🚀');
    console.log('✅ JavaScript file loaded successfully with all fixes!');
    setupTimeframeButtons();
    setupSectorTabs();
    setupNiftyCard();
    setupMobileDrawer();
    initMainChart();
    updateStocksGrid(); // Initial load of stocks (with static data first)
    
    // Load initial historical data first (wait for it to complete)
    await loadHistory(currentSymbol, currentInterval);
    
    // Wait a moment for chart to render
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Start live data polling (with initial fetch)
    refreshData();
    setInterval(refreshData, 3000); // Auto-refresh every 3 seconds
    
    // Start heartbeat monitor to detect stale data feeds
    startHeartbeatMonitor();
    
    // Fetch live stock prices (runs in background)
    fetchAllStockPrices();
    // Refresh stock prices every 30 seconds
    setInterval(fetchAllStockPrices, 30000);
    
    console.log('✅ Application initialized successfully');
});

// ====================================================================
// HEARTBEAT MONITOR
// ====================================================================

function startHeartbeatMonitor() {
    console.log('💓 Starting heartbeat monitor');
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
    }
    
    heartbeatInterval = setInterval(() => {
        const timeSinceLastUpdate = Date.now() - lastDataFeedUpdate;
        const thirtySeconds = 30000;
        
        // Check canvas existence
        const container = document.getElementById('mainChart');
        const chartCanvas = container ? container.querySelector('canvas') : null;
        
        if (!chartCanvas) {
            console.error('❌ Chart canvas NOT found in DOM - chart has been removed!');
            console.log('⚠️ Attempting full chart reinitialization...');
            
            // Reset chart references
            chart = null;
            candleSeries = null;
            ema21Series = null;
            ema50Series = null;
            supertrendSeries = null;
            
            // Reinitialize from scratch
            initMainChart();
            
            // Reload data after reinitialization
            setTimeout(() => {
                if (chart && candleSeries) {
                    console.log('✅ Chart reinitialized successfully, reloading data...');
                    loadHistory(currentSymbol, currentInterval);
                    refreshData();
                } else {
                    console.error('❌ Chart reinitialization failed!');
                }
            }, 500);
        }
        
        if (timeSinceLastUpdate > thirtySeconds) {
            console.warn(`⚠️ No dataFeedUpdate for ${(timeSinceLastUpdate / 1000).toFixed(0)}s - reconnecting...`);
            console.log('🔴 dataFeedEnd: Stale data detected - Auto-reconnect triggered');
            
            // Check if chart still exists
            if (!chart || !candleSeries) {
                console.error('⚠️ Chart components missing, reinitializing...');
                
                // Reset references
                chart = null;
                candleSeries = null;
                ema21Series = null;
                ema50Series = null;
                supertrendSeries = null;
                
                initMainChart();
                
                setTimeout(() => {
                    loadHistory(currentSymbol, currentInterval);
                    refreshData();
                }, 500);
            } else {
                // Chart exists, just refresh data
                refreshData();
            }
            
            lastDataFeedUpdate = Date.now(); // Reset heartbeat
        } else {
            console.log(`💚 Heartbeat OK - last update ${(timeSinceLastUpdate / 1000).toFixed(0)}s ago`);
        }
    }, 10000); // Check every 10 seconds
}

// ====================================================================
// TIMEFRAME BUTTONS
// ====================================================================

function setupTimeframeButtons() {
    const buttons = document.querySelectorAll('.tf-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const oldInterval = currentInterval;
            const newInterval = parseInt(btn.dataset.interval);
            
            if (oldInterval === newInterval) {
                console.log('⏭️ Same interval selected, skipping reload');
                return;
            }
            
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentInterval = newInterval;
            console.log(`🔄 Changed interval from ${oldInterval}m to ${currentInterval}m`);
            
            // Clear existing chart data to prevent stale display
            if (candleSeries) {
                console.log('🧹 Clearing old candle data');
                candleSeries.setData([]);
            }
            
            // Clear indicator series
            if (ema21Series) ema21Series.setData([]);
            if (ema50Series) ema50Series.setData([]);
            if (supertrendSeries) supertrendSeries.setData([]);
            
            // Ensure chart exists
            if (!chart || !candleSeries) {
                console.warn('⚠️ Chart not initialized, reinitializing...');
                initMainChart();
                setTimeout(() => {
                    loadHistory(currentSymbol, currentInterval);
                    refreshData();
                }, 200);
            } else {
                // Reload history for new interval
                loadHistory(currentSymbol, currentInterval);
                
                // Fetch new live data
                refreshData();
            }
        });
    });
}

// ====================================================================
// SYMBOL SELECTION LOGIC
// ====================================================================

function setupNiftyCard() {
    const niftyCard = document.getElementById('niftyCard');
    if (niftyCard) {
        niftyCard.addEventListener('click', () => {
            selectSymbol('NIFTY');
        });
    }
}

function selectSymbol(symbol) {
    const oldSymbol = currentSymbol;
    if (oldSymbol !== symbol) {
        console.log(`🔴 Unsubscribing from: ${oldSymbol}`);
        console.log(`🟢 Subscribing to: ${symbol}`);
        
        // Clear existing data to prevent stale display
        if (candleSeries) {
            candleSeries.setData([]);
        }
        if (ema21Series) {
            ema21Series.setData([]);
        }
        if (ema50Series) {
            ema50Series.setData([]);
        }
        if (supertrendSeries) {
            supertrendSeries.setData([]);
        }
    }
    
    currentSymbol = symbol;
    console.log('🔄 Selected symbol:', symbol);
    
    // Update header badge
    const symbolBadge = document.getElementById('currentSymbolBadge');
    if (symbolBadge) {
        symbolBadge.textContent = symbol === 'NIFTY' ? 'NIFTY 50' : symbol;
    }
    
    // Update active indicators
    updateActiveIndicators(symbol);
    
    // Close mobile drawer if open
    closeMobileDrawer();
    
    // Ensure chart exists before attempting to load data
    if (!chart || !candleSeries) {
        console.warn('⚠️ Chart not initialized, reinitializing...');
        initMainChart();
        // Wait for initialization
        setTimeout(() => {
            loadHistory(currentSymbol, currentInterval);
            refreshData();
        }, 200);
    } else {
        // Load historical data for new symbol
        loadHistory(currentSymbol, currentInterval);
        
        // Fetch new live data
        refreshData();
    }
}

function updateActiveIndicators(symbol) {
    // Update NIFTY card
    const niftyCard = document.getElementById('niftyCard');
    if (niftyCard) {
        if (symbol === 'NIFTY') {
            niftyCard.classList.add('active-symbol');
        } else {
            niftyCard.classList.remove('active-symbol');
        }
    }
    
    // Update stock items
    document.querySelectorAll('.stock-item').forEach(item => {
        const stockSymbol = item.dataset.symbol;
        if (stockSymbol === symbol) {
            item.classList.add('active-symbol');
        } else {
            item.classList.remove('active-symbol');
        }
    });
}

// ====================================================================
// MOBILE DRAWER
// ====================================================================

function setupMobileDrawer() {
    const floatingBtn = document.getElementById('floatingStocksBtn');
    const drawer = document.getElementById('rightSidebar');
    const backdrop = document.getElementById('drawerBackdrop');
    const closeBtn = document.getElementById('drawerCloseBtn');
    
    if (floatingBtn) {
        floatingBtn.addEventListener('click', openMobileDrawer);
    }
    
    if (backdrop) {
        backdrop.addEventListener('click', closeMobileDrawer);
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeMobileDrawer);
    }
    
    // Swipe gesture support
    let touchStartX = 0;
    let touchEndX = 0;
    
    if (drawer) {
        drawer.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        drawer.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        });
    }
    
    function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        if (swipeDistance > 100) { // Swipe right to close
            closeMobileDrawer();
        }
    }
}

function openMobileDrawer() {
    const drawer = document.getElementById('rightSidebar');
    const backdrop = document.getElementById('drawerBackdrop');
    
    if (drawer) drawer.classList.add('drawer-open');
    if (backdrop) backdrop.classList.add('active');
}

function closeMobileDrawer() {
    const drawer = document.getElementById('rightSidebar');
    const backdrop = document.getElementById('drawerBackdrop');
    
    if (drawer) drawer.classList.remove('drawer-open');
    if (backdrop) backdrop.classList.remove('active');
}

// ====================================================================
// INITIALIZE FULL CANDLESTICK CHART
// ====================================================================

function initMainChart() {
    const container = document.getElementById('mainChart');
    
    if (!container) {
        console.error('❌ Chart container #mainChart not found!');
        return;
    }

    // CRITICAL: Never reinitialize if chart exists
    // This prevents the chart from disappearing
    if (chart && candleSeries) {
        const chartCanvas = container.querySelector('canvas');
        if (chartCanvas) {
            console.log('✅ Chart already exists - PREVENTING reinitialization');
            return;
        }
        // Only reset if canvas truly missing
        console.warn('⚠️ Chart canvas missing but variables exist - resetting');
        chart = null;
        candleSeries = null;
        ema21Series = null;
        ema50Series = null;
        supertrendSeries = null;
    }

    console.log('📊 Initializing advanced chart, container:', container);
    console.log('📊 Container dimensions:', container.clientWidth, 'x', container.clientHeight);
    console.log('📊 Container offsetWidth:', container.offsetWidth);
    console.log('📊 LightweightCharts available:', typeof LightweightCharts !== 'undefined');
    
    if (typeof LightweightCharts === 'undefined') {
        console.error('❌ Chart library not loaded');
        container.innerHTML = '<div style="color:#ef4444;padding:20px;text-align:center;font-size:16px;">❌ Chart library failed to load. Check internet connection.</div>';
        return;
    }

    // Get container width and adjust for padding
    const containerWidth = container.clientWidth || container.offsetWidth || 800;
    const width = Math.max(containerWidth - 40, 600); // Subtract padding, minimum 600px
    const isMobile = width < 768;
    const height = 380; // Fixed height to fit in container
    
    console.log('📊 Creating chart with dimensions:', width, 'x', height);
    console.log('📊 Container actual width:', container.clientWidth);
    console.log('🔵 dataFeedStart: Initializing chart component for', currentSymbol);

    // Clear any placeholder content
    container.innerHTML = '';

    console.log('🔵 dataFeedStart: Initializing chart component');
    
    try {
        chart = LightweightCharts.createChart(container, {
            width: width,
            height: height,
            autoSize: false,
            layout: {
                background: { color: '#0f0f0f' },
                textColor: '#888'
            },
            grid: {
                vertLines: { color: '#1a1a1a' },
                horzLines: { color: '#1a1a1a' }
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: '#2a2a2a'
            },
            rightPriceScale: {
                borderColor: '#2a2a2a'
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: '#667eea',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed
                },
                horzLine: {
                    color: '#667eea',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed
                }
            }
        });

        // Main candlestick series
        candleSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350'
        });

        // EMA 21 series
        ema21Series = chart.addLineSeries({
            color: '#ffcc00',
            lineWidth: 2,
            title: 'EMA 21'
        });

        // EMA 50 series
        ema50Series = chart.addLineSeries({
            color: '#ff77aa',
            lineWidth: 2,
            title: 'EMA 50'
        });

        // Supertrend series
        supertrendSeries = chart.addLineSeries({
            color: '#00ff99',
            lineWidth: 2,
            title: 'Supertrend',
            priceLineVisible: false,
            lastValueVisible: false
        });
        
        // Update EMA series to hide overlays
        ema21Series.applyOptions({
            priceLineVisible: false,
            lastValueVisible: false
        });
        
        ema50Series.applyOptions({
            priceLineVisible: false,
            lastValueVisible: false
        });

        // Add legend below chart
        const legend = document.createElement('div');
        legend.style.cssText = 'padding: 8px; font-size: 11px; color: #888; display: flex; gap: 16px; flex-wrap: wrap; margin-top: 8px;';
        legend.innerHTML = `
            <span style="color: #ffcc00;">● EMA 21</span>
            <span style="color: #ff77aa;">● EMA 50</span>
            <span style="color: #00ff99;">● Supertrend</span>
        `;
        container.parentElement.insertBefore(legend, container.nextSibling);

        console.log('✅ Advanced chart initialized successfully with EMA and Supertrend');
        console.log('✅ Chart object:', chart);
        console.log('✅ CandleSeries object:', candleSeries);
        console.log('🟢 Chart mounted successfully - Component is live and ready');
        console.log('🟢 Chart mounted successfully - container element:', container.id);
        
        // DOM inspection - verify canvas visibility (initial check)
        setTimeout(() => {
            const chartCanvas = container.querySelector('canvas');
            console.log('📊 Chart canvas found:', !!chartCanvas);
            if (chartCanvas) {
                console.log('📊 Canvas dimensions:', chartCanvas.width, 'x', chartCanvas.height);
                const styles = window.getComputedStyle(chartCanvas);
                console.log('📊 Canvas visibility:', styles.visibility);
                console.log('📊 Canvas display:', styles.display);
                console.log('📊 Canvas opacity:', styles.opacity);
                console.log('📊 Container display:', window.getComputedStyle(container).display);
            } else {
                console.error('❌ Chart canvas NOT found in DOM - chart may have unmounted!');
            }
        }, 100);

        // Resize Observer - more reliable than window resize events
        const resizeObserver = new ResizeObserver(entries => {
            for (const entry of entries) {
                if (chart && container) {
                    const width = entry.contentRect.width;
                    const height = entry.contentRect.height;
                    
                    // Ensure minimum dimensions
                    const chartWidth = Math.max(width - 40, 300);
                    const chartHeight = Math.max(Math.min(height, 500), 280);
                    
                    chart.applyOptions({ width: chartWidth, height: chartHeight });
                    console.log('📊 Chart resized via observer:', chartWidth, 'x', chartHeight);
                }
            }
        });
        
        // Observe the container for size changes
        resizeObserver.observe(container);
        
        // Fallback window resize (with debounce)
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (chart && container) {
                    const newWidth = Math.max(container.clientWidth - 40, 300);
                    chart.applyOptions({ width: newWidth, height: 380 });
                    console.log('📊 Chart resized to:', newWidth, 'x', 380);
                }
            }, 250); // Debounce resize events
        });
    } catch (error) {
        console.error('❌ Error initializing chart:', error);
    }
}

// ====================================================================
// LOAD HISTORICAL CANDLES
// ====================================================================

async function loadHistory(symbol, interval) {
    try {
        console.log(`📥 Loading history for ${symbol} at ${interval}m interval`);
        console.log(`📊 Chart exists: ${!!chart}, candleSeries exists: ${!!candleSeries}`);
        
        if (!chart || !candleSeries) {
            console.error('❌ Chart or candleSeries not initialized!');
            return;
        }
        
        // Use dynamic base URL to avoid CORS
        const baseUrl = window.location.protocol === 'file:' 
            ? 'http://127.0.0.1:8000'
            : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
                ? 'http://127.0.0.1:8000'
                : window.location.origin;
        const res = await fetch(`${baseUrl}/api/history?symbol=${symbol}&interval=${interval}&limit=200`);
        const data = await res.json();

        if (data.error) {
            console.error('History error:', data.error);
            return;
        }

        const candles = data.candles || [];
        console.log(`✅ Loaded ${candles.length} historical candles`);
        console.log(`First candle sample:`, candles[0]);

        if (candles.length > 0) {
            candleSeries.setData(candles);
            chart.timeScale().fitContent();
            console.log(`✅ Set ${candles.length} candles to chart`);
        }

        // Clear EMA / supertrend (they'll be updated from /api/signal_live)
        ema21Series.setData([]);
        ema50Series.setData([]);
        supertrendSeries.setData([]);
    } catch (e) {
        console.error('❌ History fetch failed:', e);
    }
}

// ====================================================================
// UPDATE CHART FROM LIVE DATA
// ====================================================================

function updateLiveChart(candles, series) {
    if (!chart || !candleSeries) {
        console.warn('⚠ Chart not initialized yet, attempting initialization...');
        initMainChart();
        // Retry after brief delay
        setTimeout(() => {
            if (chart && candleSeries && candles && candles.length > 0) {
                updateLiveChart(candles, series);
            }
        }, 200);
        return;
    }
    
    // Verify canvas still exists in DOM
    const container = document.querySelector('.main-chart');
    const canvas = container ? container.querySelector('canvas') : null;
    
    if (!canvas) {
        console.error('❌ Chart canvas disappeared from DOM - forcing recovery');
        chart = null;
        candleSeries = null;
        ema21Series = null;
        ema50Series = null;
        initMainChart();
        return;
    }
    
    if (!candles || candles.length === 0) {
        console.warn('⚠ No candles to update chart');
        return;
    }
    
    // Validate candle data before updating
    const validCandles = candles.filter(c => {
        const open = parseFloat(c.open);
        const high = parseFloat(c.high);
        const low = parseFloat(c.low);
        const close = parseFloat(c.close);
        
        if (!isFinite(open) || !isFinite(high) || !isFinite(low) || !isFinite(close)) {
            return false;
        }
        
        if (open <= 0 || high <= 0 || low <= 0 || close <= 0) {
            return false;
        }
        
        return true;
    });
    
    if (validCandles.length === 0) {
        console.error('❌ No valid candles (all had zero/invalid prices)');
        return;
    }
    
    if (validCandles.length < candles.length) {
        console.warn(`⚠ Filtered out ${candles.length - validCandles.length} invalid candles`);
    }

    console.log(`📊 Updating live chart with ${validCandles.length} valid candles`);
    console.log('🔵 dataFeedUpdate: Pushing candle data to chart');

    // Update full candle series
    try {
        // Verify series is still valid before setting data
        if (!candleSeries || typeof candleSeries.setData !== 'function') {
            console.error('❌ CandleSeries reference is invalid, reinitializing chart...');
            chart = null;
            candleSeries = null;
            initMainChart();
            return;
        }
        
        candleSeries.setData(validCandles);
        console.log('🟢 dataFeedUpdate: Candles successfully set on chart');
        console.log('🟢 Chart updated successfully');
        lastDataFeedUpdate = Date.now(); // Update heartbeat timestamp
    } catch (error) {
        console.error('❌ Error setting candle data:', error);
        console.error('🔴 dataFeedEnd: Chart data feed failed');
        
        // Attempt recovery
        console.log('⚠️ Attempting chart recovery...');
        chart = null;
        candleSeries = null;
        ema21Series = null;
        ema50Series = null;
        supertrendSeries = null;
        
        initMainChart();
        return;
    }

    // EMA 21
    if (series.ema21 && series.ema21.length === candles.length) {
        const ema21Data = candles.map((c, idx) => ({
            time: c.time,
            value: series.ema21[idx],
        }));
        ema21Series.setData(ema21Data);
        console.log('✅ Updated EMA21');
    }

    // EMA 50
    if (series.ema50 && series.ema50.length === candles.length) {
        const ema50Data = candles.map((c, idx) => ({
            time: c.time,
            value: series.ema50[idx],
        }));
        ema50Series.setData(ema50Data);
        console.log('✅ Updated EMA50');
    }

    // Supertrend
    if (series.supertrend && series.supertrend.length === candles.length) {
        const stData = candles.map((c, idx) => ({
            time: c.time,
            value: series.supertrend[idx],
        }));
        supertrendSeries.setData(stData);
        console.log('✅ Updated Supertrend');
    }

    chart.timeScale().fitContent();
}

// ====================================================================
// FETCH AND UPDATE ALL DATA
// ====================================================================

async function refreshData() {
    try {
        // Throttle to max 1 request per second
        const now = Date.now();
        if (now - lastRefreshTime < 1000) {
            return; // Skip this refresh
        }
        lastRefreshTime = now;
        refreshCount++;
        
        // Backend expects interval in SECONDS (1m = 60s, 3m = 180s, 5m = 300s)
        const intervalSeconds = currentInterval * 60;
        // Use dynamic base URL to avoid CORS
        const baseUrl = window.location.protocol === 'file:' 
            ? 'http://127.0.0.1:8000'
            : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
                ? 'http://127.0.0.1:8000'
                : window.location.origin;
        const url = `${baseUrl}/api/signal_live?symbol=${currentSymbol}&interval=${intervalSeconds}&limit=80`;
        console.log('🔄 Fetching:', url);
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log('='.repeat(60));
        console.log(`✅ Data received for ${currentSymbol}`);
        console.log('Price:', data.price);
        console.log('Candles count:', data.candles ? data.candles.length : 0);
        if (data.candles && data.candles.length > 0) {
            console.log('First candle sample:', data.candles[0]);
            console.log('Last candle sample:', data.candles[data.candles.length - 1]);
        }
        console.log('Signal:', data.signal ? `${data.signal.action} (${data.signal.confidence})` : 'none');
        if (data.signal && data.signal.reasons) {
            console.log('Signal reasons:', data.signal.reasons);
        }
        console.log('Indicators:', data.indicators ? Object.keys(data.indicators).join(', ') : 'none');
        if (data.indicators) {
            console.log('  RSI14:', data.indicators.rsi14);
            console.log('  ATR14:', data.indicators.atr14);
            console.log('  MACD:', data.indicators.macd);
        }
        console.log('ML Predict:', data.ml_predict ? JSON.stringify(data.ml_predict) : 'none');
        console.log('ML View:', data.ml_view ? JSON.stringify(data.ml_view) : 'none');
        console.log('Global:', data.global && data.global.data ? Object.keys(data.global.data).join(', ') : 'none');
        console.log('Regime:', data.regime ? data.regime.label : 'none');
        console.log('Series:', data.series ? `EMA21: ${data.series.ema21?.length || 0}, EMA50: ${data.series.ema50?.length || 0}` : 'none');
        console.log('='.repeat(60));

        // Update all sections
        // Core data - update every time
        try { updateActionCard(data); } catch (e) { console.error('Error in updateActionCard:', e); }
        try { 
            // Update price display
            const priceLabel = document.getElementById('priceLabel');
            if (priceLabel && data.price) {
                priceLabel.textContent = `₹${data.price.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            }
            // Update chart with live data
            updateLiveChart(data.candles || [], data.series || {});
        } catch (e) { console.error('Error in updatePriceAndChart:', e); }
        try { updatePredictions(data); } catch (e) { console.error('Error in updatePredictions:', e); }
        try { updateReasons(data); } catch (e) { console.error('Error in updateReasons:', e); }
        try { updateMarketOverview(data); } catch (e) { console.error('Error in updateMarketOverview:', e); }
        
        // Expensive data - update every 10 refreshes (every 30 seconds with 3s interval)
        if (refreshCount % 10 === 0) {
            try { updateGlobalMarkets(data); } catch (e) { console.error('Error in updateGlobalMarkets:', e); }
            try { updateOptions(data); } catch (e) { console.error('Error in updateOptions:', e); }
            try { updateHeadlines(data); } catch (e) { console.error('Error in updateHeadlines:', e); }
        }
        
        // Moderate cost - update every 3 refreshes (every 9 seconds)
        if (refreshCount % 3 === 0) {
            try { updateMarketRegime(data); } catch (e) { console.error('Error in updateMarketRegime:', e); }
            try { updateSectors(data); } catch (e) { console.error('Error in updateSectors:', e); }
        }
        
        // Update NIFTY mini chart if viewing NIFTY
        if (currentSymbol === 'NIFTY' && data.price) {
            try { updateNiftyMiniInfo(data); } catch (e) { console.error('Error in updateNiftyMiniInfo:', e); }
        }

    } catch (error) {
        console.error('❌ Failed to fetch data:', error);
        console.error('URL was:', `http://127.0.0.1:8000/api/signal_live?symbol=${currentSymbol}&interval=${currentInterval}&limit=80`);
    }
}

// ====================================================================
// UPDATE ACTION CARD
// ====================================================================

function updateActionCard(data) {
    const signal = data.signal || {};
    const ml = data.ml_predict || {};
    
    const action = signal.action || 'WAIT';
    const confidence = Math.round((signal.confidence || 0) * 100);

    const card = document.getElementById('mainAction');
    const symbolLabel = document.getElementById('actionSymbolLabel');
    const titleElem = document.getElementById('actionTitle');
    const confElem = document.getElementById('actionConfidence');
    const mlElem = document.getElementById('mlTrend');

    // Update symbol label - ensure it reflects current symbol
    if (symbolLabel) {
        const displayName = currentSymbol === 'NIFTY' ? 'NIFTY 50' : 
                           currentSymbol === 'BANKNIFTY' ? 'BANKNIFTY' : 
                           currentSymbol;
        symbolLabel.textContent = displayName;
        console.log(`Updated action card for symbol: ${displayName}`);
    }

    // Update action title
    const actionMap = {
        'BUY': 'BUY',
        'SELL': 'SELL',
        'WAIT': 'WAIT'
    };
    
    if (titleElem) {
        titleElem.textContent = actionMap[action] || 'WAIT';
    }
    
    // Update card styling
    if (card) {
        card.classList.remove('buy', 'sell', 'wait');
        card.classList.add(action.toLowerCase());
    }

    // Update confidence
    if (confElem) {
        confElem.textContent = `${confidence}%`;
    }
    
    // Update ML trend using ml_view data
    if (mlElem) {
        const mlView = data.ml_view || {};
        if (mlView.enabled && mlView.trend_label) {
            const trend = mlView.trend_label.toUpperCase();
            const emoji = trend === 'UP' ? '↗' : trend === 'DOWN' ? '↘' : '→';
            mlElem.textContent = `${trend} ${emoji}`;
            mlElem.style.color = trend === 'UP' ? '#22c55e' : trend === 'DOWN' ? '#ef4444' : '#fbbf24';
        } else if (mlView.final_ml_score !== undefined) {
            // Fallback to score-based trend
            const score = mlView.final_ml_score;
            const trend = score > 0.6 ? 'UP ↗' : score < 0.4 ? 'DOWN ↘' : 'SIDEWAYS →';
            mlElem.textContent = trend;
            mlElem.style.color = score > 0.6 ? '#22c55e' : score < 0.4 ? '#ef4444' : '#fbbf24';
        } else {
            mlElem.textContent = 'NEUTRAL →';
            mlElem.style.color = '#fbbf24';
        }
    }
}

function generateActionSummary(action, confidence, ml) {
    if (action === 'BUY' && confidence > 70) {
        return 'Strong buying opportunity detected. Market conditions are favorable.';
    } else if (action === 'BUY') {
        return 'Moderate buying signal. Consider entering with caution.';
    } else if (action === 'SELL' && confidence > 70) {
        return 'Strong selling signal. Consider taking profits or exiting position.';
    } else if (action === 'SELL') {
        return 'Moderate selling pressure detected. Be cautious with new positions.';
    } else {
        return 'Market is calm but unclear. Waiting for stronger signals before trading.';
    }
}

// ====================================================================
// UPDATE PRICE AND CHART
// ====================================================================

function updatePriceAndChart(data) {
    const price = data.price || 0;
    const candles = data.candles || [];

    console.log('Updating price and chart:', { 
        price, 
        candleCount: candles.length,
        chartExists: !!chart,
        candleSeriesExists: !!candleSeries
    });

    // Update price label
    const priceLabel = document.getElementById('priceLabel');
    if (priceLabel && price > 0) {
        priceLabel.textContent = `₹${price.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }

    // Update chart - verify it exists but DON'T reinitialize unnecessarily
    if (!chart || !candleSeries) {
        console.warn('⚠️ Chart not initialized - initializing now...');
        initMainChart();
        // Wait for initialization then retry
        setTimeout(() => {
            if (chart && candleSeries && candles.length > 0) {
                updateChartData(candles);
            }
        }, 300);
        return;
    }
    
    // Chart exists - proceed with update
    console.log('📈 Updating chart with', candles.length, 'candles');

    if (candles.length > 0) {
        updateChartData(candles);
    } else {
        console.warn('No candle data available from API');
    }
}

function updateChartData(candles) {
    try {
        const chartData = candles.map(c => {
            // Handle different time field names from backend (start_ts, time, or timestamp)
            let timestamp = c.time || c.start_ts || c.timestamp;
            
            return {
                time: timestamp,
                open: parseFloat(c.open),
                high: parseFloat(c.high),
                low: parseFloat(c.low),
                close: parseFloat(c.close)
            };
        }).filter(c => !isNaN(c.time) && !isNaN(c.open)); // Filter out invalid data

        if (chartData.length === 0) {
            console.error('No valid chart data after processing');
            console.error('Sample raw candle:', candles[0]);
            return;
        }

        console.log('✅ Setting chart data:', chartData.length, 'candles');
        console.log('First candle:', chartData[0]);
        console.log('Last candle:', chartData[chartData.length - 1]);
        
        candleSeries.setData(chartData);
        chart.timeScale().fitContent();
    } catch (error) {
        console.error('❌ Error updating chart:', error);
        console.error('Sample candle:', candles[0]);
    }
}

// ====================================================================
// UPDATE PREDICTIONS
// ====================================================================

function updatePredictions(data) {
    const ml = data.ml_predict || {};
    const mlView = data.ml_view || {};
    
    console.log(`📊 updatePredictions called for ${currentSymbol}`);
    console.log('  ML data:', ml);
    console.log('  ML View:', mlView);
    console.log('  ML enabled:', mlView.enabled);
    console.log('  ML trend_label:', mlView.trend_label);
    console.log('  ML final_score:', mlView.final_ml_score);

    // ML Predict has: enabled, p1, p3, p5 (probabilities for 1, 3, 5 candles ahead)
    // ML View has: enabled, p1, p3, p5, final_ml_score, trend_label
    
    // Use ML View data which has the predictions
    const predictions = mlView.enabled ? mlView : ml;
    
    // Update LSTM (use p1 - 1 candle ahead probability)
    const lstmElem = document.getElementById('lstmPred');
    console.log('  LSTM Element found:', !!lstmElem, 'p1:', predictions.p1);
    if (lstmElem) {
        if (predictions.p1 !== undefined) {
            const prob = (parseFloat(predictions.p1) * 100).toFixed(1);
            const displayText = `${prob}% UP`;
            console.log('  Setting LSTM to:', displayText);
            lstmElem.textContent = displayText;
            lstmElem.style.color = predictions.p1 > 0.6 ? '#22c55e' : predictions.p1 < 0.4 ? '#ef4444' : '#fbbf24';
        } else if (mlView.trend_label) {
            console.log('  Setting LSTM to trend:', mlView.trend_label);
            lstmElem.textContent = mlView.trend_label;
        } else {
            console.log('  Setting LSTM to --');
            lstmElem.textContent = '--';
        }
    } else {
        console.error('  ❌ LSTM element not found!');
    }

    // Update GRU (use p3 - 3 candles ahead probability)
    const gruElem = document.getElementById('gruPred');
    if (gruElem) {
        if (predictions.p3 !== undefined) {
            const prob = (parseFloat(predictions.p3) * 100).toFixed(1);
            gruElem.textContent = `${prob}% UP`;
            gruElem.style.color = predictions.p3 > 0.6 ? '#22c55e' : predictions.p3 < 0.4 ? '#ef4444' : '#fbbf24';
        } else if (mlView.trend_label) {
            gruElem.textContent = mlView.trend_label;
        } else {
            gruElem.textContent = '--';
        }
    }

    // Update Transformer (use p5 - 5 candles ahead probability)
    const transformerElem = document.getElementById('transformerPred');
    if (transformerElem) {
        if (predictions.p5 !== undefined) {
            const prob = (parseFloat(predictions.p5) * 100).toFixed(1);
            transformerElem.textContent = `${prob}% UP`;
            transformerElem.style.color = predictions.p5 > 0.6 ? '#22c55e' : predictions.p5 < 0.4 ? '#ef4444' : '#fbbf24';
        } else if (mlView.trend_label) {
            transformerElem.textContent = mlView.trend_label;
        } else {
            transformerElem.textContent = '--';
        }
    }

    // Update Ensemble (use trend_label or final_ml_score)
    const ensembleElem = document.getElementById('ensemblePred');
    if (ensembleElem) {
        if (mlView.trend_label) {
            ensembleElem.textContent = mlView.trend_label.toUpperCase();
            ensembleElem.style.color = mlView.trend_label === 'UP' ? '#22c55e' : mlView.trend_label === 'DOWN' ? '#ef4444' : '#fbbf24';
        } else if (mlView.final_ml_score !== undefined) {
            const score = (parseFloat(mlView.final_ml_score) * 100).toFixed(1);
            ensembleElem.textContent = `${score}%`;
        } else {
            ensembleElem.textContent = '--';
        }
    }
}

function updatePredCard(id, prob, direction) {
    const elem = document.getElementById(id);
    if (!elem) return;

    const arrow = elem.querySelector('.pred-arrow');
    const percent = elem.querySelector('.pred-percent');
    const label = elem.querySelector('.pred-label');

    const probability = Math.round((prob || 0.5) * 100);
    percent.textContent = `${probability}%`;

    // Determine arrow, color, and label
    if (direction === 'UP') {
        arrow.textContent = '↗️';
        percent.style.color = '#22c55e';
        percent.classList.remove('bearish', 'neutral');
        
        if (probability > 70) label.textContent = 'Likely Up';
        else if (probability > 60) label.textContent = 'Probably Up';
        else label.textContent = 'Maybe Up';
        
    } else if (direction === 'DOWN') {
        arrow.textContent = '↘️';
        percent.style.color = '#ef4444';
        percent.classList.add('bearish');
        percent.classList.remove('neutral');
        
        if (probability > 70) label.textContent = 'Likely Down';
        else if (probability > 60) label.textContent = 'Probably Down';
        else label.textContent = 'Maybe Down';
        
    } else {
        arrow.textContent = '→';
        percent.style.color = '#fbbf24';
        percent.classList.add('neutral');
        percent.classList.remove('bearish');
        label.textContent = 'Uncertain';
    }
}

// ====================================================================
// UPDATE REASONS (PLAIN LANGUAGE)
// ====================================================================

function updateReasons(data) {
    console.log('📊 updateReasons called');
    const signal = data.signal || {};
    const indicators = data.indicators || {};
    const indicatorsAvailable = data.indicators_available === true;
    const reasons = signal.reasons || [];
    console.log('  Reasons array:', reasons);
    console.log('  Indicators available:', indicatorsAvailable);

    const reason1 = document.getElementById('reason1');
    const reason2 = document.getElementById('reason2');
    const reason3 = document.getElementById('reason3');

    // If indicators are insufficient, show appropriate message
    if (!indicatorsAvailable) {
        const price = data.price || 0;
        const priceText = price > 0 ? `₹${price.toFixed(2)}` : '—';
        if (reason1) reason1.textContent = `Based on last price ${priceText}, indicators insufficient — waiting for more data.`;
        if (reason2) reason2.textContent = 'Accumulating candles for technical analysis...';
        if (reason3) reason3.textContent = 'Reasoning will be available after sufficient market data.';
        return;
    }

    if (reasons.length > 0) {
        if (reason1) reason1.textContent = translateReason(reasons[0]);
        if (reason2 && reasons.length > 1) reason2.textContent = translateReason(reasons[1]);
        if (reason3 && reasons.length > 2) reason3.textContent = translateReason(reasons[2]);
    } else {
        if (reason1) reason1.textContent = 'Analyzing market conditions...';
        if (reason2) reason2.textContent = 'Processing indicators...';
        if (reason3) reason3.textContent = 'Evaluating ML models...';
    }
}

function translateReason(reason) {
    if (!reason) return 'Analyzing...';
    const lowerReason = reason.toLowerCase();
    
    // RSI translations
    if (lowerReason.includes('rsi') && lowerReason.includes('oversold')) {
        return 'Price dropped significantly - may bounce back soon (RSI oversold)';
    } else if (lowerReason.includes('rsi') && lowerReason.includes('overbought')) {
        return 'Price rose too fast - may see pullback soon (RSI overbought)';
    } else if (lowerReason.includes('rsi') && lowerReason.includes('bearish')) {
        return 'Downward momentum building - price may continue falling';
    } else if (lowerReason.includes('rsi') && lowerReason.includes('bullish')) {
        return 'Upward momentum strong - price may continue rising';
    }
    
    // ATR (Volatility) translations
    else if (lowerReason.includes('atr') && lowerReason.includes('too low')) {
        return 'Very low price movement - market is calm';
    } else if (lowerReason.includes('atr') && lowerReason.includes('high')) {
        return 'Large price swings - high volatility phase';
    }
    
    // Bollinger Bands translations
    else if (lowerReason.includes('bollinger') && lowerReason.includes('tight')) {
        return 'Price in narrow range - big move may be coming';
    } else if (lowerReason.includes('bollinger') && lowerReason.includes('wide')) {
        return 'Price moving in wide range - high volatility';
    }
    
    // MACD translations
    else if (lowerReason.includes('macd') && lowerReason.includes('bullish')) {
        return 'Upward trend strengthening - buyers gaining control';
    } else if (lowerReason.includes('macd') && lowerReason.includes('bearish')) {
        return 'Downward trend strengthening - sellers gaining control';
    }
    
    // EMA / Moving Average translations
    else if (lowerReason.includes('ema') || lowerReason.includes('golden cross')) {
        return 'Bullish crossover detected - positive trend forming';
    } else if (lowerReason.includes('death cross')) {
        return 'Bearish crossover detected - negative trend forming';
    }
    
    // Default fallback - just return the reason as-is
    return reason;
}

// ====================================================================
// UPDATE MARKET OVERVIEW
// ====================================================================

function updateMarketOverview(data) {
    console.log('📊 updateMarketOverview called');
    const indicators = data.indicators || {};
    console.log('  Indicators keys:', Object.keys(indicators));
    console.log('  Indicators values:', indicators);
    console.log('  Indicators available:', data.indicators_available);
    
    // Check if indicators are available (sufficient candles)
    const indicatorsAvailable = data.indicators_available === true;
    
    // RSI (backend uses rsi14)
    const rsiElem = document.getElementById('rsiValue');
    const rsiValue = indicators.rsi14 !== undefined ? indicators.rsi14 : indicators.rsi;
    console.log('  RSI Value:', rsiValue, 'Element exists:', !!rsiElem);
    if (rsiElem) {
        // RSI must be > 0 to be valid (0 or null means insufficient data)
        if (indicatorsAvailable && rsiValue !== undefined && rsiValue !== null && !isNaN(rsiValue) && rsiValue > 0) {
            const rsi = parseFloat(rsiValue).toFixed(1);
            rsiElem.textContent = rsi;
            rsiElem.style.color = rsi > 70 ? '#ef4444' : rsi < 30 ? '#22c55e' : '#fbbf24';
            rsiElem.title = `RSI(14): ${rsi}`;
        } else {
            rsiElem.textContent = '—';
            rsiElem.style.color = '#888';
            rsiElem.title = 'Indicator unavailable (insufficient candles)';
        }
    }
    
    // ATR (backend uses atr14)
    const atrElem = document.getElementById('atrValue');
    const atrValue = indicators.atr14 !== undefined ? indicators.atr14 : indicators.atr;
    console.log('  ATR Value:', atrValue, 'Element exists:', !!atrElem);
    if (atrElem) {
        // ATR must be > 0 to be valid (0 or null means insufficient data)
        if (indicatorsAvailable && atrValue !== undefined && atrValue !== null && !isNaN(atrValue) && atrValue > 0) {
            atrElem.textContent = parseFloat(atrValue).toFixed(2);
            atrElem.title = `ATR(14): ${parseFloat(atrValue).toFixed(2)}`;
        } else {
            atrElem.textContent = '—';
            atrElem.title = 'Indicator unavailable (insufficient candles)';
        }
    }
    
    // MACD - Display histogram (most important for signals)
    const macdElem = document.getElementById('macdValue');
    console.log('  MACD Value:', indicators.macd, 'Element exists:', !!macdElem);
    if (macdElem) {
        const macd = indicators.macd;
        const signal = indicators.macd_signal;
        const hist = indicators.macd_hist;
        
        // Validate all MACD components - must all be valid or all null
        if (indicatorsAvailable && 
            macd !== undefined && macd !== null && !isNaN(macd) && 
            signal !== undefined && signal !== null && !isNaN(signal) &&
            hist !== undefined && hist !== null && !isNaN(hist)) {
            // Display histogram with tooltip showing full values
            const histValue = parseFloat(hist).toFixed(2);
            macdElem.textContent = histValue;
            macdElem.title = `MACD: ${parseFloat(macd).toFixed(2)}, Signal: ${parseFloat(signal).toFixed(2)}, Hist: ${histValue}`;
            macdElem.style.color = hist > 0 ? '#22c55e' : '#ef4444';
        } else {
            macdElem.textContent = '—';
            macdElem.title = 'Indicator unavailable (insufficient candles)';
        }
    }
    
    // Bollinger % (calculate from bb_upper, bb_lower, and current price)
    const bbElem = document.getElementById('bbValue');
    if (bbElem) {
        if (indicatorsAvailable && indicators.bb_upper && indicators.bb_lower && data.price && 
            indicators.bb_upper > indicators.bb_lower && indicators.bb_upper > 0) {
            const bbPosition = (data.price - indicators.bb_lower) / (indicators.bb_upper - indicators.bb_lower);
            if (!isNaN(bbPosition) && isFinite(bbPosition)) {
                const bb = (bbPosition * 100).toFixed(1) + '%';
                bbElem.textContent = bb;
                bbElem.title = `Bollinger Band Position: ${bb}`;
            } else {
                bbElem.textContent = '—';
                bbElem.title = 'Indicator unavailable (insufficient candles)';
            }
        } else {
            bbElem.textContent = '—';
            bbElem.title = 'Indicator unavailable (insufficient candles)';
        }
    }
    
    // Volume Trend (derive from data if not provided)
    const volElem = document.getElementById('volumeTrend');
    if (volElem) {
        if (indicators.volume_trend) {
            volElem.textContent = indicators.volume_trend;
            volElem.style.color = indicators.volume_trend === 'High' ? '#22c55e' : '#888';
        } else {
            // Use volume analysis from global data
            const volAnalysis = data.volume_analysis;
            if (volAnalysis) {
                const volLabel = volAnalysis.score > 0.6 ? 'High' : volAnalysis.score > 0.4 ? 'Normal' : 'Low';
                volElem.textContent = volLabel;
                volElem.style.color = volAnalysis.score > 0.6 ? '#22c55e' : '#888';
            }
        }
    }
    
    // Momentum (derive from regime or ml_view)
    const momElem = document.getElementById('momentum');
    if (momElem) {
        if (indicators.momentum) {
            momElem.textContent = indicators.momentum;
        } else {
            // Use ml_view trend or regime
            const mlView = data.ml_view || {};
            const regime = data.regime || {};
            if (mlView.trend_label) {
                momElem.textContent = mlView.trend_label;
            } else if (regime.label) {
                momElem.textContent = regime.label;
            }
        }
    }
}

// ====================================================================
// UPDATE GLOBAL MARKETS (India-relevant)
// ====================================================================

function updateGlobalMarkets(data) {
    // API returns: data.global.data which has nested objects like:
    // { nifty_spot: {last: 24500, change_pct: 0.5}, nasdaq: {last: 16000, change_pct: -0.3}, ... }
    const globalData = (data.global && data.global.data) || {};
    
    console.log('Global data:', globalData);

    // Universal formatter for market data - NEW SPECIFICATION
    const formatMarket = (marketObj) => {
        // Handle null/undefined market object
        if (!marketObj || typeof marketObj !== 'object') return '—';
        
        const last = marketObj.last;
        const changePct = marketObj.change_pct;
        const pctChangeAvailable = marketObj.pct_change_available;
        const qualityWarning = marketObj.quality_warning;
        const isProxy = marketObj.proxy;
        
        // ALWAYS show lastPrice if available
        if (last === null || last === undefined) return '—';
        const lastValue = parseFloat(last);
        if (isNaN(lastValue) || !isFinite(lastValue) || lastValue <= 0) {
            console.warn('⚠️ Invalid last price:', last);
            return '—';
        }
        
        const value = lastValue.toFixed(2);
        
        // Check if % change is available
        if (pctChangeAvailable === false) {
            // Show last price with badge
            let formatted = value;
            
            if (qualityWarning) {
                formatted += ' <span style="font-size:9px;color:#fbbf24;opacity:0.8;" title="Data quality issue">⚠</span>';
            } else {
                formatted += ' <span style="font-size:9px;color:#888;opacity:0.7;" title="% change unavailable">—%</span>';
            }
            
            return formatted;
        }
        
        // Handle change percentage when available
        if (changePct !== null && changePct !== undefined && !isNaN(changePct) && isFinite(changePct)) {
            const sign = changePct >= 0 ? '+' : '';
            let formatted = `${value} (${sign}${changePct.toFixed(2)}%)`;
            
            // Add proxy badge if applicable
            if (isProxy === true) {
                formatted += ' <span style="font-size:9px;color:#888;opacity:0.7;" title="Using proxy data">(proxy)</span>';
            }
            
            return formatted;
        }
        
        // No change data available, just show value
        return value;
    };

    // GIFT Nifty (dedicated NSE IFSC-SGX Connect API)
    const giftElem = document.getElementById('giftnifty');
    if (giftElem) {
        const giftData = globalData.gift_nifty || {};
        const isProxy = giftData.proxy === true;
        let display = formatMarket(giftData);
        
        // If using proxy, make it more visible
        if (isProxy && giftData.last && giftData.last > 0) {
            display = display.replace('(proxy)', '<span style="font-size:10px;color:#fbbf24;font-weight:600;" title="Using NIFTY spot as proxy - awaiting distinct feed">(PROXY)</span>');
        }
        
        giftElem.innerHTML = display;
    }
    
    // Nasdaq Futures
    const nasdaqElem = document.getElementById('nasdaq');
    if (nasdaqElem) {
        nasdaqElem.textContent = formatMarket(globalData.nasdaq);
    }
    
    // Crude Oil
    const crudeElem = document.getElementById('crude');
    if (crudeElem) {
        crudeElem.textContent = formatMarket(globalData.crude);
    }
    
    // USD/INR with enhanced quality warning
    const usdinrElem = document.getElementById('usdinr');
    if (usdinrElem) {
        const usdinrData = globalData.usdinr || {};
        const last = usdinrData.last;
        const pctAvailable = usdinrData.pct_change_available;
        const qualityWarning = usdinrData.quality_warning;
        
        if (last && last > 0) {
            let display = last.toFixed(2);
            
            if (qualityWarning === true || pctAvailable === false) {
                // Outside realistic range (70-95) - show warning
                display += ' <span style="font-size:11px;color:#fbbf24;font-weight:600;" title="Value outside expected range (70-95)">⚠ Check</span>';
            } else if (usdinrData.change_pct !== null && usdinrData.change_pct !== undefined) {
                const sign = usdinrData.change_pct >= 0 ? '+' : '';
                display += ` (${sign}${usdinrData.change_pct.toFixed(2)}%)`;
            }
            
            usdinrElem.innerHTML = display;
        } else {
            usdinrElem.textContent = '—';
        }
    }
    
    // SGX Nifty (dedicated SGX API)
    const sgxElem = document.getElementById('sgxnifty');
    if (sgxElem) {
        const sgxData = globalData.sgx_nifty || {};
        const isProxy = sgxData.proxy === true;
        let display = formatMarket(sgxData);
        
        // If using proxy, make it more visible
        if (isProxy && sgxData.last && sgxData.last > 0) {
            display = display.replace('(proxy)', '<span style="font-size:10px;color:#fbbf24;font-weight:600;" title="Using NIFTY spot as proxy - awaiting distinct feed">(PROXY)</span>');
        }
        
        sgxElem.innerHTML = display;
    }
}

// ====================================================================
// UPDATE MARKET REGIME
// ====================================================================

function updateMarketRegime(data) {
    const regime = data.regime || {};
    
    const regimeValue = document.getElementById('regimeValue');
    const regimeConfidence = document.getElementById('regimeConfidence');
    
    if (regimeValue) {
        regimeValue.textContent = regime.label || 'Calculating...';
    }
    
    if (regimeConfidence && regime.confidence !== null && regime.confidence !== undefined) {
        const conf = Math.round(regime.confidence * 100);
        regimeConfidence.style.width = `${conf}%`;
    }
}

// ====================================================================
// UPDATE SECTORS
// ====================================================================

function updateSectors(data) {
    // Placeholder - sector information is displayed in the right sidebar stock list
}

// ====================================================================
// UPDATE OPTIONS SIGNAL
// ====================================================================

function updateOptions(data) {
    const options = data.options || data.options_suggestion || {};

    console.log('Options data:', options);

    // PCR - check nested structure first (options.oi.pcr), then fallback to flat structure
    const pcrElem = document.getElementById('pcrValue');
    if (pcrElem) {
        const oi = options.oi || {};
        const pcr = oi.pcr || options.pcr || options.PCR || options.put_call_ratio;
        if (pcr !== null && pcr !== undefined && !isNaN(pcr)) {
            pcrElem.textContent = parseFloat(pcr).toFixed(2);
        } else if (options.note) {
            pcrElem.textContent = '1.00';  // Neutral fallback
        } else {
            pcrElem.textContent = 'N/A';
        }
    }

    // OI Trend - check nested structure first (options.oi.sentiment), then fallback
    const oiElem = document.getElementById('oiTrend');
    if (oiElem) {
        const oi = options.oi || {};
        const oiTrend = oi.sentiment || options.oi_trend || options.OI_Trend || options.trend || options.signal;
        if (oiTrend && oiTrend !== '--') {
            oiElem.textContent = oiTrend;
        } else if (options.note) {
            oiElem.textContent = 'Neutral';
        } else {
            oiElem.textContent = 'Neutral';
        }
    }
}

// ====================================================================
// UPDATE HEADLINES
// ====================================================================

function updateHeadlines(data) {
    const news = data.news || {};
    const headlines = news.headlines || [];
    const list = document.getElementById('headlinesList');

    if (!list) return;

    if (headlines.length === 0) {
        list.innerHTML = '<div class="headline-item">No headlines available</div>';
        return;
    }

    list.innerHTML = headlines.slice(0, 5).map(item => {
        // Backend can return either strings or objects with {title, link}
        let title, link;
        if (typeof item === 'string') {
            title = item;
            link = null;
        } else if (typeof item === 'object') {
            title = item.title || item.headline || 'No title';
            link = item.link || null;
        } else {
            title = 'No title';
            link = null;
        }
        
        // Make clickable if link exists
        if (link) {
            return `<a href="${link}" target="_blank" class="headline-item" style="text-decoration: none; color: inherit; display: block;">${title}</a>`;
        } else {
            return `<div class="headline-item">${title}</div>`;
        }
    }).join('');
}

// ====================================================================
// STOCKS LIST FUNCTIONALITY
// ====================================================================

// Stocks data - matching backend sectors.py SECTOR_STOCKS
const STOCKS_DATA = {
    banks: [
        { symbol: 'HDFCBANK', name: 'HDFC Bank', exchange: 'NSE', price: 1645.80, change: 12.40, changePct: 0.76, history: [1630, 1635, 1640, 1638, 1642, 1644, 1643, 1645, 1646, 1645.80] },
        { symbol: 'ICICIBANK', name: 'ICICI Bank', exchange: 'NSE', price: 1156.25, change: -5.60, changePct: -0.48, history: [1165, 1163, 1162, 1160, 1158, 1157, 1159, 1158, 1157, 1156.25] },
        { symbol: 'SBIN', name: 'State Bank', exchange: 'NSE', price: 798.50, change: 8.30, changePct: 1.05, history: [790, 792, 794, 795, 796, 797, 797.5, 798, 798.2, 798.50] },
        { symbol: 'KOTAKBANK', name: 'Kotak Bank', exchange: 'NSE', price: 1725.60, change: -15.20, changePct: -0.87, history: [1745, 1742, 1738, 1735, 1732, 1730, 1728, 1727, 1726, 1725.60] },
        { symbol: 'AXISBANK', name: 'Axis Bank', exchange: 'NSE', price: 1126.20, change: 30.00, changePct: 2.74, history: [1095, 1100, 1105, 1110, 1115, 1118, 1120, 1123, 1125, 1126.20] },
    ],
    it: [
        { symbol: 'TCS', name: 'Tata Consultancy', exchange: 'NSE', price: 4125.80, change: 45.60, changePct: 1.12, history: [4080, 4090, 4095, 4100, 4105, 4110, 4115, 4120, 4123, 4125.80] },
        { symbol: 'INFY', name: 'Infosys', exchange: 'NSE', price: 1845.30, change: 22.10, changePct: 1.21, history: [1823, 1828, 1832, 1836, 1838, 1840, 1842, 1844, 1845, 1845.30] },
        { symbol: 'WIPRO', name: 'Wipro', exchange: 'NSE', price: 456.75, change: -3.25, changePct: -0.71, history: [462, 461, 460, 459, 458.5, 458, 457.5, 457, 456.8, 456.75] },
        { symbol: 'HCLTECH', name: 'HCL Technologies', exchange: 'NSE', price: 1542.90, change: 18.40, changePct: 1.21, history: [1524, 1528, 1532, 1536, 1538, 1540, 1541, 1542, 1542.5, 1542.90] },
        { symbol: 'TECHM', name: 'Tech Mahindra', exchange: 'NSE', price: 1678.20, change: 12.80, changePct: 0.77, history: [1665, 1668, 1670, 1672, 1674, 1675, 1676, 1677, 1678, 1678.20] },
        { symbol: 'COFORGE', name: 'Coforge', exchange: 'NSE', price: 6789.40, change: 82.30, changePct: 1.23, history: [6707, 6725, 6745, 6760, 6775, 6780, 6785, 6787, 6788, 6789.40] },
    ],
    pharma: [
        { symbol: 'SUNPHARMA', name: 'Sun Pharma', exchange: 'NSE', price: 1678.90, change: 28.40, changePct: 1.72, history: [1650, 1658, 1662, 1666, 1670, 1673, 1675, 1677, 1678.5, 1678.90] },
        { symbol: 'DRREDDY', name: 'Dr Reddy\'s Lab', exchange: 'NSE', price: 6234.50, change: -45.80, changePct: -0.73, history: [6280, 6275, 6268, 6260, 6252, 6248, 6242, 6238, 6236, 6234.50] },
        { symbol: 'CIPLA', name: 'Cipla', exchange: 'NSE', price: 1456.30, change: 18.60, changePct: 1.29, history: [1437, 1442, 1446, 1448, 1450, 1452, 1454, 1455, 1456, 1456.30] },
        { symbol: 'AUROPHARMA', name: 'Aurobindo Pharma', exchange: 'NSE', price: 1234.80, change: 15.40, changePct: 1.26, history: [1219, 1223, 1226, 1228, 1230, 1231, 1233, 1234, 1234.5, 1234.80] },
    ],
    auto: [
        { symbol: 'M&M', name: 'Mahindra & Mahindra', exchange: 'NSE', price: 2845.60, change: 38.20, changePct: 1.36, history: [2807, 2815, 2820, 2825, 2830, 2835, 2838, 2842, 2844, 2845.60] },
        { symbol: 'HEROMOTOCO', name: 'Hero MotoCorp', exchange: 'NSE', price: 4567.80, change: 56.30, changePct: 1.25, history: [4511, 4525, 4538, 4545, 4552, 4558, 4562, 4565, 4567, 4567.80] },
    ],
    fmcg: [
        { symbol: 'HINDUNILVR', name: 'Hindustan Unilever', exchange: 'NSE', price: 2678.40, change: 32.10, changePct: 1.21, history: [2646, 2655, 2660, 2665, 2668, 2670, 2673, 2676, 2677, 2678.40] },
        { symbol: 'ITC', name: 'ITC Limited', exchange: 'NSE', price: 456.90, change: 5.20, changePct: 1.15, history: [451.7, 453, 454, 455, 455.5, 456, 456.3, 456.6, 456.8, 456.90] },
        { symbol: 'NESTLEIND', name: 'Nestle India', exchange: 'NSE', price: 2456.70, change: -18.50, changePct: -0.75, history: [2478, 2475, 2470, 2467, 2464, 2462, 2460, 2458, 2457, 2456.70] },
    ],
    financial: [
        { symbol: 'HDFCLIFE', name: 'HDFC Life', exchange: 'NSE', price: 678.50, change: 8.40, changePct: 1.25, history: [670.1, 672, 674, 675, 676, 676.5, 677, 677.8, 678.2, 678.50] },
        { symbol: 'SBILIFE', name: 'SBI Life', exchange: 'NSE', price: 1567.80, change: 22.30, changePct: 1.44, history: [1545.5, 1550, 1555, 1558, 1560, 1562, 1564, 1566, 1567, 1567.80] },
        { symbol: 'BAJFINANCE', name: 'Bajaj Finance', exchange: 'NSE', price: 7234.60, change: 96.40, changePct: 1.35, history: [7138.2, 7160, 7180, 7195, 7208, 7215, 7222, 7228, 7232, 7234.60] },
        { symbol: 'BAJAJFINSV', name: 'Bajaj Finserv', exchange: 'NSE', price: 1678.90, change: 18.70, changePct: 1.13, history: [1660.2, 1665, 1668, 1670, 1672, 1674, 1676, 1677, 1678, 1678.90] },
    ],
    energy: [
        { symbol: 'RELIANCE', name: 'Reliance Industries', exchange: 'NSE', price: 2856.70, change: 42.30, changePct: 1.50, history: [2814.4, 2825, 2835, 2840, 2845, 2848, 2850, 2853, 2855, 2856.70] },
        { symbol: 'ONGC', name: 'ONGC', exchange: 'NSE', price: 267.85, change: 3.45, changePct: 1.30, history: [264.4, 265, 265.8, 266.2, 266.8, 267, 267.3, 267.6, 267.7, 267.85] },
        { symbol: 'NTPC', name: 'NTPC', exchange: 'NSE', price: 356.40, change: 4.80, changePct: 1.37, history: [351.6, 353, 354, 355, 355.5, 356, 356.1, 356.2, 356.3, 356.40] },
        { symbol: 'POWERGRID', name: 'Power Grid Corp', exchange: 'NSE', price: 287.60, change: 3.20, changePct: 1.13, history: [284.4, 285, 286, 286.5, 287, 287.2, 287.3, 287.4, 287.5, 287.60] },
    ],
    infra: [
        { symbol: 'ADANIENT', name: 'Adani Enterprises', exchange: 'NSE', price: 2567.80, change: 38.90, changePct: 1.54, history: [2528.9, 2540, 2548, 2553, 2558, 2561, 2564, 2566, 2567, 2567.80] },
        { symbol: 'ADANIPORTS', name: 'Adani Ports', exchange: 'NSE', price: 1234.50, change: 16.70, changePct: 1.37, history: [1217.8, 1223, 1227, 1229, 1231, 1232, 1233, 1233.8, 1234.2, 1234.50] },
        { symbol: 'LT', name: 'Larsen & Toubro', exchange: 'NSE', price: 3678.90, change: 52.40, changePct: 1.44, history: [3626.5, 3640, 3655, 3662, 3668, 3672, 3675, 3677, 3678, 3678.90] },
        { symbol: 'ULTRACEMCO', name: 'UltraTech Cement', exchange: 'NSE', price: 9876.50, change: 124.30, changePct: 1.27, history: [9752.2, 9780, 9810, 9835, 9850, 9860, 9865, 9870, 9874, 9876.50] },
    ]
};

let currentSector = 'all';

// Live stock data cache - populated from API
const liveStockData = {};

// Setup sector tabs
function setupSectorTabs() {
    const tabs = document.querySelectorAll('.sector-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentSector = tab.dataset.sector;
            updateStocksGrid();
        });
    });
}

// Fetch live price for a single stock
async function fetchLiveStockPrice(symbol) {
    try {
        // Use dynamic base URL to avoid CORS issues
        const baseUrl = window.location.protocol === 'file:' 
            ? 'http://127.0.0.1:8000'
            : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
                ? 'http://127.0.0.1:8000'
                : window.location.origin;
        // interval must be in SECONDS (300 = 5 minutes)
        const url = `${baseUrl}/api/signal_live?symbol=${symbol}&interval=300&limit=10`;
        console.log(`🔍 Fetching ${symbol} from: ${url}`);
        const response = await fetch(url, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            console.error(`Failed to fetch ${symbol}: ${response.status}`);
            return null;
        }
        
        const data = await response.json();
        
        // Calculate change from candles
        let change = 0;
        let changePct = 0;
        let history = [];
        
        if (data.candles && data.candles.length >= 2) {
            const latest = data.candles[data.candles.length - 1];
            const previous = data.candles[0];
            
            // Validate previous.open to avoid extreme percentages
            if (previous.open > 0 && latest.close > 0) {
                change = latest.close - previous.open;
                changePct = (change / previous.open) * 100;
                
                // Sanity check: cap extreme percentage changes (likely data errors)
                if (Math.abs(changePct) > 100) {
                    console.warn(`⚠️ Extreme change detected for ${symbol}: ${changePct.toFixed(2)}% - possible data error`);
                    // Use more conservative calculation with latest vs previous close
                    if (data.candles.length > 1) {
                        const prevClose = data.candles[data.candles.length - 2].close;
                        if (prevClose > 0) {
                            change = latest.close - prevClose;
                            changePct = (change / prevClose) * 100;
                        }
                    }
                }
            } else {
                console.warn(`⚠️ Invalid price data for ${symbol}: previous.open=${previous.open}, latest.close=${latest.close}`);
            }
            
            // Build mini history from last 10 candles
            history = data.candles.slice(-10).map(c => c.close);
        }
        
        return {
            symbol: symbol,
            price: data.price || 0,
            change: change,
            changePct: changePct,
            history: history.length > 0 ? history : [data.price || 0]
        };
    } catch (error) {
        console.error(`Failed to fetch ${symbol}:`, error);
        return null;
    }
}

// Fetch live prices for all stocks
async function fetchAllStockPrices() {
    console.log('📊 fetchAllStockPrices CALLED');
    const allSymbols = [];
    
    // Collect all symbols from STOCKS_DATA
    Object.values(STOCKS_DATA).forEach(sectorStocks => {
        sectorStocks.forEach(stock => {
            allSymbols.push(stock.symbol);
        });
    });
    
    console.log('🔄 Fetching live prices for', allSymbols.length, 'stocks...', allSymbols.slice(0, 5));
    
    // Fetch in batches to avoid overwhelming the API
    const batchSize = 5;
    for (let i = 0; i < allSymbols.length; i += batchSize) {
        const batch = allSymbols.slice(i, i + batchSize);
        const promises = batch.map(symbol => fetchLiveStockPrice(symbol));
        const results = await Promise.all(promises);
        
        results.forEach(result => {
            if (result) {
                liveStockData[result.symbol] = result;
            }
        });
        
        // Small delay between batches
        if (i + batchSize < allSymbols.length) {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }
    
    console.log('✅ Fetched live prices for', Object.keys(liveStockData).length, 'stocks');
    console.log('Sample live data:', Object.keys(liveStockData).slice(0, 3).map(k => ({ symbol: k, price: liveStockData[k].price })));
    updateStocksGrid();
}

// Generate mini sparkline SVG
function generateMiniSparkline(history, isPositive) {
    if (!history || history.length === 0) return '';
    
    const width = 60;
    const height = 24;
    const padding = 2;
    
    const min = Math.min(...history);
    const max = Math.max(...history);
    const range = max - min || 1;
    
    const points = history.map((value, index) => {
        const x = padding + (index / (history.length - 1)) * (width - padding * 2);
        const y = height - padding - ((value - min) / range) * (height - padding * 2);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
    
    const color = isPositive ? '#22c55e' : '#ef4444';
    
    return `
        <svg width="${width}" height="${height}" class="mini-spark">
            <polyline
                fill="none"
                stroke="${color}"
                stroke-width="1.5"
                points="${points}"
            />
        </svg>
    `;
}

// Update stocks grid
function updateStocksGrid() {
    console.log('📊 updateStocksGrid CALLED, liveStockData count:', Object.keys(liveStockData).length);
    const stocksGrid = document.getElementById('stocksGrid');
    if (!stocksGrid) {
        console.error('❌ stocksGrid element not found!');
        return;
    }
    
    let stocks = [];
    
    if (currentSector === 'all') {
        // Combine all sectors
        stocks = [
            ...STOCKS_DATA.banks,
            ...STOCKS_DATA.it,
            ...STOCKS_DATA.pharma,
            ...STOCKS_DATA.auto,
            ...STOCKS_DATA.fmcg,
            ...STOCKS_DATA.financial,
            ...STOCKS_DATA.energy,
            ...STOCKS_DATA.infra
        ];
    } else {
        stocks = STOCKS_DATA[currentSector] || [];
    }
    
    if (stocks.length === 0) {
        stocksGrid.innerHTML = '<div style="color: #666; font-size: 11px; padding: 20px; text-align: center;">No stocks available</div>';
        return;
    }
    
    stocksGrid.innerHTML = stocks.map(stock => {
        // ALWAYS use live data if available - prioritize real-time prices
        const liveData = liveStockData[stock.symbol];
        let price, change, changePct, history;
        
        if (liveData && liveData.price) {
            // Live data available - use it exclusively
            price = liveData.price;
            change = liveData.change || 0;
            changePct = liveData.changePct || 0;
            history = liveData.history || stock.history;
        } else {
            // Fallback to static data only if live not available
            price = stock.price;
            change = stock.change;
            changePct = stock.changePct;
            history = stock.history;
        }
        
        // Validate data before display - NEW SPEC
        const isValidPrice = price > 0 && isFinite(price);
        const isValidChange = !isNaN(change) && isFinite(change);
        const isValidChangePct = !isNaN(changePct) && isFinite(changePct) && Math.abs(changePct) <= 40;
        
        // Show lastPrice always, but gate % change display
        const pctChangeAvailable = isValidPrice && isValidChange && isValidChangePct;
        
        const isPositive = change >= 0;
        const changeClass = isPositive ? 'positive' : (change === 0 ? 'neutral' : 'negative');
        const changeSymbol = isPositive ? '↑' : (change === 0 ? '' : '↓');
        const sparkline = generateMiniSparkline(history, isPositive);
        
        // Get first letter as logo
        const logoLetter = stock.symbol.charAt(0);
        
        const isActive = stock.symbol === currentSymbol ? 'active-symbol' : '';
        
        // Format price display
        let priceDisplay = '—';
        let changeDisplay = '—';
        
        if (isValidPrice) {
            priceDisplay = '₹' + price.toFixed(2);
            
            if (pctChangeAvailable) {
                changeDisplay = `${changeSymbol} ${Math.abs(change).toFixed(2)} (${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%)`;
            } else if (price > 0) {
                // Show price is valid but % unavailable
                changeDisplay = '<span style="font-size:10px;color:#888;opacity:0.7;">% unavailable</span>';
            }
        }
        
        return `
            <div class="stock-item ${isActive}" data-symbol="${stock.symbol}">
                <div class="stock-info">
                    <div class="stock-logo">${logoLetter}</div>
                    <div class="stock-details">
                        <div class="stock-name">${stock.name}</div>
                        <div class="stock-exchange">${stock.exchange}</div>
                    </div>
                </div>
                <div class="stock-mini-chart">
                    ${sparkline}
                </div>
                <div class="stock-price-info">
                    <div class="stock-price">${priceDisplay}</div>
                    <div class="stock-change ${changeClass}">
                        ${changeDisplay}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Add click handlers to stock items
    document.querySelectorAll('.stock-item').forEach(item => {
        item.addEventListener('click', () => {
            const symbol = item.dataset.symbol;
            selectSymbol(symbol);
        });
    });
}

// ====================================================================
// UPDATE NIFTY MINI INFO (SIDEBAR CARD)
// ====================================================================

function updateNiftyMiniInfo(data) {
    const price = data.price || 0;
    const candles = data.candles || [];
    
    // Update price (validate > 0)
    const niftyPrice = document.getElementById('niftyPrice');
    if (niftyPrice) {
        if (price > 0) {
            niftyPrice.textContent = `₹${price.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        } else {
            niftyPrice.textContent = '—';
        }
    }
    
    // Calculate change from day's OPENING price (not previous candle)
    if (candles.length >= 1) {
        const currentPrice = price || candles[candles.length - 1].close;
        // Find day's opening price (first candle of today)
        // For intraday, use the open of the first candle
        const dayOpen = candles[0].open;
        
        const niftyChange = document.getElementById('niftyChange');
        if (niftyChange) {
            // Validate dayOpen > 0 to avoid extreme percentages
            let changePercent = 0;
            if (dayOpen > 0 && currentPrice > 0) {
                const changeValue = currentPrice - dayOpen;
                changePercent = ((currentPrice - dayOpen) / dayOpen) * 100;
                
                const sign = changeValue >= 0 ? '+' : '';
                niftyChange.textContent = `${sign}${changeValue.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
                
                if (changePercent > 0) {
                    niftyChange.classList.add('positive');
                    niftyChange.classList.remove('negative');
                } else if (changePercent < 0) {
                    niftyChange.classList.add('negative');
                    niftyChange.classList.remove('positive');
                }
            } else {
                niftyChange.textContent = '—';
            }
        }
        
        // Update mini chart
        const miniChartContainer = document.getElementById('niftyMiniChart');
        if (miniChartContainer && candles.length >= 10) {
            const last10 = candles.slice(-10).map(c => c.close);
            niftyHistory = last10;
            const isPositive = changePercent >= 0;
            miniChartContainer.innerHTML = generateMiniSparkline(last10, isPositive);
        }
    }
}
