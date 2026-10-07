# Kirana Daily Notepad Layout & Ingestion Specification
### Exact Column Layout, Field Definitions & AI Extraction Rules

---

## 📝 The Approved Notepad Table Format

Your notepad layout is structured as follows:

```text
Date: 07/10/2026

sale no. | time     | products quantity and size     | total amount | weather | festival
-----------------------------------------------------------------------------------------
1        | 08:15 AM | 2 amul taaza 500, 1 marie 120g | 69           | Rainy   | None
2        | 10:30 AM | 1 tea 250g, 2kg cheeni, 2 parle| 245          | Rainy   | None
3        | 01:20 PM | 1 aashirvaad 5k, 1 toor dal 1k | 400          | Rainy   | None
4        | 05:45 PM | 3 maggi 70g, 2 sting 250ml     | 82           | Rainy   | None
5        | 07:30 PM | 1 ghee 1L, 2kg cheeni, 1 besan | 755          | Pleasant| Navratri Day 1
```

---

## 🔍 How Each Column Powers the Analytics & Forecasting Engines

| Column | What You Write | How Our AI & Algorithms Use It |
| :--- | :--- | :--- |
| **Date** *(Top)* | `07/10/2026` or `07 Oct` | **Time-Series Tracking:** Anchors historical trends, month-over-month growth, and upcoming monthly forecasts. |
| **`sale no.`** | `1`, `2`, `3`... | **Customer Basket Grouping:** Informs the AI that all items on this line belong to the *same customer visit*. Unlocks **FP-Growth Co-Purchasing (Market Basket Analysis)** and true basket count. |
| **`time`** | `08:15 AM`, `06:30 PM` | **Hourly Rush & Meal-Time Shifts:** Classifies transactions into Morning (breakfast/milk), Afternoon (refreshments), Evening (snacks/dinner essentials), and Night runs. |
| **`products quantity and size`** | `2 amul taaza 500`<br>`3 maggi 70g`<br>`cheeni 2kg` | **SKU Velocity & Pack Preference:** Distinguishes between quantity sold and pack size. Fuzzy matcher automatically links informal Hinglish names to standard catalog products. |
| **`total amount`** | `69`, `82`, `755` | **Basket Spend & Revenue:** Computes average spend per visit and overall daily revenue. |
| **`weather`** | `Sunny`, `Rainy`, `Hot`, `Cold` | **Weather Demand Sensing:** Correlates weather spikes with surges in tea, instant noodles, and frying ingredients (Rainy) vs. cold drinks and dahi (Hot). |
| **`festival`** | `None`, `Navratri Day 1`, `Diwali Prep` | **Cultural Surge Forecaster:** Detects pre-festival hoarding and festive ingredient demand spikes (Ghee, Sugar, Besan, Fasting items). |

---

## 🤖 What Gemini Outputs from this Table

When you snap a photo of this table and run the prompt in [`kirana_gemini_prompt.md`](file:///C:/Users/ketan/kirana_gemini_prompt.md), Gemini returns:

```json
{
  "date": "2026-10-07",
  "day_weather": "Rainy",
  "day_festival": "None",
  "sales": [
    {
      "sale_no": 1,
      "time": "08:15 AM",
      "time_period": "Morning",
      "bill_total": 69.0,
      "weather": "Rainy",
      "festival": "None",
      "items": [
        {
          "raw_text": "2 amul taaza 500",
          "standardized_name": "Amul Taaza Milk 500ml",
          "category": "Dairy",
          "quantity": 2,
          "unit": "packet",
          "pack_size": "500ml",
          "unit_price": 27.0,
          "line_total": 54.0
        },
        {
          "raw_text": "1 marie 120g",
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

---

## 💡 Practical Counter Writing Tips

1. **Weather & Festival Shortcut:** If the weather or festival is the same for the entire day, you only need to write it **once at the top of the column** or in the header (e.g. `Date: 07/10 | Weather: Rainy | Festival: None`). You don't need to rewrite it on every single line!
2. **Products Shorthand:** Abbreviations are 100% fine (`taaza 500`, `namak 1k`, `maggi 3`, `tel 1L`).
3. **Price Omission:** If in a rush and you don't write individual item prices, just writing the line's `total amount` is enough—the system calculates the rest.
