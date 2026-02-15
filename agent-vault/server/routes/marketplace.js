/**
 * Planet Express Marketplace — Server Routes
 *
 * Multi-chain payment support for the on-chain marketplace.
 * Accepts MON, SOL, Base USDC via x402 protocol.
 *
 * GET  /marketplace/listings       — Browse all listings (free)
 * GET  /marketplace/listing/:id    — Single listing detail (free)
 * POST /marketplace/purchase       — x402-gated purchase (listing price + $1 buyer fee)
 * POST /marketplace/list           — x402-gated listing creation ($30 listing fee)
 * GET  /marketplace/my-purchases   — Facilitated purchases by buyer address (free)
 */

const express = require('express');
const { ethers } = require('ethers');
const config = require('../config');
const { fetchPrices } = require('../services/priceFeed');
const monadVerifier = require('../services/verifiers/monadVerifier');
const solanaVerifier = require('../services/verifiers/solanaVerifier');
const baseVerifier = require('../services/verifiers/baseVerifier');
const purchaseLog = require('../services/purchaseLog');
const { queueSwap } = require('../services/paymentSwapper');

const router = express.Router();

// ═══════════ CONTRACT SETUP ═══════════
const CONTRACT_ADDRESS = '0xeFc5D4f6ee82849492b1F297134872dA2Abb260d';
const ABI = [
  "function listFile(string calldata _fileId, string calldata _title, string calldata _description, string calldata _skillFileUri, bytes32 _keyHash, uint256 _price) external payable returns (uint256)",
  "function purchase(uint256 _listingId) external payable",
  "function deliverKey(uint256 _listingId, string calldata _keyHex) external",
  "function claimRefund(uint256 _listingId) external",
  "function delistFile(uint256 _listingId) external",
  "function getListing(uint256 _listingId) external view returns (tuple(address seller, string fileId, string title, string description, string skillFileUri, bytes32 keyHash, uint256 price, uint256 createdAt, address buyer, uint256 purchasedAt, bool keyRevealed, bool refunded, bool active))",
  "function listingCount() external view returns (uint256)",
  "function listingFee() external view returns (uint256)",
  "function buyerFee() external view returns (uint256)",
  "function DELIVERY_FEE_BPS() external view returns (uint256)",
  "function KEY_DELIVERY_TIMEOUT() external view returns (uint256)",
  "event Listed(uint256 indexed listingId, address indexed seller, string fileId, string title, uint256 price)",
  "event Purchased(uint256 indexed listingId, address indexed buyer, uint256 price)",
  "event KeyRevealed(uint256 indexed listingId, string key)",
  "event Refunded(uint256 indexed listingId, address indexed buyer, uint256 amount)",
  "event Delisted(uint256 indexed listingId)",
];

const readProvider = new ethers.JsonRpcProvider(config.monad.rpc);
const readContract = new ethers.Contract(CONTRACT_ADDRESS, ABI, readProvider);

// Signer for proxy purchases/listings
let signerContract = null;
if (config.monad.privateKey) {
  const wallet = new ethers.Wallet(config.monad.privateKey, readProvider);
  signerContract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);
}

// ═══════════ PURCHASE LOCK ═══════════
const purchaseLocks = new Map();

// ═══════════ HELPERS ═══════════
function formatListing(id, l) {
  const status = l.refunded ? 'refunded'
    : l.keyRevealed ? 'delivered'
    : l.buyer !== ethers.ZeroAddress ? 'pending'
    : !l.active ? 'delisted'
    : 'available';
  return {
    id,
    seller: l.seller,
    fileId: l.fileId,
    title: l.title,
    description: l.description,
    skillFileUri: l.skillFileUri,
    price: ethers.formatEther(l.price),
    priceWei: l.price.toString(),
    createdAt: Number(l.createdAt),
    buyer: l.buyer === ethers.ZeroAddress ? null : l.buyer,
    purchasedAt: Number(l.purchasedAt),
    keyRevealed: l.keyRevealed,
    refunded: l.refunded,
    active: l.active,
    status,
  };
}

async function getMarketplacePricing(totalUSD) {
  const prices = await fetchPrices();
  return {
    totalUSD,
    totalMON: totalUSD / prices.mon,
    totalSOL: totalUSD / prices.sol,
    totalUSDC: totalUSD,
    prices,
  };
}

// ═══════════ x402 VERIFICATION ═══════════
async function verifyPayment(req, requiredUSD) {
  const paymentHeader = req.headers['x-payment'];
  if (!paymentHeader) return { needs402: true };

  const paymentData = JSON.parse(Buffer.from(paymentHeader, 'base64').toString('utf-8'));
  const { network, txHash } = paymentData;
  const pricing = await getMarketplacePricing(requiredUSD);

  let result;

  if (network === 'eip155:143' || network === 'monad') {
    const minWei = ethers.parseEther(pricing.totalMON.toFixed(8));
    result = await monadVerifier.verifyPayment(txHash, config.monad.receiveAddress, minWei);
    if (result.valid) {
      return { valid: true, chain: 'monad', payer: result.payer, amount: result.amount, txHash, pricing };
    }
  } else if (network === 'solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp' || network === 'solana') {
    const minLamports = Math.floor(pricing.totalSOL * 1e9);
    result = await solanaVerifier.verifyPayment(txHash, config.solana.receiveAddress, minLamports);
    if (result.valid) {
      return { valid: true, chain: 'solana', payer: result.payer, amount: result.amountLamports / 1e9, txHash, pricing };
    }
  } else if (network === 'eip155:8453' || network === 'base') {
    const minUSDC = Math.ceil(pricing.totalUSDC * 1e6);
    result = await baseVerifier.verifyPayment(txHash, config.base.receiveAddress, minUSDC);
    if (result.valid) {
      return { valid: true, chain: 'base', payer: result.payer, amount: result.amount, txHash, pricing };
    }
  } else {
    return { error: `Unsupported network: ${network}` };
  }

  return { error: result?.error || 'Payment verification failed' };
}

function send402(res, totalUSD, pricing, description) {
  const monAmountWei = ethers.parseEther(pricing.totalMON.toFixed(8)).toString();
  const solAmountLamports = Math.floor(pricing.totalSOL * 1e9).toString();
  const usdcAmount = Math.ceil(pricing.totalUSDC * 1e6).toString();

  res.status(402).json({
    x402Version: 2,
    resource: {
      url: `${config.domain}/marketplace/purchase`,
      method: 'POST',
      description,
    },
    accepts: [
      {
        scheme: 'exact',
        network: 'eip155:143',
        asset: 'native',
        payTo: config.monad.receiveAddress,
        maxAmountRequired: monAmountWei,
        extra: { service: 'planet-express-marketplace', totalUSD, tokenPrice: pricing.prices.mon },
      },
      {
        scheme: 'exact',
        network: 'solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp',
        asset: 'native',
        payTo: config.solana.receiveAddress,
        maxAmountRequired: solAmountLamports,
        extra: { service: 'planet-express-marketplace', totalUSD, tokenPrice: pricing.prices.sol },
      },
      {
        scheme: 'exact',
        network: 'eip155:8453',
        asset: config.base.usdcAddress,
        payTo: config.base.receiveAddress,
        maxAmountRequired: usdcAmount,
        extra: { service: 'planet-express-marketplace', totalUSD },
      },
    ],
  });
}

// ═══════════ ROUTES ═══════════

/**
 * GET /marketplace/listings — Browse all listings
 */
router.get('/listings', async (req, res) => {
  try {
    const count = Number(await readContract.listingCount());
    const prices = await fetchPrices();
    const listingFee = await readContract.listingFee();
    const buyerFee = await readContract.buyerFee();

    const listings = [];
    const promises = [];
    for (let i = 0; i < count; i++) {
      ((idx) => {
        promises.push(
          readContract.getListing(idx)
            .then(l => { listings[idx] = formatListing(idx, l); })
            .catch(() => { /* skip failed reads */ })
        );
      })(i);
    }
    await Promise.all(promises);

    res.json({
      listings: listings.filter(Boolean),
      contractAddress: CONTRACT_ADDRESS,
      listingFee: ethers.formatEther(listingFee),
      listingFeeUSD: parseFloat(ethers.formatEther(listingFee)) * prices.mon,
      buyerFee: ethers.formatEther(buyerFee),
      buyerFeeUSD: parseFloat(ethers.formatEther(buyerFee)) * prices.mon,
      prices,
    });
  } catch (e) {
    console.error('[Marketplace] Listings error:', e.message);
    res.status(500).json({ error: 'Failed to fetch listings' });
  }
});

/**
 * GET /marketplace/listing/:id — Single listing detail
 */
router.get('/listing/:id', async (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const l = await readContract.getListing(id);
    const prices = await fetchPrices();
    const buyerFee = await readContract.buyerFee();
    const listing = formatListing(id, l);

    const priceMON = parseFloat(listing.price);
    const buyerFeeMON = parseFloat(ethers.formatEther(buyerFee));
    const totalMON = priceMON + buyerFeeMON;
    const totalUSD = totalMON * prices.mon;

    // Check if this was a facilitated purchase
    const purchaseRecord = purchaseLog.getPurchase(id);

    res.json({
      ...listing,
      priceUSD: (priceMON * prices.mon).toFixed(2),
      buyerFee: buyerFeeMON.toFixed(4),
      buyerFeeUSD: (buyerFeeMON * prices.mon).toFixed(2),
      totalMON: totalMON.toFixed(4),
      totalSOL: (totalUSD / prices.sol).toFixed(6),
      totalUSDC: totalUSD.toFixed(2),
      totalUSD: totalUSD.toFixed(2),
      prices,
      contractAddress: CONTRACT_ADDRESS,
      facilitatedPurchase: purchaseRecord || null,
    });
  } catch (e) {
    console.error('[Marketplace] Listing detail error:', e.message);
    res.status(404).json({ error: 'Listing not found' });
  }
});

/**
 * POST /marketplace/purchase — x402-gated purchase
 * Body: { listingId, buyerAddress? }
 */
router.post('/purchase', async (req, res) => {
  try {
    const { listingId, buyerAddress } = req.body || {};
    if (listingId === undefined) {
      return res.status(400).json({ error: 'listingId required' });
    }

    // Get listing details and calculate total cost
    const listing = await readContract.getListing(listingId);
    if (listing.buyer !== ethers.ZeroAddress) {
      return res.status(409).json({ error: 'Listing already purchased' });
    }
    if (!listing.active) {
      return res.status(410).json({ error: 'Listing not active' });
    }

    const buyerFeeWei = await readContract.buyerFee();
    const priceMON = parseFloat(ethers.formatEther(listing.price));
    const buyerFeeMON = parseFloat(ethers.formatEther(buyerFeeWei));
    const totalMON = priceMON + buyerFeeMON;
    const prices = await fetchPrices();
    const totalUSD = totalMON * prices.mon;

    // x402 gate
    const payment = await verifyPayment(req, totalUSD);

    if (payment.needs402) {
      const pricing = await getMarketplacePricing(totalUSD);
      return send402(res, totalUSD, pricing,
        `Purchase listing #${listingId}: ${listing.title} (${priceMON.toFixed(4)} MON + $${(buyerFeeMON * prices.mon).toFixed(2)} fee)`
      );
    }

    if (payment.error) {
      return res.status(402).json({ error: payment.error });
    }

    // Acquire purchase lock
    if (purchaseLocks.has(listingId)) {
      return res.status(409).json({ error: 'Purchase in progress for this listing' });
    }
    purchaseLocks.set(listingId, Date.now());

    try {
      // Execute on-chain purchase from server wallet
      if (!signerContract) {
        return res.status(503).json({ error: 'Server wallet not configured' });
      }

      const totalWei = listing.price + buyerFeeWei;
      const tx = await signerContract.purchase(listingId, { value: totalWei });
      console.log(`[Marketplace] Purchase tx sent: ${tx.hash}`);
      const receipt = await tx.wait();
      console.log(`[Marketplace] Purchase confirmed: ${tx.hash}`);

      // Record the real buyer
      purchaseLog.recordPurchase(listingId, {
        realBuyer: buyerAddress || payment.payer,
        chain: payment.chain,
        paymentTxHash: payment.txHash,
        purchaseTxHash: tx.hash,
        listingPrice: priceMON.toFixed(4),
        buyerFeeUSD: (buyerFeeMON * prices.mon).toFixed(2),
        timestamp: new Date().toISOString(),
      });

      // Queue fee swap (50% to FARNS)
      try {
        queueSwap({
          chain: payment.chain,
          payer: payment.payer,
          amount: payment.amount,
          txHash: payment.txHash,
          purpose: 'marketplace-buyer-fee',
          feeAmount: buyerFeeMON * prices.mon,
        }, { totalGas: receipt.gasUsed.toString() });
      } catch (swapErr) {
        console.warn('[Marketplace] Fee swap queue failed:', swapErr.message);
      }

      res.json({
        success: true,
        listingId,
        purchaseTxHash: tx.hash,
        paymentChain: payment.chain,
        buyerFeeUSD: (buyerFeeMON * prices.mon).toFixed(2),
        message: 'Purchase complete. Key will be delivered by seller on-chain.',
      });
    } finally {
      purchaseLocks.delete(listingId);
    }
  } catch (e) {
    console.error('[Marketplace] Purchase error:', e.message);
    purchaseLocks.delete(req.body?.listingId);
    res.status(500).json({ error: 'Purchase failed: ' + e.message });
  }
});

/**
 * POST /marketplace/list — x402-gated listing creation
 * Body: { fileId, title, description, skillFileUri, keyHash, price }
 */
router.post('/list', async (req, res) => {
  try {
    const { fileId, title, description, skillFileUri, keyHash, price } = req.body || {};
    if (!fileId || !title || !keyHash || !price) {
      return res.status(400).json({ error: 'Missing required fields: fileId, title, keyHash, price' });
    }

    // Listing fee is $30 USD
    const listingFeeUSD = 30;

    // x402 gate
    const payment = await verifyPayment(req, listingFeeUSD);

    if (payment.needs402) {
      const pricing = await getMarketplacePricing(listingFeeUSD);
      return send402(res, listingFeeUSD, pricing,
        `List file "${title}" on Planet Express Marketplace ($${listingFeeUSD} listing fee)`
      );
    }

    if (payment.error) {
      return res.status(402).json({ error: payment.error });
    }

    if (!signerContract) {
      return res.status(503).json({ error: 'Server wallet not configured' });
    }

    // Get current on-chain listing fee
    const listingFeeWei = await readContract.listingFee();
    const priceWei = ethers.parseEther(price.toString());

    // Create listing on-chain (server pays listing fee)
    const tx = await signerContract.listFile(
      fileId, title, description || '', skillFileUri || '', keyHash, priceWei,
      { value: listingFeeWei }
    );
    console.log(`[Marketplace] List tx sent: ${tx.hash}`);
    const receipt = await tx.wait();

    // Parse Listed event to get listingId
    let listingId = null;
    for (const log of receipt.logs) {
      try {
        const parsed = readContract.interface.parseLog({ topics: log.topics, data: log.data });
        if (parsed && parsed.name === 'Listed') {
          listingId = Number(parsed.args.listingId);
          break;
        }
      } catch (e) { /* skip non-matching logs */ }
    }

    console.log(`[Marketplace] Listed #${listingId}: ${title}`);

    // Queue fee swap (50% to FARNS)
    try {
      queueSwap({
        chain: payment.chain,
        payer: payment.payer,
        amount: payment.amount,
        txHash: payment.txHash,
        purpose: 'marketplace-listing-fee',
        feeAmount: listingFeeUSD,
      }, { totalGas: receipt.gasUsed.toString() });
    } catch (swapErr) {
      console.warn('[Marketplace] Fee swap queue failed:', swapErr.message);
    }

    res.json({
      success: true,
      listingId,
      listTxHash: tx.hash,
      paymentChain: payment.chain,
      listingFeeUSD,
      message: 'Listing created successfully.',
    });
  } catch (e) {
    console.error('[Marketplace] List error:', e.message);
    res.status(500).json({ error: 'Listing failed: ' + e.message });
  }
});

/**
 * GET /marketplace/my-purchases — Facilitated purchases by buyer address
 */
router.get('/my-purchases', (req, res) => {
  const buyer = req.query.buyer;
  if (!buyer) return res.status(400).json({ error: 'buyer query param required' });
  res.json({ purchases: purchaseLog.getPurchasesByBuyer(buyer) });
});

module.exports = router;
