# Zoho form helper (userscript): spec draft for approval

Status: **DRAFT, 20 Sep 2026. Not approved; no code until the user approves.**
Source: open-questions answer Q7 (`/root/Open Questions 2026-09-19/README.md`); spec §17.2 step 4 and §17.5 in `CLAUDE.md`.

## 1. Goal

Senuri (SH Team 03) creates the Zoho sales order and picklist for every order Hazeem has released in the portal. Today she retypes the order: the customer, every item line with its quantity, the order type, the business unit, the invoice type and more. The helper fills those fields **on her screen, in her browser**. She checks them and clicks **Save** herself.

```
Portal (VPS)                          Senuri's browser                                 Zoho (SH org)
order OR-000123, Released ──GET──►  userscript panel on Zoho's "New Sales Order" page
                                     fills the form fields on screen ──────────────►  (nothing sent)
                                     Senuri checks, clicks Save ────────────────────►  sales order created by Senuri
Portal sync (read-only) ◄──────────────────────────── reads the new SO, matches "Portal Order No"
```

## 2. Hard rules (these are acceptance criteria)

1. **It never writes to Zoho by itself.** It never clicks Save, never submits a form, and never calls a Zoho API. Only the employee's own click saves.
2. **It runs only in the employee's browser.** No server-side Zoho writes, and no Zoho credentials anywhere in our software.
3. **It runs only on the SH org's sales-order and picklist create pages:** `@match https://inventory.zoho.com/app/843061977*`. It checks the page route before doing anything; any other page means no panel.
4. **One outbound call, a read:** `GET` of the released order from the portal over HTTPS (`@connect` = the portal host only), using the employee's own portal session. It shows only orders the employee's role may see.
5. **Nothing is typed from memory.** Any value it can't match exactly (customer, item, location) is left **empty and highlighted red** for Senuri to pick. It never picks the "closest" match.
6. **Undo is simple.** Leaving the page without saving discards everything. Nothing is stored in the browser except the last order number used.

## 3. Pages (to verify on the live page)

| # | Zoho page | Route (hash, SH org 843061977) | What the helper does |
|---|---|---|---|
| P1 | New Sales Order | `#/salesorders/new` *(to verify)* | Panel: "Fill from portal order", plus a list of Released orders waiting for Senuri. It fills the header fields and the item lines |
| P2 | New Picklist | `#/picklists/new` *(to verify)* | Nothing in version 1. Zoho builds the picklist from the saved SO; the panel only shows the portal order number as a cross-check |
| P3 | Sales Order view | `#/salesorders/{id}` | Read-only badge: "Linked to OR-000123", or "not linked" |

## 4. Fields filled on P1

The values below are from the 71,982 SH sales orders pulled on 19 Sep.

| Zoho field (API name) | Filled from the portal | Known values in SH data | Selector |
|---|---|---|---|
| Customer (`customer_id`) | portal customer → the Zoho customer id held by the mirror | — | TBC |
| Location (`location_id`) | the portal's SH location | Head Office 55,874 · South Branch 13,873 · Central Branch 2,235 (the only 3 with SOs) | TBC |
| Sales order date (`date`) | today | — | leave the Zoho default |
| Expected shipment date (`shipment_date`) | the portal's requested date | — | TBC |
| Reference# (`reference_number`) | **the customer's PO number** (it holds customer POs today, so we keep that meaning) | free text | TBC |
| **Portal Order No** (new custom field) | `OR-000123` | — | TBC, **admin action A1** |
| Business Unit (`cf_business_unit`) | portal | Packaging · Specialities · General · Manufacturing | TBC |
| Order Pick Type (`cf_order_pick_type`) | portal | Bulk · Retail · Key Customer · Sample · Freeport · Screen Processing · MTO · Export | TBC |
| Invoice Type (`cf_invoice_type`) | portal / customer default | VAT · Tax Inclusive · Sample Note · SVAT · Internal Transfers · Freeport · Inventory Loan … (the values carry a trailing space in Zoho; match exactly) | TBC |
| Urgent (`cf_urgent`) | portal | true / false | TBC |
| Created By (`cf_created_by`) | leave to Zoho / Senuri | — | none |
| Delivery method (`delivery_method`) | portal | DELIVERY · COLLECTION · Ex Work · VIA FREEPORT … | TBC |
| Salesperson (`salesperson_name`) | the portal placer, if they're a Zoho salesperson | — | TBC |
| Item lines: item, quantity, (rate) | portal lines → Zoho item ids | — | TBC |

**Rate:** by default the helper leaves Zoho's price-list rate alone and shows the portal's rate beside it when they differ. Pricing stays Zoho's job.

**Selectors (TBC).** They are captured from the live page after the browser is signed in again: open P1, read the DOM, don't save. They're recorded here with a screenshot before any code. Zoho's customer and item fields are search dropdowns, so filling them means typing the exact text and choosing the one exact match. If Zoho changes its page, the helper must fail loudly ("fields not found, fill by hand"), never half-fill.

## 5. Linking back

When Senuri saves, the portal's read-only Zoho sync finds the new SO by **Portal Order No** and moves the portal order to "SO created" with the SO number, recording who and when from Zoho's `created_time`/creator. No Zoho write is involved.

## 5b. Linking decision (user, 20 Sep)

- **Until SH admin access arrives:** Senuri pastes the Zoho SO number on the portal order (way B), and the portal checks that the number exists in the mirror.
- **After SH admin access arrives:** the "Portal Order No" custom field (A1) is created, and the sync links orders automatically (way A). The helper fills the field, so Senuri types nothing extra, and the paste step is removed. Pasted numbers stay as a fallback.
- **Never:** guessing from customer + date + lines (way C), because it links the wrong orders.

## 6. Fallback: the portal helper page (no extension)

If a browser extension isn't allowed on the office PCs, or Zoho's page defeats the selectors, the portal order page gets:
- **copy-to-field buttons** for each value above, including the item lines as "code × qty";
- a **deep link** to P1.

This needs no install and carries no risk to Zoho, so it's worth building first either way; the userscript is the upgrade.

## 7. Admin actions (the user)

- **A1.** Create a custom field on SH sales orders, "Portal Order No" (text, not mandatory). Until it exists, Senuri pastes the SO number on the portal order (§5b).
- **A2.** Allow Tampermonkey on Senuri's PC (and the backups').
- **A3.** Confirm the portal host name (for `@connect`).

## 8. Acceptance tests (before rollout)

1. On P1, filling from a Released order sets every mappable field; unmatched fields are empty and red. **No network request to Zoho is made by the script** (checked in DevTools).
2. The script is inert on every other Zoho page and on the SPS org.
3. Closing the page without Save creates no SO (checked in the Zoho SO list).
4. After Save, the portal shows "SO created" and the SO number within one sync cycle.
5. A changed Zoho page (a selector missing) shows "fill by hand" and fills nothing.

## 9. Open points for approval

- Userscript first, or helper page first? **Recommended: helper page first**, as it's zero-install; the userscript follows once the selectors are verified.
- Is the picklist (P2) left to Zoho in version 1? Recommended: yes.
- A1: create the "Portal Order No" custom field?
