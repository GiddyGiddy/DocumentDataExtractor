import "dotenv/config";
import express from "express";
import cors from "cors";
import multer from "multer";
import OpenAI from "openai";
import schema from "./contracts/vollmacht.json";
import { rules } from "./prompts/system_contract_reglen";

// ---------- config ----------
const app = express();
app.use(cors({ origin: "http://localhost:5173" }));
app.use(express.json());

/** multer saves the file temporally in the RAM */
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 15 * 1024 * 1024 }, // 15MB
});

const AZURE_ENDPOINT = process.env.AZURE_ENDPOINT;
const AZURE_KEY = process.env.AZURE_KEY;
const AZURE_API_VERSION = process.env.AZURE_API_VERSION || "2024-11-30";
const DI_MODEL_ID = process.env.DI_MODEL_ID || "prebuilt-layout";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// ---------- helpers ----------
const sleep = (ms: any) => new Promise((r) => setTimeout(r, ms));

async function pollAnalyzeResult(
  opLocation: string,
  apiKey: string,
  { intervalMs = 1000, maxMs = 60000 } = {}
) {
  const start = Date.now();
  while (true) {
    const r = await fetch(opLocation, {
      headers: { "Ocp-Apim-Subscription-Key": apiKey },
    });
    if (!r.ok) {
      const body = await r.text();
      throw new Error(`Polling error ${r.status}: ${body}`);
    }
    const data = await r.json();
    const status = data.status?.toLowerCase?.();
    if (status === "succeeded") return data;
    if (status === "failed")
      throw new Error(`Analyze failed: ${JSON.stringify(data.error || data)}`);
    if (Date.now() - start > maxMs) throw new Error("Analyze timed out");
    await sleep(intervalMs);
  }
}

// ---------- endpoint ----------
app.post("/api/process-pdf", upload.single("file"), async (req, res) => {
  try {
    // Grundlegende Validierungen
    if (!req.file) return res.status(400).json({ error: "Datei fehlt" });
    if (req.file.mimetype !== "application/pdf")
      return res.status(415).json({ error: "Es werden nur PDFs akzeptiert" });
    if (!AZURE_ENDPOINT || !AZURE_KEY)
      return res.status(500).json({ error: "Azure-Anmeldedaten fehlen" });
    if (!process.env.OPENAI_API_KEY)
      return res.status(500).json({ error: "OPENAI_API_KEY fehlt" });

    // 1) Analyse bei Azure Document Intelligence starten (asynchron + Polling)
    const analyzeUrl = new URL(
      `${AZURE_ENDPOINT}/documentintelligence/documentModels/${DI_MODEL_ID}:analyze`
    );
    analyzeUrl.search = new URLSearchParams({
      _overload: "analyzeDocument",
      "api-version": AZURE_API_VERSION,
      outputContentFormat: "markdown",
      // stringIndexType: "utf16CodeUnit", // optional: Offsets kompatibel mit JS
      // features: "queryFields",                  // optional
      // queryFields: "Notar,Kunde,Vertragsdatum"  // optional für deine Verträge
    }).toString();

    const start = await fetch(analyzeUrl, {
      method: "POST",
      headers: {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        base64Source: req.file.buffer.toString("base64"),
      }),
    });

    if (start.status !== 202) {
      const body = await start.text();
      return res.status(502).json({
        error: "Azure hat die Anfrage nicht akzeptiert",
        details: body,
      });
    }

    const opLocation = start.headers.get("operation-location");
    if (!opLocation)
      return res
        .status(502)
        .json({ error: "Operation-Location fehlt in der Azure-Antwort" });

    const final = await pollAnalyzeResult(opLocation, AZURE_KEY);

    // 2) Konsolidierten Text übernehmen (bei prebuilt-layout ist es analyzeResult.content)
    const text = final?.analyzeResult?.content ?? "";

    // 3) Aufruf an OpenAI (SDK v6) mit der Responses API und JSON-Ausgabe
    //    (falls gewünscht, auf json_schema umstellen und strenges Schema definieren)
    const prompt = `${rules} Text: ${text}`;

    const ai = await openai.responses.create({
      model: "gpt-4o-mini",
      input: prompt,
      temperature: 0.2,
      text: {
        format: {
          type: "json_schema",
          name: "estructura_documento",
          strict: true,
          schema: schema,
        },
      },
    });

    // In v6 steht der vollständige Text in ai.output_text
    const jsonText = ai.output_text || "{}";
    let payload;
    try {
      payload = JSON.parse(jsonText);
    } catch {
      payload = { raw: jsonText }; // defensiver Fallback
    }

    return res.json(payload);
  } catch (err) {
    console.error(err);
    return res.status(500).json({
      error: "Fehler bei der Verarbeitung des PDFs",
      details: (err as Error)?.message ?? String(err),
    });
  }
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Backend hört auf http://localhost:${PORT}`);
});
