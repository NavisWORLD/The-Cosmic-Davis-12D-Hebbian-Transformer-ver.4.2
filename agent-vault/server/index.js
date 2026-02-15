/**
 * DropClaw — x402 Encrypted On-Chain Storage for AI Agents
 *
 * Express server that accepts encrypted blobs, chunks them, and stores
 * permanently on Monad blockchain via calldata. Multi-chain payment via x402.
 *
 * The server is a BLIND ENCRYPTED RELAY — it never sees plaintext.
 * Client-side encryption only (proprietary stack).
 */

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const config = require('./config');
const { registerWithBazaar } = require('./bazaar');
const { loadJobs } = require('./services/uploadJobManager');

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ extended: true, limit: '100mb' }));

// Multer for file uploads (in-memory storage)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 100 * 1024 * 1024 }, // 100MB max
});

// PayAI facilitator payment middleware (x402 standard protocol)
// Must be before multer so unpaid requests get 402 without file parsing
try {
  const { paymentMiddleware } = require('x402-express');
  app.use(
    paymentMiddleware(
      config.base.receiveAddress,
      {
        "POST /vault/store/pay": {
          price: `$${config.SERVICE_FEE_USD}`,
          network: "base",
        },
      },
      { url: "https://facilitator.payai.network" }
    )
  );
  console.log('[Facilitator] PayAI payment middleware active');
} catch (err) {
  console.warn(`[Facilitator] x402-express not available: ${err.message}`);
}

// Apply multer to store routes (single middleware that skips if already parsed,
// since /vault/store prefix-matches /vault/store/zauth and /vault/store/pay)
const uploadOnce = (req, res, next) => {
  if (req.file) return next();
  upload.single('file')(req, res, next);
};
app.use('/vault/store', uploadOnce);

// Static files — website
app.use(express.static(path.join(__dirname, '..', 'public')));

// Routes
app.use('/vault/store/zauth', require('./routes/storeZauth'));
app.use('/vault/store/pay', require('./routes/storeFacilitated'));
app.use('/vault/store', require('./routes/store'));
app.use('/vault/status', require('./routes/status'));
app.use('/vault/retrieve', require('./routes/retrieve'));
app.use('/vault/pricing', require('./routes/pricing'));
app.use('/.well-known/x402', require('./routes/wellknown'));
app.use('/marketplace', require('./routes/marketplace'));

// Serve terms of service
app.get('/legal/terms', (req, res) => {
  const termsPath = path.join(__dirname, '..', 'legal', 'terms-of-service.md');
  if (fs.existsSync(termsPath)) {
    res.type('text/markdown').send(fs.readFileSync(termsPath, 'utf-8'));
  } else {
    res.status(404).json({ error: 'Terms not found' });
  }
});

// Skill file download
app.get('/skill', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'dropclaw-skill.json'));
});

// Tool definitions for agents
app.get('/openai-tools', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'openai-tools.json'));
});
app.get('/claude-tools', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'claude-tools.json'));
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'dropclaw',
    version: '1.0.0',
    uptime: process.uptime(),
    port: config.port,
    monadRpc: config.monad.rpc,
    walletConfigured: !!config.monad.privateKey,
    receiveAddresses: {
      monad: config.monad.receiveAddress ? 'configured' : 'missing',
      solana: config.solana.receiveAddress ? 'configured' : 'missing',
      base: config.base.receiveAddress ? 'configured' : 'missing',
    },
  });
});

// Ensure data directory exists
fs.mkdirSync(config.dataDir, { recursive: true });

// Restore upload jobs from disk (marks interrupted jobs as failed)
loadJobs();

// Start server
app.listen(config.port, '0.0.0.0', () => {
  console.log(`
  ____                   ____ _
 |  _ \\ _ __ ___  _ __  / ___| | __ ___      __
 | | | | '__/ _ \\| '_ \\| |   | |/ _\` \\ \\ /\\ / /
 | |_| | | | (_) | |_) | |___| | (_| |\\ V  V /
 |____/|_|  \\___/| .__/ \\____|_|\\__,_| \\_/\\_/
                 |_|

  x402 Encrypted On-Chain Storage for AI Agents

  Port:       ${config.port}
  Domain:     ${config.domain}
  Monad RPC:  ${config.monad.rpc}
  Wallet:     ${config.monad.receiveAddress || 'NOT CONFIGURED'}
  Fee:        $${config.SERVICE_FEE_USD} USD per upload
  Chunk Size: ${config.CHUNK_SIZE / 1024}KB

  Endpoints:
    POST /vault/store            — Store encrypted file ($${config.SERVICE_FEE_USD})
    POST /vault/store/zauth      — Store via zauth ($${config.SERVICE_FEE_USD + 5})
    POST /vault/store/pay        — Store via PayAI facilitator ($${config.SERVICE_FEE_USD})
    GET  /vault/status/:jobId    — Poll upload job progress
    GET  /vault/retrieve/:id     — Retrieve encrypted file (free)
    GET  /vault/pricing          — Cost estimates
    GET  /.well-known/x402       — Discovery manifest
    GET  /health                 — Health check
    GET  /skill                  — DropClaw skill file
    GET  /openai-tools           — OpenAI function definitions
    GET  /claude-tools           — Claude tool definitions

  Planet Express Marketplace:
    GET  /marketplace/listings   — Browse all listings (free)
    GET  /marketplace/listing/:id— Listing detail (free)
    POST /marketplace/purchase   — Purchase via x402 ($1 fee)
    POST /marketplace/list       — List file via x402 ($30 fee)
    GET  /marketplace/my-purchases — Facilitated purchases
  `);

  // Register with x402 Bazaar after server is ready (non-blocking)
  setTimeout(() => registerWithBazaar(), 3000);
});

module.exports = app;
