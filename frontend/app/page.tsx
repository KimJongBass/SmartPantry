"use client";

import { useRef, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [detections, setDetections] = useState<
  { name: string; confidence: number }[] | null
  >(null);
  // User's list with a present (yes/no) flag per item, returned by /predict
  const [pantry, setPantry] = useState<
  { id: number; name: string; present: boolean }[] | null
  >(null);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraActive(true);
      }
    } catch (error) {
      console.error("Error al acceder a la cámara:", error);
      alert("No se pudo acceder a la cámara. Revisa los permisos.");
    }
  }

  function captureImage() {
  const video = videoRef.current;

  if (!video || video.videoWidth === 0) {
    return;
  }

  const canvas = document.createElement("canvas");

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const context = canvas.getContext("2d");

  if (!context) {
    return;
  }

  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  setCapturedImage(canvas.toDataURL("image/jpeg", 0.9));
}


async function analyzeImage() {
  if (!capturedImage) {
    return;
  }

  try {
    const response = await fetch(capturedImage);
    const blob = await response.blob();

    const formData = new FormData();
    formData.append("file", blob, "pantry.jpg");

    const result = await fetch(`${API_URL}/predict`, {
      method: "POST",
      body: formData,
    });

    if (!result.ok) {
      throw new Error(`Error del servidor: ${result.status}`);
    }

    const data = await result.json();

    console.log("Respuesta de YOLO:", data);
    setDetections(data.detections);
    setPantry(data.pantry ?? null);
  } catch (error) {
    console.error("Error al analizar la imagen:", error);
    alert("No se pudo analizar la imagen. Revisa la consola del navegador.");
  }
}

  
return (
  <main className="min-h-screen bg-zinc-100 p-6 text-zinc-900">
    <h1 className="mb-6 text-3xl font-bold">Smart Pantry</h1>

    <div className="mx-auto max-w-2xl">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="w-full rounded-xl bg-black"
      />

      <button
        onClick={startCamera}
        disabled={cameraActive}
        className="mt-4 rounded-lg bg-green-700 px-5 py-3 text-white disabled:opacity-50"
      >
        {cameraActive ? "Cámara activada" : "Activar cámara"}
      </button>

      {cameraActive && (
        <button
          onClick={captureImage}
          className="ml-3 mt-4 rounded-lg bg-blue-700 px-5 py-3 text-white"
        >
          Capturar imagen
        </button>
      )}

      {capturedImage && (
        <div className="mt-6">
          <h2 className="mb-2 text-xl font-semibold">
            Imagen capturada
          </h2>
          <img
            src={capturedImage}
            alt="Captura de la despensa"
            className="w-full rounded-xl"
          />
        </div>
      )}
      
      {capturedImage && (
        <button
         onClick={analyzeImage}
         className="mt-4 rounded-lg bg-purple-700 px-5 py-3 text-white"
        >
         Analizar imagen
        </button>
      )}

      
      {detections && (
        <div className="mt-6 rounded-xl bg-white p-5 shadow">
        <h2 className="mb-3 text-xl font-bold">
        Objetos detectados
        </h2>

      {detections.length === 0 ? (
       <p>No se detectaron objetos.</p>
      ) : (
        <ul className="space-y-2">
          {detections.map((item, index) => (
          <li key={`${item.name}-${index}`}>
            {item.name} — {(item.confidence * 100).toFixed(1)}%
          </li>
        ))}
        </ul>
         )}
        </div>
        )}


      {pantry && (
        <div className="mt-6 rounded-xl bg-white p-5 shadow">
          <h2 className="mb-3 text-xl font-bold">
            Mi lista
          </h2>

          <ul className="space-y-2">
            {pantry.map((item) => (
              <li key={item.id} className="flex items-center justify-between">
                <span>{item.name}</span>
                <span
                  className={
                    item.present
                      ? "rounded-full bg-green-100 px-3 py-1 text-sm font-semibold text-green-800"
                      : "rounded-full bg-zinc-200 px-3 py-1 text-sm font-semibold text-zinc-600"
                  }
                >
                  {item.present ? "Sí hay" : "No hay"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  </main>
);

}