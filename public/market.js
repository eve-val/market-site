(function(document, window, undefined) {
  window.formatDecimal = function(amt) {
    return amt.toLocaleString('en', {
      maximumFractionDigits: 2,
      minimumFractionDigits: 2
    });
  }

  function stockIsLow(r) {
    if (r.price >= 50000000) {
      return r.volume <= 2;
    } else if (r.hub_volume > 100000) {
      return r.volume < 5000;
    }
    return r.volume < 10;
  }

  window.market = function() {

    return {
      filter: '',
      text: 'Hello, LSC4-P',
      rows: [],
      showLow: true,
      showMissing: true,
      showStocked: true,

      initialize() {
        let hash = decodeURIComponent(window.location.hash.split('#').pop());
        let hashParts = hash.split('&');
        this.filter = hashParts[0];
        if (hashParts.length > 1) {
          this.showLow = this.showMissing = this.showStocked = false;
          for (let i = 1; i < hashParts.length; ++i) {
            let part = hashParts[i];
            if ('low' === part)
              this.showLow = true;
            if ('missing' === part)
              this.showMissing = true;
            if ('stocked' === part)
              this.showStocked = true;
          }
        }

        fetch('/LSC4-P.json')
          .then(resp => {
            if (!resp.ok) {
              throw new Error('error fetching market data');
            }
            return resp.json();
          })
          .then(data => {
            rows = this.rows = data;
            this.rows.forEach((r) => {
              // These are arbitrary thresholds I picked because it looks like
              // a lot of things get stocked in stacks of 10. We should
              // consider setting thresholds in the JSON and then using those
              // here instead of my magic numbers. -ST
              if (r.volume == 0) {
                r.missing = true
                r.status = 'Missing'
              } else if (stockIsLow(r)) {
                r.stockLow = true
                r.status = 'Low'
              } else {
                r.stocked = true
                r.status = 'Stocked'
              }
            })
          });

        var viewData = this;
        new ClipboardJS('#clipboard', {
          text: function() {
            let rows = viewData.filteredRows;
            return rows.map(r => r.item).join("\n");
          }
        });
      },

      get filteredRows() {
        let q = this.filter.toLowerCase();
        if (!q) return this.rows;
        let tokens = q.split(/\s+/);
        return this.rows.filter((row) => {
          let matchStatus = (
            (this.showLow && row.stockLow) ||
            (this.showMissing && row.missing) ||
            (this.showStocked && row.stocked))

          let matchSearch = tokens.reduce((isMatch, token) => {
            let negate = (token && token[0] === '-');
            if (negate) { token = token.substring(1); }
            if (!token) { return isMatch }
            let matched = (
              row.item.toLowerCase().includes(token) ||
              row.group.toLowerCase().includes(token));
            return isMatch && ((negate !== matched) || !token);
          }, true);

          return matchSearch && matchStatus;
        });
      },

      fuzzworkPrice(typeID) {
        return 'https://market.fuzzwork.co.uk/hub/type/' + typeID + '/';
      },

      iconURL(typeID) {
        return 'https://images.evetech.net/types/' + typeID + '/icon';
      },

      updateLocationHash() {
        let hash = '#' + this.filter;
        if (!this.showLow || !this.showMissing || !this.showStocked) {
          if (this.showLow)
            hash += '&low';
          if (this.showMissing)
            hash += '&missing';
          if (this.showStocked)
            hash += '&stocked';
        }
        history.pushState(null, null, hash);
      },

      updateStatusFilter() {
        if (!this.showLow && !this.showMissing && !this.showStocked) {
            this.showLow = this.showMissing = this.showStocked = true;
        }
        this.updateLocationHash();
      }
    }
  }
})(document, window);
