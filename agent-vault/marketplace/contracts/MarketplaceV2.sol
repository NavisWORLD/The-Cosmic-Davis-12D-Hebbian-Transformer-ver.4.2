// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * Planet Express Marketplace V2 — Decentralized File Marketplace
 *
 * Sellers list encrypted files for sale (pays listing fee).
 * Buyers purchase with MON (pays listing price + buyer fee).
 * Commit-reveal key exchange with escrow.
 * 50% of protocol fees go to treasury (FARNS buyback).
 */
contract MarketplaceV2 {
    // ═══════════ CONSTANTS ═══════════
    uint256 public constant DELIVERY_FEE_BPS = 250; // 2.5% on delivery
    uint256 public constant KEY_DELIVERY_TIMEOUT = 24 hours;

    // ═══════════ STATE ═══════════
    address payable public immutable treasury;
    uint256 public listingFee;  // MON wei — seller pays to list (~$30 equiv)
    uint256 public buyerFee;    // MON wei — buyer pays on top of price (~$1 equiv)

    struct Listing {
        address payable seller;
        string fileId;
        string title;
        string description;
        string skillFileUri;  // IPFS CID for skill file JSON
        bytes32 keyHash;      // keccak256(abi.encodePacked(keyHex))
        uint256 price;        // in wei (MON)
        uint256 createdAt;
        address buyer;
        uint256 purchasedAt;
        bool keyRevealed;
        bool refunded;
        bool active;
    }

    uint256 public listingCount;
    mapping(uint256 => Listing) public listings;

    // ═══════════ EVENTS ═══════════
    event Listed(
        uint256 indexed listingId,
        address indexed seller,
        string fileId,
        string title,
        uint256 price
    );
    event Purchased(
        uint256 indexed listingId,
        address indexed buyer,
        uint256 price
    );
    event KeyRevealed(
        uint256 indexed listingId,
        string key
    );
    event Refunded(
        uint256 indexed listingId,
        address indexed buyer,
        uint256 amount
    );
    event Delisted(
        uint256 indexed listingId
    );
    event FeesUpdated(
        uint256 newListingFee,
        uint256 newBuyerFee
    );

    // ═══════════ CONSTRUCTOR ═══════════
    constructor(
        address payable _treasury,
        uint256 _listingFee,
        uint256 _buyerFee
    ) {
        require(_treasury != address(0), "Invalid treasury");
        treasury = _treasury;
        listingFee = _listingFee;
        buyerFee = _buyerFee;
    }

    // ═══════════ MODIFIERS ═══════════
    modifier listingExists(uint256 _listingId) {
        require(_listingId < listingCount, "Listing does not exist");
        _;
    }

    modifier onlyTreasury() {
        require(msg.sender == treasury, "Only treasury");
        _;
    }

    // ═══════════ ADMIN ═══════════

    /**
     * @notice Update listing and buyer fees (treasury only)
     * @dev Call this periodically to keep fees aligned with USD targets
     */
    function setFees(uint256 _listingFee, uint256 _buyerFee) external onlyTreasury {
        listingFee = _listingFee;
        buyerFee = _buyerFee;
        emit FeesUpdated(_listingFee, _buyerFee);
    }

    // ═══════════ FUNCTIONS ═══════════

    /**
     * @notice List a file for sale — seller pays listing fee
     */
    function listFile(
        string calldata _fileId,
        string calldata _title,
        string calldata _description,
        string calldata _skillFileUri,
        bytes32 _keyHash,
        uint256 _price
    ) external payable returns (uint256) {
        require(bytes(_fileId).length > 0, "Empty fileId");
        require(bytes(_title).length > 0, "Empty title");
        require(_keyHash != bytes32(0), "Invalid keyHash");
        require(_price > 0, "Price must be > 0");
        require(msg.value >= listingFee, "Insufficient listing fee");

        // Send listing fee to treasury
        if (listingFee > 0) {
            (bool sent, ) = treasury.call{value: listingFee}("");
            require(sent, "Fee transfer failed");
        }

        // Refund excess
        uint256 excess = msg.value - listingFee;
        if (excess > 0) {
            (bool refunded, ) = payable(msg.sender).call{value: excess}("");
            require(refunded, "Refund failed");
        }

        uint256 listingId = listingCount;
        listings[listingId] = Listing({
            seller: payable(msg.sender),
            fileId: _fileId,
            title: _title,
            description: _description,
            skillFileUri: _skillFileUri,
            keyHash: _keyHash,
            price: _price,
            createdAt: block.timestamp,
            buyer: address(0),
            purchasedAt: 0,
            keyRevealed: false,
            refunded: false,
            active: true
        });

        listingCount++;
        emit Listed(listingId, msg.sender, _fileId, _title, _price);
        return listingId;
    }

    /**
     * @notice Purchase a listed file — buyer pays listing price + buyer fee
     */
    function purchase(uint256 _listingId) external payable listingExists(_listingId) {
        Listing storage l = listings[_listingId];
        require(l.active, "Listing not active");
        require(l.buyer == address(0), "Already purchased");
        require(msg.sender != l.seller, "Seller cannot buy own listing");

        uint256 totalRequired = l.price + buyerFee;
        require(msg.value >= totalRequired, "Insufficient payment");

        // Send buyer fee to treasury
        if (buyerFee > 0) {
            (bool sent, ) = treasury.call{value: buyerFee}("");
            require(sent, "Fee transfer failed");
        }

        // Refund excess
        uint256 excess = msg.value - totalRequired;
        if (excess > 0) {
            (bool refunded, ) = payable(msg.sender).call{value: excess}("");
            require(refunded, "Refund failed");
        }

        l.buyer = msg.sender;
        l.purchasedAt = block.timestamp;

        emit Purchased(_listingId, msg.sender, l.price);
    }

    /**
     * @notice Seller delivers the decryption key — reveal phase
     */
    function deliverKey(uint256 _listingId, string calldata _keyHex) external listingExists(_listingId) {
        Listing storage l = listings[_listingId];
        require(msg.sender == l.seller, "Only seller");
        require(l.buyer != address(0), "Not purchased");
        require(!l.keyRevealed, "Key already revealed");
        require(!l.refunded, "Already refunded");

        require(
            keccak256(abi.encodePacked(_keyHex)) == l.keyHash,
            "Key does not match committed hash"
        );

        l.keyRevealed = true;

        uint256 fee = (l.price * DELIVERY_FEE_BPS) / 10000;
        uint256 sellerPayout = l.price - fee;

        (bool sentSeller, ) = l.seller.call{value: sellerPayout}("");
        require(sentSeller, "Seller payment failed");

        if (fee > 0) {
            (bool sentTreasury, ) = treasury.call{value: fee}("");
            require(sentTreasury, "Treasury payment failed");
        }

        emit KeyRevealed(_listingId, _keyHex);
    }

    /**
     * @notice Buyer claims refund if seller doesn't deliver key within timeout
     */
    function claimRefund(uint256 _listingId) external listingExists(_listingId) {
        Listing storage l = listings[_listingId];
        require(msg.sender == l.buyer, "Only buyer");
        require(l.buyer != address(0), "Not purchased");
        require(!l.keyRevealed, "Key was delivered");
        require(!l.refunded, "Already refunded");
        require(
            block.timestamp >= l.purchasedAt + KEY_DELIVERY_TIMEOUT,
            "Timeout not reached"
        );

        l.refunded = true;

        // Refund listing price only (buyer fee is non-refundable)
        (bool sent, ) = payable(l.buyer).call{value: l.price}("");
        require(sent, "Refund failed");

        emit Refunded(_listingId, l.buyer, l.price);
    }

    /**
     * @notice Seller removes an unsold listing
     */
    function delistFile(uint256 _listingId) external listingExists(_listingId) {
        Listing storage l = listings[_listingId];
        require(msg.sender == l.seller, "Only seller");
        require(l.buyer == address(0), "Cannot delist after purchase");
        require(l.active, "Already delisted");

        l.active = false;
        emit Delisted(_listingId);
    }

    /**
     * @notice Get full listing details
     */
    function getListing(uint256 _listingId)
        external
        view
        listingExists(_listingId)
        returns (Listing memory)
    {
        return listings[_listingId];
    }
}
