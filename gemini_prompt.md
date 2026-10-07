You are an expert Indian Kirana retail data specialist. I have attached a photo of my daily sales handwritten notepad page.

The notepad is written in this tabular format:
- Top: Date (e.g., 07/10/2026 or 07 Oct)
- Columns: [sale no.]  [time]  [products quantity and size]  [total amount]  [weather]  [festival]

Your task is to transcribe, interpret, clean, and convert each sale entry into a structured JSON record.

### Parsing Guidelines:
1. "sale no." -> Customer bill/sale number (1, 2, 3...) used for customer basket grouping.
2. "time" -> Transcribe time (e.g., "8:30 AM", "6:15 PM"). Auto-classify into time_period: "Morning" (6AM-12PM), "Afternoon" (12PM-5PM), "Evening" (5PM-9PM), or "Night" (9PM onwards).
3. "products quantity and size" -> Split individual items in the customer's purchase:
   - Handle informal names ("amul taaza 500", "tata namak 1k", "cheeni 2kg", "3 maggi", "surf 500g", "2 sting").
   - Extract standardized name, quantity (count or weight), unit (packet, kg, bottle, piece), and pack size (e.g. 500ml, 1kg, 250ml).
4. "total amount" -> Extract the bill total amount (₹).
5. "weather" -> Transcribe the weather condition (e.g., Sunny, Rainy, Hot, Cold, Normal). If written once at the top, apply to all entries.
6. "festival" -> Transcribe the festival or occasion (e.g., None, Navratri, Diwali, Holi, Sunday Rush).

---

### Strict Output Format:
Return ONLY the following JSON structure:

```json
{
  "date": "YYYY-MM-DD",
  "day_weather": "Sunny | Rainy | Hot | Cold | Normal",
  "day_festival": "None | Navratri | Diwali | Holi | etc.",
  "sales": [
    {
      "sale_no": 1,
      "time": "08:30 AM",
      "time_period": "Morning | Afternoon | Evening | Night",
      "bill_total": 69.0,
      "weather": "Rainy",
      "festival": "None",
      "items": [
        {
          "raw_text": "2 amul taaza 500",
          "standardized_name": "Amul Taaza Milk 500ml",
          "category": "Dairy | Staples | Snacks | Beverages | Personal Care | Cleaning | Other",
          "quantity": 2,
          "unit": "packet",
          "pack_size": "500ml",
          "unit_price": 27.0,
          "line_total": 54.0
        },
        {
          "raw_text": "1 marie gold 120g",
          "standardized_name": "Britannia Marie Gold 120g",
          "category": "Snacks",
          "quantity": 1,
          "unit": "packet",
          "pack_size": "120g",
          "unit_price": 15.0,
          "line_total": 15.0
        }
      ]
    }
  ]
}
```
