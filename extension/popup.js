const BACKEND_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', async () => {
  const urlLabel = document.getElementById('url-label');
  const analyzeBtn = document.getElementById('analyze-btn');
  const resultCard = document.getElementById('result-card');
  const scoreDisplay = document.getElementById('score-display');
  const fakePct = document.getElementById('fake-pct');
  const alertsContainer = document.getElementById('alerts-container');

  // Query active browser tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const tabUrl = tab?.url || '';

  const isSupported = tabUrl.includes('amazon.') || tabUrl.includes('flipkart.');

  if (!isSupported) {
    urlLabel.textContent = 'Please open an Amazon or Flipkart product listing to analyze.';
    analyzeBtn.disabled = true;
    return;
  }

  urlLabel.textContent = tabUrl.substring(0, 50) + '...';

  // Check if product report is already cached in PostgreSQL
  try {
    const lookupRes = await fetch(`${BACKEND_BASE}/api/products/lookup/?url=${encodeURIComponent(tabUrl)}`);
    if (lookupRes.ok) {
      const productData = await lookupRes.json();
      if (productData.analysis_report) {
        renderScore(productData.analysis_report);
        analyzeBtn.textContent = 'Re-Analyze Product';
      }
    }
  } catch (err) {
    console.log('Backend not reachable yet or uncached:', err);
  }

  // Trigger analysis on click
  analyzeBtn.addEventListener('click', async () => {
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing in Background...';
    urlLabel.textContent = 'Scraping and analyzing reviews...';

    try {
      const response = await fetch(`${BACKEND_BASE}/api/products/analyze/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: tabUrl })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to trigger');

      // Poll product lookup until report is ready
      pollReport(tabUrl);
    } catch (err) {
      urlLabel.textContent = 'Error: ' + err.message;
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = 'Analyze Current Page';
    }
  });

  async function pollReport(url) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_BASE}/api/products/lookup/?url=${encodeURIComponent(url)}`);
        if (res.ok) {
          const productData = await res.json();
          if (productData.analysis_report) {
            clearInterval(interval);
            renderScore(productData.analysis_report);
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analysis Complete';
            urlLabel.textContent = 'Analysis finished successfully.';
          }
        }
      } catch (e) {
        // continue polling
      }
    }, 2000);
  }

  function renderScore(report) {
    resultCard.style.display = 'block';
    const score = report.trust_score;
    scoreDisplay.textContent = `${score}/100`;

    scoreDisplay.className = 'score-val ' + (
      score >= 75 ? 'score-good' : score >= 50 ? 'score-avg' : 'score-bad'
    );

    fakePct.textContent = `${report.fake_review_percentage}%`;

    alertsContainer.innerHTML = '';
    const patterns = report.dark_patterns_detected || [];
    patterns.slice(0, 2).forEach(p => {
      const div = document.createElement('div');
      div.className = 'alert-item';
      div.textContent = `${p.type.replace(/_/g, ' ')}: ${p.description}`;
      alertsContainer.appendChild(div);
    });
  }
});