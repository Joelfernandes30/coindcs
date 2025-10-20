async function loadCrypto() {
  const res = await fetch('/api/crypto');
  const data = await res.json();

  const tbody = document.querySelector('#crypto-table tbody');
  tbody.innerHTML = '';

  data.forEach((coin, index) => {
    const change = coin.price_change_percentage_24h;
    const techRating = change > 2 ? 'Buy' : change < -2 ? 'Sell' : 'Neutral';

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${index + 1}</td>
      <td class="coin-cell">
        <img src="${coin.image}" alt="${coin.name}" style="width:24px;height:24px;border-radius:50%;">
        <button class="symbol-box" data-symbol="${coin.id}">
          ${coin.symbol.toUpperCase()}
        </button>
        <span class="coin-name">${coin.name}</span>
      </td>
      <td>₹${coin.current_price.toLocaleString()}</td>
      <td class="${change < 0 ? 'negative' : 'positive'}">${change.toFixed(2)}%</td>
      <td>₹${coin.market_cap.toLocaleString()}</td>
      <td>₹${coin.total_volume.toLocaleString()}</td>
      <td>${coin.circulating_supply.toLocaleString()}</td>
      <td>${(Math.random() * 10).toFixed(2)}%</td>
      <td>${coin.categories ? coin.categories[0] : 'Cryptocurrency'}</td>
      <td class="${techRating === 'Buy' ? 'tech-buy' : 'tech-sell'}">${techRating}</td>
    `;
    tbody.appendChild(row);
  });

  // Add event listeners to symbol buttons
  document.querySelectorAll('.symbol-box').forEach((btn) => {
    btn.addEventListener('mouseenter', () => {
      btn.style.backgroundColor = '#007bff';
      btn.style.color = 'white';
      btn.style.cursor = 'pointer';
      btn.style.transition = '0.3s ease';
    });

    btn.addEventListener('mouseleave', () => {
      btn.style.backgroundColor = '#f0f0f0';
      btn.style.color = '#333';
    });

    btn.addEventListener('click', () => {
      const symbol = btn.dataset.symbol;
      window.location.href = `/crypto/${symbol}`; // Redirect to detail page
    });
  });
}

document.addEventListener('DOMContentLoaded', loadCrypto);
