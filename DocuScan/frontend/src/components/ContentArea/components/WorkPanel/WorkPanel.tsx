import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import { ErrorAlert } from "../../../ErrorAlert/ErrorAlert";
import { StatusAlert } from "../../../StatusAlert/StatusAlert";
import styles from "./WorkPanel.module.css";
import UploadArea from "../UploadArea/UploadArea";
import { ResultArea } from "../ResultArea/ResultArea";
import { isPdf } from "../../../../utils/isPdf";

export default function WorkPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>();
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const endpoint = import.meta.env.VITE_BACKEND_URL;
  /* const endpoint =
    "https://world.openfoodfacts.org/api/v2/search?fields=code,product_name,brands&page_size=20";*/

    const socket = io('http://127.0.0.1:5555/', {
    transports: ["websocket"],
       
      });
         
// to receive a websocket event
useEffect(()=>{
    socket.on('send_message', (data) => {
      console.log("socket - connected users:", data);
      // do stuff here
    })
     
    return function cleanup() {
      socket.disconnect();
    }
  },[socket])


  const handleFileSelected = (file: File | null) => {
    setResult(null);
    setError(null);
    if (!file) {
      setFile(null);
      return;
    }
    if (!isPdf(file)) {
      setFile(null);
      setError("Bitte nur PDF-Dateien hochladen.");
      return;
    }
    setFile(file);
  };

  const handleUpload = async () => {
    setError(null);
    setResult(null);
    if (!file) {
      setError("Bitte wähle eine PDF-Datei aus oder ziehe sie hierher.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
   
    try {
      setStatus("Datei ist hochgeladen, Dokument wird weiter verarbeitet..........");
      const res = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });
      // const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`Error HTTP: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err?.message ?? "Fehler beim Hochladen der Datei");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.wrapper} role="region" aria-label="Arbeitsbereich">
      <section className={styles.col} aria-label="PDF hochladen">
        <UploadArea
          selectedFile={file}
          accept="application/pdf"
          onFileSelected={handleFileSelected}
        />

        <div className={styles.actions}>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || loading}
            className={styles.submitBtn}
          >
            {loading ? "Wird hochgeladen..." : "Senden"}
          </button>
        </div>
         {error && <ErrorAlert message={error} />}
        {status && <StatusAlert statusmessage={status} />}
      </section>
      <section className={styles.col} aria-label="Ergebnis">
        <ResultArea data={result} />
      </section>
    </div>
  );
}
