require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });
const { ethers } = require('ethers');

// Updates MarketplaceV2 listing fee (~$30) and buyer fee (~$1) in MON
// Run periodically to track MON price movements

const CONTRACT = '0xeFc5D4f6ee82849492b1F297134872dA2Abb260d';
const LISTING_FEE_USD = 30;
const BUYER_FEE_USD = 1;
const DRIFT_THRESHOLD = 0.15; // Only update if >15% drift
const ABI = [
  'function setFees(uint256 _listingFee, uint256 _buyerFee)',
  'function listingFee() view returns (uint256)',
  'function buyerFee() view returns (uint256)',
];

async function fetchMONPrice() {
  try {
    const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=monad&vs_currencies=usd');
    const data = await res.json();
    return data.monad?.usd || 0.023;
  } catch { return 0.023; }
}

async function main() {
  const rpc = process.env.MONAD_RPC || 'https://rpc.monad.xyz';
  const pk = process.env.MONAD_PRIVATE_KEY;
  if (!pk) { console.log('Missing MONAD_PRIVATE_KEY'); process.exit(1); }

  const provider = new ethers.JsonRpcProvider(rpc);
  const wallet = new ethers.Wallet(pk, provider);
  const contract = new ethers.Contract(CONTRACT, ABI, wallet);

  const monPrice = await fetchMONPrice();

  const currentListingFee = await contract.listingFee();
  const currentBuyerFee = await contract.buyerFee();
  const currentListingMON = parseFloat(ethers.formatEther(currentListingFee));
  const currentBuyerMON = parseFloat(ethers.formatEther(currentBuyerFee));
  const currentListingUSD = currentListingMON * monPrice;
  const currentBuyerUSD = currentBuyerMON * monPrice;

  const targetListingMON = Math.ceil(LISTING_FEE_USD / monPrice);
  const targetBuyerMON = Math.ceil(BUYER_FEE_USD / monPrice);

  console.log('MON price: $' + monPrice);
  console.log('Listing fee: ' + currentListingMON.toFixed(2) + ' MON (~$' + currentListingUSD.toFixed(2) + ') target: $' + LISTING_FEE_USD);
  console.log('Buyer fee: ' + currentBuyerMON.toFixed(2) + ' MON (~$' + currentBuyerUSD.toFixed(2) + ') target: $' + BUYER_FEE_USD);

  const listingDrift = Math.abs(currentListingUSD - LISTING_FEE_USD) / LISTING_FEE_USD;
  const buyerDrift = Math.abs(currentBuyerUSD - BUYER_FEE_USD) / BUYER_FEE_USD;
  console.log('Listing drift: ' + (listingDrift * 100).toFixed(1) + '%, Buyer drift: ' + (buyerDrift * 100).toFixed(1) + '%');

  if (listingDrift > DRIFT_THRESHOLD || buyerDrift > DRIFT_THRESHOLD) {
    console.log('Updating fees...');
    console.log('  Listing: ' + targetListingMON + ' MON (~$' + LISTING_FEE_USD + ')');
    console.log('  Buyer: ' + targetBuyerMON + ' MON (~$' + BUYER_FEE_USD + ')');

    const tx = await contract.setFees(
      ethers.parseEther(targetListingMON.toString()),
      ethers.parseEther(targetBuyerMON.toString())
    );
    console.log('TX: ' + tx.hash);
    await tx.wait();
    console.log('Fees updated successfully');
  } else {
    console.log('Within threshold, no update needed');
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
