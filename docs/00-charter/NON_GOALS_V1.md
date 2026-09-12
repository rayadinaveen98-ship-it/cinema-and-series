# V1 Non-Goals

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

The following are intentionally **not** V1 priorities unless a later frozen specification explicitly changes the decision.

## Consumer/social features deferred beyond V1

- social feed
- followers/following
- public community profiles
- comments/forums
- private messaging/chat
- influencer/creator network features
- user-generated news feed

## Opinion/recommendation features deferred beyond V1

- user reviews
- user ratings
- critic score aggregation
- recommendation engine
- AI-generated recommendations
- personality-based discovery
- ranking charts derived from user behavior

## Commerce/consumption features deferred beyond V1

- ticket purchasing
- streaming playback
- subscription bundling
- transactional VOD purchasing
- merchandise

## Advanced industry layers deferred beyond V1

- complete box-office accounting
- box-office forecasting
- production budgeting
- rights marketplace
- talent agency/representation database
- awards prediction
- industry CRM

## Newsroom deferred beyond V1

Cinema/series news may later become a separate product layer, but V1 should not let news workflows distort the canonical title/people/release data model.

## Explicit architectural non-goals

- building the product as a thin wrapper around one third-party movie API
- using any external provider's identifier as the canonical primary identity
- creating dozens of microservices before scale justifies them
- storing only final values without source history
- treating AI output as authoritative metadata
- scraping or republishing data simply because it is publicly viewable, without checking permissions/licensing/terms
- claiming literal 100% coverage of all films or series ever created

## Why these are deferred

V1 succeeds only if Cinema and Series first proves that it can reliably identify works, reconcile sources, preserve provenance, model releases and production state, search multilingual metadata, and expose data quality. Feature breadth before that foundation would make later corrections far more expensive.
