# ADR 0014: Relay authentication to gateways

**Status:** proposed

**Date:** 2026-10-15

**Deciders:** none seated; adoption is proposed in [CIP-0005](../cip/0005-phase-one-implementation.md)

## Context

The node design requires the gateway to accept job traffic only from a registered relay: a `NodeRegistry` relay record with `unlockAt == 0` whose operator is not this node's. The gateway row of docs/node/node-design.md §3 states the rule, states that a directly connecting client is refused even when its request is correctly encapsulated, and marks the mechanism by which a connecting relay proves that it is the registered operator UNVERIFIED and open. Open question 12 of the same document repeats that no mechanism is proposed and that the implementation CIP must define one before the node can enforce the rule. The configuration sketch fixes `require_registered_relay = true` as never configurable off. Until this record, the rule was a requirement with no way to meet it.

The relay record holds four fields, `(operator, endpoint, bondWei, unlockAt)`, and nothing that a transport could present as a credential. The functions are `registerRelay(string endpoint) payable`, `updateRelay(string endpoint)` and `deregisterRelay()`, and the events are `RelayRegistered(operator*, endpoint, bondWei)`, `RelayUpdated(operator*, endpoint)` and `RelayDeregistered(operator*, unlockAt)`. The function signatures are defined in [ADR 0011](0011-anonymous-credits.md), which carries every signature of the 23-function list, and transcribed by docs/protocol/contracts-and-settlement.md; the event fields are defined once, in docs/protocol/contracts-and-settlement.md §11. Any new field in the record, the functions or the events would therefore need a CIP that amends the contracts document.

The off-chain API fixes the rest of the setting. Section 3 says the client picks the relay at random from records with `unlockAt` zero and an operator different from the node's, fails closed with `relay_unavailable` when none exists, and offers no direct connection to the node endpoint. Before this proposal, the capability document was the only request without a sessionSigner. Under [ADR 0015](0015-node-key-possession.md), the capability document and the `key_probe` exchange are the only two such requests; both are served through a relay, only on a connection the gateway has authenticated under this record, and neither carries a client identifier. Open question 2 asks whether the client chooses a relay per request or per session; open question 7 asks how a relay that may serve any registered node is told the target gateway, and whether a relay may refuse some gateways. The spend's relay is checked on-chain: `openSessionFromCredit` binds `relay` into the proof message and reverts unless it is a registered, non-deregistering relay other than the node. A reconnect may come through a different relay (docs/node/node-design.md §6).

Two documents constrain the design further. The privacy document forbids any persistent client identifier at a relay, and its relay-transport section and [ADR 0010](0010-anonymous-by-default.md) both state that the relay already sees the target gateway, together with the client's network address, sizes and timing. Oblivious HTTP gives the relay the client's address but not the content, and the gateway the content but not the address, and requires relay and gateway to be run by different entities (evidence register §15, [V]); ADR 0010 adopts that rule and makes relays tunnel the client's RPC and indexer reads as well as its jobs. The node terminates TLS 1.3 itself (the HTTPS listener of docs/node/node-design.md §3) and its certificate authenticates the endpoint to relays, in that direction only.

The threat model has no row for an unregistered relay reaching the gateway or for a client that connects directly. T25 assumes a third party can open TLS to the node; T31 and T32 cover the same-address and two-address cases of a relay that is also the node; T37 covers timing correlation. Risk RR-40 covers relay-equals-node and Sybil registration only. The evidence register records no fact about relay-to-gateway authentication. The baseline's mutual TLS bound to operator keys (docs/review-report.md, KI-8) was a sharding transport, since replaced ([ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md), Context).

This record proposes the mechanism, answers open questions 2 and 7 of the off-chain API and open question 12 of the node design, and changes no contract. Nothing here is implemented, audited or deployed.

## Decision

**(1) Contracts unchanged.** The relay record `(operator, endpoint, bondWei, unlockAt)`, the functions `registerRelay`, `updateRelay` and `deregisterRelay`, and the events `RelayRegistered`, `RelayUpdated` and `RelayDeregistered` stay exactly as [ADR 0011](0011-anonymous-credits.md) carries them. No transport credential is registered on-chain. No CIP amendment of ADR 0011 or of the contracts document is needed for this record.

**(2) Identity: an off-chain EIP-712 credential signed by the operator key.** The connecting relay proves that it is the record's operator with the same Ethereum key that signed `registerRelay`, through typed data that touches no contract. The domain is `name = "Comuns RelayAuth"`, `version = "1"`, `chainId` the deployment's chain id (filled at deployment; the Arbitrum Sepolia chain id is UNVERIFIED in the documents and is written as an integer nowhere in this record), and `verifyingContract` the deployed `NodeRegistry` address. The contract never verifies these structures; naming it in the domain binds the credential to one deployment. Two typed structs:

- `RelayDelegation(address relayOperator, address delegateKey, uint64 notBefore, uint64 notAfter)`, signed offline by the operator key. It authorizes a secp256k1 key held by the relay process to connect on the operator's behalf during `[notBefore, notAfter]`.
- `RelayConnect(address relayOperator, address nodeOperator, bytes32 nodeEndpointHash, bytes32 nonce, uint64 expiresAt)`, signed by `delegateKey` for one connection.

A relay may use the operator key itself as `delegateKey` (self-delegation, with the delegation signed by the same key). The recommended operation keeps the operator key cold, signs delegations with a short `notAfter`, and lets the relay process hold only the delegate key. The credential's expiry is the delegation's `notAfter`.

**(3) The per-connection exchange.** On every TLS 1.3 connection from a relay, before anything else:

1. The gateway sends a challenge: a fresh 32-byte nonce from the OS CSPRNG, its own operator address (`nodeOperator`), `nodeEndpointHash = keccak256` of its registered endpoint string, an `expiresAt` no more than 60 seconds ahead, and the EIP-712 domain it expects, that is the deployment's `chainId` and the `NodeRegistry` address as `verifyingContract`, so that the relay has something to compare in the next step. The gateway binds the nonce to the TLS connection it was issued on and consumes it exactly once; a nonce presented on another connection, or presented twice, is refused.
2. The relay validates the challenge against the record it resolved before it signs anything. It checks five things: the TLS connection goes to the HTTPS origin of the endpoint it resolved from its own `NodeRegistry` view, for the node operator it selected; the challenge's `nodeOperator` equals that operator; `nodeEndpointHash` equals `keccak256` of that record's endpoint; the EIP-712 domain's `chainId` and `NodeRegistry` address equal its own deployment; and `expiresAt` is no more than 60 seconds ahead. If any check fails, the relay closes the connection with `gateway_challenge_mismatch` and signs nothing. This stops a gateway from relaying another gateway's challenge, and stops a credential for one deployment being harvested on another.
3. The relay answers with the `RelayDelegation` and its operator signature, and the `RelayConnect` signature by `delegateKey` over the challenge values.
4. The gateway accepts only when all of the following hold. It recovers both signatures under this deployment's own EIP-712 domain, never under a domain the relay supplies. `ecrecover` of the `RelayDelegation` signature yields `RelayDelegation.relayOperator`; `RelayDelegation.relayOperator == RelayConnect.relayOperator`, and that recovered address is the only relay identity the gateway uses; `relayOperator` has a relay record with `unlockAt == 0` in the gateway's own chain view; `relayOperator` is not this node's operator; the current time is within `[notBefore, notAfter]`; the `RelayConnect` signature recovers to `RelayDelegation.delegateKey`; the signed `nonce`, `nodeOperator`, `nodeEndpointHash` and `expiresAt` equal exactly what the gateway issued on this TLS connection, with `expiresAt` no more than 60 seconds ahead of the time of issue; the nonce is unused; and `expiresAt` has not passed.

Authentication lasts for that connection only, or until the delegation's `notAfter`, or until the gateway's chain view shows the relay deregistered (`RelayDeregistered`) or its endpoint changed (`RelayUpdated`), whichever comes first; the gateway then closes the connection and the relay reconnects with a fresh exchange. An unauthenticated connection receives nothing but the challenge: job envelopes, `credit_spend`, `hello`, vouchers, the capability document, the key probe of ADR 0015 and the public self-benchmark results are served only on an authenticated connection. The exchange is rate-limited per source address and carries no client data: nothing in it names a session, a nullifier, a `sessionSigner` or a client address, and the gateway records the relay operator address as a relay identity, never as or joined to a client identity, as the node design already requires.

Because the node process terminates TLS itself, no forwarded header, proxy protocol line or source address can establish identity; only the signatures do. TLS channel binding (a TLS exporter value in the signed struct) is not required by this record and is UNVERIFIED in the evidence register; the connection-bound, single-use nonce and the relay's own origin check are what tie the credential to the connection. Phase 1 supports externally owned operator accounts; a contract-wallet operator (ERC-1271 signature validation) cannot satisfy `ecrecover` and is deferred to [CIP-0005](../cip/0005-phase-one-implementation.md).

**(4) Granularity: per connection for the relay, per exchange for the client.** Authentication is per relay-gateway connection, as in (3); a relay keeps one authenticated connection, or a small pool, to each gateway it serves and multiplexes exchanges over it. Client relay choice is per OHTTP exchange: for each exchange the reference client draws uniformly at random among relay records with `unlockAt == 0` and operator different from the node's operator, which is the proposed resolution of off-chain open question 2 in favour of spreading one session's traffic across relays. The fee relay is the address bound into the credit spend and copied onto the session by `openSessionFromCredit`; it never changes for the life of the session, and it is paid the relay split whether or not later exchanges go through it. Reconnects through another registered relay stay allowed, as the node design already provides. When no eligible relay is available the client fails closed with `relay_unavailable` and never opens a direct connection.

**(5) Naming the gateway at the relay (off-chain open question 7).** The client addresses the relay as `POST {relay endpoint}/comuns/v1/gateway/{nodeOperatorAddress}`, with the OHTTP-encapsulated request as the body. The relay resolves the node's registered endpoint from its own `NodeRegistry` view, requiring `unlockAt == 0` and an operator different from the relay's own, and never accepts a client-supplied URL, host or port. It connects only over HTTPS to that registered endpoint, follows no redirects, refuses non-public destinations (loopback, link-local, private and otherwise non-routable addresses) and uses the authenticated connection of (3). A relay may refuse a gateway by its own policy; it answers with a distinct error, `gateway_refused`, and the client tries another relay for that exchange. A node operator address is public registry data, present in every `NodeRegistered` event and in the spend message, and is not a client identifier: the relay already sees the target gateway ([ADR 0010](0010-anonymous-by-default.md) (2); docs/security/privacy-and-contexts.md, relay transport), so naming it by operator address adds nothing the relay did not have.

**(6) What this record does not do.** Same-person operation of a relay and a node from two addresses remains the residual recorded in T32 and RR-40; this record adds no personhood or operator-identity check and does not claim one. It authenticates the registry role of the connecting party and nothing else.

## Alternatives considered

### A credential field in the relay record

Rejected. Adding a transport public key, certificate hash or similar field to the relay record changes the signatures of `registerRelay` and `updateRelay`, which [ADR 0011](0011-anonymous-credits.md) carries, and the `RelayRegistered` and `RelayUpdated` event layouts, which docs/protocol/contracts-and-settlement.md §11 defines; a new event field needs a CIP that amends the contracts document, the event-layout source, and the signature change needs the same CIP to amend ADR 0011. It adds nothing a signature by the operator key cannot give: the operator address is already the record's identity, and an operator who can sign `registerRelay` can sign a delegation. Rotating the field would also cost gas and a transaction per rotation, where an off-chain delegation with a short `notAfter` rotates for free.

### Mutual TLS with operator-bound certificates

Rejected. The baseline used mutual TLS bound to operator keys for the sharding transport (docs/review-report.md, KI-8), and [ADR 0003](0003-hpke-and-the-executor-plaintext-limit.md) records its replacement. Certificate issuance has no on-chain anchor: nothing in the registry says which certificate belongs to an operator, so the gateway would still need an operator signature over the certificate, which is this record's delegation under another name. Whether TLS client certificates carrying secp256k1 keys are supported by the TLS libraries the node and relay would use is UNVERIFIED in the evidence register, and the operator key would have to be either the certificate key or a signer over it.

### A signature per request

Rejected. Signing every OHTTP exchange with the delegate key costs a signature and a recovery per request on both sides for no privacy gain: the relay is a public registrant whose identity is not secret, and the exchange carries no client data either way. A per-connection credential bound to a single-use nonce authenticates the same party at a fraction of the cost. Nothing prevents a later record from adding per-request signatures if a need appears.

### Trusting the TCP source address or the endpoint string

Rejected. Anyone can connect to the gateway's public endpoint, and a source address proves nothing about who registered a record. Matching the connecting address to a DNS resolution of the registered endpoint string ties the check to DNS, shared hosting and address churn, is trivially defeated by any party that can reach the gateway from a shared address, and gives the node design's "registered relay" rule no cryptographic content.

### Locking transport to the fee relay for the whole session

Rejected. Binding every exchange of a session to the relay named in the spend would give that relay the session's full timing profile (off-chain open question 2, R8) and would make the fee relay's availability the session's availability. The node design already allows a reconnect through a different relay, and the fee split does not depend on which relay carries a given exchange. The fee relay stays fixed by the spend; transport does not.

## Consequences

- Open question 12 of docs/node/node-design.md, and open questions 2 and 7 of docs/protocol/off-chain-api.md, get a proposed resolution that points here; they are not closed, because nothing is adopted.
- The threat model gains a threat for an unregistered relay or direct client reaching the gateway (T46), and the risk register a row (RR-48) with a release gate, both added by other tasks of the same proposal; this record defines the mechanism they refer to.
- The relay binary needs a delegation tool that signs `RelayDelegation` with the operator key offline, and a key file for the delegate key with the same at-rest protection the node gives its HPKE secret; both go into the implementation CIP.
- Each exchange costs the client a fresh relay draw and a fresh OHTTP context; a relay that serves many gateways holds one authenticated connection per gateway and must re-authenticate when its delegation expires or its record changes.
- Conformance tests must include the negative cases: a direct client connection; an unregistered relay; a relay whose record has `unlockAt != 0`; a relay whose operator is the node's own operator; a replayed nonce, including one issued on another connection; an expired or not-yet-valid delegation; a challenge relayed from another gateway; a challenge whose domain carries a wrong `chainId`; a challenge whose domain carries a wrong `NodeRegistry` address; a `RelayDelegation` and `RelayConnect` whose `relayOperator` fields differ; and a `RelayConnect` whose `expiresAt` is far in the future or altered from the issued value. Each must be refused by the gateway or closed by the relay with `gateway_challenge_mismatch`.
- A contract-wallet operator cannot run a relay in Phase 1; ERC-1271 support is a [CIP-0005](../cip/0005-phase-one-implementation.md) item.
- TLS channel binding is left out and recorded as UNVERIFIED; a later record may add it to the signed struct without changing a contract.
- The two-address residual of T32 and RR-40 is unchanged.

## Links

- [docs/node/node-design.md](../node/node-design.md) §3 (gateway row), §6, §9 and open question 12
- [docs/protocol/off-chain-api.md](../protocol/off-chain-api.md) §3, §4 and open questions 2 and 7
- [ADR 0010](0010-anonymous-by-default.md)
- [ADR 0011](0011-anonymous-credits.md)
- [ADR 0015](0015-node-key-possession.md)
- [docs/protocol/contracts-and-settlement.md](../protocol/contracts-and-settlement.md) §5 relay record, §6 functions and §11 events
- [docs/security/privacy-and-contexts.md](../security/privacy-and-contexts.md) relay transport and the forbidden list
- [docs/security/threat-model.md](../security/threat-model.md) T25, T31, T32, T37
- [docs/evidence-register.md](../evidence-register.md) §15
- [CIP-0005](../cip/0005-phase-one-implementation.md)
