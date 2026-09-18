'use strict';
// Deployment-owned links; no private hostnames are baked into the shared UI.
fetch('/certificate.json', {cache: 'no-store'})
  .then(response => {if (!response.ok) throw Error(); return response.json();})
  .then(config => {
    for (const [key, protocol] of [['reader_url', 'https:'], ['bootstrap_url', 'http:']]) {
      let url;
      try {url = new URL(config[key]);} catch {continue;}
      if (url.protocol !== protocol || url.username || url.password) continue;
      document.querySelectorAll(`[data-certificate-link="${key}"]`).forEach(link => {
        link.href = url.href;
        link.hidden = false;
      });
    }
  }).catch(() => {});
