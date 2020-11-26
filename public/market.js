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
        fetch('/LSC4-P.json')
          .then(resp => {
            if (!resp.ok) {
              throw new Error('error fetching market data');
            }
            return resp.json();
          })
          .then(rows => {
            this.rows = rows;
            this.rows.forEach((r) => {
              // These are arbitrary thresholds I picked because it looks like
              // a lot of things get stocked in stacks of 10. We should
              // consider setting thresholds in the JSON and then using those
              // here instead of my magic numbers. -ST
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
            let negate = (token && token[0] === '-');
            if (negate) { token = token.substring(1); }
            let matched = (
              (token === 'missing' && row.missing) ||
              (token === 'stocked' && row.stocked) ||
              (token === 'low' && row.stockLow) ||
              row.item.toLowerCase().includes(token) ||
              row.group.toLowerCase().includes(token));
            return isMatch && (negate !== matched);
              
          }, true));
      },

      updateLocationHash() {
        history.pushState(null, null, '#'+this.filter);
      }
    }
  }
})(document, window);
