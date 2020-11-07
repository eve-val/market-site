(function(document, window, undefined) {
  window.formatDecimal = function(amt) {
    return amt.toLocaleString('en', { 
      maximumFractionDigits: 2,
      minimumFractionDigits: 2
    });
  }

  window.market = function() {
    return {
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
            this.rows = rows
          });
      },

      get filteredRows() {
        return this.rows;
      }
    }
  }
})(document, window);
