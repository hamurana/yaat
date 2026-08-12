---
title: Price Moves When Someone Stops Waiting
topic: Investment
date: 2026-01-08
description: "Price doesn't move because of news. It moves because somebody decided they'd waited long enough and accepted a worse deal. Every chart you've ever looked at is a record of who ran out of patience first."
tags:
  - Order Book Depth
  - Slippage
  - Liquidity Provision
  - Stop-Loss Cascade
  - Gap Risk
draft: false
---

{{< lead >}}
Price doesn't move because of news. It moves because somebody decided they'd waited long enough and accepted a worse deal. Every chart you've ever looked at is a record of who ran out of patience first.
{{< /lead >}}

### The order book is where price actually happens

Forget the chart for a moment and look at the thing underneath it.

On one side, buyers posting what they'll pay: top bid $99.95 for 200 shares. On the other, sellers posting what they'll accept: top ask $100.05 for 150 shares. Between them is the spread, and nothing happens in there, because nobody has agreed to anything.

The critical thing: **a price only exists at the instant a trade occurs.** Before that there are just two lists of conditional intentions. When someone accepts the $100.05 ask, that becomes the price — then the book resets and starts hunting for the next agreement.

Deeper levels tell you how much force it takes to move things. A thick book, with size stacked at every level, moves in small steps. A thin book moves in jumps, because there's nothing in between to absorb anything.

### Two order types, one trade-off

**A market order buys certainty and gives up price.** It says fill me now, at whatever's available. It works through the book — takes the best ask, then the next level, then the next, until it's done. The difference between the price you expected and the average you actually got is slippage. That's not a fee; it's your urgency meeting the limited supply that happened to be sitting there.

**A limit order buys price and gives up certainty.** You name a level and wait. It might not fill. It might fill partially if there isn't enough on the other side.

Neither is safe or reckless. They're opposite trades on the same axis.

There's a structural asymmetry worth knowing: market orders *take* liquidity and typically pay a fee for it, while limit orders *provide* liquidity and in many venues earn a small rebate. Your limit buy sitting at $9.90 is a wall of demand that absorbs selling pressure — you're supplying a service, and the market's plumbing is set up to pay you a sliver for it.

Queue position runs price first, then time. Earlier orders at the same price fill first.

### Where a market order genuinely hurts

Consider a thinly traded stock: a few shares at $10, nothing at $10.10, and the next sellers at $10.30.

A market buy takes the $10 and jumps straight to $10.30. You've paid 3% more than the last traded price and nothing went wrong — that's just what the book contained. The empty space is gap risk, and it's invisible on a chart, which will simply show a tick from $10 to $10.30 as though a decision was made.

The check takes ten seconds: look at volume and average volume before you trade. Higher volume means a thicker book and a market order that behaves the way you assumed it would.

The practical rule: **liquid stocks and big index ETFs, market orders are fine** — certainty is worth a cent. **Thin stocks, small caps, anything outside main trading hours, use a limit** and accept you might not get filled.

### Why crashes feel so sudden

This mechanism explains something charts never do.

A stop loss isn't resting in the book. It's dormant until price touches a level, at which point it converts into a **market order** — and market orders take whatever's available.

Stops cluster, because people put them in the same obvious places: under round numbers, under recent lows. So price drifts down into a cluster, dozens of stops fire simultaneously as market sells, they consume the resting bids, the consumption pushes price lower, the lower price triggers the next cluster, and so on.

Nothing happened. No news, no earnings, no change in any company's prospects. The structure of everyone's protective orders was itself the cause, and the people whose stops fired were, collectively, the sellers who caused the fall that triggered them.

Two things follow. Don't put your stop where everyone else put theirs — a round number is the worst available choice. And be sceptical of explanations offered for sharp intraday moves, because a good many of them are liquidity events that were narrated afterwards as though someone had decided something.

### So what to actually do

1. **Look at the order book once** on any broker that shows depth. Ten minutes changes how you read charts permanently.
2. **Check average volume before trading anything unfamiliar.**
3. **Market orders for liquid instruments, limit orders for thin ones.** That single rule covers most of it.
4. **Don't place stops at round numbers**, where everyone else's are waiting.
5. **When something moves violently for no reason, assume the book emptied** before assuming someone knew something.

---

### Sources & further reading

- [The Profitability of Technical Analysis: A Review — Park & Irwin](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=603481) — on how much of what looks like a pattern is transaction cost and market structure rather than signal.
- [Federal Funds Target Range — FRED, St. Louis Fed](https://fred.stlouisfed.org/series/DFEDTARU) — for the macro backdrop against which liquidity conditions tighten and loosen.
