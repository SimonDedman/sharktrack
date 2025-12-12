# Blockchain Infrastructure for Shark Knowledge Attribution

This document specifies the complete blockchain infrastructure for attributing contributions to marine species knowledge, implementing a Proof-of-Science consensus mechanism with token economics for research collaboration.

## System Architecture Overview

### Core Concept
A blockchain-based system that creates immutable records of scientific contributions to marine species knowledge, enabling researchers to receive attribution and rewards for their data contributions while building collective intelligence about ocean life.

### Technology Stack
- **Blockchain Platform**: Custom Ethereum-compatible chain (Polygon or BSC for lower costs)
- **Smart Contracts**: Solidity contracts for knowledge attribution and token economics
- **Consensus Mechanism**: Proof-of-Science (PoS) - Custom algorithm validating scientific contributions
- **Token Standard**: ERC-20 compatible "SHARK" tokens for research incentives
- **Storage**: IPFS for distributed storage of research data and metadata
- **Oracle Network**: Chainlink-compatible oracles for external data verification
- **API Layer**: GraphQL for blockchain data queries and research analytics

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Shark Knowledge Blockchain                     │
├─────────────────────────────────────────────────────────────────┤
│  Smart Contracts Layer                                         │
│  ├── SpeciesIntelligence.sol     (Living species models)       │
│  ├── KnowledgeAttribution.sol    (Contribution tracking)       │
│  ├── ProofOfScience.sol          (Consensus validation)        │
│  ├── ResearchToken.sol           (SHARK token economics)       │
│  └── ReputationSystem.sol        (Researcher credibility)      │
├─────────────────────────────────────────────────────────────────┤
│  Consensus & Validation Layer                                  │
│  ├── Validator Nodes             (Research institutions)       │
│  ├── Peer Review Oracle          (Scientific validation)       │
│  ├── Data Quality Scoring        (Contribution assessment)     │
│  └── Consensus Algorithm         (Proof-of-Science)           │
├─────────────────────────────────────────────────────────────────┤
│  Storage & Integration Layer                                   │
│  ├── IPFS Storage               (Distributed data)            │
│  ├── SharkTrack Integration     (AI detection results)        │
│  ├── Research Database          (Metadata indexing)           │
│  └── External Data Sources      (Environmental, taxonomic)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Smart Contract Implementation

### Core Species Intelligence Contract (`contracts/SpeciesIntelligence.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./interfaces/IKnowledgeAttribution.sol";
import "./interfaces/IResearchToken.sol";

/**
 * @title SpeciesIntelligence
 * @dev Manages living species models that evolve with contributions
 */
contract SpeciesIntelligence is AccessControl, ReentrancyGuard {
    using Counters for Counters.Counter;

    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    bytes32 public constant RESEARCHER_ROLE = keccak256("RESEARCHER_ROLE");

    struct Species {
        uint256 speciesId;
        string scientificName;
        string commonName;
        string taxonomicClassification;

        // Knowledge dimensions
        MorphologicalSpace morphology;
        BehaviouralSpace behaviour;
        EnvironmentalSpace environment;
        IndividualSpace individuals;

        // Model metadata
        uint256 totalContributions;
        uint256 lastUpdated;
        uint256 confidenceScore; // 0-10000 (basis points)
        bool isValidated;

        // Economic data
        uint256 totalValueLocked;
        uint256 contributorCount;
        mapping(address => uint256) contributorStakes;
    }

    struct MorphologicalSpace {
        // Physical characteristics as probability distributions
        SizeDistribution sizeRange;
        ColorPattern[] colorPatterns;
        BodyShape bodyShapeMetrics;
        uint256 morphologyConfidence;
        string[] identifyingFeatures;
    }

    struct BehaviouralSpace {
        // Behaviour patterns as temporal models
        MovementPattern[] movementPatterns;
        FeedingBehaviour[] feedingBehaviours;
        SocialStructure socialMetrics;
        SeasonalBehaviour[] seasonalPatterns;
        uint256 behaviourConfidence;
    }

    struct EnvironmentalSpace {
        // Ecological niche as multidimensional preference surface
        DepthRange preferredDepth;
        TemperatureRange temperatureRange;
        HabitatPreference[] habitats;
        GeographicDistribution[] distributions;
        uint256 environmentConfidence;
    }

    struct IndividualSpace {
        // Individual recognition and tracking
        uint256 recognizedIndividuals;
        BiometricModel[] biometricModels;
        LifeStageModels[] lifeStages;
        PopulationEstimates populationData;
        uint256 individualConfidence;
    }

    struct Contribution {
        uint256 contributionId;
        address contributor;
        uint256 speciesId;
        ContributionType contributionType;
        string ipfsHash; // Points to contribution data
        uint256 qualityScore; // Determined by peer review
        uint256 noveltyScore; // How new this information is
        uint256 timestamp;
        uint256 tokensAwarded;
        bool isValidated;
        address[] validators;
    }

    enum ContributionType {
        MORPHOLOGICAL,
        BEHAVIOURAL,
        ENVIRONMENTAL,
        INDIVIDUAL_IDENTIFICATION,
        POPULATION_DATA,
        GENETIC_DATA,
        VIDEO_ANALYSIS,
        ACOUSTIC_DATA
    }

    // State variables
    Counters.Counter private _speciesIds;
    Counters.Counter private _contributionIds;

    mapping(uint256 => Species) public species;
    mapping(uint256 => Contribution) public contributions;
    mapping(string => uint256) public scientificNameToId;
    mapping(address => uint256[]) public researcherContributions;
    mapping(uint256 => uint256[]) public speciesContributions;

    // Token and attribution contracts
    IKnowledgeAttribution public knowledgeAttribution;
    IResearchToken public researchToken;

    // Events
    event SpeciesCreated(uint256 indexed speciesId, string scientificName, address creator);
    event ContributionAdded(uint256 indexed contributionId, uint256 indexed speciesId, address contributor);
    event KnowledgeUpdated(uint256 indexed speciesId, ContributionType contributionType, uint256 qualityScore);
    event SpeciesValidated(uint256 indexed speciesId, address[] validators);
    event TokensAwarded(address indexed recipient, uint256 amount, uint256 contributionId);

    constructor(address _knowledgeAttribution, address _researchToken) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(VALIDATOR_ROLE, msg.sender);

        knowledgeAttribution = IKnowledgeAttribution(_knowledgeAttribution);
        researchToken = IResearchToken(_researchToken);
    }

    /**
     * @dev Create a new species model
     */
    function createSpecies(
        string memory _scientificName,
        string memory _commonName,
        string memory _taxonomicClassification,
        string memory _initialDataHash
    ) external onlyRole(RESEARCHER_ROLE) returns (uint256) {
        require(scientificNameToId[_scientificName] == 0, "Species already exists");

        _speciesIds.increment();
        uint256 newSpeciesId = _speciesIds.current();

        Species storage newSpecies = species[newSpeciesId];
        newSpecies.speciesId = newSpeciesId;
        newSpecies.scientificName = _scientificName;
        newSpecies.commonName = _commonName;
        newSpecies.taxonomicClassification = _taxonomicClassification;
        newSpecies.lastUpdated = block.timestamp;
        newSpecies.contributorCount = 1;

        scientificNameToId[_scientificName] = newSpeciesId;

        // Create initial contribution
        _addContribution(
            newSpeciesId,
            ContributionType.MORPHOLOGICAL,
            _initialDataHash,
            500, // Initial quality score
            1000  // High novelty for new species
        );

        emit SpeciesCreated(newSpeciesId, _scientificName, msg.sender);
        return newSpeciesId;
    }

    /**
     * @dev Add knowledge contribution to existing species
     */
    function addContribution(
        uint256 _speciesId,
        ContributionType _type,
        string memory _ipfsHash,
        uint256 _qualityScore,
        uint256 _noveltyScore
    ) external onlyRole(RESEARCHER_ROLE) {
        require(_speciesId <= _speciesIds.current() && _speciesId > 0, "Invalid species ID");
        require(_qualityScore <= 10000, "Quality score too high");
        require(_noveltyScore <= 10000, "Novelty score too high");

        _addContribution(_speciesId, _type, _ipfsHash, _qualityScore, _noveltyScore);
    }

    /**
     * @dev Internal function to add contribution
     */
    function _addContribution(
        uint256 _speciesId,
        ContributionType _type,
        string memory _ipfsHash,
        uint256 _qualityScore,
        uint256 _noveltyScore
    ) internal {
        _contributionIds.increment();
        uint256 newContributionId = _contributionIds.current();

        Contribution storage newContribution = contributions[newContributionId];
        newContribution.contributionId = newContributionId;
        newContribution.contributor = msg.sender;
        newContribution.speciesId = _speciesId;
        newContribution.contributionType = _type;
        newContribution.ipfsHash = _ipfsHash;
        newContribution.qualityScore = _qualityScore;
        newContribution.noveltyScore = _noveltyScore;
        newContribution.timestamp = block.timestamp;

        // Calculate token reward based on quality and novelty
        uint256 baseReward = 100 * 10**18; // 100 SHARK tokens base
        uint256 qualityMultiplier = (_qualityScore * 100) / 10000; // 0-100%
        uint256 noveltyMultiplier = (_noveltyScore * 100) / 10000; // 0-100%
        uint256 tokensAwarded = (baseReward * (100 + qualityMultiplier + noveltyMultiplier)) / 200;

        newContribution.tokensAwarded = tokensAwarded;

        // Update species model
        Species storage targetSpecies = species[_speciesId];
        targetSpecies.totalContributions++;
        targetSpecies.lastUpdated = block.timestamp;

        if (targetSpecies.contributorStakes[msg.sender] == 0) {
            targetSpecies.contributorCount++;
        }
        targetSpecies.contributorStakes[msg.sender] += tokensAwarded;
        targetSpecies.totalValueLocked += tokensAwarded;

        // Update knowledge dimension based on contribution type
        _updateKnowledgeDimension(_speciesId, _type, _qualityScore, _noveltyScore);

        // Track contributions
        researcherContributions[msg.sender].push(newContributionId);
        speciesContributions[_speciesId].push(newContributionId);

        // Award tokens through attribution contract
        knowledgeAttribution.recordContribution(
            msg.sender,
            _speciesId,
            newContributionId,
            tokensAwarded
        );

        // Mint tokens to contributor
        researchToken.mint(msg.sender, tokensAwarded);

        emit ContributionAdded(newContributionId, _speciesId, msg.sender);
        emit KnowledgeUpdated(_speciesId, _type, _qualityScore);
        emit TokensAwarded(msg.sender, tokensAwarded, newContributionId);
    }

    /**
     * @dev Update specific knowledge dimension
     */
    function _updateKnowledgeDimension(
        uint256 _speciesId,
        ContributionType _type,
        uint256 _qualityScore,
        uint256 _noveltyScore
    ) internal {
        Species storage targetSpecies = species[_speciesId];

        if (_type == ContributionType.MORPHOLOGICAL) {
            // Update morphological confidence weighted by quality
            uint256 currentConfidence = targetSpecies.morphology.morphologyConfidence;
            uint256 weightedUpdate = (_qualityScore * _noveltyScore) / 10000;
            targetSpecies.morphology.morphologyConfidence =
                (currentConfidence * 90 + weightedUpdate * 10) / 100;
        } else if (_type == ContributionType.BEHAVIOURAL) {
            uint256 currentConfidence = targetSpecies.behaviour.behaviourConfidence;
            uint256 weightedUpdate = (_qualityScore * _noveltyScore) / 10000;
            targetSpecies.behaviour.behaviourConfidence =
                (currentConfidence * 90 + weightedUpdate * 10) / 100;
        } else if (_type == ContributionType.ENVIRONMENTAL) {
            uint256 currentConfidence = targetSpecies.environment.environmentConfidence;
            uint256 weightedUpdate = (_qualityScore * _noveltyScore) / 10000;
            targetSpecies.environment.environmentConfidence =
                (currentConfidence * 90 + weightedUpdate * 10) / 100;
        } else if (_type == ContributionType.INDIVIDUAL_IDENTIFICATION) {
            uint256 currentConfidence = targetSpecies.individuals.individualConfidence;
            uint256 weightedUpdate = (_qualityScore * _noveltyScore) / 10000;
            targetSpecies.individuals.individualConfidence =
                (currentConfidence * 90 + weightedUpdate * 10) / 100;
        }

        // Update overall species confidence
        targetSpecies.confidenceScore = _calculateOverallConfidence(_speciesId);
    }

    /**
     * @dev Calculate overall species model confidence
     */
    function _calculateOverallConfidence(uint256 _speciesId) internal view returns (uint256) {
        Species storage targetSpecies = species[_speciesId];

        uint256 totalConfidence =
            targetSpecies.morphology.morphologyConfidence +
            targetSpecies.behaviour.behaviourConfidence +
            targetSpecies.environment.environmentConfidence +
            targetSpecies.individuals.individualConfidence;

        return totalConfidence / 4; // Average across dimensions
    }

    /**
     * @dev Validate species model through validator consensus
     */
    function validateSpecies(uint256 _speciesId, bool _isValid)
        external
        onlyRole(VALIDATOR_ROLE)
    {
        require(_speciesId <= _speciesIds.current() && _speciesId > 0, "Invalid species ID");

        Species storage targetSpecies = species[_speciesId];

        // Simple validation for now - could be enhanced with multi-signature
        targetSpecies.isValidated = _isValid;

        if (_isValid) {
            // Bonus tokens for validated species contributors
            uint256 bonusPool = targetSpecies.totalValueLocked / 10; // 10% bonus

            // Distribute bonus proportionally to contributors
            // Implementation would iterate through contributors

            emit SpeciesValidated(_speciesId, new address[](1));
        }
    }

    /**
     * @dev Get species information
     */
    function getSpecies(uint256 _speciesId) external view returns (
        string memory scientificName,
        string memory commonName,
        uint256 totalContributions,
        uint256 confidenceScore,
        bool isValidated,
        uint256 contributorCount
    ) {
        require(_speciesId <= _speciesIds.current() && _speciesId > 0, "Invalid species ID");

        Species storage targetSpecies = species[_speciesId];
        return (
            targetSpecies.scientificName,
            targetSpecies.commonName,
            targetSpecies.totalContributions,
            targetSpecies.confidenceScore,
            targetSpecies.isValidated,
            targetSpecies.contributorCount
        );
    }

    /**
     * @dev Get contributor's stake in species
     */
    function getContributorStake(uint256 _speciesId, address _contributor)
        external
        view
        returns (uint256)
    {
        return species[_speciesId].contributorStakes[_contributor];
    }

    /**
     * @dev Get total number of species
     */
    function getTotalSpecies() external view returns (uint256) {
        return _speciesIds.current();
    }

    /**
     * @dev Get researcher's contributions
     */
    function getResearcherContributions(address _researcher)
        external
        view
        returns (uint256[] memory)
    {
        return researcherContributions[_researcher];
    }
}
```

### Knowledge Attribution Contract (`contracts/KnowledgeAttribution.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title KnowledgeAttribution
 * @dev Tracks and attributes scientific contributions with immutable records
 */
contract KnowledgeAttribution is AccessControl, ReentrancyGuard {

    bytes32 public constant SPECIES_CONTRACT_ROLE = keccak256("SPECIES_CONTRACT_ROLE");

    struct Attribution {
        address contributor;
        uint256 speciesId;
        uint256 contributionId;
        uint256 tokensAwarded;
        uint256 timestamp;
        string ipfsHash; // Link to detailed contribution data
        bytes32 contributionHash; // Hash of contribution data for integrity
        bool isPeerReviewed;
        uint256 citationCount;
        uint256 replicationCount;
    }

    struct ContributorProfile {
        address contributorAddress;
        string name;
        string institution;
        string orcidId;
        uint256 totalContributions;
        uint256 totalTokensEarned;
        uint256 reputationScore;
        string[] specialties;
        bool isVerified;
    }

    struct Citation {
        uint256 citationId;
        uint256 originalContributionId;
        address citingResearcher;
        string citationContext; // DOI, paper reference, etc.
        uint256 timestamp;
    }

    // State variables
    mapping(uint256 => Attribution) public attributions;
    mapping(address => ContributorProfile) public contributorProfiles;
    mapping(address => uint256[]) public contributorAttributions;
    mapping(uint256 => Citation[]) public contributionCitations;
    mapping(bytes32 => bool) public usedContributionHashes;

    uint256 public totalAttributions;
    uint256 public totalCitations;

    // Events
    event ContributionRecorded(
        uint256 indexed contributionId,
        address indexed contributor,
        uint256 indexed speciesId,
        uint256 tokensAwarded
    );
    event ContributorVerified(address indexed contributor, string institution);
    event CitationAdded(
        uint256 indexed citationId,
        uint256 indexed originalContributionId,
        address indexed citingResearcher
    );
    event ReputationUpdated(address indexed contributor, uint256 newScore);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    /**
     * @dev Record a scientific contribution
     */
    function recordContribution(
        address _contributor,
        uint256 _speciesId,
        uint256 _contributionId,
        uint256 _tokensAwarded
    ) external onlyRole(SPECIES_CONTRACT_ROLE) {

        Attribution storage newAttribution = attributions[_contributionId];
        newAttribution.contributor = _contributor;
        newAttribution.speciesId = _speciesId;
        newAttribution.contributionId = _contributionId;
        newAttribution.tokensAwarded = _tokensAwarded;
        newAttribution.timestamp = block.timestamp;

        // Update contributor profile
        ContributorProfile storage profile = contributorProfiles[_contributor];
        profile.contributorAddress = _contributor;
        profile.totalContributions++;
        profile.totalTokensEarned += _tokensAwarded;

        // Track attributions
        contributorAttributions[_contributor].push(_contributionId);
        totalAttributions++;

        // Update reputation score
        _updateReputationScore(_contributor);

        emit ContributionRecorded(_contributionId, _contributor, _speciesId, _tokensAwarded);
    }

    /**
     * @dev Set detailed contribution metadata
     */
    function setContributionMetadata(
        uint256 _contributionId,
        string memory _ipfsHash,
        bytes32 _contributionHash
    ) external {
        Attribution storage attribution = attributions[_contributionId];
        require(attribution.contributor == msg.sender, "Not the contributor");
        require(!usedContributionHashes[_contributionHash], "Contribution hash already used");

        attribution.ipfsHash = _ipfsHash;
        attribution.contributionHash = _contributionHash;
        usedContributionHashes[_contributionHash] = true;
    }

    /**
     * @dev Verify a researcher's credentials
     */
    function verifyContributor(
        address _contributor,
        string memory _name,
        string memory _institution,
        string memory _orcidId
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        ContributorProfile storage profile = contributorProfiles[_contributor];
        profile.name = _name;
        profile.institution = _institution;
        profile.orcidId = _orcidId;
        profile.isVerified = true;

        emit ContributorVerified(_contributor, _institution);
    }

    /**
     * @dev Add citation to a contribution
     */
    function addCitation(
        uint256 _contributionId,
        string memory _citationContext
    ) external {
        require(attributions[_contributionId].contributor != address(0), "Contribution does not exist");

        Citation memory newCitation = Citation({
            citationId: totalCitations,
            originalContributionId: _contributionId,
            citingResearcher: msg.sender,
            citationContext: _citationContext,
            timestamp: block.timestamp
        });

        contributionCitations[_contributionId].push(newCitation);
        totalCitations++;

        // Update citation count
        attributions[_contributionId].citationCount++;

        // Award bonus tokens to original contributor for being cited
        address originalContributor = attributions[_contributionId].contributor;
        uint256 citationBonus = 10 * 10**18; // 10 SHARK tokens per citation

        // This would call the token contract to mint citation rewards
        // IResearchToken(researchTokenAddress).mint(originalContributor, citationBonus);

        emit CitationAdded(totalCitations - 1, _contributionId, msg.sender);
    }

    /**
     * @dev Update reputation score based on contributions and citations
     */
    function _updateReputationScore(address _contributor) internal {
        ContributorProfile storage profile = contributorProfiles[_contributor];

        // Calculate reputation based on:
        // 1. Number of contributions (weight: 30%)
        // 2. Total tokens earned (weight: 40%)
        // 3. Citation count (weight: 30%)

        uint256 contributionScore = profile.totalContributions * 100;
        uint256 tokenScore = profile.totalTokensEarned / (10**18); // Convert to whole tokens

        // Calculate total citations received
        uint256 totalCitationsReceived = 0;
        uint256[] memory userAttributions = contributorAttributions[_contributor];
        for (uint256 i = 0; i < userAttributions.length; i++) {
            totalCitationsReceived += attributions[userAttributions[i]].citationCount;
        }

        uint256 citationScore = totalCitationsReceived * 200; // Citations worth more

        // Weighted reputation score
        uint256 newReputationScore =
            (contributionScore * 30 + tokenScore * 40 + citationScore * 30) / 100;

        profile.reputationScore = newReputationScore;

        emit ReputationUpdated(_contributor, newReputationScore);
    }

    /**
     * @dev Get contribution details
     */
    function getAttribution(uint256 _contributionId) external view returns (
        address contributor,
        uint256 speciesId,
        uint256 tokensAwarded,
        uint256 timestamp,
        string memory ipfsHash,
        uint256 citationCount
    ) {
        Attribution memory attribution = attributions[_contributionId];
        return (
            attribution.contributor,
            attribution.speciesId,
            attribution.tokensAwarded,
            attribution.timestamp,
            attribution.ipfsHash,
            attribution.citationCount
        );
    }

    /**
     * @dev Get contributor profile
     */
    function getContributorProfile(address _contributor) external view returns (
        string memory name,
        string memory institution,
        uint256 totalContributions,
        uint256 totalTokensEarned,
        uint256 reputationScore,
        bool isVerified
    ) {
        ContributorProfile memory profile = contributorProfiles[_contributor];
        return (
            profile.name,
            profile.institution,
            profile.totalContributions,
            profile.totalTokensEarned,
            profile.reputationScore,
            profile.isVerified
        );
    }

    /**
     * @dev Get citations for a contribution
     */
    function getContributionCitations(uint256 _contributionId)
        external
        view
        returns (Citation[] memory)
    {
        return contributionCitations[_contributionId];
    }

    /**
     * @dev Get contributor's attribution IDs
     */
    function getContributorAttributions(address _contributor)
        external
        view
        returns (uint256[] memory)
    {
        return contributorAttributions[_contributor];
    }
}
```

### Research Token Contract (`contracts/ResearchToken.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title ResearchToken (SHARK)
 * @dev ERC20 token for incentivizing marine research contributions
 */
contract ResearchToken is ERC20, AccessControl, Pausable {

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // Token economics parameters
    uint256 public constant MAX_SUPPLY = 1000000000 * 10**18; // 1 billion SHARK tokens
    uint256 public constant RESEARCH_ALLOCATION = 600000000 * 10**18; // 60% for research
    uint256 public constant ECOSYSTEM_ALLOCATION = 200000000 * 10**18; // 20% for ecosystem
    uint256 public constant TEAM_ALLOCATION = 100000000 * 10**18; // 10% for team
    uint256 public constant COMMUNITY_ALLOCATION = 100000000 * 10**18; // 10% for community

    // Vesting and distribution tracking
    mapping(address => VestingSchedule) public vestingSchedules;
    mapping(address => uint256) public researcherEarnings;
    mapping(address => uint256) public institutionAllocations;

    struct VestingSchedule {
        uint256 totalAmount;
        uint256 startTime;
        uint256 cliffPeriod;
        uint256 vestingPeriod;
        uint256 releasedAmount;
    }

    // Research impact multipliers
    mapping(address => uint256) public impactMultipliers; // Basis points (10000 = 100%)

    // Governance parameters
    uint256 public researchInflationRate = 500; // 5% annually in basis points
    uint256 public lastInflationUpdate;

    // Events
    event ResearchTokensAwarded(address indexed researcher, uint256 amount, string reason);
    event InstitutionFunded(address indexed institution, uint256 amount);
    event VestingScheduleCreated(address indexed beneficiary, uint256 amount, uint256 startTime);
    event ImpactMultiplierUpdated(address indexed researcher, uint256 multiplier);

    constructor() ERC20("SharkTrack Research Token", "SHARK") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);

        lastInflationUpdate = block.timestamp;

        // Mint initial allocations to contract for controlled distribution
        _mint(address(this), ECOSYSTEM_ALLOCATION + TEAM_ALLOCATION + COMMUNITY_ALLOCATION);
    }

    /**
     * @dev Mint tokens for research contributions
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");

        // Apply impact multiplier if set
        if (impactMultipliers[to] > 0) {
            amount = (amount * impactMultipliers[to]) / 10000;
        }

        _mint(to, amount);
        researcherEarnings[to] += amount;

        emit ResearchTokensAwarded(to, amount, "Research contribution");
    }

    /**
     * @dev Create vesting schedule for team/advisor allocations
     */
    function createVestingSchedule(
        address beneficiary,
        uint256 amount,
        uint256 cliffPeriod,
        uint256 vestingPeriod
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(vestingSchedules[beneficiary].totalAmount == 0, "Vesting already exists");
        require(balanceOf(address(this)) >= amount, "Insufficient contract balance");

        vestingSchedules[beneficiary] = VestingSchedule({
            totalAmount: amount,
            startTime: block.timestamp,
            cliffPeriod: cliffPeriod,
            vestingPeriod: vestingPeriod,
            releasedAmount: 0
        });

        emit VestingScheduleCreated(beneficiary, amount, block.timestamp);
    }

    /**
     * @dev Release vested tokens
     */
    function releaseVestedTokens() external {
        VestingSchedule storage schedule = vestingSchedules[msg.sender];
        require(schedule.totalAmount > 0, "No vesting schedule");

        uint256 releasable = getReleasableAmount(msg.sender);
        require(releasable > 0, "No tokens to release");

        schedule.releasedAmount += releasable;
        _transfer(address(this), msg.sender, releasable);
    }

    /**
     * @dev Calculate releasable vested amount
     */
    function getReleasableAmount(address beneficiary) public view returns (uint256) {
        VestingSchedule memory schedule = vestingSchedules[beneficiary];

        if (block.timestamp < schedule.startTime + schedule.cliffPeriod) {
            return 0;
        }

        uint256 timeVested = block.timestamp - schedule.startTime;
        if (timeVested >= schedule.vestingPeriod) {
            return schedule.totalAmount - schedule.releasedAmount;
        }

        uint256 vestedAmount = (schedule.totalAmount * timeVested) / schedule.vestingPeriod;
        return vestedAmount - schedule.releasedAmount;
    }

    /**
     * @dev Set impact multiplier for high-impact researchers
     */
    function setImpactMultiplier(address researcher, uint256 multiplier)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        require(multiplier >= 5000 && multiplier <= 20000, "Multiplier out of range"); // 50%-200%
        impactMultipliers[researcher] = multiplier;

        emit ImpactMultiplierUpdated(researcher, multiplier);
    }

    /**
     * @dev Fund research institution
     */
    function fundInstitution(address institution, uint256 amount)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        require(balanceOf(address(this)) >= amount, "Insufficient contract balance");

        institutionAllocations[institution] += amount;
        _transfer(address(this), institution, amount);

        emit InstitutionFunded(institution, amount);
    }

    /**
     * @dev Apply annual research inflation
     */
    function applyResearchInflation() external {
        require(block.timestamp >= lastInflationUpdate + 365 days, "Too early for inflation");

        uint256 currentResearchSupply = RESEARCH_ALLOCATION;
        uint256 inflationAmount = (currentResearchSupply * researchInflationRate) / 10000;

        require(totalSupply() + inflationAmount <= MAX_SUPPLY, "Would exceed max supply");

        _mint(address(this), inflationAmount);
        lastInflationUpdate = block.timestamp;
    }

    /**
     * @dev Pause token transfers (emergency only)
     */
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /**
     * @dev Unpause token transfers
     */
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    /**
     * @dev Get researcher statistics
     */
    function getResearcherStats(address researcher) external view returns (
        uint256 totalEarned,
        uint256 currentBalance,
        uint256 impactMultiplier,
        uint256 vestedAmount,
        uint256 releasableVested
    ) {
        return (
            researcherEarnings[researcher],
            balanceOf(researcher),
            impactMultipliers[researcher],
            vestingSchedules[researcher].totalAmount,
            getReleasableAmount(researcher)
        );
    }

    /**
     * @dev Override transfer to respect pause
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual override {
        require(!paused(), "Token transfers paused");
        super._beforeTokenTransfer(from, to, amount);
    }
}
```

---

## Proof-of-Science Consensus Mechanism

### Consensus Validator (`contracts/ProofOfScience.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./interfaces/ISpeciesIntelligence.sol";
import "./interfaces/IKnowledgeAttribution.sol";

/**
 * @title ProofOfScience
 * @dev Consensus mechanism that validates scientific contributions
 */
contract ProofOfScience is AccessControl {

    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    bytes32 public constant INSTITUTION_ROLE = keccak256("INSTITUTION_ROLE");

    struct ValidationProposal {
        uint256 proposalId;
        uint256 contributionId;
        address proposer;
        string validationCriteria;
        uint256 proposedQualityScore;
        uint256 proposedNoveltyScore;

        // Voting data
        mapping(address => Vote) votes;
        address[] voters;
        uint256 votingDeadline;
        bool isExecuted;
        bool isPassed;

        // Peer review data
        string[] peerReviewHashes; // IPFS hashes of peer reviews
        uint256 totalReviewScore;
        uint256 reviewCount;
    }

    struct Vote {
        bool hasVoted;
        bool support;
        uint256 weight; // Based on validator's reputation
        string justification;
        uint256 timestamp;
    }

    struct Validator {
        address validatorAddress;
        string institution;
        string expertise; // JSON array of expertise areas
        uint256 reputation;
        uint256 validationsCompleted;
        uint256 successRate; // Percentage of successful validations
        bool isActive;
        uint256 lastActivityTime;
    }

    struct PeerReview {
        address reviewer;
        uint256 contributionId;
        string reviewHash; // IPFS hash of detailed review
        uint256 qualityScore; // 0-10000
        uint256 noveltyScore; // 0-10000
        uint256 reproducibilityScore; // 0-10000
        string methodology; // Review methodology used
        uint256 timestamp;
        bool isAnonymous;
    }

    // State variables
    mapping(uint256 => ValidationProposal) public validationProposals;
    mapping(address => Validator) public validators;
    mapping(uint256 => PeerReview[]) public contributionReviews;
    mapping(address => uint256[]) public validatorProposals;

    uint256 public totalProposals;
    uint256 public votingPeriod = 7 days;
    uint256 public minValidatorReputation = 1000;
    uint256 public requiredValidators = 3;

    ISpeciesIntelligence public speciesIntelligence;
    IKnowledgeAttribution public knowledgeAttribution;

    // Events
    event ValidatorAdded(address indexed validator, string institution);
    event ValidationProposed(uint256 indexed proposalId, uint256 contributionId, address proposer);
    event VoteCast(uint256 indexed proposalId, address indexed voter, bool support);
    event ProposalExecuted(uint256 indexed proposalId, bool passed);
    event PeerReviewSubmitted(uint256 indexed contributionId, address reviewer, uint256 qualityScore);
    event ValidatorReputationUpdated(address indexed validator, uint256 newReputation);

    constructor(address _speciesIntelligence, address _knowledgeAttribution) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);

        speciesIntelligence = ISpeciesIntelligence(_speciesIntelligence);
        knowledgeAttribution = IKnowledgeAttribution(_knowledgeAttribution);
    }

    /**
     * @dev Add a new validator to the network
     */
    function addValidator(
        address _validator,
        string memory _institution,
        string memory _expertise
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(validators[_validator].validatorAddress == address(0), "Validator already exists");

        validators[_validator] = Validator({
            validatorAddress: _validator,
            institution: _institution,
            expertise: _expertise,
            reputation: 1000, // Starting reputation
            validationsCompleted: 0,
            successRate: 100, // Starting at 100%
            isActive: true,
            lastActivityTime: block.timestamp
        });

        _grantRole(VALIDATOR_ROLE, _validator);
        emit ValidatorAdded(_validator, _institution);
    }

    /**
     * @dev Propose validation for a contribution
     */
    function proposeValidation(
        uint256 _contributionId,
        string memory _validationCriteria,
        uint256 _proposedQualityScore,
        uint256 _proposedNoveltyScore
    ) external onlyRole(VALIDATOR_ROLE) {
        require(_proposedQualityScore <= 10000, "Quality score too high");
        require(_proposedNoveltyScore <= 10000, "Novelty score too high");
        require(validators[msg.sender].isActive, "Validator not active");

        totalProposals++;
        uint256 proposalId = totalProposals;

        ValidationProposal storage proposal = validationProposals[proposalId];
        proposal.proposalId = proposalId;
        proposal.contributionId = _contributionId;
        proposal.proposer = msg.sender;
        proposal.validationCriteria = _validationCriteria;
        proposal.proposedQualityScore = _proposedQualityScore;
        proposal.proposedNoveltyScore = _proposedNoveltyScore;
        proposal.votingDeadline = block.timestamp + votingPeriod;

        validatorProposals[msg.sender].push(proposalId);

        emit ValidationProposed(proposalId, _contributionId, msg.sender);
    }

    /**
     * @dev Cast vote on validation proposal
     */
    function castVote(
        uint256 _proposalId,
        bool _support,
        string memory _justification
    ) external onlyRole(VALIDATOR_ROLE) {
        ValidationProposal storage proposal = validationProposals[_proposalId];
        require(block.timestamp <= proposal.votingDeadline, "Voting period ended");
        require(!proposal.votes[msg.sender].hasVoted, "Already voted");
        require(validators[msg.sender].isActive, "Validator not active");

        Validator storage validator = validators[msg.sender];

        proposal.votes[msg.sender] = Vote({
            hasVoted: true,
            support: _support,
            weight: _calculateVotingWeight(msg.sender),
            justification: _justification,
            timestamp: block.timestamp
        });

        proposal.voters.push(msg.sender);
        validator.lastActivityTime = block.timestamp;

        emit VoteCast(_proposalId, msg.sender, _support);

        // Auto-execute if enough votes
        if (proposal.voters.length >= requiredValidators) {
            _executeProposal(_proposalId);
        }
    }

    /**
     * @dev Submit peer review for contribution
     */
    function submitPeerReview(
        uint256 _contributionId,
        string memory _reviewHash,
        uint256 _qualityScore,
        uint256 _noveltyScore,
        uint256 _reproducibilityScore,
        string memory _methodology,
        bool _isAnonymous
    ) external onlyRole(VALIDATOR_ROLE) {
        require(_qualityScore <= 10000, "Quality score too high");
        require(_noveltyScore <= 10000, "Novelty score too high");
        require(_reproducibilityScore <= 10000, "Reproducibility score too high");

        PeerReview memory review = PeerReview({
            reviewer: _isAnonymous ? address(0) : msg.sender,
            contributionId: _contributionId,
            reviewHash: _reviewHash,
            qualityScore: _qualityScore,
            noveltyScore: _noveltyScore,
            reproducibilityScore: _reproducibilityScore,
            methodology: _methodology,
            timestamp: block.timestamp,
            isAnonymous: _isAnonymous
        });

        contributionReviews[_contributionId].push(review);

        // Update validator activity
        validators[msg.sender].lastActivityTime = block.timestamp;

        emit PeerReviewSubmitted(_contributionId, msg.sender, _qualityScore);
    }

    /**
     * @dev Execute validation proposal
     */
    function executeProposal(uint256 _proposalId) external {
        ValidationProposal storage proposal = validationProposals[_proposalId];
        require(block.timestamp > proposal.votingDeadline, "Voting still active");
        require(!proposal.isExecuted, "Already executed");

        _executeProposal(_proposalId);
    }

    /**
     * @dev Internal function to execute proposal
     */
    function _executeProposal(uint256 _proposalId) internal {
        ValidationProposal storage proposal = validationProposals[_proposalId];

        (bool passed, uint256 supportWeight, uint256 totalWeight) = _calculateVoteResult(_proposalId);

        proposal.isExecuted = true;
        proposal.isPassed = passed;

        if (passed) {
            // Update reputation scores for validators who voted correctly
            _updateValidatorReputations(_proposalId, true);

            // Update contribution scores in species intelligence contract
            // This would call the species contract to update quality/novelty scores
        } else {
            // Update reputation scores for validators who voted correctly
            _updateValidatorReputations(_proposalId, false);
        }

        emit ProposalExecuted(_proposalId, passed);
    }

    /**
     * @dev Calculate voting result
     */
    function _calculateVoteResult(uint256 _proposalId)
        internal
        view
        returns (bool passed, uint256 supportWeight, uint256 totalWeight)
    {
        ValidationProposal storage proposal = validationProposals[_proposalId];

        uint256 support = 0;
        uint256 total = 0;

        for (uint256 i = 0; i < proposal.voters.length; i++) {
            address voter = proposal.voters[i];
            Vote memory vote = proposal.votes[voter];

            total += vote.weight;
            if (vote.support) {
                support += vote.weight;
            }
        }

        // Require 60% support to pass
        bool result = (support * 100) / total >= 60;
        return (result, support, total);
    }

    /**
     * @dev Calculate voting weight based on validator reputation
     */
    function _calculateVotingWeight(address _validator) internal view returns (uint256) {
        Validator memory validator = validators[_validator];

        // Base weight from reputation
        uint256 baseWeight = validator.reputation / 100; // 1000 rep = 10 weight

        // Bonus for high success rate
        uint256 successBonus = validator.successRate / 10; // 100% = 10 bonus

        // Bonus for recent activity (anti-aging mechanism)
        uint256 activityBonus = 0;
        if (block.timestamp - validator.lastActivityTime < 30 days) {
            activityBonus = 5;
        }

        return baseWeight + successBonus + activityBonus;
    }

    /**
     * @dev Update validator reputations based on vote outcomes
     */
    function _updateValidatorReputations(uint256 _proposalId, bool proposalPassed) internal {
        ValidationProposal storage proposal = validationProposals[_proposalId];

        for (uint256 i = 0; i < proposal.voters.length; i++) {
            address voter = proposal.voters[i];
            Vote memory vote = proposal.votes[voter];
            Validator storage validator = validators[voter];

            if (vote.support == proposalPassed) {
                // Correct vote - increase reputation
                validator.reputation += 50;
                validator.successRate =
                    (validator.successRate * validator.validationsCompleted + 100) /
                    (validator.validationsCompleted + 1);
            } else {
                // Incorrect vote - decrease reputation
                if (validator.reputation > 50) {
                    validator.reputation -= 50;
                }
                validator.successRate =
                    (validator.successRate * validator.validationsCompleted) /
                    (validator.validationsCompleted + 1);
            }

            validator.validationsCompleted++;

            // Deactivate validator if reputation too low
            if (validator.reputation < minValidatorReputation) {
                validator.isActive = false;
            }

            emit ValidatorReputationUpdated(voter, validator.reputation);
        }
    }

    /**
     * @dev Get proposal details
     */
    function getProposal(uint256 _proposalId) external view returns (
        uint256 contributionId,
        address proposer,
        uint256 proposedQualityScore,
        uint256 proposedNoveltyScore,
        uint256 votingDeadline,
        bool isExecuted,
        bool isPassed,
        uint256 voterCount
    ) {
        ValidationProposal storage proposal = validationProposals[_proposalId];
        return (
            proposal.contributionId,
            proposal.proposer,
            proposal.proposedQualityScore,
            proposal.proposedNoveltyScore,
            proposal.votingDeadline,
            proposal.isExecuted,
            proposal.isPassed,
            proposal.voters.length
        );
    }

    /**
     * @dev Get validator information
     */
    function getValidator(address _validator) external view returns (
        string memory institution,
        uint256 reputation,
        uint256 validationsCompleted,
        uint256 successRate,
        bool isActive
    ) {
        Validator memory validator = validators[_validator];
        return (
            validator.institution,
            validator.reputation,
            validator.validationsCompleted,
            validator.successRate,
            validator.isActive
        );
    }

    /**
     * @dev Get peer reviews for contribution
     */
    function getContributionReviews(uint256 _contributionId)
        external
        view
        returns (PeerReview[] memory)
    {
        return contributionReviews[_contributionId];
    }
}
```

---

## Hybrid Model Distribution Architecture

### Blockchain-Centered Attribution with Distributed Storage

The SharkTrack blockchain serves as the **attribution layer** in a hybrid architecture that optimizes for both decentralization and performance. Rather than storing large model files on-chain, the blockchain maintains registries and attribution records while leveraging multiple storage layers for efficient content delivery.

### Updated Storage Architecture

```javascript
// Enhanced model registry with hybrid distribution
contract ModelRegistry {
    struct ModelVersion {
        string ipfsHash;           // IPFS content identifier
        string gitLFSPointer;      // GitHub LFS reference
        bytes32 torrentHash;       // BitTorrent infohash
        address contributor;       // Researcher wallet address
        uint256 accuracyScore;     // Performance metrics (basis points)
        uint256 timestamp;         // Submission time
        string[] regions;          // Geographic coverage areas
        uint256 downloadCount;     // Usage tracking
        string cdnUrls;           // CDN mirror locations
        mapping(address => uint256) votes;  // Peer validation
    }

    mapping(bytes32 => ModelVersion) public models;
    mapping(address => uint256) public contributorTokens;

    event ModelRegistered(
        bytes32 indexed modelId,
        address indexed contributor,
        string ipfsHash,
        string gitLFSPointer,
        uint256 accuracyScore
    );

    event ModelDownloaded(
        bytes32 indexed modelId,
        address indexed user,
        string distributionMethod
    );
}
```

### Multi-Layer Distribution Strategy

#### **1. Blockchain Layer - Attribution & Registry**
```solidity
function registerModel(
    string memory _modelName,
    string memory _ipfsHash,
    string memory _gitLFSPointer,
    bytes32 _torrentHash,
    uint256 _accuracyScore,
    string[] memory _regions,
    string memory _cdnUrls
) external {
    bytes32 modelId = keccak256(abi.encodePacked(_modelName, block.timestamp));

    ModelVersion storage newModel = models[modelId];
    newModel.ipfsHash = _ipfsHash;
    newModel.gitLFSPointer = _gitLFSPointer;
    newModel.torrentHash = _torrentHash;
    newModel.contributor = msg.sender;
    newModel.accuracyScore = _accuracyScore;
    newModel.timestamp = block.timestamp;
    newModel.regions = _regions;
    newModel.cdnUrls = _cdnUrls;

    // Award tokens based on model quality and novelty
    uint256 reward = calculateModelReward(_accuracyScore, _regions.length);
    contributorTokens[msg.sender] += reward;

    emit ModelRegistered(modelId, msg.sender, _ipfsHash, _gitLFSPointer, _accuracyScore);
}

function recordDownload(bytes32 _modelId, string memory _distributionMethod) external {
    models[_modelId].downloadCount++;
    emit ModelDownloaded(_modelId, msg.sender, _distributionMethod);

    // Micro-rewards for popular models
    address contributor = models[_modelId].contributor;
    contributorTokens[contributor] += 1; // 1 token per download
}
```

#### **2. Integration Service with Fallback Strategy**

```javascript
class HybridModelDistribution {
    constructor(config) {
        this.blockchain = new ethers.Contract(config.registryAddress, abi, provider);
        this.ipfs = IPFS.create(config.ipfs);
        this.torrentClient = new WebTorrent();
        this.cdnBase = config.cdnBase;
    }

    async downloadModel(modelId, preferredMethod = 'auto') {
        const modelInfo = await this.blockchain.models(modelId);

        const distributionStrategies = {
            'fast': () => this.downloadFromCDN(modelInfo.cdnUrls),
            'reliable': () => this.downloadFromGitLFS(modelInfo.gitLFSPointer),
            'decentralized': () => this.downloadFromIPFS(modelInfo.ipfsHash),
            'p2p': () => this.downloadFromTorrent(modelInfo.torrentHash),
            'auto': () => this.smartDownload(modelInfo)
        };

        try {
            const modelData = await distributionStrategies[preferredMethod]();

            // Record download on blockchain for attribution
            await this.blockchain.recordDownload(modelId, preferredMethod);

            return modelData;
        } catch (error) {
            console.log(`${preferredMethod} failed, trying fallback strategies...`);
            return this.downloadWithFallbacks(modelInfo);
        }
    }

    async smartDownload(modelInfo) {
        // Intelligent routing based on user context
        const userRegion = await this.detectUserRegion();
        const networkSpeed = await this.testNetworkSpeed();
        const modelSize = await this.getModelSize(modelInfo.ipfsHash);

        if (modelSize < 50_000_000 && networkSpeed > 10_000_000) {
            // Small models or fast connections: direct CDN
            return this.downloadFromCDN(modelInfo.cdnUrls);
        } else if (this.isInRegion(userRegion, modelInfo.regions)) {
            // Regional models: Git LFS for reliability
            return this.downloadFromGitLFS(modelInfo.gitLFSPointer);
        } else {
            // Large models or slow connections: P2P torrent
            return this.downloadFromTorrent(modelInfo.torrentHash);
        }
    }

    async downloadWithFallbacks(modelInfo) {
        const strategies = [
            () => this.downloadFromCDN(modelInfo.cdnUrls),
            () => this.downloadFromGitLFS(modelInfo.gitLFSPointer),
            () => this.downloadFromIPFS(modelInfo.ipfsHash),
            () => this.downloadFromTorrent(modelInfo.torrentHash)
        ];

        for (const strategy of strategies) {
            try {
                return await strategy();
            } catch (error) {
                console.log(`Strategy failed:`, error.message);
                continue;
            }
        }

        throw new Error('All distribution methods failed');
    }
}
```

### Integration with SharkTrack Platform

```javascript
// Updated SharkTrack integration
class BlockchainIntegrationService {
    constructor(config) {
        this.config = config;
        this.provider = new ethers.providers.JsonRpcProvider(config.rpcUrl);
        this.wallet = new ethers.Wallet(config.privateKey, this.provider);
        this.modelDistribution = new HybridModelDistribution(config);

        // Initialize contract instances
        this.initializeContracts();
    }

    async initializeContracts() {
        const speciesABI = JSON.parse(await fs.readFile('./abis/SpeciesIntelligence.json'));
        const attributionABI = JSON.parse(await fs.readFile('./abis/KnowledgeAttribution.json'));
        const tokenABI = JSON.parse(await fs.readFile('./abis/ResearchToken.json'));

        this.speciesContract = new ethers.Contract(
            this.config.contracts.speciesIntelligence,
            speciesABI,
            this.wallet
        );

        this.attributionContract = new ethers.Contract(
            this.config.contracts.knowledgeAttribution,
            attributionABI,
            this.wallet
        );

        this.tokenContract = new ethers.Contract(
            this.config.contracts.researchToken,
            tokenABI,
            this.wallet
        );
    }

    /**
     * Process SharkTrack results and create blockchain records
     */
    async processSharkTrackResults(videoAnalysisResult, researcherAddress) {
        try {
            // Upload detailed results to IPFS
            const ipfsHash = await this.uploadToIPFS(videoAnalysisResult);

            // Determine species or create new one
            const speciesId = await this.getOrCreateSpecies(
                videoAnalysisResult.detectedSpecies,
                researcherAddress
            );

            // Calculate contribution quality and novelty scores
            const scores = await this.calculateContributionScores(videoAnalysisResult);

            // Add contribution to blockchain
            const contributionTx = await this.speciesContract.addContribution(
                speciesId,
                this.getContributionType(videoAnalysisResult.analysisType),
                ipfsHash,
                scores.qualityScore,
                scores.noveltyScore
            );

            await contributionTx.wait();

            // Record attribution
            const contributionId = await this.getLatestContributionId();
            await this.recordAttribution(
                researcherAddress,
                speciesId,
                contributionId,
                videoAnalysisResult
            );

            console.log(`Blockchain record created for contribution ${contributionId}`);

            return {
                success: true,
                contributionId,
                speciesId,
                ipfsHash,
                tokensAwarded: scores.tokensAwarded,
                transactionHash: contributionTx.hash
            };

        } catch (error) {
            console.error('Blockchain integration error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Upload data to IPFS
     */
    async uploadToIPFS(data) {
        try {
            const result = await this.ipfs.add(JSON.stringify(data, null, 2));
            console.log(`Data uploaded to IPFS: ${result.path}`);
            return result.path;
        } catch (error) {
            console.error('IPFS upload error:', error);
            throw new Error('Failed to upload to IPFS');
        }
    }

    /**
     * Get existing species or create new one
     */
    async getOrCreateSpecies(detectedSpecies, researcherAddress) {
        try {
            // Check if species exists
            const speciesId = await this.speciesContract.scientificNameToId(
                detectedSpecies.scientificName
            );

            if (speciesId.toNumber() > 0) {
                return speciesId.toNumber();
            }

            // Create new species
            const createTx = await this.speciesContract.createSpecies(
                detectedSpecies.scientificName,
                detectedSpecies.commonName || detectedSpecies.scientificName,
                detectedSpecies.taxonomicClassification || 'Elasmobranchii',
                await this.uploadToIPFS({
                    initialObservation: detectedSpecies,
                    observer: researcherAddress,
                    timestamp: new Date().toISOString()
                })
            );

            const receipt = await createTx.wait();
            const speciesCreatedEvent = receipt.events.find(e => e.event === 'SpeciesCreated');

            return speciesCreatedEvent.args.speciesId.toNumber();

        } catch (error) {
            console.error('Species creation error:', error);
            throw error;
        }
    }

    /**
     * Calculate contribution quality and novelty scores
     */
    async calculateContributionScores(analysisResult) {
        let qualityScore = 5000; // Base 50%
        let noveltyScore = 5000; // Base 50%

        // Quality factors
        if (analysisResult.confidence > 0.8) qualityScore += 1000;
        if (analysisResult.confidence > 0.9) qualityScore += 1000;
        if (analysisResult.trackCount > 5) qualityScore += 500;
        if (analysisResult.videoDuration > 300) qualityScore += 500; // 5+ minutes
        if (analysisResult.gpsData) qualityScore += 500;
        if (analysisResult.environmentalData) qualityScore += 500;

        // Novelty factors
        const speciesRarity = await this.calculateSpeciesRarity(analysisResult.detectedSpecies);
        noveltyScore += Math.min(speciesRarity * 100, 2000);

        const locationNovelty = await this.calculateLocationNovelty(analysisResult.location);
        noveltyScore += Math.min(locationNovelty * 50, 1000);

        // Behavior novelty
        if (analysisResult.behaviorAnalysis && analysisResult.behaviorAnalysis.novelBehaviors) {
            noveltyScore += 1000;
        }

        // Cap scores at maximum
        qualityScore = Math.min(qualityScore, 10000);
        noveltyScore = Math.min(noveltyScore, 10000);

        // Calculate token reward
        const baseReward = ethers.utils.parseEther("100"); // 100 SHARK
        const qualityMultiplier = qualityScore / 10000;
        const noveltyMultiplier = noveltyScore / 10000;
        const tokensAwarded = baseReward.mul(
            Math.floor((1 + qualityMultiplier + noveltyMultiplier) * 100)
        ).div(200);

        return {
            qualityScore,
            noveltyScore,
            tokensAwarded: tokensAwarded.toString()
        };
    }

    /**
     * Calculate species rarity score
     */
    async calculateSpeciesRarity(species) {
        try {
            // Query existing contributions for this species
            const speciesId = await this.speciesContract.scientificNameToId(
                species.scientificName
            );

            if (speciesId.toNumber() === 0) {
                return 100; // New species = maximum rarity
            }

            const speciesData = await this.speciesContract.getSpecies(speciesId);
            const contributionCount = speciesData.totalContributions.toNumber();

            // Rarity inversely proportional to existing contributions
            if (contributionCount < 5) return 80;
            if (contributionCount < 20) return 60;
            if (contributionCount < 50) return 40;
            if (contributionCount < 100) return 20;
            return 10;

        } catch (error) {
            console.error('Rarity calculation error:', error);
            return 50; // Default rarity
        }
    }

    /**
     * Calculate location novelty
     */
    async calculateLocationNovelty(location) {
        if (!location || !location.coordinates) {
            return 0;
        }

        // This would query existing contributions within a geographic radius
        // For now, return a placeholder based on coordinate precision
        const precision = location.coordinates.length;
        return Math.min(precision * 10, 100);
    }

    /**
     * Get contribution type enum value
     */
    getContributionType(analysisType) {
        const typeMap = {
            'morphological': 0,
            'behavioral': 1,
            'environmental': 2,
            'individual': 3,
            'population': 4,
            'genetic': 5,
            'video': 6,
            'acoustic': 7
        };

        return typeMap[analysisType] || 6; // Default to video analysis
    }

    /**
     * Record detailed attribution information
     */
    async recordAttribution(researcherAddress, speciesId, contributionId, analysisResult) {
        const detailedContribution = {
            contributor: researcherAddress,
            analysisResult,
            timestamp: new Date().toISOString(),
            methodology: 'SharkTrack AI Analysis',
            equipment: analysisResult.equipment || 'BRUV Camera System',
            location: analysisResult.location,
            environmentalConditions: analysisResult.environmentalData
        };

        const ipfsHash = await this.uploadToIPFS(detailedContribution);
        const contributionHash = ethers.utils.keccak256(
            ethers.utils.toUtf8Bytes(JSON.stringify(detailedContribution))
        );

        await this.attributionContract.setContributionMetadata(
            contributionId,
            ipfsHash,
            contributionHash
        );
    }

    /**
     * Get latest contribution ID
     */
    async getLatestContributionId() {
        // This would need to be implemented based on contract events or state
        const filter = this.speciesContract.filters.ContributionAdded();
        const events = await this.speciesContract.queryFilter(filter, -1000); // Last 1000 blocks

        if (events.length > 0) {
            return events[events.length - 1].args.contributionId.toNumber();
        }

        return 0;
    }

    /**
     * Get researcher profile and statistics
     */
    async getResearcherProfile(address) {
        try {
            const profile = await this.attributionContract.getContributorProfile(address);
            const tokenStats = await this.tokenContract.getResearcherStats(address);
            const contributions = await this.attributionContract.getContributorAttributions(address);

            return {
                name: profile.name,
                institution: profile.institution,
                totalContributions: profile.totalContributions.toNumber(),
                totalTokensEarned: ethers.utils.formatEther(profile.totalTokensEarned),
                reputationScore: profile.reputationScore.toNumber(),
                isVerified: profile.isVerified,
                currentBalance: ethers.utils.formatEther(tokenStats.currentBalance),
                impactMultiplier: tokenStats.impactMultiplier.toNumber(),
                contributions: contributions.map(c => c.toNumber())
            };
        } catch (error) {
            console.error('Profile retrieval error:', error);
            return null;
        }
    }

    /**
     * Verify researcher credentials
     */
    async verifyResearcher(address, name, institution, orcidId) {
        try {
            const tx = await this.attributionContract.verifyContributor(
                address,
                name,
                institution,
                orcidId
            );
            await tx.wait();
            return { success: true, transactionHash: tx.hash };
        } catch (error) {
            console.error('Verification error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get species intelligence summary
     */
    async getSpeciesIntelligence(speciesId) {
        try {
            const speciesData = await this.speciesContract.getSpecies(speciesId);
            const contributions = await this.attributionContract.getContributorAttributions(speciesId);

            return {
                scientificName: speciesData.scientificName,
                commonName: speciesData.commonName,
                totalContributions: speciesData.totalContributions.toNumber(),
                confidenceScore: speciesData.confidenceScore.toNumber(),
                isValidated: speciesData.isValidated,
                contributorCount: speciesData.contributorCount.toNumber(),
                lastUpdated: new Date(speciesData.lastUpdated.toNumber() * 1000),
                contributions: contributions.map(c => c.toNumber())
            };
        } catch (error) {
            console.error('Species intelligence error:', error);
            return null;
        }
    }
}

module.exports = BlockchainIntegrationService;
```

---

## Deployment and Configuration

### Deployment Script (`scripts/deploy.js`)

```javascript
const { ethers } = require('hardhat');

async function main() {
    console.log('Deploying SharkTrack Blockchain Infrastructure...');

    // Get deployer account
    const [deployer] = await ethers.getSigners();
    console.log('Deploying contracts with account:', deployer.address);
    console.log('Account balance:', (await deployer.getBalance()).toString());

    // Deploy Research Token
    console.log('\n1. Deploying Research Token...');
    const ResearchToken = await ethers.getContractFactory('ResearchToken');
    const researchToken = await ResearchToken.deploy();
    await researchToken.deployed();
    console.log('ResearchToken deployed to:', researchToken.address);

    // Deploy Knowledge Attribution
    console.log('\n2. Deploying Knowledge Attribution...');
    const KnowledgeAttribution = await ethers.getContractFactory('KnowledgeAttribution');
    const knowledgeAttribution = await KnowledgeAttribution.deploy();
    await knowledgeAttribution.deployed();
    console.log('KnowledgeAttribution deployed to:', knowledgeAttribution.address);

    // Deploy Species Intelligence
    console.log('\n3. Deploying Species Intelligence...');
    const SpeciesIntelligence = await ethers.getContractFactory('SpeciesIntelligence');
    const speciesIntelligence = await SpeciesIntelligence.deploy(
        knowledgeAttribution.address,
        researchToken.address
    );
    await speciesIntelligence.deployed();
    console.log('SpeciesIntelligence deployed to:', speciesIntelligence.address);

    // Deploy Proof of Science
    console.log('\n4. Deploying Proof of Science...');
    const ProofOfScience = await ethers.getContractFactory('ProofOfScience');
    const proofOfScience = await ProofOfScience.deploy(
        speciesIntelligence.address,
        knowledgeAttribution.address
    );
    await proofOfScience.deployed();
    console.log('ProofOfScience deployed to:', proofOfScience.address);

    // Set up permissions
    console.log('\n5. Setting up permissions...');

    // Grant minter role to species intelligence contract
    await researchToken.grantRole(
        await researchToken.MINTER_ROLE(),
        speciesIntelligence.address
    );
    console.log('✓ Granted MINTER_ROLE to SpeciesIntelligence');

    // Grant species contract role to species intelligence
    await knowledgeAttribution.grantRole(
        await knowledgeAttribution.SPECIES_CONTRACT_ROLE(),
        speciesIntelligence.address
    );
    console.log('✓ Granted SPECIES_CONTRACT_ROLE to SpeciesIntelligence');

    // Grant researcher role to deployer (for testing)
    await speciesIntelligence.grantRole(
        await speciesIntelligence.RESEARCHER_ROLE(),
        deployer.address
    );
    console.log('✓ Granted RESEARCHER_ROLE to deployer');

    // Grant validator role to deployer (for testing)
    await speciesIntelligence.grantRole(
        await speciesIntelligence.VALIDATOR_ROLE(),
        deployer.address
    );
    console.log('✓ Granted VALIDATOR_ROLE to deployer');

    // Verify deployment
    console.log('\n6. Verifying deployment...');
    const totalSupply = await researchToken.totalSupply();
    console.log('✓ ResearchToken total supply:', ethers.utils.formatEther(totalSupply));

    const totalSpecies = await speciesIntelligence.getTotalSpecies();
    console.log('✓ SpeciesIntelligence total species:', totalSpecies.toString());

    // Save deployment addresses
    const deploymentInfo = {
        network: await ethers.provider.getNetwork(),
        deployer: deployer.address,
        timestamp: new Date().toISOString(),
        contracts: {
            ResearchToken: researchToken.address,
            KnowledgeAttribution: knowledgeAttribution.address,
            SpeciesIntelligence: speciesIntelligence.address,
            ProofOfScience: proofOfScience.address
        },
        transactionHashes: {
            ResearchToken: researchToken.deployTransaction.hash,
            KnowledgeAttribution: knowledgeAttribution.deployTransaction.hash,
            SpeciesIntelligence: speciesIntelligence.deployTransaction.hash,
            ProofOfScience: proofOfScience.deployTransaction.hash
        }
    };

    console.log('\n7. Deployment Summary:');
    console.log(JSON.stringify(deploymentInfo, null, 2));

    // Save to file
    const fs = require('fs');
    fs.writeFileSync(
        `./deployments/${deploymentInfo.network.name}-${Date.now()}.json`,
        JSON.stringify(deploymentInfo, null, 2)
    );

    console.log('\n✅ Deployment completed successfully!');
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
```

### Configuration Files

#### Hardhat Configuration (`hardhat.config.js`)

```javascript
require('@nomiclabs/hardhat-ethers');
require('@nomiclabs/hardhat-waffle');
require('hardhat-gas-reporter');
require('solidity-coverage');
require('dotenv').config();

module.exports = {
    solidity: {
        version: '0.8.19',
        settings: {
            optimizer: {
                enabled: true,
                runs: 200
            }
        }
    },
    networks: {
        hardhat: {
            chainId: 1337
        },
        polygon: {
            url: process.env.POLYGON_RPC_URL,
            accounts: [process.env.PRIVATE_KEY],
            chainId: 137
        },
        mumbai: {
            url: process.env.MUMBAI_RPC_URL,
            accounts: [process.env.PRIVATE_KEY],
            chainId: 80001
        },
        bsc: {
            url: process.env.BSC_RPC_URL,
            accounts: [process.env.PRIVATE_KEY],
            chainId: 56
        }
    },
    gasReporter: {
        enabled: process.env.REPORT_GAS !== undefined,
        currency: 'USD'
    },
    paths: {
        sources: './contracts',
        tests: './test',
        cache: './cache',
        artifacts: './artifacts'
    }
};
```

#### Environment Configuration (`.env.example`)

```bash
# Network Configuration
POLYGON_RPC_URL=https://polygon-rpc.com
MUMBAI_RPC_URL=https://matic-mumbai.chainstacklabs.com
BSC_RPC_URL=https://bsc-dataseed.binance.org

# Deployment Account
PRIVATE_KEY=your_deployer_private_key_here

# IPFS Configuration
IPFS_HOST=localhost
IPFS_PORT=5001
IPFS_PROTOCOL=http

# API Keys
POLYGONSCAN_API_KEY=your_polygonscan_api_key
BSCSCAN_API_KEY=your_bscscan_api_key

# Application Configuration
RESEARCHER_REGISTRY_API=https://api.researcher-registry.org
ORCID_API_KEY=your_orcid_api_key

# Security
JWT_SECRET=your_jwt_secret_for_api_authentication
ENCRYPTION_KEY=your_encryption_key_for_sensitive_data
```

This blockchain infrastructure provides a complete foundation for attributing marine research contributions with cryptographic proof, token incentives, and collective intelligence building around marine species knowledge.
