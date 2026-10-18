import test from "node:test";
import assert from "node:assert/strict";
import { releaseDateLabel, countryDisplayLabel } from "../src/media-presentation.ts";

test("Year-only source date must not claim an exact premiere day", () => {
  assert.equal(releaseDateLabel({ releaseDate: "2027-01-12", releaseYear: 2027, datePrecision: "year" }), "2027 · Exact date unconfirmed");
  assert.equal(releaseDateLabel({ releaseYear: 2030, datePrecision: "year" }), "2030 · Exact date unconfirmed");
  assert.equal(releaseDateLabel({ datePrecision: "year" }), "Release date unconfirmed");
});

test("Correctly sourced exact dates retain their day", () => {
  assert.equal(releaseDateLabel({ releaseDate: "2026-10-18", datePrecision: "day" }), "18 Oct 2026");
  assert.equal(releaseDateLabel({ releaseDate: "2028-02-29", datePrecision: "day" }), "29 Feb 2028");
});

test("Impossible dates and incomplete dates do not appear exact", () => {
  assert.equal(releaseDateLabel({ releaseDate: "2027-02-29", datePrecision: "day" }), "2027 · Exact date unconfirmed");
  assert.equal(releaseDateLabel({ releaseDate: "2027-13-41", datePrecision: "day" }), "2027 · Exact date unconfirmed");
  assert.equal(releaseDateLabel({ releaseDate: "2027-07", datePrecision: "day" }), "2027 · Exact date unconfirmed");
  assert.equal(releaseDateLabel({ releaseDate: "", datePrecision: "day" }), "Release date unconfirmed");
});

test("Unknown country is never misleadingly called Global", () => {
  assert.equal(countryDisplayLabel(undefined), "Country unknown");
  assert.equal(countryDisplayLabel(" ", { IN: "India" }), "Country unknown");
  assert.equal(countryDisplayLabel("IN", { IN: "India" }), "India");
  assert.equal(countryDisplayLabel("NZ", { IN: "India" }), "NZ");
});
