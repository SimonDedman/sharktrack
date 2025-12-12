# SharkTrack Interactive Review Platform

## Overview

A citizen science platform for marine biodiversity research that transforms SharkTrack detection outputs into an interactive video review system. This platform would enable global collaboration between researchers, taxonomists, and marine scientists to validate AI detections while continuously improving model accuracy through human expertise.

## Core Concept

The platform builds on SharkTrack's existing detection capabilities (without requiring classifier.pt) by:

1. **Converting detection outputs** into a structured database format
2. **Creating an interactive web interface** for video review and annotation
3. **Implementing smart prioritisation** to serve clips in order of research value
4. **Establishing a feedback loop** to improve AI models through confirmed annotations
5. **Gamifying the review process** to encourage volunteer participation

## Technical Architecture

### Database Schema

```sql
-- Detection results from SharkTrack processing
CREATE TABLE detections (
    id UUID PRIMARY KEY,
    video_id UUID,
    track_id INTEGER,
    frame_number INTEGER,
    timestamp_ms INTEGER,
    confidence_score FLOAT,
    bounding_box JSONB,  -- {x, y, width, height}
    detection_features JSONB,  -- Raw model outputs, embeddings
    maxn_event BOOLEAN,
    created_at TIMESTAMP
);

-- Video metadata (from BRUV deployments)
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    file_path TEXT,
    location GEOGRAPHY(POINT),
    depth_m FLOAT,
    water_temperature FLOAT,
    visibility_m FLOAT,
    substrate_type TEXT,
    gear_type TEXT,  -- BRUV, ROV, etc
    deployment_duration INTEGER,
    gopro_version TEXT,
    deployment_date DATE,
    research_group TEXT,
    processed_at TIMESTAMP
);

-- Human annotations and confirmations
CREATE TABLE annotations (
    id UUID PRIMARY KEY,
    detection_id UUID REFERENCES detections(id),
    reviewer_id UUID,
    species TEXT,
    sex TEXT,
    individual_id TEXT,  -- For known individuals
    confidence_level INTEGER,  -- 1-5 reviewer confidence
    annotation_time_ms INTEGER,  -- Time spent reviewing
    behavioural_notes TEXT,
    interaction_events TEXT[],
    reviewed_at TIMESTAMP
);

-- Reviewer profiles and gamification
CREATE TABLE reviewers (
    id UUID PRIMARY KEY,
    username TEXT,
    email TEXT,
    institution TEXT,
    total_points INTEGER DEFAULT 0,
    accuracy_score FLOAT,
    specialisation TEXT[],  -- Areas of expertise
    geographic_focus TEXT[],  -- Preferred regions
    joined_at TIMESTAMP,
    last_active TIMESTAMP
);

-- Achievement tracking
CREATE TABLE achievements (
    id UUID PRIMARY KEY,
    reviewer_id UUID REFERENCES reviewers(id),
    achievement_type TEXT,
    description TEXT,
    points_awarded INTEGER,
    earned_at TIMESTAMP
);
```

### Smart Prioritisation System

```python
class ReviewPriority:
    def rank_detections(self, filters=None):
        """
        Rank detections for review based on:
        - Model uncertainty (confidence near decision boundary)
        - Rare species likelihood based on geographic context
        - Environmental context clustering
        - Expert availability and specialisation match
        - Research priority (new locations, unusual behaviours)
        """

    def suggest_next_clip(self, reviewer_id):
        """
        Suggest next clip based on:
        - Reviewer expertise and accuracy history
        - Current accuracy in similar environmental conditions
        - Learning objectives (new species, difficult conditions)
        - Time available for review session
        """

    def batch_similar_detections(self, detection_id):
        """
        Group similar detections for efficient batch review:
        - Same species in similar conditions
        - Same individual across multiple frames
        - Similar environmental context
        """
```

### Interactive Web Interface Features

**Video Player Components:**
- Frame-precise playback with detection overlay boxes
- Zoom and pan functionality for detailed examination
- Speed controls for behaviour analysis
- Timeline scrubbing with detection markers

**Review Tools:**
- Species dropdown with autocomplete and synonyms
- Confidence sliders for reviewer certainty
- Quick-tag buttons for common species
- Individual ID linking for known animals
- Behavioural annotation tools

**Context Panels:**
- Environmental metadata display
- Similar detections from nearby locations
- Species distribution maps
- Previous annotations for comparison
- Real-time model confidence explanations

**Collaboration Features:**
- Multi-reviewer consensus tracking
- Expert review requests for difficult cases
- Discussion threads for uncertain identifications
- Version control for annotation changes

## Machine Learning Feedback Loop

### Adaptive Learning Pipeline

```python
class AdaptiveLearning:
    def update_model_weights(self, confirmed_annotations):
        """
        Use confirmed annotations to:
        - Fine-tune species classification boundaries
        - Improve detection confidence calibration
        - Learn from systematic misclassifications
        - Weight expert reviewers based on accuracy history
        - Adapt to regional species variations
        """

    def active_learning_selection(self):
        """
        Identify clips that would most improve model performance:
        - High uncertainty detections
        - Rare species candidates
        - Novel environmental conditions
        - Geographic regions with limited training data
        """

    def model_performance_monitoring(self):
        """
        Track model performance metrics:
        - Accuracy trends over time
        - Performance by species and environment
        - Reviewer agreement rates
        - Regional accuracy variations
        """
```

### Continuous Improvement Strategy

1. **Daily model updates** using overnight annotation batches
2. **Regional specialisation** - models adapted for specific geographic areas
3. **Temporal adaptation** - account for seasonal species variations
4. **Expert weighting** - prioritise annotations from proven accurate reviewers
5. **Uncertainty quantification** - better model confidence estimates

## Gamification System

### Points Structure

**Basic Actions:**
- Species confirmation: 10 points
- Sex determination: 5 points
- Behavioural annotation: 15 points
- Individual ID linking: 25 points

**Difficulty Bonuses:**
- Rare species identification: +50 points
- Poor visibility conditions: +20 points
- Juvenile/difficult specimens: +30 points
- Novel behavioural observations: +100 points

**Quality Multipliers:**
- Expert consensus match: 2x points
- High reviewer confidence: 1.5x points
- Detailed annotations: 1.3x points

### Achievement System

**Expertise Badges:**
- "Eagle Eye": 95%+ accuracy on 100+ difficult detections
- "Deep Specialist": Expert in deep-water species (>50m)
- "Juvenile Expert": Specialised in identifying young animals
- "Behaviour Analyst": 500+ behavioural annotations

**Contribution Levels:**
- "Marine Cadet": 1,000 points
- "Reef Ranger": 5,000 points
- "Shark Guardian": 25,000 points
- "Ocean Ambassador": 100,000 points

**Regional Champions:**
- Top contributor per geographic region
- Seasonal challenges (e.g., "Migration Season")
- Research expedition partnerships

### Leaderboards

**Global Rankings:**
- All-time point leaders
- Monthly top contributors
- Species specialists by accuracy
- Regional champions

**Research Impact Metrics:**
- Papers enabled by annotations
- New species discoveries
- Conservation actions triggered
- Model improvement contributions

## Research Applications

### Immediate Benefits

**Scale and Efficiency:**
- Process thousands of hours of BRUV footage rapidly
- Standardised annotation protocols across research groups
- Real-time quality control and error detection
- Reduced manual review time for researchers

**Expert Knowledge Leverage:**
- Distributed expertise across global research community
- Consistent species identification standards
- Knowledge transfer from senior to junior researchers
- Rapid validation of unusual or rare sightings

### Long-term Research Vision

**Global Species Database:**
- Standardised marine life records across institutions
- Individual animal tracking across sites and years
- Migration pattern analysis at unprecedented scale
- Population dynamics monitoring in real-time

**Conservation Applications:**
- Rapid response alerts for unusual species sightings
- Real-time monitoring of marine protected areas
- Evidence base for policy and management decisions
- Public engagement and education platform

**Scientific Discovery:**
- Novel behavioural pattern recognition
- Species distribution change detection
- Climate change impact monitoring
- Ecosystem health indicators

## Implementation Roadmap

### Phase 1: Foundation (3-6 months)
1. **Database design and setup** with existing SharkTrack outputs
2. **Basic web interface** for video viewing and annotation
3. **Simple authentication** and user management
4. **Core annotation tools** for species identification

### Phase 2: Smart Features (6-12 months)
1. **Prioritisation algorithms** for detection ranking
2. **Expert matching** based on specialisation
3. **Basic gamification** with points and achievements
4. **Annotation quality metrics** and feedback

### Phase 3: Advanced Platform (1-2 years)
1. **Machine learning integration** for model improvement
2. **Advanced visualisation** and analysis tools
3. **Mobile application** for field researchers
4. **API development** for third-party integrations

### Phase 4: Community Growth (2+ years)
1. **Multi-language support** for global participation
2. **Educational partnerships** with schools and universities
3. **Citizen science expansion** beyond research community
4. **Integration with existing biodiversity platforms**

## Technical Requirements

### Infrastructure
- **Database**: PostgreSQL with PostGIS for spatial data
- **Backend**: Python/Django or Node.js/Express
- **Frontend**: React or Vue.js for interactive components
- **Video Storage**: Cloud storage with CDN for global access
- **Authentication**: OAuth integration with research institutions

### Performance Considerations
- **Video streaming optimisation** for various connection speeds
- **Caching strategies** for frequently accessed clips
- **Load balancing** for global user base
- **Offline capability** for field researchers

### Security and Privacy
- **Data access controls** based on research agreements
- **Anonymisation options** for sensitive locations
- **Audit trails** for all annotation changes
- **GDPR compliance** for international users

## Partnership Opportunities

### Research Institutions
- Marine biological research stations
- University marine science departments
- Government fisheries agencies
- Conservation organisations

### Technology Partners
- Cloud infrastructure providers
- Video streaming platforms
- Machine learning services
- Citizen science platforms

### Funding Sources
- Marine research grants
- Conservation foundation funding
- Technology company sponsorship
- Citizen science initiative grants

## Success Metrics

### Platform Metrics
- Number of active reviewers
- Annotations completed per month
- Model accuracy improvement over time
- User retention and engagement rates

### Research Impact
- Papers published using platform data
- New species or behaviours documented
- Conservation actions informed
- Research time savings quantified

### Community Building
- Geographic diversity of contributors
- Expert participation rates
- Educational institution partnerships
- Public engagement levels

## Conclusion

The SharkTrack Interactive Review Platform represents a paradigm shift in marine biodiversity research - from isolated research groups working with limited data to a global, collaborative ecosystem that leverages both artificial intelligence and distributed human expertise.

By combining SharkTrack's proven detection capabilities with modern web technologies and gamification principles, this platform could become the "Galaxy Zoo for marine life" - enabling unprecedented scale and accuracy in marine biodiversity monitoring while building a vibrant community of researchers, educators, and citizen scientists.

The platform's success would not only advance marine science but also demonstrate how AI-human collaboration can address complex environmental challenges at global scale.

---

**Document Created:** 2025-09-27
**Author:** Claude Code Session
**Status:** Conceptual Design
**Next Action:** Stakeholder consultation and prototype development