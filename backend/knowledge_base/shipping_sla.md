# AETHER INDIA — Shipping & Delivery SLA Guide
**Document Version:** 2.3 | **Effective Date:** 1 August 2024

---

## 1. Overview

AETHER INDIA ships across all 28 states and 8 Union Territories of India through two premier logistics partners: **BlueDart** and **Delhivery**. This document details our shipping tiers, delivery timelines, tracking protocols, and escalation procedures.

---

## 2. Carrier Assignment Logic

| Delivery Zone | Primary Carrier | Fallback Carrier |
|---|---|---|
| Metro Cities (Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Kolkata, Pune, Ahmedabad) | **BlueDart** | Delhivery |
| Tier-2 Cities (Indore, Jaipur, Bhopal, Lucknow, Chandigarh, Coimbatore, Kochi, Nagpur, Surat) | **Delhivery** | BlueDart |
| Tier-3 & Semi-Urban Areas | **Delhivery** | Xpressbees |
| Remote / PIN-code restricted areas | **India Post Speed Post** | — |

---

## 3. Shipping Tiers & Pricing

| Tier | Description | Carrier | Estimated Delivery | Price |
|---|---|---|---|---|
| **Standard Shipping** | Default for all orders | Delhivery | 5–7 business days | **₹99** |
| **Express Shipping** | Priority handling + fast transit | BlueDart | 2–3 business days | **₹199** |
| **Same-Day Delivery** | Available in select metro areas only | BlueDart Dart Surfaceline | Within 24 hours | **₹499** |
| **Free Shipping** | Automatically applied | Based on zone | Same as Standard | **FREE** (on orders ≥ ₹1,999) |

> **Free Shipping Threshold:** All orders with a cart value of **₹1,999 or above** qualify for free Standard Shipping automatically. No coupon code required.

---

## 4. Delivery SLA by City & Zone

### Metro Cities (BlueDart — Express)
| City | Express SLA | Standard SLA |
|---|---|---|
| Mumbai (Maharashtra) | 1–2 business days | 3–4 business days |
| Delhi NCR (Delhi, Gurugram, Noida, Ghaziabad) | 1–2 business days | 3–4 business days |
| Bengaluru (Karnataka) | 1–2 business days | 4–5 business days |
| Chennai (Tamil Nadu) | 2–3 business days | 4–5 business days |
| Hyderabad (Telangana) | 2–3 business days | 4–5 business days |
| Kolkata (West Bengal) | 2–3 business days | 5–6 business days |
| Pune (Maharashtra) | 1–2 business days | 3–4 business days |
| Ahmedabad (Gujarat) | 2–3 business days | 4–5 business days |

### Tier-2 Cities (Delhivery — Standard)
| City | Standard SLA | Express Option |
|---|---|---|
| Indore (Madhya Pradesh) | 4–5 business days | 2–3 days (via BlueDart) |
| Jaipur (Rajasthan) | 4–5 business days | 2–3 days (via BlueDart) |
| Bhopal (Madhya Pradesh) | 5–6 business days | 3–4 days (via BlueDart) |
| Lucknow (Uttar Pradesh) | 4–5 business days | 2–3 days (via BlueDart) |
| Chandigarh (Punjab) | 3–4 business days | 2–3 days (via BlueDart) |
| Coimbatore (Tamil Nadu) | 5–6 business days | 3–4 days (via BlueDart) |
| Nagpur (Maharashtra) | 4–5 business days | 2–3 days (via BlueDart) |
| Kochi (Kerala) | 5–7 business days | 3–4 days (via BlueDart) |

### Remote Areas & North-East India
| Region | Carrier | Estimated SLA |
|---|---|---|
| North-East (Assam, Meghalaya, Manipur, Mizoram, Nagaland, Tripura, Arunachal Pradesh, Sikkim) | Delhivery | 7–10 business days |
| Jammu & Kashmir | Delhivery / India Post | 7–12 business days |
| Andaman & Nicobar Islands | India Post Speed Post | 10–15 business days |
| Lakshadweep | India Post Speed Post | 12–18 business days |

---

## 5. Order Processing Timelines

| Stage | Timeline |
|---|---|
| Order Confirmed | Immediate (same as placement) |
| Payment Verified (UPI/Card) | Within 15 minutes of payment |
| Payment Verified (COD) | At time of order placement |
| Packed & Dispatched | Within **1 business day** (Mon–Sat, cut-off at 2 PM IST) |
| Tracking Number Assigned | Within **2–4 hours** of dispatch |
| First Carrier Scan | Within **6–12 hours** of pickup |

> **Business Days:** Monday to Saturday. Orders placed after 2 PM IST on Saturday or on public holidays are processed on the next business day.

---

## 6. Live Order Status Definitions

| Status in System | Customer-Facing Meaning |
|---|---|
| **Processing** | Order confirmed; being picked and packed in our warehouse. |
| **Packed** | Item is packed and ready for pickup by the carrier. |
| **In Transit** | Carrier has picked up the parcel; it is moving through the logistics network. |
| **Out for Delivery** | Parcel is with the local delivery agent and will arrive today. |
| **Delivered** | Parcel has been handed to the customer or left at the designated safe location. |
| **Cancelled** | Order was cancelled before dispatch; refund/void initiated. |
| **Return in Transit** | Returned item is on its way back to AETHER's warehouse. |
| **Exchanged** | Replacement item has been dispatched under a new tracking number. |

---

## 7. Tracking Your Order

### Via AI Chat (Recommended)
Type: *"Track my order AETH-XXXX"* or *"Where is my order?"* and the `OrderAndInventoryAgent` will return:
- Current status in the AETHER system.
- Carrier name (BlueDart / Delhivery) and tracking number.
- Estimated delivery date.
- Last carrier scan location.

### Via Carrier Portals
| Carrier | Tracking URL |
|---|---|
| BlueDart | https://www.bluedart.com/tracking |
| Delhivery | https://www.delhivery.com/track |

### Via Email / SMS
Tracking updates are automatically sent:
- When order is **dispatched** (email + SMS).
- When order is **Out for Delivery** (SMS + WhatsApp if opted in).
- When order is **Delivered** (email).

---

## 8. Failed Delivery & Re-Delivery Policy

- **Missed Delivery:** If no one is available at the address, the carrier attempts delivery **up to 3 times** on consecutive business days.
- **After 3 Failed Attempts:** The parcel is returned to AETHER's warehouse. The customer is notified via email and chat.
- **Re-Delivery Fee:** ₹99 for re-dispatch of a returned-to-origin (RTO) parcel.
- **Undeliverable PIN Codes:** AETHER will proactively contact the customer before dispatch if the destination PIN code is flagged as non-serviceable.

---

## 9. Cancellation Policy (Shipping Stage)

| Order Status | Cancellation Permitted? | Notes |
|---|---|---|
| Processing | ✅ Yes | Full refund / void initiated immediately. Stock restored. |
| Packed | ✅ Yes | Carrier pickup intercepted; full refund initiated. Stock restored. |
| In Transit | ❌ No | Parcel is with carrier; cannot be recalled. Request return after delivery. |
| Delivered | ❌ No | Initiate a return or exchange instead. |

To cancel, ask the AI: *"Cancel my order AETH-XXXX"*. The `OrderAndInventoryAgent` will verify the status and process the cancellation if eligible.

---

## 10. Damaged in Transit

If your order arrives damaged:
1. **Take photos/videos** of the outer packaging and damaged product before opening further.
2. Report within **48 hours of delivery** via chat: *"My order AETH-XXXX arrived damaged"*.
3. AETHER will arrange a **free reverse pickup** and send a replacement or issue a full refund — your choice.
4. No return shipping fee applies for carrier-damaged items.

---

## 11. Holiday & Peak Season Delays

During high-traffic sales events (Diwali, Big Billion Days, Republic Day Sale), standard SLAs may extend by **2–3 additional business days**. Express shipping SLAs remain largely unaffected. Customers will be notified of any peak-season delays at checkout and via email.

---

## 12. Shipping Support Contacts

| Channel | Contact |
|---|---|
| AI Chat (24/7) | Available on platform — fastest route |
| Email | shipping@aether.in |
| BlueDart Customer Care | 1860-233-1234 (Mon–Sat, 9 AM – 6 PM IST) |
| Delhivery Customer Care | 011-4209-9910 (Mon–Sat, 9 AM – 7 PM IST) |
| WhatsApp | +91-98765-43210 (Mon–Sat, 10 AM – 7 PM IST) |

---

*AETHER INDIA Pvt. Ltd. is not liable for delays caused by natural disasters, government restrictions, carrier strikes, or force-majeure events. SLAs are estimates and not guaranteed delivery dates.*
