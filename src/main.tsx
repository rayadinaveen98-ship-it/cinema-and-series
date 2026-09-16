import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import App from "./App";
import SeriesShelf from "./SeriesShelf";
import "./styles.css";
import "./artwork.css";
import "./detail.css";
import "./series.css";
import "./stream-cleanup.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
      <SeriesShelf />
    </BrowserRouter>
  </StrictMode>,
);
