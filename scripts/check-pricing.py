#!/usr/bin/env python3
"""Check illustrative pricing arithmetic; read only, standard library only.

This is an accounting fixture checker, not an implementation of signatures,
contracts, model admission, or on-chain state transitions. No price is adopted.
Dollar results round half up to 12 decimals; multipliers to at most 4 decimals.
"""

import json
import re
import sys
import unicodedata
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path


MILLION = 1_000_000
CLASSES = ("S", "M", "L", "X")


def emit(line):
    """Print with control, format and separator characters made visible.

    Fixture ids and labels come from the JSON file, which a pull request can
    change; escaping keeps them from rewriting the terminal.
    """
    out = []
    for ch in str(line):
        if ch.isprintable() and unicodedata.category(ch) not in ("Cc", "Cf", "Zl", "Zp"):
            out.append(ch)
        elif ord(ch) < 0x100:
            out.append(f"\\x{ord(ch):02x}")
        elif ord(ch) < 0x10000:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(f"\\U{ord(ch):08x}")
    print("".join(out))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value):
    require(isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value),
            f"expected unsigned integer string, got {value!r}")
    return int(value)


def decimal(value):
    require(isinstance(value, str) and re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value),
            f"expected nonnegative decimal string, got {value!r}")
    return Decimal(value)


def equal(actual, expected, label):
    require(actual == expected, f"{label}: computed {actual}, expected {expected}")


def numerator(record, input_tokens=None, output_tokens=None):
    incoming = integer(record["inputTokens"]) if input_tokens is None else input_tokens
    outgoing = integer(record["outputTokens"]) if output_tokens is None else output_tokens
    return (integer(record["priceInPerMillion"]) * incoming
            + integer(record["priceOutPerMillion"]) * outgoing)


def payment(record, input_tokens=None, output_tokens=None):
    return numerator(record, input_tokens, output_tokens) // MILLION


def formula(fixture):
    quotient, remainder = divmod(numerator(fixture), MILLION)
    equal(quotient, integer(fixture["expectedWei"]), "paymentWei")
    equal(remainder, integer(fixture["expectedRemainder"]), "floor remainder")


def session(fixture):
    equal(len(fixture["jobs"]), integer(fixture["N"]), "prompt count")
    chunk_limit = integer(fixture["chunkTokens"])
    require(chunk_limit > 0, "chunk limit must be positive")
    incoming = outgoing = 0
    expected_counts = []
    partial_last_chunk = False
    for job in fixture["jobs"]:
        incoming += integer(job["promptTokens"]) + integer(job["grantedContextTokens"])
        expected_counts.append((incoming, outgoing))  # Input receipt before prefill.
        chunks = [integer(value) for value in job["outputChunks"]]
        for chunk in chunks:
            require(0 < chunk <= chunk_limit, "chunk exceeds fixture limit")
            outgoing += chunk
            expected_counts.append((incoming, outgoing))
        partial_last_chunk |= bool(chunks and chunks[-1] < chunk_limit)
    require(partial_last_chunk, "fixture must exercise a partial last chunk")
    expected_counts.append((incoming, outgoing))  # Separate closing voucher.
    equal(incoming, integer(fixture["expectedInputTokens"]), "cumulative input")
    equal(outgoing, integer(fixture["expectedOutputTokens"]), "cumulative output")
    equal(len(expected_counts), len(fixture["vouchers"]), "receipt/voucher cadence")
    deposit = integer(fixture["depositWei"])
    maximum = integer(fixture["maxSpendWei"])
    require(deposit <= maximum, "deposit exceeds maxSpendWei")
    cap = min(deposit, maximum)
    equal(cap, integer(fixture["expectedCapWei"]), "effective cap")
    settled = refund = last_seq = last_in = last_out = last_amount = 0
    closed = False
    for index, (voucher, counts) in enumerate(zip(fixture["vouchers"], expected_counts)):
        require(not closed, "voucher after settlement")
        seq = integer(voucher["seq"])
        require(seq > last_seq and (index != 0 or seq == 1), "invalid sequence")
        current_in = integer(voucher["inputTokens"])
        current_out = integer(voucher["outputTokens"])
        equal((current_in, current_out), counts, "receipt cumulative counts")
        amount = payment(fixture, current_in, current_out)
        equal(amount, integer(voucher["cumulativeWei"]), "cumulative voucher")
        require(current_in >= last_in and current_out >= last_out and amount >= last_amount,
                "voucher decreases a cumulative field")
        require(type(voucher["isFinal"]) is bool, "isFinal must be boolean")
        action = voucher["action"]
        require(action in ("sign", "redeemVoucher", "closeWithVoucher"), "unknown action")
        equal(voucher["isFinal"], action == "closeWithVoucher", "closing flag")
        payout = 0
        if action != "sign":
            payout = min(amount, cap) - settled
            require(payout >= 0, "negative incremental payout")
            settled += payout
        if action == "closeWithVoucher":
            refund = deposit - settled  # Uses the updated node credit.
            closed = True
        else:
            equal(refund, 0, "no refund before closing")
        equal(payout, integer(voucher["expectedPayoutWei"]), "incremental credit")
        require(settled <= cap, "effective cap exceeded")
        last_seq, last_in, last_out, last_amount = seq, current_in, current_out, amount
    require(closed, "fixture must settle")
    equal(settled, integer(fixture["expectedSettledWei"]), "settledWei")
    equal(refund, integer(fixture["expectedRefundWei"]), "refundWei")
    equal(settled + refund, deposit, "credited node + credited user conservation")
    equal(settled, min(payment(fixture, incoming, outgoing), cap), "cumulative cap")
    if fixture.get("expectOverCap"):
        require(last_amount > cap, "over-cap case did not exceed cap")


def credit_session(fixture):
    values = fixture["denominationsWei"]
    require(isinstance(values, list) and values, "denominationsWei must be a nonempty list")
    denominations = [integer(value) for value in values]
    require(denominations[0] > 0, "denominations must be positive")
    require(all(previous < current for previous, current in zip(denominations, denominations[1:])),
            "denominationsWei must be strictly increasing")
    denomination = integer(fixture["denominationWei"])
    require(denomination in denominations, "denominationWei must be listed in denominationsWei")
    owed = payment(fixture)
    settled = min(owed, denomination)
    pending = denomination - settled  # Recorded at settlement, before claimChange.
    dust = pending
    for value in reversed(denominations):
        dust %= value  # Greedy multi-note change, per ADR 0011; no adopted note limit.
    change = pending - dust  # Total face value of all minted change notes.
    relay = min(integer(fixture["relayFeeWei"]), settled)
    node_payout = settled - relay + dust
    for key, result in (
        ("expectedOwedWei", owed),
        ("expectedSettledWei", settled),
        ("expectedPendingWei", pending),
        ("expectedChangeWei", change),
        ("expectedDustWei", dust),
        ("expectedRelayWei", relay),
        ("expectedNodePayoutWei", node_payout),
    ):
        equal(result, integer(fixture[key]), key)
    equal((settled - relay) + relay + pending, denomination, "settlement conservation")
    equal(node_payout + relay + change, denomination, "node + relay + change conservation")
    require(dust < denominations[0], "dust must be below the smallest denomination")


def bands(fixture):
    require(fixture["tier"] in ("T0", "T1", "T2", "T3", "T4"), "unknown tier")
    equal(set(fixture["bands"]), set(CLASSES), "all four classes")
    previous = None
    for hardware_class in CLASSES:
        band = {key: integer(value) for key, value in fixture["bands"][hardware_class].items()}
        for side in ("In", "Out"):
            require(band["floor" + side] <= band["ceiling" + side], "inverted band")
            if previous is not None:
                require(band["floor" + side] > previous["ceiling" + side],
                        f"non-strict {side} ordering at {hardware_class}")
        previous = band
    outcomes = []
    for quote in fixture["quotes"]:
        # maxTier is informational: neither it nor a class-tier matrix gates a quote.
        band = fixture["bands"][quote["hardwareClass"]]
        accepted = all(integer(band["floor" + side]) <= integer(quote[price])
                       <= integer(band["ceiling" + side])
                       for side, price in (("In", "priceInPerMillion"),
                                           ("Out", "priceOutPerMillion")))
        require(type(quote["expectedAccepted"]) is bool, "acceptance must be boolean")
        equal(accepted, quote["expectedAccepted"], "quote acceptance")
        equal("inside-band" if accepted else "outside-band", quote["expectedReason"], "reason")
        outcomes.append(accepted)
    require(True in outcomes and False in outcomes, "need accepted and rejected quotes")


def operator(fixture):
    utilization = decimal(fixture["utilization"])
    throughput = decimal(fixture["tokensPerActiveSecond"])
    require(0 < utilization <= 1 and throughput > 0, "invalid utilization or throughput")
    require(fixture["throughputMode"] in ("single-stream", "batched"), "unknown throughput mode")
    if fixture["accounting"] == "owned":
        require("rentalDollarsPerHour" not in fixture, "owned/rented accounting mixed")
        kilowatts = decimal(fixture["activeWatts"]) / Decimal(1000)
        electricity = kilowatts * decimal(fixture["dollarsPerKWh"])
        equal(kilowatts, decimal(fixture["expectedActiveKilowatts"]), "watts / 1000")
        equal(electricity, decimal(fixture["expectedElectricityPerActiveHour"]), "active electricity")
        idle = decimal(fixture["idleWatts"]) / Decimal(1000) * decimal(fixture["dollarsPerKWh"])
        capital = decimal(fixture["acquisitionDollars"]) - decimal(fixture["residualDollars"])
        life = decimal(fixture["amortizationHours"])
        require(capital >= 0 and life > 0, "invalid amortization")
        hourly = utilization * electricity + (1 - utilization) * idle + capital / life
    else:
        equal(fixture["accounting"], "rented", "accounting method")
        require(not any(key in fixture for key in ("activeWatts", "idleWatts", "dollarsPerKWh",
                    "acquisitionDollars", "residualDollars", "amortizationHours")),
                "rental must not add owned electricity or amortization")
        hourly = decimal(fixture["rentalDollarsPerHour"])
    tokens_per_hour = throughput * Decimal(3600) * utilization
    cost = hourly * MILLION / tokens_per_hour
    equal(hourly, decimal(fixture["expectedCostPerPaidHour"]), "cost per paid hour")
    equal(tokens_per_hour, decimal(fixture["expectedTokensPerPaidHour"]), "tokens per paid hour")
    equal(cost.quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_UP),
          decimal(fixture["expectedDollarsPerMillion"]), "dollars per million")


def collective(fixture):
    k, prompt, answer, critique, synthesis = (integer(fixture[key]) for key in ("k", "P", "A", "C", "S"))
    equal(k, 3, "three answerers")
    equal(integer(fixture["reviewPasses"]), 2, "position-swapped review passes")
    records = fixture["sessions"]
    equal(len({record["sessionId"] for record in records}), len(records), "unique sessions")
    roles = {role: [record for record in records if record["role"] == role]
             for role in ("answerer", "reviewer", "synthesizer")}
    equal(tuple(len(roles[role]) for role in roles), (k, k, 1), "job counts")
    equal(len(records), 2 * k + 1, "session count")
    equal(len({record["node"] for record in roles["answerer"]}), k, "distinct answerer nodes")
    counts = {"answerer": (prompt, answer), "reviewer": (2 * (prompt + k * answer), critique),
              "synthesizer": (prompt + k * answer + k * critique, synthesis)}
    total = caps = total_in = total_out = 0
    for record in records:
        incoming, outgoing = counts[record["role"]]
        equal(integer(record["inputTokens"]), incoming, "per-session input")
        equal(integer(record["outputTokens"]), outgoing, "per-session output")
        amount = payment(record)  # Floor each session before summing.
        equal(amount, integer(record["expectedWei"]), record["sessionId"])
        cap = integer(record["capWei"])
        require(amount <= cap, "collective session exceeds its cap")
        total += amount
        caps += cap
        total_in += incoming
        total_out += outgoing
    equal(total, integer(fixture["expectedTotalWei"]), "collective total")
    equal(caps, integer(fixture["expectedSumCapsWei"]), "sum of session caps")
    require(caps <= integer(fixture["combinedCapWei"]), "combined cap exceeded")
    equal(total_in, integer(fixture["expectedInputTokens"]), "collective input")
    equal(total_out, integer(fixture["expectedOutputTokens"]), "collective output")
    equal(len(records), integer(fixture["expectedHappyPathTransactionPairs"]), "transaction pairs")
    baseline = fixture["baseline"]
    equal((integer(baseline["inputTokens"]), integer(baseline["outputTokens"])), (prompt, answer), "baseline counts")
    baseline_wei = payment(baseline)
    equal(baseline_wei, integer(baseline["expectedWei"]), "baseline payment")
    require(baseline_wei > 0, "baseline must have positive cost")
    multiplier = fixture["expectedMultiplier"]
    require(isinstance(multiplier, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]{1,4})?", multiplier),
            "multiplier must be a decimal string with at most 4 decimals")
    equal((Decimal(total) / Decimal(baseline_wei)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
          decimal(multiplier), "inference-only multiplier")


def amortization(fixture):
    prompt_cost = (integer(fixture["inputTokens"]) * decimal(fixture["dollarsInPerMillion"])
                   + integer(fixture["outputTokens"]) * decimal(fixture["dollarsOutPerMillion"])) / MILLION
    prompts = integer(fixture["prompts"])
    require(prompts > 0 and prompt_cost > 0, "positive prompts and price required")
    pair = 2 * decimal(fixture["transactionProxyDollars"])
    for key, result in (
        ("expectedInferencePerPromptDollars", prompt_cost),
        ("expectedTransactionPairDollars", pair),
        ("expectedSinglePromptGasRatio", pair / prompt_cost),
        ("expectedSessionInferenceDollars", prompts * prompt_cost),
        ("expectedGasPerPromptDollars", pair / prompts),
    ):
        equal(result, decimal(fixture[key]), key)


CHECKERS = {"formula": formula, "session": session, "bands": bands, "operator": operator,
            "collective": collective, "amortization": amortization, "credit_session": credit_session}


def reject_number(value):
    raise ValueError(f"JSON numbers must be strings: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    if len(sys.argv) > 2:
        emit("FAIL input: usage: check-pricing.py [pricing-examples.json]")
        return 1
    path = Path(sys.argv[1] if len(sys.argv) == 2 else "docs/economics/pricing-examples.json")
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream, parse_int=reject_number, parse_float=reject_number,
                             parse_constant=reject_number, object_pairs_hook=unique_object)
        require("FIXTURE — not an adopted price" in data["note"], "missing fixture warning")
        fixtures = data["fixtures"]
        require(isinstance(fixtures, list) and fixtures, "no fixtures")
        ids = [fixture["id"] for fixture in fixtures]
        equal(len(ids), len(set(ids)), "unique fixture ids")
        require({"class-S-on-T4-band", "collective-answer-three-answerers"}.issubset(ids),
                "required class-S-on-T4 or collective fixture missing")
        require(set(CHECKERS).issubset({fixture["kind"] for fixture in fixtures}), "missing fixture category")
    except (OSError, ValueError, KeyError, TypeError) as error:
        emit(f"FAIL input: {error}")
        return 1
    failures = 0
    for fixture in fixtures:
        try:
            with localcontext() as context:
                context.prec = 80
                CHECKERS[fixture["kind"]](fixture)
            emit(f"PASS {fixture['id']}")
        except (ValueError, KeyError, TypeError, ArithmeticError) as error:
            failures += 1
            emit(f"FAIL {fixture['id']}: {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
