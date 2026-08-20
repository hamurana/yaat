---
title: Your Valuation Is Wrong, So Demand a Discount
topic: Investment
date: 2026-03-06
description: "Every intrinsic value calculation you will ever do is wrong. That's not a criticism of the method — it's the reason the method includes a margin of safety. The discount isn't caution. It's an admission built into the arithmetic."
tags:
  - Margin of Safety
  - Owner Earnings
  - Terminal Value Sensitivity
  - Circle of Competence
draft: false
---

{{< lead >}}
Every intrinsic value calculation you will ever do is wrong. That's not a criticism of the method — it's the reason the method includes a margin of safety. The discount isn't caution. It's an admission built into the arithmetic.
{{< /lead >}}

### What the number is trying to be

Buffett's definition is unglamorous and precise: intrinsic value is *the present value of the cash that can be taken out of a business during its remaining life*. Three ideas packed into one sentence — all the future cash, when each piece of it arrives, and what that's worth in today's money.

The useful reframe is that a discounted cash flow model is a machine for turning a stock into a bond. A bond tells you exactly what it pays and when, printed on the certificate. A stock pays nothing on paper. So you estimate the payments and print them yourself, then discount them back the way you would with any bond.

That's the whole job. Everything else is choosing inputs.

### Running it once, end to end

Take a deliberately boring business — stable, predictable, the kind that doesn't need heroic assumptions.

**1. Find the owner's cash.** Buffett's measure is owner earnings: net income, plus non-cash charges, minus *maintenance* capital spending. There's a practical problem — companies report total capex, not the maintenance slice. The conservative workaround is to treat all of it as maintenance: free cash flow = operating cash flow − total capex. That understates the cash available to owners, which is the direction you want to be wrong in. Call it **$120M a year**.

**2. Pick a growth rate you'd defend to a sceptic.** A mature business growing roughly with the economy: **4%**.

**3. Project ten years** of that.

**4. Choose a discount rate** — the return you require to bother. **10%**.

**5. Discount each year back.** Later cash is worth less, so the present values shrink even while the nominal flows grow.

**6. Terminal value**, because the business doesn't evaporate in year eleven. Take year-10 free cash flow of about **$171M**, grow it at a modest **2%** forever, divide by (10% − 2%): roughly **$2.18B**. Discount that back ten years: about **$924M**.

**7. Add it up.** Ten years of discounted flows plus the discounted terminal value ≈ **$1.75B**.

Then the comparison that justifies the entire exercise. At a $2B market cap, it's expensive. At $1.75B, fair. At $1.1B, now you're interested.

### Where it's fragile, and why that matters

Look again at step six. The terminal value came out at $924M of a $1.75B total — **more than half the answer** comes from a single assumption about what happens after the period you actually modelled.

And that assumption is unstable. Nudge terminal growth from 2% to 3% and the denominator goes from 8% to 7%, lifting terminal value by roughly 14%. Move the discount rate from 10% to 9% and it moves far more. You can produce almost any valuation you like by adjusting two numbers nobody can check.

This isn't an argument against DCF. It's an argument for knowing which lever is carrying the weight, and it's the real reason the margin of safety exists. **Buffett's 30–40% discount to intrinsic value isn't timidity about the market — it's honesty about the model.** The output was never a number. It was a range, and the discount is how you buy insurance against being wrong inside it.

Two habits follow. Run the model at three sets of assumptions — pessimistic, base, optimistic — and treat the spread as the actual answer. And if you need optimistic inputs to make the price work, you've found your conclusion.

### The bits that aren't arithmetic

The method assumes you can forecast a decade of cash flow, which is only true for certain businesses. That's why the worked example is deliberately dull. A stable industrial company growing at 4% is forecastable. A company whose product may or may not exist in five years is not, and running a DCF on it produces a number with a false air of authority.

Hence the constraint that does more work than the maths: never invest in a business you cannot understand. Not modesty — a filter for the cases where the model means anything.

There's also a limit worth naming: the numbers can be false. Enron's fundamentals looked fine until the company didn't exist. A DCF built on fabricated cash flow returns a beautifully precise wrong answer, and no discount rate saves you from that.

### The uncomfortable closing note

If you do this properly, you will mostly find nothing worth buying.

Prices today are set largely by sentiment and growth expectations rather than by discounted cash flow, so genuinely undervalued businesses are rare, and the honest output of most valuations is "pass." That is the correct result, not a failure of the process — but it's why very few people who learn this method actually use it. Doing the work and then not buying feels like wasted effort. It's the entire discipline.

### So what to actually do

1. **Value one business you already own.** Seven steps, one afternoon.
2. **Use free cash flow = operating cash flow − total capex** and accept the understatement.
3. **Run three scenarios** and treat the spread as the answer.
4. **Check what share of your valuation is terminal value.** Over half means the answer rests on an assumption you can't test.
5. **Demand 30–40% below your estimate** before buying.
6. **Be prepared to conclude "no."** Most of the time that's the right call.

---

### Sources & further reading

- [Berkshire Hathaway shareholder letters — Warren Buffett](https://www.berkshirehathaway.com/letters/letters.html) — the primary source for owner earnings, intrinsic value, and the margin of safety as Buffett defines them.
- [The Profitability of Technical Analysis: A Review — Park & Irwin](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=603481) — useful contrast on how much harder it is to demonstrate an edge from price data than from business analysis.
