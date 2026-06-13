# Channel Manager Integration — API & Architecture

## 1. API Comparison

### Channex API (v1)

| Aspect | Details |
|--------|---------|
| **Base URL** | `https://api.channex.io/v1/` |
| **Auth** | API Key in `Authorization` header |
| **Format** | REST JSON |
| **Rate Limits** | 20 ARI calls/min total |
| **Webhooks** | Booking events (create/update/cancel) |
| **Booking Feed** | Webhook (recommended) or polling (Booking Revision Feed) |

**Core Endpoints:**
- `GET /properties` — List properties
- `GET /properties/:id/room_types` — Room types
- `GET /properties/:id/rate_plans` — Rate plans
- `POST /properties/:id/availability` — Push ARI (availability/rates/inventory)
- `GET /properties/:id/bookings` — List bookings
- `POST /webhooks` — Register webhook endpoint

**Booking Statuses:**
`new` → `sent_to_pms` → `processed` → `rejected` / `expired`

---

### Beds24 API (v2)

| Aspect | Details |
|--------|---------|
| **Base URL** | `https://beds24.com/api/v2/` |
| **Auth** | OAuth2-like (invite code → refresh token → access token) |
| **Format** | REST JSON |
| **Rate Limits** | 100 credits/5min default (dynamic cost per request) |
| **Webhooks** | Booking events (alpha stage) |
| **Booking Feed** | Polling GET /bookings (recommended) |

**Core Endpoints:**
- `GET /properties` — List properties
- `GET /properties/{id}/rooms` — Room types
- `GET /properties/{id}/rateplans` — Rate plans
- `POST /properties/{id}/inventory` — Push prices/availability
- `GET /properties/{id}/bookings` — List bookings
- `POST /webhooks` — Register webhook (limited)

**Booking Statuses:**
`new` → `processed` → `rejected` / `cancelled`

---

## 2. Integration Sequence Diagrams

### 2.1 Property Sync (PMS → Channel Manager)

```
┌─────┐        ┌──────────┐        ┌─────────────┐        ┌──────┐
│ PMS │        │ CM Adapter│       │ Channel Mgr │        │ OTAs │
└──┬──┘        └─────┬─────┘        └──────┬──────┘        └──┬───┘
   │  create/update │                     │                   │
   │  property      │                     │                   │
   │───────────────>│  POST /properties   │                   │
   │                │────────────────────>│                   │
   │                │  200 OK {prop_id}   │                   │
   │                │<────────────────────│                   │
   │  sync rooms    │                     │                   │
   │───────────────>│  POST /prop/rooms   │                   │
   │                │────────────────────>│                   │
   │                │  200 OK             │                   │
   │                │<────────────────────│                   │
   │  sync rates    │                     │                   │
   │───────────────>│  POST /prop/rates   │                   │
   │                │────────────────────>│                   │
   │                │  200 OK             │                   │
   │                │<────────────────────│                   │
   │  success       │                     │                   │
   │<───────────────│                     │                   │
   │                │                     │  push to OTAs     │
   │                │                     │──────────────────>│
```

### 2.2 Availability/Rates/Inventory Push (Daily)

```
┌─────┐        ┌──────────┐        ┌─────────────┐
│ PMS │        │ CM Adapter│       │ Channel Mgr │
└──┬──┘        └─────┬─────┘        └──────┬──────┘
   │  ARI delta      │                     │
   │  (dates, rates, │                     │
   │   min_stay,     │                     │
   │   stop_sale)    │                     │
   │───────────────>│                     │
   │                 │  format for CM      │
   │                 │────────────────────>│
   │                 │  POST /availability │
   │                 │  or POST /inventory │
   │                 │<────────────────────│
   │  200 OK         │  200 OK             │
   │<───────────────│                     │
   │                 │                     │  broadcast to
   │                 │                     │  all connected
   │                 │                     │  OTAs
```

### 2.3 Incoming Booking (Channel Manager → PMS)

```
┌──────┐        ┌─────────────┐        ┌──────────┐        ┌─────┐
│ OTAs │        │ Channel Mgr │        │ CM Adapter│       │ PMS │
└──┬──┘        └──────┬──────┘        └─────┬─────┘        └──┬──┘
   │  guest books     │                     │                  │
   │  on Booking.com  │                     │                  │
   │─────────────────>│                     │                  │
   │                  │  webhook /          │                  │
   │                  │  polling detects    │                  │
   │                  │  new booking        │                  │
   │                  │────────────────────>│                  │
   │                  │                     │  transform to    │
   │                  │                     │  PMS format      │
   │                  │                     │─────────────────>│
   │                  │                     │  200 OK          │
   │                  │                     │<─────────────────│
   │                  │                     │                  │
   │                  │  ack booking        │                  │
   │                  │  (set status to     │                  │
   │                  │   sent_to_pms)      │                  │
   │                  │<────────────────────│                  │
   │  confirmed       │                     │                  │
   │<─────────────────│                     │                  │
```

### 2.4 Booking Modification / Cancellation

```
┌──────┐        ┌─────────────┐        ┌──────────┐        ┌─────┐
│ OTAs │        │ Channel Mgr │        │ CM Adapter│       │ PMS │
└──┬──┘        └──────┬──────┘        └─────┬─────┘        └──┬──┘
   │  guest modifies  │                     │                  │
   │  or cancels      │                     │                  │
   │─────────────────>│                     │                  │
   │                  │  webhook /          │                  │
   │                  │  polling detects    │                  │
   │                  │  change             │                  │
   │                  │────────────────────>│                  │
   │                  │                     │  update/create/  │
   │                  │                     │  cancel in PMS   │
   │                  │                     │─────────────────>│
   │                  │                     │  200 OK          │
   │                  │                     │<─────────────────│
   │                  │  ack                │                  │
   │                  │<────────────────────│                  │
   │  confirmed       │                     │                  │
   │<─────────────────│                     │                  │
```

---

## 3. Abstract Channel Manager Adapter

### 3.1 Domain Model

```
┌──────────────────────────────────────────────────────┐
│                 ChannelManagerPort                    │
│                 (Interface)                           │
├──────────────────────────────────────────────────────┤
│ + sync_property(property: Property) → SyncResult     │
│ + sync_ari(property_id, ari: ARI) → SyncResult       │
│ + fetch_bookings(property_id, since) → Booking[]     │
│ + acknowledge_booking(booking_id) → AckResult        │
│ + register_webhook(url: str) → WebhookConfig         │
│ + health_check() → HealthStatus                      │
└──────────────────┬───────────────────────────────────┘
                   │ implements
          ┌────────┴────────┐
          │                 │
┌─────────┴───────┐ ┌──────┴──────────┐
│  ChannexAdapter │ │  Beds24Adapter  │
│  (v1 REST)      │ │  (v2 REST)      │
└─────────────────┘ └─────────────────┘
```

### 3.2 Core Abstractions

```python
# Domain models

@dataclass
class Property:
    id: str                    # PMS property ID
    name: str
    address: str
    timezone: str
    rooms: list[RoomType]
    rate_plans: list[RatePlan]

@dataclass
class RoomType:
    id: str
    name: str
    max_occupancy: int
    quantity: int

@dataclass
class RatePlan:
    id: str
    name: str
    room_type_id: str
    currency: str

@dataclass
class ARI:
    """Availability, Rates, Inventory — delta update."""
    date: date
    room_type_id: str
    rate_plan_id: str
    available: int           # rooms available
    rate: Decimal            # nightly rate
    min_stay: int | None = None
    max_stay: int | None = None
    stop_sale: bool = False

@dataclass
class Booking:
    id: str
    cm_booking_id: str       # channel manager's booking ID
    channel: str             # "booking.com", "airbnb", etc.
    property_id: str
    room_type_id: str
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    total: Decimal
    status: BookingStatus    # new, confirmed, cancelled

# Port interface

class ChannelManagerPort(ABC):
    @abstractmethod
    def sync_property(self, property: Property) -> SyncResult:
        """Push property + rooms + rates to channel manager."""

    @abstractmethod
    def sync_ari(self, property_id: str, updates: list[ARI]) -> SyncResult:
        """Push availability/rates/inventory delta."""

    @abstractmethod
    def fetch_bookings(self, property_id: str, since: datetime) -> list[Booking]:
        """Pull new/modified bookings from channel manager."""

    @abstractmethod
    def acknowledge_booking(self, cm_booking_id: str) -> AckResult:
        """Mark booking as received by PMS."""

    @abstractmethod
    def register_webhook(self, callback_url: str) -> WebhookConfig:
        """Register webhook endpoint for real-time booking events."""

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Check API connectivity and auth validity."""
```

### 3.3 Channex Adapter

```python
class ChannexAdapter(ChannelManagerPort):
    BASE_URL = "https://api.channex.io/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers["Authorization"] = api_key
        self.rate_limiter = TokenBucket(max_tokens=20, refill_rate=20/60)

    def sync_property(self, property: Property) -> SyncResult:
        """Channex: POST /properties/{id}/room_types + /rate_plans"""
        self.rate_limiter.acquire()
        resp = self.session.post(
            f"{self.BASE_URL}/properties/{self._cm_property_id(property.id)}/room_types",
            json={"room_types": [self._map_room(r) for r in property.rooms]}
        )
        # ... handle response
        return SyncResult(success=resp.ok, ...)

    def sync_ari(self, property_id: str, updates: list[ARI]) -> SyncResult:
        """Channex: POST /properties/{id}/availability
        Rate limit: 20 calls/min total (not per property).
        """
        self.rate_limiter.acquire()  # respect 20/min
        payload = {
            "availability": [
                {
                    "date": u.date.isoformat(),
                    "room_type_id": self._map_room_type(u.room_type_id),
                    "available": u.available,
                    "rate": str(u.rate),
                    "min_stay": u.min_stay,
                    "stop_sale": u.stop_sale,
                }
                for u in updates
            ]
        }
        resp = self.session.post(
            f"{self.BASE_URL}/properties/{self._cm_property_id(property_id)}/availability",
            json=payload
        )
        return SyncResult(success=resp.ok, ...)

    def fetch_bookings(self, property_id: str, since: datetime) -> list[Booking]:
        """Channex: GET /properties/{id}/bookings?since=...
        Prefer webhook; polling is fallback.
        """
        resp = self.session.get(
            f"{self.BASE_URL}/properties/{self._cm_property_id(property_id)}/bookings",
            params={"since": since.isoformat()}
        )
        return [self._map_booking(b) for b in resp.json()["bookings"]]

    def _map_booking(self, raw: dict) -> Booking:
        """Map Channex booking → domain Booking."""
        return Booking(
            id=raw["id"],
            cm_booking_id=raw["id"],
            channel=raw["channel"],
            property_id=self._pms_property_id(raw["property_id"]),
            room_type_id=self._pms_room_type(raw["room_type_id"]),
            guest_name=raw["guest"]["name"],
            guest_email=raw["guest"]["email"],
            check_in=date.fromisoformat(raw["checkin"]),
            check_out=date.fromisoformat(raw["checkout"]),
            total=Decimal(raw["total"]),
            status=BookingStatus(raw["status"]),
        )
```

### 3.4 Beds24 Adapter

```python
class Beds24Adapter(ChannelManagerPort):
    BASE_URL = "https://beds24.com/api/v2"

    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
        self.access_token: str | None = None
        self.token_expires: datetime | None = None
        self.session = requests.Session()
        self._refresh_auth()

    def _refresh_auth(self):
        """OAuth2-like token refresh."""
        resp = requests.post(f"{self.BASE_URL}/authentication/token", json={
            "refreshToken": self.refresh_token
        })
        self.access_token = resp.json()["accessToken"]
        self.session.headers["Authorization"] = f"Bearer {self.access_token}"

    def sync_ari(self, property_id: str, updates: list[ARI]) -> SyncResult:
        """Beds24: POST /properties/{id}/inventory
        Dynamic rate cost per request.
        """
        # Beds24 uses inventory endpoint for availability + rates
        payload = {
            "inventory": [
                {
                    "roomId": self._map_room_type(u.room_type_id),
                    "date": u.date.isoformat(),
                    "price": str(u.rate),
                    "available": u.available,
                    "minStay": u.min_stay,
                    "stopSell": u.stop_sale,
                }
                for u in updates
            ]
        }
        resp = self.session.post(
            f"{self.BASE_URL}/properties/{self._cm_property_id(property_id)}/inventory",
            json=payload
        )
        return SyncResult(success=resp.ok, ...)

    def fetch_bookings(self, property_id: str, since: datetime) -> list[Booking]:
        """Beds24: GET /bookings?propertyId=...&modifiedSince=...
        Webhooks are alpha — prefer polling.
        """
        resp = self.session.get(
            f"{self.BASE_URL}/bookings",
            params={
                "propertyId": self._cm_property_id(property_id),
                "modifiedSince": since.isoformat(),
            }
        )
        return [self._map_booking(b) for b in resp.json()["bookings"]]
```

### 3.5 Adapter Factory

```python
class ChannelManagerFactory:
    """Create the right adapter based on configuration."""

    _registry: dict[str, type[ChannelManagerPort]] = {
        "channex": ChannexAdapter,
        "beds24": Beds24Adapter,
    }

    @classmethod
    def create(cls, cm_type: str, **credentials) -> ChannelManagerPort:
        adapter_cls = cls._registry.get(cm_type)
        if not adapter_cls:
            raise ValueError(f"Unknown channel manager: {cm_type}")
        return adapter_cls(**credentials)

    @classmethod
    def register(cls, name: str, adapter_cls: type[ChannelManagerPort]):
        """Register a new channel manager adapter at runtime."""
        cls._registry[name] = adapter_cls
```

### 3.6 Usage in PMS Service

```python
class ChannelSyncService:
    def __init__(self, adapter: ChannelManagerPort, pms_repo: PropertyRepository):
        self.adapter = adapter
        self.pms_repo = pms_repo

    def sync_property(self, property_id: str) -> SyncResult:
        property = self.pms_repo.get(property_id)
        return self.adapter.sync_property(property)

    def sync_ari_batch(self, property_id: str) -> SyncResult:
        """Push daily ARI delta to channel manager."""
        updates = self.pms_repo.get_ari_delta(property_id, since=last_sync)
        return self.adapter.sync_ari(property_id, updates)

    def poll_bookings(self, property_id: str) -> list[Booking]:
        """Pull new bookings (webhook fallback)."""
        bookings = self.adapter.fetch_bookings(property_id, since=last_poll)
        for b in bookings:
            self.pms_repo.create_booking(b)
            self.adapter.acknowledge_booking(b.cm_booking_id)
        return bookings

# Configuration (in config.yaml or env)
# CHANNEL_MANAGER=channex
# CHANNEX_API_KEY=xxx
# or
# CHANNEL_MANAGER=beds24
# BEDS24_REFRESH_TOKEN=xxx
```

---

## 4. Key Differences Summary

| Aspect | Channex | Beds24 |
|--------|---------|--------|
| **Auth** | API Key | OAuth2 token |
| **Rate Limit** | 20 ARI/min (hard) | 100 credits/5min (dynamic) |
| **Webhook Maturity** | Production-ready | Alpha |
| **Booking Feed** | Webhook preferred | Polling preferred |
| **Property Sync** | Separate endpoints per entity | Nested under property |
| **Certification** | 4-stage mandatory | None |
| **Cost** | Per-property flat fee | €15.50/mo + €0.55/channel |

### Adapter Behavior Matrix

| Operation | Channex | Beds24 | Abstraction |
|-----------|---------|--------|-------------|
| Auth | API Key header | OAuth2 token refresh | `__init__` + `_refresh_auth()` |
| Property push | `POST /properties` | `POST /properties` | `sync_property()` |
| Room types | `POST .../room_types` | `POST .../rooms` | Internal mapping |
| Rate plans | `POST .../rate_plans` | `POST .../rateplans` | Internal mapping |
| ARI push | `POST .../availability` | `POST .../inventory` | `sync_ari()` |
| Booking pull | `GET .../bookings` | `GET /bookings` | `fetch_bookings()` |
| Webhook | `POST /webhooks` | `POST /webhooks` (alpha) | `register_webhook()` |
| Ack booking | Set `sent_to_pms` status | N/A (auto) | `acknowledge_booking()` |
