You are an expert Indian Kirana retail data specialist. I have attached a photo of my daily sales handwritten notepad page. 

Your task is to transcribe, interpret, clean, and convert every line into a structured, standardized sales record.

### Parsing Guidelines:
1. Handle Kirana Abbreviations & Phonetic Names:
   - "amul t/taaza/gold 500" -> Amul Taaza / Amul Gold (Milk)
   - "tata namak / namak 1k" -> Tata Salt 1kg
   - "aashirvaad / aata 5k/10k" -> Aashirvaad Atta
   - "cheeni / sugar 2k 90" -> Loose Sugar, 2kg, Rs 90
   - "surf / surf excel 500g" -> Surf Excel Detergent
   - "maggi 4" -> Maggi 2-Minute Noodles (4 packets)
   - "thums up / thumsup 250ml" -> Thums Up Beverage
2. Quantities vs. Pack Sizes:
   - Differentiate carefully between quantity sold (e.g., 2 pieces) and pack size (e.g., 500g, 1kg, 200ml).
   - For loose commodities (grains, sugar, pulses), quantity is the weight in kg/grams.
3. Pricing & Calculations:
   - If unit price and quantity are given, calculate line total (Total = Qty * Unit Price).
   - If only a total amount is written (e.g., "oil 1L 145"), assign 145 as the total.
   - If price is missing or illegible, mark it as null.
4. Payment Mode & Notes:
   - Identify payment mentions: "UPI", "GPay", "PhonePe", "Paytm", "Cash", or "Khata / Udhar" with customer name.
   - If not mentioned on a line, mark payment_mode as "unspecified".
5. Illegible Text:
   - Do NOT invent items. If a word or number is scratched out or unreadable, flag it with "is_uncertain": true.

---

### Output Format:
Provide your response strictly in two sections:

#### Section 1: JSON Data Block (For Analytics Ingestion)
```json
{
  "date": "YYYY-MM-DD",
  "transactions": [
    {
      "raw_text": "Exact handwritten text snippet",
      "standardized_name": "Standard Brand & Product Name",
      "category": "Dairy | Staples | Snacks | Beverages | Personal Care | Cleaning | Other",
      "quantity": 1,
      "unit": "packet | piece | kg | g | litre | ml",
      "pack_size": "e.g., 500g, 1kg, 1L, or Standard",
      "unit_price": 0.0,
      "total_amount": 0.0,
      "payment_mode": "Cash | UPI | Khata | Unspecified",
      "customer_note": "Customer name if Khata, otherwise null",
      "is_uncertain": false
    }
  ]
}
```

#### Section 2: Quick Daily Summary (For My Immediate Review)
- Total Recorded Sales (₹)
- Payment Breakdown (Cash ₹ vs UPI ₹ vs Khata ₹)
- Top 3 Best-Selling Items by Volume
- Items requiring clarification (if any handwriting was hard to read)
