require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });

const { ethers } = require('ethers');

// Derive wallet address from private key if available
let monadReceiveAddress = process.env.MONAD_RECEIVE_ADDRESS || null;
if (!monadReceiveAddress && process.env.MONAD_PRIVATE_KEY) {
  try {
    const wallet = new ethers.Wallet(process.env.MONAD_PRIVATE_KEY);
    monadReceiveAddress = wallet.address;
  } catch (e) {
    console.warn('[Config] Could not derive MONAD address from private key');
  }
}

const config = {
  port: parseInt(process.env.VAULT_PORT) || 4402,

  monad: {
    rpc: process.env.MONAD_RPC || 'https://rpc.monad.xyz',
    chainId: 143,
    privateKey: process.env.MONAD_PRIVATE_KEY || '',
    receiveAddress: monadReceiveAddress,
  },

  solana: {
    rpc: process.env.SOLANA_RPC || 'https://api.mainnet-beta.solana.com',
    receiveAddress: process.env.SOLANA_RECEIVE_ADDRESS || '',
  },

  base: {
    rpc: process.env.BASE_RPC || 'https://mainnet.base.org',
    chainId: 8453,
    receiveAddress: process.env.BASE_RECEIVE_ADDRESS || '',
    usdcAddress: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
  },

  // Storage constants
  CHUNK_SIZE: 80 * 1024,           // 80KB per chunk
  CALLDATA_PREFIX: 'DCLAW01',      // 7-byte protocol signature (internal only — never expose in responses)
  HEADER_BYTES: 47,                // 7 (prefix) + 32 (fileId) + 4 (segmentIndex) + 4 (totalSegments)
  TX_VALUE: '0.0001',              // Tiny MON dust per chunk tx

  // Pricing
  SERVICE_FEE_USD: parseFloat(process.env.SERVICE_FEE_USD) || 30,

  // Swap engine
  swap: {
    solanaPrivateKey: process.env.SOLANA_PRIVATE_KEY || '',
    farnsMint: process.env.FARNS_MINT || '9crfy4udrHQo8eP6mP393b5qwpGLQgcxVg9acmdwBAGS',
    gasBufferPercent: parseInt(process.env.GAS_BUFFER_PERCENT) || 15,
    farnsBuyPercent: parseInt(process.env.FARNS_BUY_PERCENT) || 50,
    jupiterApi: process.env.JUPITER_API || 'https://quote-api.jup.ag/v6',
    usdcMint: process.env.USDC_MINT || 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    maxRetries: 3,
  },

  // Domain
  domain: process.env.DOMAIN || 'https://dropclaw.cloud',

  // Marketplace
  marketplace: {
    contractAddress: '0xeFc5D4f6ee82849492b1F297134872dA2Abb260d',
  },

  // Local data storage
  dataDir: require('path').join(__dirname, '..', 'data'),
  indexFile: require('path').join(__dirname, '..', 'data', 'vault-index.json'),
  swapLogFile: require('path').join(__dirname, '..', 'data', 'swap-log.json'),
  uploadJobsFile: require('path').join(__dirname, '..', 'data', 'upload-jobs.json'),
};

module.exports = config;
