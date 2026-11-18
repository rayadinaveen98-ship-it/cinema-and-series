import { Hono } from 'hono';

type Bindings = { DATABASE_URL?: string };
const app = new Hono<{ Bindings: Bindings }>();

// Liveness is not database or catalogue readiness.
app.get('/v1/health', (c) => c.json({
  service: 'cinema-and-series-api',
  status: 'alive',
  catalogueReady: false,
}));

app.notFound((c) => c.json({ error: { code: 'NOT_FOUND', message: 'Route not found' } }, 404));
app.onError((_error, c) =>
  c.json({ error: { code: 'INTERNAL_ERROR', message: 'Unexpected service error' } }, 500)
);

export default app;
