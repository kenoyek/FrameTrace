# CODEX MASTER PROMPT — FRAMETRACE

World-Class AI Video Recognition Mobile Application · Android & iOS · Complete Product Engineering Specification

This is the comprehensive implementation prompt for FrameTrace, our proposed mobile equivalent of Shazam for videos.

The brief directs Codex to build a genuine, production-oriented mobile product—not just an attractive interface. It covers native video sharing, multimodal recognition, source discovery, a searchable media catalog, backend infrastructure, security, performance, and Play Store/App Store readiness.

I recommend React Native + Expo for the mobile application, FastAPI for recognition services, Supabase for authentication and relational data, and Cloudflare R2 for media storage.

One important technical consideration: Expo's receiving-shared-content functionality currently has experimental limitations on iOS. The prompt therefore requires Codex to assess and implement a compliant native share-extension approach rather than assuming that one plugin works reliably everywhere.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.expo.dev\&sz=32)

Expo documentation



# WORLD-CLASS CODEX MASTER BRIEF

# FRAMETRACE — UNIVERSAL VIDEO SHAZAM

**Product:** FrameTrace\
**Category:** Artificial Intelligence / Video Recognition / Content Discovery\
**Platforms:** Android and iOS\
**Product Type:** Native Mobile Application\
**Architecture:** Mobile-First, Cloud-Powered Recognition\
**Engineering Standard:** Production-Grade\
**Product Vision:** Identify the original source of almost any video clip.

---

# 1. YOUR ROLE AND RESPONSIBILITIES

Act as an elite multidisciplinary product engineering team consisting of:

- Principal Software Architect
- Senior React Native Engineer
- Senior Android Engineer
- Senior iOS Engineer
- AI/ML Research Engineer
- Computer Vision Engineer
- Audio Signal Processing Engineer
- Senior Python Backend Engineer
- Database and Search Infrastructure Engineer
- Cloud/DevOps Engineer
- Application Security Engineer
- Senior UI/UX Product Designer
- Quality Assurance and Automation Engineer
- Technical Product Manager

You are responsible for designing, implementing, testing, and documenting FrameTrace as a commercially viable, high-quality Android and iOS application.

Your objective is not to create a proof-of-concept interface.

Your objective is to build the foundation of a real mobile video recognition platform capable of identifying source videos using multimodal matching and a growing reference media database.

Take ownership of the engineering process.

Make technically sound decisions, explain important trade-offs, and implement working functionality.

**Do not fabricate AI recognition results, database records, processing success, deployment status, or completed test results.**

---

# 2. PRODUCT VISION

FrameTrace is a universal video identification application.

Users should be able to:

1. Find an interesting video clip on social media.
2. Share the video to FrameTrace or upload it from their device.
3. Allow FrameTrace to analyze the clip.
4. Identify its likely original source.
5. Discover the full movie, television episode, anime, interview, documentary, podcast, or other referenced media.
6. See the corresponding timestamp within the original recording.
7. Open an authorized source to watch the original video.
8. Save the discovery for future reference.

## Product positioning

FrameTrace should feel as intuitive as Shazam, but for video.

**Brand tagline: Every clip has a story. Find its source.**

Alternative supporting headline:

**See a clip. Find the original.**

The app should emphasize speed, accuracy, simplicity, and credibility.

The primary experience must be usable by someone with no technical knowledge.

---

# 3. PRODUCT STRATEGY

## Long-term vision

Create a universal video-source discovery ecosystem covering:

- Movies
- Television series
- Anime
- Documentaries
- Podcasts
- Interviews
- Viral social-media videos
- Educational videos
- Sports footage
- News footage
- Creator content
- Historical recordings

## MVP strategy

Do not attempt to index the entire internet initially.

Build a reliable recognition system against a controlled, legally usable reference catalog.

Prove recognition accuracy with a small dataset before expanding media coverage.

## Fundamental principle

Recognizing a visually similar video is not the same as proving its original source.

The system must distinguish between:

- Exact media matches
- Near-duplicate matches
- Matching segments within longer videos
- Semantically similar but unrelated footage
- Earliest known indexed upload
- Verified original publisher
- Verified rights holder
- Unknown source

Never claim to have identified an original creator when the available evidence only supports a matching or earlier indexed video.

---

# 4. REQUIRED TECHNOLOGY STACK

## Mobile application

Use:

- React Native
- Expo
- TypeScript
- Expo Router
- React Native Reanimated
- React Native Gesture Handler
- TanStack Query
- Zustand where appropriate
- Native media picker
- Native video playback
- Native share integrations
- Secure authentication storage
- EAS Build

Use Expo development builds when native integrations require them.

Do not rely on Expo Go for features that require native configuration.

Verify library compatibility and current SDK support before installation.

## Backend

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Redis
- Celery or Dramatiq
- Background processing workers
- OpenAPI contracts

## Database and authentication

Use Supabase for:

- PostgreSQL
- Authentication
- Row Level Security
- User profiles
- Recognition history
- App configuration
- Administrative records

## File storage

Use Cloudflare R2 for:

- Temporary query clips
- Authorized reference media
- Processing artifacts
- Thumbnail assets
- Short-lived signed access

## AI recognition

Use a hybrid architecture supporting:

- OpenCV
- FFmpeg
- PySceneDetect
- Perceptual image hashing
- Audio fingerprinting
- Speech recognition
- OCR
- Multimodal embeddings
- Vector similarity search
- Temporal sequence verification

Evaluate TwelveLabs or an equivalent video embedding service.

Implement providers behind interchangeable interfaces.

## Vector database

Begin with PostgreSQL and pgvector where practical.

Design a migration path to Qdrant if benchmarks demonstrate that a dedicated vector search service is advantageous.

Do not introduce unnecessary infrastructure complexity prematurely.

## Monitoring

Use:

- Structured logs
- Sentry
- OpenTelemetry
- Worker health metrics
- Recognition latency metrics
- Database performance monitoring
- Cost tracking

---

# 5. REPOSITORY STRUCTURE

Use a maintainable monorepo.

Suggested structure:

```
frametrace/
│
├── apps/
│   ├── mobile/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── theme/
│   │   └── assets/
│   │
│   └── admin/
│
├── services/
│   ├── api/
│   ├── recognition/
│   ├── ingestion/
│   └── workers/
│
├── packages/
│   ├── contracts/
│   ├── evaluation/
│   └── shared-config/
│
├── supabase/
│   └── migrations/
│
├── infrastructure/
│   ├── docker/
│   ├── deployment/
│   └── monitoring/
│
├── tests/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── recognition/
│   ├── privacy/
│   └── deployment/
│
└── .github/
    └── workflows/
```

There must be no public web application dependency for end users.

A restricted administrative interface is permitted for managing reference media and operations.

---

# 6. PREMIUM MOBILE UI/UX DESIGN

Create an extraordinary mobile product experience.

The design must be polished enough to compete with leading consumer applications.

## Visual philosophy

Use a premium cinematic design language.

Characteristics:

- Dark-first interface
- Deep midnight backgrounds
- Refined violet and electric-blue accents
- Subtle background gradients
- Elegant typography
- Sophisticated animations
- Premium iconography
- Carefully controlled spacing
- Soft shadows and translucent surfaces
- Smooth navigation transitions
- Accessible color contrast

Avoid:

- Generic AI-generated visual clutter
- Excessive glowing borders
- Oversized decorative cards
- Inconsistent spacing
- Unnecessary gradients
- Overcomplicated menus
- Excessive animation
- Poor keyboard behavior
- Screen overflow
- Unresponsive controls

## Design system

Create reusable design tokens:

- Background colors
- Surface colors
- Border colors
- Typography scales
- Spacing
- Corner radii
- Elevation
- Animation durations
- Icon sizes
- Component states

Implement both dark mode and light mode, but prioritize the dark experience.

Respect device system preferences and allow manual selection.

## Mobile quality

Support:

- Android edge-to-edge layouts
- iOS safe areas
- Dynamic Island and notched devices
- Variable screen sizes
- Accessibility font scaling
- Screen readers
- Reduced-motion preferences
- Haptic feedback
- Keyboard avoidance
- Portrait-first layouts
- Appropriate tablet adaptation

No content should be obscured by status bars, navigation bars, keyboards, or notches.

---

# 7. MOBILE APPLICATION SCREENS

## 7.1 Splash Screen

Create a sophisticated branded splash screen with:

- FrameTrace logo
- Brand mark
- Cinematic dark background
- Native splash configuration
- Fast application initialization

Avoid artificial startup delays.

## 7.2 Onboarding

Create a concise onboarding experience explaining:

1. Find a video.
2. Share or upload it.
3. Identify the source.
4. Watch the original.

Use polished illustrations or animations only where they improve clarity.

Provide a clear Skip option.

Do not force account creation before users understand the application.

## 7.3 Home Screen

This is the most important product screen.

Design an attractive, minimal home interface.

Primary headline:

**What video is this from?**

Supporting text:

**Upload a clip and discover its source.**

Primary action:

**Identify a Video**

Secondary actions:

- Choose from Gallery
- Import Shared Video
- Record a Clip
- View Recent Discoveries

The upload action should be visually dominant.

Show selected content categories without overwhelming the interface.

## 7.4 Video Selection

Support:

- MP4 and MOV where decodable
- Common supported video codecs
- Gallery selection
- Camera capture
- Video preview
- File metadata
- Duration validation
- File-size validation

MVP limit:

- Target 5–30-second clips
- Apply configurable server-enforced maximum upload size
- Explain unsupported formats clearly

Allow users to trim longer clips before uploading.

Do not require device-level full-library access when a limited media picker is sufficient.

## 7.5 Video Preview and Trimming

Implement:

- Video preview player
- Playback controls
- Timeline scrubbing
- Start/end selection
- Clip duration display
- Trim confirmation
- Cancel and retry controls

Where practical, perform trimming on-device to reduce network upload size.

Avoid requiring expensive on-device processing that is inconsistent across low-end devices.

## 7.6 Recognition Processing

Create an elegant analysis screen.

Display real processing stages:

- Preparing video
- Uploading
- Extracting features
- Searching reference catalog
- Verifying candidates
- Preparing results

Show genuine upload progress and meaningful processing state.

Do not invent percentage progress.

Allow users to leave the screen while processing continues on the server.

Provide a mechanism to resume or retrieve the result.

## 7.7 Recognition Results

Create a premium results experience.

Display:

- Matching video title
- Cover image or permitted thumbnail
- Media category
- Creator or publisher
- Episode/season information where applicable
- Production/release year where known
- Original video duration
- Match classification
- Matched timestamp
- Source links
- Evidence explanation

Primary action:

**Watch Original**

Additional actions:

- Save Result
- Share Result
- View Other Matches
- Report Incorrect Result

Do not generate a source link when one cannot be verified.

## 7.8 Alternative Matches

When results are ambiguous, display multiple candidates.

Show supporting evidence and explain uncertainty.

Do not automatically label the highest-scoring candidate as confirmed.

## 7.9 No-Match Screen

Create a meaningful failure experience.

Example:

**We couldn't identify this clip yet.**

Offer:

- Try another clip
- Use a longer excerpt
- Upload a clearer version
- Check your connection
- Submit feedback

Clearly distinguish:

- No reliable database match
- Unsupported media
- Temporary recognition failure
- Network failure

## 7.10 Search History

Allow authenticated users to:

- See previous recognitions
- Reopen results
- Save favorites
- Delete history
- Clear history
- Manage privacy settings

History must remain private.

## 7.11 User Profile

Support:

- Display name
- Profile image
- Email
- Subscription status
- Search usage
- Notification preferences
- Privacy preferences
- Account deletion
- Logout

## 7.12 Settings

Include:

- Appearance
- Language preference
- Notification preferences
- Storage and privacy
- Help and support
- Terms of service
- Privacy policy
- About FrameTrace

---

# 8. CORE MOBILE FEATURE — SHARE TO FRAMETRACE

This must be a high-priority feature.

FrameTrace should appear as an eligible share destination when compatible video content is shared through Android or iOS.

## Android

Implement Android share intent support for compatible:

- Video file URIs
- Video MIME types
- Supported text/URL payloads

Ensure that content URI permissions are handled correctly.

Never assume that a shared URI is a permanent accessible file.

Copy permitted temporary content into application-controlled storage when required.

## iOS

Investigate the current recommended native share-extension implementation.

The solution must comply with Apple's extension lifecycle and platform requirements.

Use App Groups or other approved shared-container mechanisms where required.

Do not assume experimental Expo share-target behavior is production-ready.

Implement a custom native extension or compatible maintained approach if necessary.

## Shared-content processing

When content arrives:

1. Validate the payload.
2. Determine whether it contains a video file, URL, or unsupported content.
3. Verify access to the underlying media.
4. Import permitted content.
5. Open the recognition preview.
6. Allow the user to confirm the search.
7. Begin upload only after confirmation.

## URL sharing

Social platforms may share only links.

Do not assume FrameTrace can download content from arbitrary platform URLs.

Create a provider adapter architecture for permitted sources.

Use approved APIs and authorized access.

For unsupported sources, inform the user and offer local video selection.

Never bypass platform security, DRM, authentication, or usage restrictions.

---

# 9. VIDEO RECOGNITION ENGINE

This is the application's core technology.

Build a real multimodal recognition system.

Do not implement a language-model prompt that guesses a title based on a few screenshots and calls it a verified result.

Use retrieval against an indexed reference catalog.

## 9.1 Video preprocessing

Implement:

- Secure media validation
- File metadata inspection
- FFprobe analysis
- Frame extraction
- Scene segmentation
- Audio extraction
- Video normalization
- Timestamp preservation
- Duplicate detection
- Processing cancellation
- Resource usage limits

Generate representative video frames with timestamps.

Configure frame sampling according to clip length and scene complexity.

## 9.2 Visual fingerprint matching

Implement visual fingerprints using suitable perceptual hashing algorithms.

Support:

- Exact scene matching
- Similar-frame matching
- Compressed video
- Downscaled footage
- Reframed video
- Cropped footage
- Letterboxing
- Overlaid text
- Watermarks

Recognize that perceptual hashes alone will not solve all these transformations.

Use additional visual embeddings or robust local matching where necessary.

## 9.3 Audio recognition

Implement audio fingerprint extraction.

The system should identify matching audio sequences from indexed reference recordings.

Support:

- Original audio
- Recompressed audio
- Clips with background noise
- Partial audio excerpts

Handle muted or replaced audio gracefully.

Never make audio matching mandatory for an otherwise valid visual match.

## 9.4 Speech recognition

Implement timestamped speech-to-text extraction.

Use dialogue matching as an additional retrieval signal.

Store normalized transcript segments for authorized reference videos.

Support punctuation normalization and approximate transcript matching.

Design for multilingual recognition in future versions.

## 9.5 OCR

Extract text from video frames when it may assist retrieval.

Potential signals:

- Subtitles
- Captions
- Channel logos
- Visible title cards
- On-screen quotations
- Event identifiers

Treat OCR evidence as supplementary, not definitive proof.

## 9.6 Multimodal embeddings

Implement an interface for generating video embeddings.

Evaluate a provider such as TwelveLabs.

Support:

- Video segment embeddings
- Visual similarity retrieval
- Semantic similarity retrieval
- Model version tracking
- Embedding regeneration
- Index versioning
- Provider fallback
- Cost monitoring

Keep the AI provider replaceable.

## 9.7 Candidate retrieval

Retrieve possible matches using:

- Frame fingerprints
- Audio fingerprints
- Vector similarity
- Transcript matching
- OCR matching

Combine candidates into a unified retrieval set.

Avoid unnecessary expensive model inference when a strong fingerprint match already exists.

## 9.8 Temporal verification

This component is mandatory.

For candidate reference videos:

1. Locate likely matching segments.
2. Compare consecutive video frames.
3. Estimate source offsets.
4. Compare corresponding audio where available.
5. Validate temporal consistency.
6. Reject unrelated similar-looking scenes.
7. Estimate the matching timestamp.

Return the matched start time and optional end time.

Record any uncertainty in temporal alignment.

## 9.9 Confidence and ranking

Develop an evidence-based ranking system.

Use:

- Visual matching strength
- Audio matching strength
- Transcript correspondence
- Temporal alignment
- Candidate separation
- Source quality

Initial scoring may use configurable heuristics.

Do not display numerical confidence percentages as probabilities without validation and calibration.

Support:

- Verified match
- Possible match
- Ambiguous candidates
- No reliable match

The definition of "verified" must be documented and based on tested evidence criteria.

## 9.10 Unknown-source recognition

Implement out-of-catalog detection.

The engine must know when it does not have sufficient evidence.

It is better to return "not found" than an incorrect confident identification.

---

# 10. REFERENCE MEDIA DATABASE

Recognition requires access to reference footage.

Build a reference media indexing system.

## Media catalog fields

Every indexed source should contain:

- Unique media ID
- Title
- Media category
- Description
- Original or authorized source URL
- Creator/publisher
- Release date
- Duration
- Language
- Reference file location
- Copyright/license information
- Authorization evidence
- Ingestion date
- Fingerprint version
- Embedding model version
- Searchable status

## Media segments

Divide source media into timestamped segments.

Store:

- Parent media ID
- Segment ID
- Start timestamp
- End timestamp
- Fingerprint references
- Embedding references
- Transcript references

All results must trace back to a valid source media record.

## Source attribution

Distinguish between:

- Original creator
- Publisher
- Distribution platform
- Earliest known indexed upload
- Verified rights holder
- Authorized viewing destination

Do not collapse all these fields into a single "original source" value.

---

# 11. DATA ACQUISITION STRATEGY

Create a legally sound, expandable media ingestion architecture.

## Initial dataset

Begin with:

- Developer-owned sample videos
- Creator-authorized recordings
- License-verified media
- Properly documented public-domain videos
- Approved synthetic test clips

Target an initial reference catalog of approximately 100–300 videos if feasible.

Generate evaluation excerpts from those references.

## Creator contribution system

Design future support for creators to contribute original content.

Features:

- Creator registration
- Channel/profile information
- Media submission
- Ownership declaration
- Licensing agreement
- Indexing authorization
- Attribution preferences
- Removal requests
- Usage analytics

Do not assume an uploader's ownership declaration alone conclusively establishes rights.

## External platform integrations

Create extensible adapters for supported providers.

Do not implement unauthorized scraping or automatic bulk downloading as the foundation of the product.

Follow applicable provider policies and copyright requirements.

## Rights and revocation

Every reference media item must have a documented rights status.

Support:

- Rights verification status
- License expiration
- Permission revocation
- Takedown requests
- Search-index removal
- Storage deletion where required
- Audit events

---

# 12. DATABASE SCHEMA

Design migrations and indexes for:

### Identity

- users
- profiles
- user_preferences
- account_roles

### Reference media

- creators
- media_assets
- media_sources
- media_rights
- media_segments
- media_fingerprints
- embedding_references
- media_transcripts

### Recognition

- recognition_jobs
- recognition_candidates
- recognition_results
- recognition_evidence
- recognition_feedback
- recognition_history

### Processing

- ingestion_jobs
- worker_events
- processing_errors
- model_versions
- index_versions

### Business

- usage_events
- search_quotas
- subscription_plans
- user_entitlements

### Security

- audit_logs
- deletion_requests
- rate_limit_events

Implement appropriate foreign keys, uniqueness constraints, indexes, and timestamps.

Use Row Level Security for exposed user-owned records.

Maintain server-side authorization for privileged operations.

---

# 13. BACKEND API

Create a versioned API.

## Recognition endpoints

```
POST   /v1/uploads
POST   /v1/recognitions
GET    /v1/recognitions/{id}
GET    /v1/recognitions/{id}/candidates
POST   /v1/recognitions/{id}/feedback
DELETE /v1/recognitions/{id}
```

## User endpoints

```
GET    /v1/profile
PATCH  /v1/profile
GET    /v1/history
DELETE /v1/history/{id}
GET    /v1/usage
DELETE /v1/account
```

## Administrative endpoints

```
POST   /v1/admin/media
GET    /v1/admin/media
POST   /v1/admin/media/{id}/index
POST   /v1/admin/media/{id}/revoke
GET    /v1/admin/ingestion-jobs
GET    /v1/admin/recognition-metrics
```

API responses must have consistent contracts.

Use typed error codes and validation.

Use pagination for collection endpoints.

Apply idempotency where needed.

Never expose administrative endpoints without backend authorization.

---

# 14. ASYNCHRONOUS RECOGNITION PROCESSING

Recognition must run asynchronously.

Define states:

```
CREATED
UPLOADING
UPLOADED
QUEUED
PREPROCESSING
RETRIEVING
VERIFYING
COMPLETED
FAILED
CANCELLED
EXPIRED
```

The mobile application must handle state transitions correctly.

Implement:

- Reliable queue dispatch
- Retry policies
- Worker timeouts
- Idempotent processing
- Dead-letter handling
- Job cancellation
- Error categorization
- Processing metrics

The app must not hang while awaiting a long-running recognition operation.

Use polling or a suitable push mechanism to retrieve job results.

---

# 15. MOBILE NETWORK RESILIENCE

FrameTrace must work gracefully on unreliable mobile connections.

Implement:

- Network-state awareness
- Interrupted upload recovery where supported
- Upload retry controls
- Server-side idempotency
- Upload integrity checks
- Short-lived upload credentials
- Cancellation
- Graceful connection errors

Consider resumable uploads if benchmarks justify them.

Use sensible compression or trimming before uploading.

Do not silently downgrade media to the point that recognition becomes unreliable.

The user should never lose a completed recognition result merely because they navigate away from the processing screen.

---

# 16. USER ACCOUNTS AND AUTHENTICATION

Implement:

- Guest recognition with abuse prevention
- Email/password authentication
- Google sign-in
- Apple sign-in on iOS where required or appropriate
- Session persistence
- Account recovery
- Logout
- Account deletion

Use platform-appropriate secure credential storage.

Verify OAuth redirect handling in native development and release builds.

Do not store service-role credentials in the mobile application.

Protect user history with authorization checks and database policies.

---

# 17. NOTIFICATIONS

Use appropriate push-notification infrastructure.

Support:

- Recognition completion
- Recognition failure when relevant
- Optional source discovery updates
- Account/security notices

Ask for notification permission contextually.

Do not require notification permission to identify videos.

Notifications must be deep-linked to the corresponding result.

Avoid exposing sensitive media details in notification previews.

Support notification opt-out and token cleanup.

---

# 18. PRIVACY AND SECURITY

Design security from the beginning.

## Mobile security

Implement:

- Secure authentication storage
- Session invalidation
- Deep-link validation
- Share-payload validation
- Minimum necessary device permissions
- Safe media cache handling
- Secure network communication
- No embedded backend secrets

## Backend security

Implement:

- JWT validation
- Ownership checks
- Role-based access control
- Rate limiting
- Abuse prevention
- Payload validation
- Database access restrictions
- Secure administrative actions
- Auditing

## Media security

All uploaded files are untrusted.

Use:

- Private object storage
- File-signature verification
- Decoder isolation
- Worker resource limits
- Video size/duration restrictions
- Processing timeouts
- Temporary storage expiration
- Controlled signed URLs
- Cleanup after failed processing

## Data retention

Default to short retention for raw user search clips, such as 24 hours.

Make retention configurable.

Provide delete-history and delete-account functionality.

Do not automatically add user query videos to the reference library.

## Legal and platform compliance

Review applicable:

- Apple App Store policies
- Google Play policies
- Copyright requirements
- Privacy laws
- Social-platform developer terms
- Third-party model provider terms

Do not implement DRM circumvention, unauthorized media downloading, or covert recording.

---

# 19. RECOGNITION BENCHMARK AND ACCURACY

Do not define success solely by whether the app displays a result.

Build a benchmark suite.

## Evaluation scenarios

Test:

1. Unmodified clip from indexed video.
2. Compressed clip.
3. Cropped clip.
4. Vertical-format excerpt.
5. Watermarked clip.
6. Clip containing captions.
7. Muted clip.
8. Clip with replaced audio.
9. Short dialogue excerpt.
10. Clip from an unindexed video.
11. Visually similar but incorrect video.
12. Repeated shots within the same recording.

## Required metrics

Measure:

- Top-1 accuracy
- Top-5 recall
- False-positive rate
- False-negative rate
- Out-of-catalog rejection
- Matching timestamp error
- P50 recognition latency
- P95 recognition latency
- Worker failure rate
- Cost per recognition
- Reference indexing throughput

Use a separate holdout dataset.

Do not tune on the same evaluation clips that are used for final accuracy claims.

## Proposed performance targets

Treat the following as engineering goals, not existing results:

- At least 90% top-1 recognition for clean, in-catalog benchmark clips.
- At least 80% top-1 recognition for defined edited in-catalog clips.
- At least 95% correct rejection of out-of-catalog benchmark clips.
- P95 completed recognition within approximately 15 seconds under defined benchmark conditions.
- Zero fabricated or unsupported confirmed source links.

Where these goals are not met, report actual measured performance and prioritized improvements.

---

# 20. ADMINISTRATION AND MEDIA OPERATIONS

Although the consumer product must be mobile-first, build a restricted administrative console.

This console may be a private web interface.

Required capabilities:

- Admin login
- Media catalog management
- Rights metadata
- Reference uploads
- Index generation
- Index health
- Reindexing
- Job monitoring
- Worker failure logs
- Recognition quality reports
- Cost metrics
- Media removal
- Administrative audit logs

Implement strict access control.

Do not expose this interface as the public consumer application.

---

# 21. PRODUCT ANALYTICS

Build privacy-conscious analytics.

Track:

- App installs and activation
- Recognition attempts
- Completed recognitions
- Recognized versus unrecognized clips
- Result feedback
- Search-to-source-open conversion
- Return usage
- Processing time
- App crashes
- Recognition costs

Avoid recording raw uploaded media or sensitive transcript content in ordinary analytics events.

Measure actual catalog coverage separately from recognition accuracy.

---

# 22. MONETIZATION ARCHITECTURE

Design for future monetization without introducing unnecessary payment complexity into the initial MVP.

Potential business models:

### Freemium

- Free daily searches
- Higher premium quotas
- Expanded history and saved results

### Pro creator tools

- Content attribution monitoring
- Media catalog management
- Source verification
- Reuse analytics

### Enterprise/API

- Recognition API
- High-volume matching
- Private media catalogs
- Usage-based billing

For native digital subscriptions, implement platform-compliant in-app purchases when monetization is introduced.

Do not add Stripe checkout inside the mobile app as a workaround for applicable store payment rules.

Do not implement billing until product value and recognition operating costs have been validated.

---

# 23. PERFORMANCE OPTIMIZATION

Optimize the complete system.

## Mobile

- Fast startup
- Smooth navigation
- Efficient media previews
- Controlled memory usage
- No unnecessary rerenders
- Minimal battery drain
- Lazy loading
- Appropriate image caching

## Backend

- Efficient frame sampling
- Candidate search pruning
- Adaptive matching
- Embedding caching where authorized
- Appropriate batch processing
- Efficient database indexes
- Worker concurrency control
- Query timeout protection

## Recognition

Use a staged pipeline:

1. Fast fingerprint search.
2. Candidate retrieval.
3. Multimodal similarity search if needed.
4. Temporal verification.
5. Confidence classification.
6. Final result generation.

Expensive analysis should operate on narrowed candidate sets whenever possible.

---

# 24. OFFLINE BEHAVIOR

Do not promise full offline recognition in the MVP.

When offline:

- Allow navigation through locally cached metadata where appropriate.
- Explain that recognition requires a connection.
- Preserve a selected clip temporarily when permitted.
- Allow retry after connectivity returns.
- Avoid automatic uploading without user consent.

Keep offline behavior predictable and privacy-conscious.

---

# 25. AUTOMATED TESTING

Build comprehensive test coverage.

## React Native

Use:

- Jest or an appropriate current test runner
- React Native Testing Library
- Mobile end-to-end test tooling such as Maestro or Detox where compatible

Test:

- Navigation
- File selection
- Upload validation
- Authentication
- Recognition status
- Results rendering
- Error handling
- Search history
- Account deletion

## Backend

Use pytest and integration testing.

Test:

- Authentication
- Authorization
- API validation
- Job lifecycle
- Worker retries
- Media ingestion
- Candidate ranking
- Temporal verification
- Database access policies

## Native integration tests

Test on real devices:

- Android shared video files
- Android content URIs
- iOS share extension
- Shared URLs
- App terminated/foreground handling
- Permission rejection
- Interrupted uploads
- App backgrounding
- Deep linking

## Security tests

Validate:

- Cross-user data isolation
- Unauthorized admin access
- Malformed media
- Excessive resource usage
- Unsupported files
- Replay/idempotency behavior
- Storage URL expiration
- URL ingestion restrictions
- Revoked reference media

---

# 26. CI/CD AND DEPLOYMENT

Configure:

- GitHub Actions
- TypeScript checks
- ESLint
- Formatting
- Automated tests
- Python linting/type checking
- Backend integration tests
- Docker image builds
- Dependency vulnerability scans
- Database migration verification

## Mobile builds

Set up:

- Expo EAS Build
- Android development builds
- Android internal testing builds
- iOS development builds
- iOS TestFlight builds
- Production build profiles

Use separate environment configurations for development, staging, and production.

Do not publish applications or modify live production systems without authorization.

Do not claim a signed release artifact exists until the build has completed and been verified.

---

# 27. BRANDING AND PRODUCT IDENTITY

Use FrameTrace as the working name.

Design a memorable identity centered around:

- Video frames
- Search and recognition
- Source discovery
- Motion
- Precision

Explore a distinctive symbol combining a video frame and an intelligent search mark.

The identity must remain recognizable at mobile app icon sizes.

Create:

- App icon
- Splash screen
- Wordmark
- Dark/light variations
- Design tokens
- Mobile navigation icons

Do not copy the Shazam brand or visual identity.

Use original artwork and properly licensed assets.

Verify name and trademark availability before public branding or store publication.

---

# 28. DEVELOPMENT ROADMAP

Work incrementally.

## PHASE 0 — Technical Discovery

Tasks:

- Audit the repository.
- Confirm versions and dependencies.
- Inspect available infrastructure.
- Establish system architecture.
- Create technical decision records.
- Set up local development.
- Define benchmark requirements.

Deliverable:

Architecture specification and executable development environment.

## PHASE 1 — Recognition Proof of Concept

Tasks:

- Prepare authorized reference videos.
- Extract video frames.
- Generate visual fingerprints.
- Implement basic candidate retrieval.
- Implement timestamp alignment.
- Evaluate known clips and negatives.

Deliverable:

A functioning local recognition engine that matches uploaded excerpts against indexed reference media.

## PHASE 2 — Backend and Indexing

Tasks:

- Create database migrations.
- Implement FastAPI.
- Configure storage.
- Implement ingestion workers.
- Implement recognition jobs.
- Add vector retrieval.
- Add audio matching.
- Add recognition metrics.

Deliverable:

An end-to-end functional recognition API.

## PHASE 3 — Native Mobile Application

Tasks:

- Scaffold Expo app.
- Implement design system.
- Build onboarding.
- Build home screen.
- Add video selection.
- Add video trimming.
- Connect backend.
- Render genuine recognition results.
- Add error and no-match states.

Deliverable:

Android and iOS development builds with a functioning upload-to-result experience.

## PHASE 4 — Native Sharing and Accounts

Tasks:

- Implement Android share handling.
- Implement supported iOS share extension.
- Add authentication.
- Add user history.
- Add saved results.
- Add notification integration.
- Implement privacy controls.

Deliverable:

A reliable mobile sharing and recognition workflow.

## PHASE 5 — Production Hardening

Tasks:

- Security review.
- Performance optimization.
- Media processing isolation.
- Error recovery.
- Automated test expansion.
- Monitoring.
- App crash analysis.
- Real-device QA.

Deliverable:

Release-candidate builds and an evidence-based quality report.

## PHASE 6 — Beta Launch

Tasks:

- Increase authorized reference catalog.
- Recruit early testers.
- Monitor recognition quality.
- Collect structured feedback.
- Evaluate catalog coverage.
- Analyze cost per search.
- Prioritize defects and improvements.

Deliverable:

A private beta with measurable recognition performance and user engagement.

---

# 29. ACCEPTANCE CRITERIA

The MVP is complete only when the following are demonstrated:

- Android application launches successfully.
- iOS application launches successfully on available test infrastructure.
- A user can select and preview a video.
- The selected clip can be securely uploaded.
- The backend creates a real recognition job.
- Real processing workers analyze the clip.
- The engine searches an actual reference index.
- Known clips can be matched to their reference videos.
- Matching timestamps are returned.
- Unknown clips can produce no-match results.
- The mobile interface displays actual results.
- Users cannot access other users' private records.
- Authorized media can be indexed and revoked.
- Failures produce useful and recoverable error messages.
- Tests and measurements are documented.
- The application can be built through configured Android and iOS workflows.

If an external service, credential, Apple provisioning step, or paid API is unavailable, clearly report the blocker and continue implementing independent components.

Never substitute simulated success for an uncompleted integration.

---

# 30. CODE QUALITY REQUIREMENTS

Enforce:

- Strict TypeScript
- Strong Python typing
- Modular architecture
- Small focused components
- Reusable UI primitives
- Explicit domain models
- Typed API contracts
- Structured error handling
- Predictable state management
- Unit and integration testing
- Secure secrets handling
- Meaningful documentation

Avoid unnecessary abstractions and overengineering.

Do not introduce new dependencies without evaluating their maintenance, compatibility, and security.

Prefer mature, well-supported packages.

---

# 31. DOCUMENTATION

Maintain:

- README.md
- ARCHITECTURE.md
- DEVELOPMENT.md
- RECOGNITION_ENGINE.md
- DATABASE_SCHEMA.md
- API.md
- SECURITY.md
- DATA_RIGHTS.md
- TESTING.md
- DEPLOYMENT.md
- MOBILE_RELEASE.md
- KNOWN_LIMITATIONS.md

Document the difference between completed functionality and planned functionality.

Maintain an implementation status checklist.

---

# 32. REQUIRED CODEX WORKFLOW

Follow this process:

### Step 1: Inspect

Inspect the existing repository and environment.

If the repository is empty, initialize the application.

### Step 2: Plan

Create an actionable implementation plan with phases, dependencies, acceptance criteria, and risks.

### Step 3: Build

Begin implementing the highest-priority foundation immediately.

Do not stop after generating the plan.

### Step 4: Test

Run relevant automated tests and report actual results.

### Step 5: Review

Review code changes for correctness, security, performance, and maintainability.

### Step 6: Report

At the end of each implementation stage, report:

- Features implemented
- Files changed
- Database migrations
- Tests executed
- Results obtained
- Known limitations
- External dependencies
- Remaining work

### Step 7: Continue

Proceed through the roadmap according to dependency order.

Do not repeatedly ask for minor design decisions that can be resolved using this specification.

Use sensible defaults, document decisions, and continue.

Request approval before destructive operations, paid-service purchases, production deployments, or other externally consequential actions.

---

# 33. CRITICAL ENGINEERING PRINCIPLES

1. FrameTrace is a native mobile product, not a wrapped website.
2. The recognition engine must perform genuine source retrieval.
3. An indexed source catalog is mandatory.
4. Source attribution must be evidence-based.
5. No-match results are a legitimate outcome.
6. Never fabricate confidence scores or source links.
7. Source licensing and media permissions must be tracked.
8. User videos must be private by default.
9. Mobile sharing must be tested on real devices.
10. AI providers must remain replaceable.
11. Recognition latency and costs must be measurable.
12. Backend processing must be asynchronous.
13. The interface must be polished but never compromise functional correctness.
14. Android and iOS must share the majority of application logic.
15. Native platform differences must be handled explicitly.
16. Security and privacy are core product requirements.
17. Tests must validate actual behavior, not merely mocked success.
18. Keep documentation accurate and current.
19. Prioritize search accuracy over superficial features.
20. Build the foundation for a scalable video recognition company.

---

# 34. FIRST EXECUTION INSTRUCTION

Start implementing FrameTrace now.

Your first objective is to demonstrate that the system can accurately identify a short video excerpt within an indexed reference recording.

Begin with the following tasks:

1. Inspect or create the repository.
2. Establish the monorepo architecture.
3. Configure Docker-based local development.
4. Set up the backend and database.
5. Build a small authorized reference dataset.
6. Implement video segmentation.
7. Implement visual fingerprints.
8. Implement fingerprint retrieval.
9. Implement temporal matching.
10. Build a basic benchmark.
11. Create the React Native mobile application foundation.
12. Connect a video upload to the working recognition service.

**Critical milestone:**

A user selects a real video clip on an Android or iOS device, uploads it, and receives the correct corresponding reference media and timestamp from a genuinely indexed database.

Once this milestone is demonstrated, expand the recognition engine, native sharing, premium interface, and production infrastructure according to the roadmap.

Do not stop at an attractive prototype.

Do not claim universal internet-wide video recognition without the catalog coverage to support it.

Build FrameTrace into a credible, secure, high-quality, mobile-first video discovery platform.

**The ultimate experience should be simple: Share a clip. Tap Identify. Discover its source.**

## Recommended execution approach

I would use the master brief above as the project's permanent engineering specification. Then instruct Codex to work through the phases sequentially, with the recognition proof of concept as the first major acceptance gate.

Important implementation priorities

Build Android and iOS from one codebase

React Native + Expo allows us to reuse most business logic, navigation, and UI while implementing native sharing where required.

Prove recognition before expanding the catalog

A small, functioning recognition engine will tell us more than thousands of lines of untested AI integration code.

Make native sharing the signature feature

The long-term goal is to let users send a compatible clip directly from another app into FrameTrace, without needing to manually navigate through multiple screens.

My recommendation: Start with the Android development build as the first device-validation target, then test the iOS build and native share extension early rather than leaving iOS integration until release.

The most valuable milestone is not publishing FrameTrace on an app store. It is proving that a real clip can be matched accurately to its source, with a reliable timestamp and a legitimate link to the original media.