import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputPath = "C:/Users/ritis/QUANT-T.Y.-Project/sample_data/monthly_bank_statement_upi.csv";

const rows = [
  ["tx_date", "description", "amount", "tx_type", "category"],
  ["2026-09-01", "Salary Credit - September", 120000, "credit", "SALARY"],
  ["2026-09-01", "UPI/P2P/ANJALI RENT SHARE", 18000, "debit", "RENT"],
  ["2026-09-02", "UPI/SWIGGY/ORDER 94721", 685, "debit", "FOOD"],
  ["2026-09-03", "UPI/BLINKIT/GROCERIES", 2340, "debit", "GROCERIES"],
  ["2026-09-04", "NEFT/HDFC HOME LOAN EMI", 18500, "debit", "LOAN_EMI"],
  ["2026-09-05", "UPI/UBER/LOCAL TRAVEL", 428, "debit", "TRANSPORT"],
  ["2026-09-06", "UPI/RAHUL/PERSONAL TRANSFER", 1500, "debit", "TRANSFER"],
  ["2026-09-07", "UPI/NETMEDS/PHARMACY", 1260, "debit", "HEALTHCARE"],
  ["2026-09-08", "UPI/IRCTC/TICKET BOOKING", 1845, "debit", "TRAVEL"],
  ["2026-09-09", "UPI/PVR CINEMAS/MOVIE", 920, "debit", "ENTERTAINMENT"],
  ["2026-09-10", "UPI/TATA POWER/ELECTRICITY", 2180, "debit", "UTILITIES"],
  ["2026-09-11", "UPI/JIO PREPAID/RECHARGE", 749, "debit", "MOBILE"],
  ["2026-09-12", "UPI/AMAZON/PURCHASE", 3299, "debit", "SHOPPING"],
  ["2026-09-13", "UPI/AMAZON/REFUND", 799, "credit", "REFUND"],
  ["2026-09-14", "UPI/ZOMATO/ORDER 32811", 575, "debit", "FOOD"],
  ["2026-09-15", "NACH/AXIS ELSS SIP", 5000, "debit", "ELSS"],
  ["2026-09-16", "UPI/DMART/GROCERIES", 3825, "debit", "GROCERIES"],
  ["2026-09-17", "ATM CASH WITHDRAWAL", 4000, "debit", "CASH_WITHDRAWAL"],
  ["2026-09-18", "UPI/DR MEHTA/CONSULTATION", 900, "debit", "HEALTHCARE"],
  ["2026-09-19", "UPI/BHARAT PETROLEUM/FUEL", 2800, "debit", "FUEL"],
  ["2026-09-20", "IMPS/FREELANCE PAYMENT", 12500, "credit", "FREELANCE"],
  ["2026-09-21", "UPI/NETFLIX/SUBSCRIPTION", 649, "debit", "ENTERTAINMENT"],
  ["2026-09-22", "UPI/LOCAL KIRANA/FOOD", 1185, "debit", "GROCERIES"],
  ["2026-09-23", "NACH/LIC PREMIUM", 12000, "debit", "LIC"],
  ["2026-09-24", "UPI/OLA CABS/RIDE", 365, "debit", "TRANSPORT"],
  ["2026-09-25", "UPI/P2P/NEHA DINNER SHARE", 850, "credit", "TRANSFER"],
  ["2026-09-26", "UPI/BOOKMYSHOW/EVENT", 1350, "debit", "ENTERTAINMENT"],
  ["2026-09-27", "NACH/PPF CONTRIBUTION", 5000, "debit", "PPF"],
  ["2026-09-28", "UPI/BIGBASKET/GROCERIES", 2140, "debit", "GROCERIES"],
  ["2026-09-29", "UPI/STARBUCKS/COFFEE", 410, "debit", "FOOD"],
  ["2026-09-30", "SAVINGS ACCOUNT INTEREST", 315, "credit", "INTEREST"],
];

const csvText = rows
  .map((row) => row.map((value) => {
    const text = String(value);
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }).join(","))
  .join("\n") + "\n";

const workbook = await Workbook.fromCSV(csvText, { sheetName: "Monthly Statement" });
const sheet = workbook.worksheets.getItem("Monthly Statement");
sheet.getRange("A:A").format.columnWidth = 14;
sheet.getRange("B:B").format.columnWidth = 38;
sheet.getRange("C:C").format.columnWidth = 12;
sheet.getRange("D:D").format.columnWidth = 10;
sheet.getRange("E:E").format.columnWidth = 20;
sheet.getRange("A1:E1").format.font = { bold: true };
const inspection = await workbook.inspect({
  kind: "table",
  range: "Monthly Statement!A1:E32",
  include: "values,formulas",
  tableMaxRows: 40,
  tableMaxCols: 6,
  maxChars: 12000,
});
console.log(inspection.ndjson);

const errorScan = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
});
console.log(errorScan.ndjson);

await fs.mkdir("C:/Users/ritis/QUANT-T.Y.-Project/sample_data", { recursive: true });
const preview = await workbook.render({ sheetName: "Monthly Statement", range: "A1:E32", scale: 1.2 });
await fs.writeFile("C:/Users/ritis/QUANT-T.Y.-Project/.artifact-tool/monthly_bank_statement_preview.png", new Uint8Array(await preview.arrayBuffer()));
await fs.writeFile(outputPath, csvText, "utf8");
console.log(`Saved ${outputPath}`);
