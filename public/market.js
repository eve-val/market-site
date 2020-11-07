(function(document, window, undefined) {
  window.formatDecimal = function(amt) {
    return amt.toLocaleString('en', { 
      maximumFractionDigits: 2,
      minimumFractionDigits: 2
    });
  }

  window.market = function() {
    return {
      filter: decodeURIComponent(window.location.hash.split('#').pop()),
      text: 'Hello, LSC4-P',
      rows: [],
      
      fetchData() {
        fetch('/market.json')
          .then(resp => {
            if (!resp.ok) {
              throw new Error('error fetching market data');
            }
            return resp.json();
          })
          .then(rows => {
            this.rows = rows;
            this.rows.forEach((r) => {
              if (r.volume > 5) {
                r.stocked = true
                r.status = 'Stocked'
              } else if (r.volume > 0) {
                r.stockLow = true
                r.status = 'Low'
              } else {
                r.missing = true
                r.status = 'Missing'
              }
            })
          });
      },

      get filteredRows() {
        let q = this.filter.toLowerCase();
        if (!q) return this.rows;
        let tokens = q.split(/\s+/);
        return this.rows.filter((row) =>
          tokens.reduce((isMatch, token) => {
            return isMatch &&
              ((token === 'missing' && row.missing) ||
               (token === 'stocked' && row.stocked) ||
               (token === 'low' && row.stockLow) ||
               row.item.toLowerCase().includes(token) ||
               row.group.toLowerCase().includes(token))
          }, true));
      },

      updateLocationHash() {
        history.pushState(null, null, '#'+this.filter);
      }
    }
  }
})(document, window);
