# Response to Reviewers — Round 3

**Manuscript:** *Multi-Modal Expert Networks for Induction-Motor Fault Diagnosis and Remaining Useful Life Prediction: Real-Benchmark Validation and the Limits of Cross-Dataset Meta-Fusion*

**Prior decision:** Minor Revision (borderline Accept) · **Revised length:** 9 pages · **Template:** `conference-template-a4.docx` (verified identical page setup, section structure and IEEE styles)

---

## Response to the one substantive item

### 4.1 — RUL protocol parity (P1)

**Addressed honestly rather than asserted.** We checked our own evidence files before answering. Our stored baseline record (`results/publication_metrics/ims_literature_baselines.json`) documents dataset, method, year and error values for the cited works, but it records **no evaluation-horizon or RUL-clipping metadata for any baseline**, and re-running those methods under our protocol was not possible.

We therefore took the reviewer's second option and stated the caveat explicitly. §V-E now reads:

> "Protocol parity is stated explicitly because this comparison carries the paper's positive claim. Our figures use the final 30% of the 984-file 1st-test sequence under a chronological holdout — the final 99.4 h before failure — with MAE and RMSE in hours on the unclipped RUL target. Baseline figures are reproduced as reported in their source publications, which do not uniformly specify an identical horizon or RUL clipping, and re-running them under our protocol was not possible. The comparison is therefore indicative of competitive performance rather than strictly like-for-like, and the 57.8% and 28.4% improvements should be read with that caveat; matched-protocol re-evaluation is left to future work."

We did **not** claim parity we could not verify. The 28.4% figure is retained but explicitly bounded.

---

## Response to the remaining items

| Item | Where | Resolution |
|---|---|---|
| **4.2** "independently validated" vs the thermal expert | Abstract, §I contribution 1, §V-D, §VIII | Softened in all four places: "four are evaluated on real held-out partitions, whereas the thermal expert is validated on its training split only." |
| **4.3** Abstract "two" vs Introduction "four" contributions | Abstract, §I | Reconciled using the panel's suggested framing: the paper states **two** contributions, "comprising the following four specific items," so the existing numbered list is retained under the two themes. |
| **4.3** DT-PINN vs SA-PINN | §V-E, Abstract, §VIII, Table VII | Standardised on **SA-PINN**, which matches reference [26] (Liao et al., *self-attention-assisted* PINN, 2023). "DT-PINN" no longer appears anywhere. |
| **5** Abstract scoping line | Abstract, sentence 3 | Added verbatim in spirit: "We present the multi-modal fusion component as a cautionary study: on a corpus assembled across disjoint datasets the reported F1 = 0.9089 reflects label leakage, not fusion benefit, and should not be cited as a fusion result." |
| **5** Stray "A" in §III-C | §III-C | Removed — now "The physics-grounded IEC 60034-1 [38] scalar safety expert…". |
| **5** RUL dual-use | §V-E | Added: "The NASA data serve two distinct roles: the standalone benchmark evaluates the scalar RUL regression directly in hours, whereas within the fusion corpus the same model's RUL output is mapped to a three-state label via the Table I thresholds and enters the meta-feature vector only as one expert's probability vector." |
| **5** Equation typography/numbering | §III-C – §III-F | **Root cause found and fixed** (see below). |
| **5** Reference tidy | References | All 38 entries are cited in text (verified programmatically; max citation `[38]`, 38 entries). The digital-twin citations [33]–[37] remain cited in §II-E and were therefore kept. |
| Internal consistency | Table VII | "Li-HAGCN (Li 2022)" corrected to **(Li 2021)** to match reference [25]. |

### Equation numbering — root cause

The reviewer correctly observed that equation numbers appeared out of order. The cause was structural, not cosmetic: the numbers are floating text boxes, and **(5), (6), (7) carried a horizontal offset of −0.60 in and (8) −0.69 in**, placing them outside their own column, while a duplicate "(3)" existed. Each has been re-anchored to its own equation at +2.95 in (the column's right edge). The final PDF now carries exactly **(1)–(10), sequential, one per equation, none overlapping body text** — verified programmatically and visually.

---

## Two corrections we made on our own initiative

While preparing this round we found that our own Round-2 edit had silently damaged two paragraphs: prose had been written into an anchored equation-number box instead of the body text, which **deleted the body of §III-D's opening and the whole of §IV-B "Benchmark Datasets,"** and destroyed equation numbers (3), (4) and (8). Both sections have been fully restored, and this is very likely part of what the reviewer was seeing in the "equation numbering" item. We flag it here rather than let it pass silently.

---

## Template compliance

The revised manuscript was verified against `conference-template-a4.docx`:

- **Page size** 595.30 × 841.90 pt (A4) — match
- **Margins** T 54 / B 72 / L 44.65 / R 44.65 pt — match
- **Section structure** title (1-col) → author block (3-col ×2) → body (2-col, 18 pt gutter) — match
- **IEEE styles** `papertitle`, `Author`, `Abstract`, `Keywords`, `BodyText`, `Heading1`, `Heading2`, `tablehead`, `figurecaption`, `references` — all 10 identical in size and justification
- **Length** 9 pages

---

## Note to the panel

Thank you — the point about protocol parity was the right one to press. Checking it sent us back to our own evidence files, where we found that the horizon metadata for the cited baselines simply is not recorded. Rather than assert a parity we cannot demonstrate, we have stated exactly what our protocol is, what the baselines' provenance is, and what that means for the comparison. The RUL result stands on its own measurement; the ranking against prior work is now presented as indicative, with the matched-protocol study named as future work.
