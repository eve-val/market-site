(function(document, window, undefined) {
  window.formatDecimal = function(amt) {
    return amt.toLocaleString('en', { 
      maximumFractionDigits: 2,
      minimumFractionDigits: 2
    });
  }

  window.market = function() {
    return {
      filter: "",
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
              r.stocked = r.volume > 0;
            })
          });
      },

      get filteredRows() {
        return this.rows.filter((row) => {
          let q = this.filter.toLowerCase();
          return q === "" ||
            row.item.toLowerCase().includes(q) ||
            row.group.toLowerCase().includes(q);
        });
      }
    }
  }
})(document, window);
