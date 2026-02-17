/** Redirect root to existing page */
module.exports = {
  async redirects() {
    return [
      {
        source: '/',
        destination: '/activate',
        permanent: false,
      },
    ];
  },
};
