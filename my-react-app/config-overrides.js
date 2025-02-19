module.exports = function override(config, env) {
  // Only modify config in development mode
  if (env === 'development') {
    config.devtool = 'source-map'; // Enable source map in development mode
  }
  return config;
};
