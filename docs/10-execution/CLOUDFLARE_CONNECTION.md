# Cloudflare Connection — Fast V1

Fast V1 can build and pass CI without any Cloudflare credentials. Production deployment requires exactly two GitHub Actions secrets:

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

Do not commit or paste the token into source files or chat transcripts.

The deployment workflow will:

1. detect whether those secrets exist;
2. find an existing D1 database named `cinema-and-series` or create it in the APAC region;
3. inject the D1 binding into the transient CI Wrangler configuration;
4. apply tracked migrations;
5. build the React/Vite application and Worker;
6. deploy to Cloudflare.

The token must be scoped to the account and have the minimum permissions necessary to create/use D1 and deploy the Worker. D1 creation requires `D1 Write`. The first creation of a new Worker may require broader Workers product permission than subsequent deployments; keep D1 and Workers scope only, rather than granting unrelated account access.
