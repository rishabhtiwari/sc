const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// Add path aliases for Metro bundler
config.resolver.alias = {
  '@models': path.resolve(__dirname, 'src/models'),
  '@views': path.resolve(__dirname, 'src/views'),
  '@controllers': path.resolve(__dirname, 'src/controllers'),
  '@services': path.resolve(__dirname, 'src/services'),
  '@utils': path.resolve(__dirname, 'src/utils'),
  '@navigation': path.resolve(__dirname, 'src/navigation'),
};

module.exports = config;
