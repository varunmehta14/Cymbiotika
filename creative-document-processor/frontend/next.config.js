/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    // Handle canvas binary module
    config.resolve.alias.canvas = false;
    
    // This prevents webpack from attempting to process binary files
    config.module.rules.push({
      test: /\.node$/,
      use: 'node-loader',
    });
    
    return config;
  },
  // Add support for static image imports
  images: {
    disableStaticImages: false,
  },
};

module.exports = nextConfig;
